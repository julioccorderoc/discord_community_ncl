from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, Json
from enum import Enum

# --- ENUMS ---
# We mirror the SQL Enums here. 
# This ensures that if the DB sends "in_progress", Python understands it.
class TicketStatus(str, Enum):
    OPEN = 'open'
    IN_PROGRESS = 'in_progress'
    WAITING = 'waiting_for_user'
    RESOLVED = 'resolved'
    CLOSED = 'closed'

class TicketPriority(str, Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'

class ActivityType(str, Enum):
    MESSAGE_SENT = 'message_sent'
    REACTION_ADD = 'reaction_add'
    THREAD_CREATE = 'thread_create'
    # VOICE_JOIN deferred to post-MVP

# --- BASE MODEL ---
# Common configuration for all models
class CommunityBaseModel(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,       # Allows Pydantic to read from ORM-like objects if we switch later
        populate_by_name=True,      # Good for mapping DB column names to Python attributes
        extra='ignore'              # If DB has a new column we don't know about yet, don't crash
    )

# --- ENTITY MODELS ---

class DiscordUser(CommunityBaseModel):
    discord_id: int
    username: str
    avatar_url: Optional[str] = None
    is_staff: bool = False
    guild_join_date: Optional[datetime] = None
    first_seen_at: datetime
    last_seen_at: datetime

class ActivityLog(CommunityBaseModel):
    id: Optional[int] = None # Optional because it doesn't exist before we insert
    user_id: int
    type: ActivityType
    channel_id: int
    points_value: int = 0
    # In DB it's JSONB. In Pydantic, it's a Dict.
    # We default to empty dict to avoid NoneType errors.
    metadata: Dict[str, Any] = Field(default_factory=dict) 
    created_at: Optional[datetime] = None

class Ticket(CommunityBaseModel):
    id: Optional[int] = None
    author_id: int
    assignee_id: Optional[int] = None
    discord_channel_id: Optional[int] = None
    status: TicketStatus = TicketStatus.OPEN
    priority: TicketPriority = TicketPriority.MEDIUM
    subject: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class TicketEvent(CommunityBaseModel):
    id: Optional[int] = None
    ticket_id: int
    actor_id: int
    is_internal: bool = False
    message_content: Optional[str] = None
    system_note: Optional[str] = None
    created_at: Optional[datetime] = None

class AIAuditLog(CommunityBaseModel):
    id: Optional[str] = None # UUID is a string in Python usually
    user_id: Optional[int] = None
    command_name: str
    input_prompt: str
    llm_response: Optional[str] = None
    tokens_used: Optional[int] = None
    processing_time_ms: Optional[int] = None
    created_at: Optional[datetime] = None