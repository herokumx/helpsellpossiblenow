import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from zoneinfo import ZoneInfo


class Base(DeclarativeBase):
    pass


class CalendarEvent(Base):
    """
    A superset schema intended to capture fields from:
    - Google Calendar Events resource (incl. common "New event" fields)
    - Microsoft Graph / Outlook calendar event model

    Strategy:
    - Strongly-typed columns for common fields used for querying/sorting.
    - JSONB for nested/extended/provider-specific payloads to avoid loss.
    """

    __tablename__ = "calendar_events"

    # Identity
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[str | None] = mapped_column(String(32), nullable=True)  # "google" | "microsoft" | null
    external_id: Mapped[str | None] = mapped_column(String(256), nullable=True)  # provider event id
    ical_uid: Mapped[str | None] = mapped_column(String(512), nullable=True)  # iCalUID / iCalUId
    etag: Mapped[str | None] = mapped_column(String(256), nullable=True)  # Google etag
    change_key: Mapped[str | None] = mapped_column(String(256), nullable=True)  # Outlook changeKey

    # Core semantics
    title: Mapped[str | None] = mapped_column(String(1024), nullable=True)  # summary/subject
    description: Mapped[str | None] = mapped_column(Text, nullable=True)  # description/body.content
    description_content_type: Mapped[str | None] = mapped_column(String(32), nullable=True)  # "text" | "html"
    location: Mapped[str | None] = mapped_column(String(2048), nullable=True)  # display name
    location_details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)  # address/coords, MS locations[]

    # Time
    start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    start_timezone: Mapped[str | None] = mapped_column(String(128), nullable=True)
    end_timezone: Mapped[str | None] = mapped_column(String(128), nullable=True)
    is_all_day: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    original_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)  # Google originalStartTime

    # Status / visibility / availability
    status: Mapped[str | None] = mapped_column(String(64), nullable=True)  # confirmed/cancelled/tentative
    show_as: Mapped[str | None] = mapped_column(String(64), nullable=True)  # MS showAs: free/busy/tentative/oof/workingElsewhere/unknown
    transparency: Mapped[str | None] = mapped_column(String(32), nullable=True)  # Google transparency: opaque/transparent
    visibility: Mapped[str | None] = mapped_column(String(32), nullable=True)  # Google visibility: default/public/private/confidential
    sensitivity: Mapped[str | None] = mapped_column(String(32), nullable=True)  # MS sensitivity: normal/personal/private/confidential

    # Importance & flags
    importance: Mapped[str | None] = mapped_column(String(16), nullable=True)  # MS importance: low/normal/high
    is_cancelled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_draft: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_online_meeting: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # People
    organizer: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    creator: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    attendees: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)  # array of attendees

    # Recurrence
    recurrence_rules: Mapped[list[str] | None] = mapped_column(ARRAY(Text), nullable=True)  # RRULE-like strings
    recurrence: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)  # MS recurrence object / Google recurrence[] details
    series_master_id: Mapped[str | None] = mapped_column(String(256), nullable=True)  # MS seriesMasterId

    # Reminders / notifications
    reminders_use_default: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    reminder_minutes_before_start: Mapped[int | None] = mapped_column(Integer, nullable=True)  # MS reminderMinutesBeforeStart
    is_reminder_on: Mapped[bool | None] = mapped_column(Boolean, nullable=True)  # MS isReminderOn
    reminders: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)  # Google reminders overrides

    # Conferencing / meeting links
    online_meeting_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)  # MS onlineMeeting.joinUrl
    hangout_link: Mapped[str | None] = mapped_column(String(2048), nullable=True)  # Google hangoutLink
    conference_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)  # Google conferenceData / MS onlineMeeting

    # Links / source
    html_link: Mapped[str | None] = mapped_column(String(2048), nullable=True)  # Google htmlLink
    web_link: Mapped[str | None] = mapped_column(String(2048), nullable=True)  # MS webLink
    source: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)  # Google source

    # Classification / appearance
    color_id: Mapped[str | None] = mapped_column(String(32), nullable=True)  # Google colorId
    categories: Mapped[list[str] | None] = mapped_column(ARRAY(String(256)), nullable=True)  # MS categories

    # Attachments
    attachments: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB, nullable=True)  # Google attachments / MS attachments

    # Extended/provider-specific raw fields
    google: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    microsoft: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    extended_properties: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)  # Google extendedProperties

    # Audit
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    provider_created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "provider": self.provider,
            "external_id": self.external_id,
            "ical_uid": self.ical_uid,
            "etag": self.etag,
            "change_key": self.change_key,
            "title": self.title,
            "description": self.description,
            "description_content_type": self.description_content_type,
            "location": self.location,
            "location_details": self.location_details,
            "start_at": self.start_at.isoformat() if self.start_at else None,
            "end_at": self.end_at.isoformat() if self.end_at else None,
            "start_timezone": self.start_timezone,
            "end_timezone": self.end_timezone,
            "is_all_day": self.is_all_day,
            "original_start_at": self.original_start_at.isoformat() if self.original_start_at else None,
            "status": self.status,
            "show_as": self.show_as,
            "transparency": self.transparency,
            "visibility": self.visibility,
            "sensitivity": self.sensitivity,
            "importance": self.importance,
            "is_cancelled": self.is_cancelled,
            "is_draft": self.is_draft,
            "is_online_meeting": self.is_online_meeting,
            "organizer": self.organizer,
            "creator": self.creator,
            "attendees": self.attendees,
            "recurrence_rules": self.recurrence_rules,
            "recurrence": self.recurrence,
            "series_master_id": self.series_master_id,
            "reminders_use_default": self.reminders_use_default,
            "reminder_minutes_before_start": self.reminder_minutes_before_start,
            "is_reminder_on": self.is_reminder_on,
            "reminders": self.reminders,
            "online_meeting_url": self.online_meeting_url,
            "hangout_link": self.hangout_link,
            "conference_data": self.conference_data,
            "html_link": self.html_link,
            "web_link": self.web_link,
            "source": self.source,
            "color_id": self.color_id,
            "categories": self.categories,
            "attachments": self.attachments,
            "google": self.google,
            "microsoft": self.microsoft,
            "extended_properties": self.extended_properties,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "provider_created_at": self.provider_created_at.isoformat() if self.provider_created_at else None,
            "provider_updated_at": self.provider_updated_at.isoformat() if self.provider_updated_at else None,
        }

    @staticmethod
    def from_dict(payload: dict[str, Any]) -> "CalendarEvent":
        e = CalendarEvent()
        e.apply_patch(payload)
        return e

    def apply_patch(self, payload: dict[str, Any]) -> None:
        # Minimal/forgiving mapping. If you send full provider payloads, put them in `google` or `microsoft`.
        for key in [
            "provider",
            "external_id",
            "ical_uid",
            "etag",
            "change_key",
            "title",
            "description",
            "description_content_type",
            "location",
            "location_details",
            "start_timezone",
            "end_timezone",
            "status",
            "show_as",
            "transparency",
            "visibility",
            "sensitivity",
            "importance",
            "reminders_use_default",
            "reminder_minutes_before_start",
            "is_reminder_on",
            "reminders",
            "online_meeting_url",
            "hangout_link",
            "conference_data",
            "html_link",
            "web_link",
            "source",
            "color_id",
            "categories",
            "attachments",
            "google",
            "microsoft",
            "extended_properties",
            "recurrence_rules",
            "recurrence",
            "series_master_id",
        ]:
            if key in payload:
                setattr(self, key, payload[key])

        # Convert local naive datetimes + IANA tz -> stored UTC timestamps.
        # Payload should send start_local/end_local like "2025-12-15T10:00:00" and start_timezone like "America/New_York".
        def _local_to_utc(local_iso: str, tz_name: str) -> datetime:
            naive = datetime.fromisoformat(local_iso)
            tz = ZoneInfo(tz_name)
            aware = naive.replace(tzinfo=tz)
            return aware.astimezone(ZoneInfo("UTC"))

        if payload.get("start_local") and payload.get("start_timezone"):
            try:
                self.start_at = _local_to_utc(str(payload["start_local"]), str(payload["start_timezone"]))
            except Exception:
                # If conversion fails, leave as-is; client can use start_at instead.
                pass

        if payload.get("end_local") and payload.get("end_timezone"):
            try:
                self.end_at = _local_to_utc(str(payload["end_local"]), str(payload["end_timezone"]))
            except Exception:
                pass

        for bool_key in ["is_all_day", "is_cancelled", "is_draft", "is_online_meeting"]:
            if bool_key in payload and payload[bool_key] is not None:
                setattr(self, bool_key, bool(payload[bool_key]))

        # Datetimes can be passed as ISO strings
        for dt_key in ["start_at", "end_at", "original_start_at", "provider_created_at", "provider_updated_at"]:
            if dt_key in payload:
                value = payload[dt_key]
                if value is None:
                    setattr(self, dt_key, None)
                elif isinstance(value, str):
                    setattr(self, dt_key, datetime.fromisoformat(value.replace("Z", "+00:00")))
                elif isinstance(value, datetime):
                    setattr(self, dt_key, value)


