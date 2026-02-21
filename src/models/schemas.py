from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum


# --- ENUMS ---

class TicketStatus(str, Enum):
    """Lifecycle states for a support ticket, mirroring the DB `ticket_status` enum."""
    OPEN = 'open'                        # Newly created, awaiting staff response.
    IN_PROGRESS = 'in_progress'          # A staff member has picked it up.
    WAITING = 'waiting_for_user'         # Staff replied; waiting on the member.
    RESOLVED = 'resolved'                # Issue addressed; channel will be deleted.
    CLOSED = 'closed'                    # Archived — no further action expected.


class TicketPriority(str, Enum):
    """Urgency level assigned to a ticket, mirroring the DB `ticket_priority` enum."""
    LOW = 'low'          # Informational; no deadline.
    MEDIUM = 'medium'    # Standard — default for all new tickets.
    HIGH = 'high'        # Elevated impact; resolve within the day.
    CRITICAL = 'critical'  # Blocking or safety issue; escalate immediately.


class ActivityType(str, Enum):
    """Discrete user actions that contribute to the engagement score.

    Point weights (see CLAUDE.md):
      message_sent  → 1 pt
      reaction_add  → 0.5 pt
      thread_create → tracked, not yet scored (post-MVP)
    """
    MESSAGE_SENT = 'message_sent'    # User sent a message in any tracked channel.
    REACTION_ADD = 'reaction_add'    # User added a reaction to any message.
    THREAD_CREATE = 'thread_create'  # User created a thread (scoring deferred post-MVP).
    # VOICE_JOIN deferred to post-MVP


# --- BASE MODEL ---

class CommunityBaseModel(BaseModel):
    """Shared Pydantic V2 configuration inherited by all project models.

    - `from_attributes=True`  — lets Pydantic read from dict-like DB rows directly.
    - `populate_by_name=True` — allows both alias and field name during construction.
    - `extra='ignore'`        — silently drops unknown DB columns; prevents crash on schema drift.
    """
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra='ignore',
    )


# --- ENTITY MODELS ---

class DiscordUser(CommunityBaseModel):
    """A Discord member who has been observed at least once in the guild.

    Created or updated on every bot event via `upsert_user()` in
    `src/services/activity_service.py`. Serves as the FK anchor for all
    other tables (`activity_logs`, `tickets`, `ticket_events`, `ai_audit_logs`).
    """
    discord_id: int = Field(
        ...,
        description=(
            "Discord snowflake ID — the globally unique, immutable identifier assigned "
            "by Discord. Maps to BIGINT PRIMARY KEY in the DB. Never changes even if "
            "the user renames themselves."
        ),
    )
    username: str = Field(
        ...,
        description=(
            "Discord username at the time of the last upsert (e.g. 'julio' or legacy "
            "'julio#1234'). Updated on every activity event so it stays reasonably fresh."
        ),
    )
    avatar_url: Optional[str] = Field(
        None,
        description=(
            "CDN URL for the user's current avatar (e.g. 'https://cdn.discordapp.com/...'). "
            "NULL for users who have never set a custom avatar."
        ),
    )
    is_staff: bool = Field(
        False,
        description=(
            "True if this user holds the role configured as STAFF_ROLE_ID in .env. "
            "Currently set manually; not auto-synced from Discord roles."
        ),
    )
    guild_join_date: Optional[datetime] = Field(
        None,
        description=(
            "Timestamp of when the user joined the NCL guild (member.joined_at). "
            "NULL for members whose join date predates bot tracking."
        ),
    )
    first_seen_at: datetime = Field(
        ...,
        description="DB-generated timestamp of the first event that triggered an upsert for this user.",
    )
    last_seen_at: datetime = Field(
        ...,
        description="Timestamp of the most recent activity event — updated on every upsert call.",
    )


class ActivityLog(CommunityBaseModel):
    """A single scored engagement event recorded for a Discord user.

    The engagement score is never stored directly — it is always computed at
    query time by summing `points_value` across rows filtered by user and date.
    See `src/services/dashboard_service.py` for the aggregation logic.
    """
    id: Optional[int] = Field(
        None,
        description="DB-generated BIGINT identity. Absent (None) before the row is inserted.",
    )
    user_id: int = Field(
        ...,
        description="FK → discord_users.discord_id. The user who performed the logged action.",
    )
    type: ActivityType = Field(
        ...,
        description="Which category of action was performed (message, reaction, thread).",
    )
    channel_id: int = Field(
        ...,
        description=(
            "Discord channel snowflake where the action occurred. Stored as BIGINT to "
            "match Discord's 64-bit ID format."
        ),
    )
    points_value: int = Field(
        0,
        description=(
            "Pre-calculated score weight for this event type. message_sent=1, "
            "reaction_add=0 (stored as 0 because 0.5 can't be INT — the dashboard "
            "applies the 0.5 multiplier during aggregation)."
        ),
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Flexible JSONB payload for event-specific context. Examples: "
            "{message_id: 123} for messages, {message_id: 123, emoji: '👍'} for reactions."
        ),
    )
    created_at: Optional[datetime] = Field(
        None,
        description="DB-generated timestamp of when this event row was written.",
    )


