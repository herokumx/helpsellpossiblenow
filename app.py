import os

import hashlib
from datetime import UTC, datetime
from urllib.parse import urlencode

from flask import Flask, Response, jsonify, redirect, render_template, request
from werkzeug.http import http_date

from src.db import get_engine, get_session
from src.ics import calendar_event_to_ics_event, render_calendar_ics
from src.models import CalendarEvent


def create_app() -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only")

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        # Force DB connectivity check
        with get_engine().connect() as conn:
            conn.exec_driver_sql("select 1")
        return jsonify({"ok": True})

    @app.get("/api/events")
    def list_events():
        with get_session() as session:
            events = (
                session.query(CalendarEvent)
                .order_by(CalendarEvent.start_at.asc().nullslast(), CalendarEvent.created_at.desc())
                .limit(200)
                .all()
            )
            return jsonify([e.to_dict() for e in events])

    @app.get("/calendar.ics")
    def public_calendar_ics():
        """
        Public, unauthenticated ICS feed of all events.
        """
        # Serve from a stable URL, but redirect to a versioned querystring to help
        # clients (notably Google Calendar) refresh when the feed changes.
        return _public_calendar_ics_impl(canonical=True)

    @app.get("/calendar/<slug>.ics")
    def public_calendar_ics_versioned(slug: str):
        """
        Versioned public ICS URL (cache-busting for clients that aggressively cache by URL).
        Example: /calendar/v2.ics
        """
        return _public_calendar_ics_impl(slug=slug)

    def _public_calendar_ics_impl(slug: str | None = None, canonical: bool = False):
        limit = request.args.get("limit", default=2000, type=int)
        limit = max(1, min(limit, 10000))
        with get_session() as session:
            rows = (
                session.query(CalendarEvent)
                .order_by(CalendarEvent.start_at.asc().nullslast(), CalendarEvent.created_at.desc())
                .limit(limit)
                .all()
            )
            # Strong validators to help caches / clients detect changes.
            newest = None
            for r in rows:
                if r.updated_at and (newest is None or r.updated_at > newest):
                    newest = r.updated_at
            newest = newest or datetime.now(UTC)
            etag_src = f"{len(rows)}:{newest.isoformat()}".encode("utf-8")
            etag = hashlib.sha256(etag_src).hexdigest()

            # Canonical URL cache-busting: if the version param is missing or stale,
            # redirect to /calendar.ics?v=<etag> (while keeping the user-facing URL stable).
            if canonical:
                v = request.args.get("v")
                if v != etag:
                    qs = request.args.to_dict(flat=True)
                    qs["v"] = etag
                    location = request.base_url + "?" + urlencode(qs)
                    resp = redirect(location, code=302)
                    resp.headers["Cache-Control"] = "no-store, max-age=0, must-revalidate"
                    resp.headers["Pragma"] = "no-cache"
                    resp.headers["Expires"] = "0"
                    return resp

            if request.headers.get("If-None-Match") == etag:
                return Response(status=304)

            ics = render_calendar_ics(calendar_event_to_ics_event(r) for r in rows)
            return Response(
                ics,
                status=200,
                content_type="text/calendar; charset=utf-8",
                # Some calendar clients cache/poll slowly; these headers encourage revalidation.
                headers={
                    "Cache-Control": "no-store, max-age=0, must-revalidate",
                    "Pragma": "no-cache",
                    "Expires": "0",
                    # Helps some clients keep a friendly name when doing one-time "import file" flows.
                    "Content-Disposition": 'inline; filename="PossibleNow Events.ics"',
                    "ETag": etag,
                    "Last-Modified": http_date(newest.timestamp()),
                },
            )

    @app.post("/api/events")
    def create_event():
        payload = request.get_json(force=True, silent=False) or {}
        with get_session() as session:
            event = CalendarEvent.from_dict(payload)
            session.add(event)
            session.commit()
            session.refresh(event)
            return jsonify(event.to_dict()), 201

    @app.get("/api/events/<event_id>")
    def get_event(event_id: str):
        with get_session() as session:
            event = session.get(CalendarEvent, event_id)
            if not event:
                return jsonify({"error": "not_found"}), 404
            return jsonify(event.to_dict())

    @app.patch("/api/events/<event_id>")
    def patch_event(event_id: str):
        payload = request.get_json(force=True, silent=False) or {}
        with get_session() as session:
            event = session.get(CalendarEvent, event_id)
            if not event:
                return jsonify({"error": "not_found"}), 404
            event.apply_patch(payload)
            session.commit()
            session.refresh(event)
            return jsonify(event.to_dict())

    @app.delete("/api/events/<event_id>")
    def delete_event(event_id: str):
        with get_session() as session:
            event = session.get(CalendarEvent, event_id)
            if not event:
                return jsonify({"error": "not_found"}), 404
            session.delete(event)
            session.commit()
            return "", 204

    return app


