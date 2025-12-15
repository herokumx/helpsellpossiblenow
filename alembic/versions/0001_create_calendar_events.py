"""create calendar_events

Revision ID: 0001
Revises: 
Create Date: 2025-12-15

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "calendar_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=True),
        sa.Column("external_id", sa.String(length=256), nullable=True),
        sa.Column("ical_uid", sa.String(length=512), nullable=True),
        sa.Column("etag", sa.String(length=256), nullable=True),
        sa.Column("change_key", sa.String(length=256), nullable=True),
        sa.Column("title", sa.String(length=1024), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("description_content_type", sa.String(length=32), nullable=True),
        sa.Column("location", sa.String(length=2048), nullable=True),
        sa.Column("location_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("start_timezone", sa.String(length=128), nullable=True),
        sa.Column("end_timezone", sa.String(length=128), nullable=True),
        sa.Column("is_all_day", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("original_start_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=64), nullable=True),
        sa.Column("show_as", sa.String(length=64), nullable=True),
        sa.Column("transparency", sa.String(length=32), nullable=True),
        sa.Column("visibility", sa.String(length=32), nullable=True),
        sa.Column("sensitivity", sa.String(length=32), nullable=True),
        sa.Column("importance", sa.String(length=16), nullable=True),
        sa.Column("is_cancelled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_draft", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_online_meeting", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("organizer", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("creator", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("attendees", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("recurrence_rules", postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column("recurrence", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("series_master_id", sa.String(length=256), nullable=True),
        sa.Column("reminders_use_default", sa.Boolean(), nullable=True),
        sa.Column("reminder_minutes_before_start", sa.Integer(), nullable=True),
        sa.Column("is_reminder_on", sa.Boolean(), nullable=True),
        sa.Column("reminders", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("online_meeting_url", sa.String(length=2048), nullable=True),
        sa.Column("hangout_link", sa.String(length=2048), nullable=True),
        sa.Column("conference_data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("html_link", sa.String(length=2048), nullable=True),
        sa.Column("web_link", sa.String(length=2048), nullable=True),
        sa.Column("source", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("color_id", sa.String(length=32), nullable=True),
        sa.Column("categories", postgresql.ARRAY(sa.String(length=256)), nullable=True),
        sa.Column("attachments", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("google", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("microsoft", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("extended_properties", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("provider_created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("provider_updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index("ix_calendar_events_external_id", "calendar_events", ["external_id"])
    op.create_index("ix_calendar_events_ical_uid", "calendar_events", ["ical_uid"])
    op.create_index("ix_calendar_events_provider", "calendar_events", ["provider"])
    op.create_index("ix_calendar_events_start_at", "calendar_events", ["start_at"])


def downgrade() -> None:
    op.drop_index("ix_calendar_events_start_at", table_name="calendar_events")
    op.drop_index("ix_calendar_events_provider", table_name="calendar_events")
    op.drop_index("ix_calendar_events_ical_uid", table_name="calendar_events")
    op.drop_index("ix_calendar_events_external_id", table_name="calendar_events")
    op.drop_table("calendar_events")


