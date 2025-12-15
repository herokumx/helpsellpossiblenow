import os

from flask import Flask, Response, jsonify, render_template, request

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
        limit = request.args.get("limit", default=2000, type=int)
        limit = max(1, min(limit, 10000))
        with get_session() as session:
            rows = (
                session.query(CalendarEvent)
                .order_by(CalendarEvent.start_at.asc().nullslast(), CalendarEvent.created_at.desc())
                .limit(limit)
                .all()
            )
            ics = render_calendar_ics(calendar_event_to_ics_event(r) for r in rows)
            return Response(
                ics,
                status=200,
                content_type="text/calendar; charset=utf-8",
                headers={"Cache-Control": "public, max-age=60"},
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


