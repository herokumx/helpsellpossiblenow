from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from typing import Iterable


def _escape_ical_text(value: str) -> str:
    # iCalendar TEXT escaping: backslash, semicolon, comma, newline
    # (see RFC 5545 §3.3.11)
    return (
        value.replace("\\", "\\\\")
        .replace(";", r"\;")
        .replace(",", r"\,")
        .replace("\r\n", r"\n")
        .replace("\n", r"\n")
        .replace("\r", r"\n")
    )


def _fold_ical_line(line: str, limit: int = 75) -> str:
    """
    Fold long lines per RFC 5545: insert CRLF + space. Limit is octets in spec;
    we approximate by characters (OK for typical ASCII output).
    """
    if len(line) <= limit:
        return line
    out = []
    while len(line) > limit:
        out.append(line[:limit])
        line = " " + line[limit:]
    out.append(line)
    return "\r\n".join(out)


def _fmt_dt_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def _fmt_date(d: date) -> str:
    return d.strftime("%Y%m%d")


@dataclass(frozen=True)
class IcsEvent:
    uid: str
    dtstamp: datetime
    dtstart: datetime | date
    dtend: datetime | date | None
    summary: str | None = None
    description: str | None = None
    location: str | None = None
    status: str | None = None
    transp: str | None = None
    url: str | None = None
    rrule: str | None = None


def render_calendar_ics(
    events: Iterable[IcsEvent],
    *,
    prodid: str = "-//HelpSellPossibleNow//Calendar//EN",
    calname: str = "PossibleNow Events",
) -> str:
    lines: list[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{prodid}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        # Many clients (Apple Calendar, Google Calendar import, etc.) use X-WR-CALNAME for display name.
        f"X-WR-CALNAME:{_escape_ical_text(calname)}",
        # RFC 7986 NAME property is supported by some clients as well.
        f"NAME:{_escape_ical_text(calname)}",
    ]

    for e in events:
        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{_escape_ical_text(e.uid)}")
        lines.append(f"DTSTAMP:{_fmt_dt_utc(e.dtstamp)}")

        if isinstance(e.dtstart, date) and not isinstance(e.dtstart, datetime):
            lines.append(f"DTSTART;VALUE=DATE:{_fmt_date(e.dtstart)}")
        else:
            lines.append(f"DTSTART:{_fmt_dt_utc(e.dtstart)}")

        if e.dtend is not None:
            if isinstance(e.dtend, date) and not isinstance(e.dtend, datetime):
                lines.append(f"DTEND;VALUE=DATE:{_fmt_date(e.dtend)}")
            else:
                lines.append(f"DTEND:{_fmt_dt_utc(e.dtend)}")

        if e.summary:
            lines.append(f"SUMMARY:{_escape_ical_text(e.summary)}")
        if e.description:
            lines.append(f"DESCRIPTION:{_escape_ical_text(e.description)}")
        if e.location:
            lines.append(f"LOCATION:{_escape_ical_text(e.location)}")
        if e.status:
            lines.append(f"STATUS:{_escape_ical_text(e.status).upper()}")
        if e.transp:
            lines.append(f"TRANSP:{_escape_ical_text(e.transp).upper()}")
        if e.url:
            lines.append(f"URL:{_escape_ical_text(e.url)}")
        if e.rrule:
            # Expect already like "FREQ=DAILY;..." (no "RRULE:" prefix)
            lines.append(f"RRULE:{_escape_ical_text(e.rrule)}")

        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold_ical_line(l) for l in lines) + "\r\n"


def calendar_event_to_ics_event(row) -> IcsEvent:
    """
    Map a src.models.CalendarEvent row to an ICS event.
    - Uses UTC date-times for DTSTART/DTEND.
    - For all-day events, uses DTSTART/DTEND as VALUE=DATE. DTEND is exclusive.
    """
    uid = row.ical_uid or str(row.id)
    dtstamp = row.updated_at or row.created_at or datetime.now(UTC)

    if row.is_all_day and row.start_at:
        start_d = row.start_at.date()
        if row.end_at:
            end_d = row.end_at.date()
        else:
            end_d = start_d + timedelta(days=1)

        return IcsEvent(
            uid=uid,
            dtstamp=dtstamp,
            dtstart=start_d,
            dtend=end_d,
            summary=row.title,
            description=row.description,
            location=row.location,
            status=row.status,
            transp=row.transparency,
            url=row.html_link or row.web_link,
            rrule=(row.recurrence_rules[0].removeprefix("RRULE:") if row.recurrence_rules else None),
        )

    return IcsEvent(
        uid=uid,
        dtstamp=dtstamp,
        dtstart=row.start_at or dtstamp,
        dtend=row.end_at,
        summary=row.title,
        description=row.description,
        location=row.location,
        status=row.status,
        transp=row.transparency,
        url=row.html_link or row.web_link,
        rrule=(row.recurrence_rules[0].removeprefix("RRULE:") if row.recurrence_rules else None),
    )