class Ticket(CommunityBaseModel):
    """A support ticket opened by a community member via /help or the Open Ticket button.

    Each ticket has a 1:1 relationship with a private Discord channel
    (`discord_channel_id`). The channel is the live conversation; this row
    is the metadata and status record.
    """
    id: Optional[int] = Field(
        None,
        description="DB-generated BIGINT identity. Absent before insert.",
    )
    author_id: int = Field(
        ...,
        description=(
            "FK → discord_users.discord_id. The member who opened the ticket. "
            "Must exist in discord_users before insert (FK constraint enforced by DB)."
        ),
    )
    assignee_id: Optional[int] = Field(
        None,
        description=(
            "FK → discord_users.discord_id. The staff member currently handling "
            "this ticket. NULL means unassigned."
        ),
    )
    discord_channel_id: Optional[int] = Field(
        None,
        description=(
            "Snowflake of the private Discord text channel created for this ticket. "
            "UNIQUE — enforces one ticket per channel. Used by !close to look up "
            "the ticket from within the channel."
        ),
    )
    status: TicketStatus = Field(
        TicketStatus.OPEN,
        description="Current lifecycle state. New tickets always start as OPEN.",
    )
    priority: TicketPriority = Field(
        TicketPriority.MEDIUM,
        description="Urgency level. Defaults to MEDIUM; staff can escalate via the dashboard.",
    )
    subject: str = Field(
        ...,
        description=(
            "One-line summary of the issue, entered by the member via the /help "
            "command or the modal TextInput."
        ),
    )
    created_at: Optional[datetime] = Field(
        None,
        description="DB-generated creation timestamp.",
    )
    updated_at: Optional[datetime] = Field(
        None,
        description=(
            "Last-modified timestamp, maintained automatically by the "
            "`update_tickets_modtime` DB trigger on every UPDATE."
        ),
    )


class TicketEvent(CommunityBaseModel):
    """An immutable audit trail entry or message within a ticket's history.

    There are two distinct uses for this model:

    1. **System audit events** — bot-generated entries logged on status changes
       (ticket opened, ticket closed). These populate `system_note` and leave
       `message_content` NULL.

    2. **Conversation messages** — user or staff messages relayed into the DB for
       archival. These populate `message_content` and leave `system_note` NULL.
       (Not yet implemented — the Discord channel is the primary conversation store.)
    """
    id: Optional[int] = Field(
        None,
        description="DB-generated BIGINT identity. Absent before insert.",
    )
    ticket_id: int = Field(
        ...,
        description="FK → tickets.id. The ticket this event is associated with.",
    )
    actor_id: int = Field(
        ...,
        description=(
            "FK → discord_users.discord_id. Who triggered this event — either "
            "the ticket author (member) or a staff responder."
        ),
    )
    is_internal: bool = Field(
        False,
        description=(
            "If True, this is a private staff note not visible to the ticket author. "
            "Used for inter-team coordination within a ticket."
        ),
    )
    message_content: Optional[str] = Field(
        None,
        description=(
            "The verbatim text of a user or staff message. NULL for system-generated "
            "audit events (status changes, open/close events). Will be populated "
            "if message-mirroring to DB is implemented post-MVP."
        ),
    )
    system_note: Optional[str] = Field(
        None,
        description=(
            "Auto-generated audit note describing a bot action "
            "(e.g. 'Ticket opened by julio#1234. Subject: billing issue'). "
            "NULL for regular conversation messages."
        ),
    )
    created_at: Optional[datetime] = Field(
        None,
        description="DB-generated timestamp of when this event was recorded.",
    )


class AIAuditLog(CommunityBaseModel):
    """Records every LLM call made via /audit for compliance and cost tracking.

    This table is populated by EPIC-006. EPIC-005 created the /audit command
    but deferred DB logging; this model is the schema contract between the two epics.
    """
    id: Optional[str] = Field(
        None,
        description=(
            "UUID primary key, DB-generated via gen_random_uuid(). String in Python "
            "because UUID is not natively an int. Used for distributed log tracing."
        ),
    )
    user_id: Optional[int] = Field(
        None,
        description=(
            "FK → discord_users.discord_id. The staff member who invoked /audit. "
            "NULL if the user cannot be resolved at log time."
        ),
    )
    command_name: str = Field(
        ...,
        description="The slash command that triggered this LLM call (e.g. '/audit').",
    )
    input_prompt: str = Field(
        ...,
        description="The full text submitted by the staff member for analysis.",
    )
    llm_response: Optional[str] = Field(
        None,
        description=(
            "Raw response text from the LLM before JSON parsing. Stored verbatim "
            "for auditability — even if parsing fails."
        ),
    )
    tokens_used: Optional[int] = Field(
        None,
        description=(
            "Total token count for the API call (input + output). "
            "Primary input for the cost ledger in EPIC-006."
        ),
    )
    processing_time_ms: Optional[int] = Field(
        None,
        description=(
            "Wall-clock duration of the LLM round-trip in milliseconds. "
            "Used for SLA monitoring in the EPIC-006 Admin Dashboard."
        ),
    )
    created_at: Optional[datetime] = Field(
        None,
        description="DB-generated timestamp of when this audit record was written.",
    )
