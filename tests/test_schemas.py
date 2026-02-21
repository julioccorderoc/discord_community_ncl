from datetime import datetime, timezone
from src.models.schemas import (
    DiscordUser,
    ActivityLog,
    Ticket,
    TicketEvent,
    ActivityType,
    TicketStatus,
    TicketPriority,
)


def test_discord_user_valid():
    now = datetime.now(timezone.utc)
    user = DiscordUser(
        discord_id=123456789,
        username="TestUser",
        first_seen_at=now,
        last_seen_at=now,
    )
    assert user.is_staff is False
    assert user.avatar_url is None


def test_activity_log_points_default():
    log = ActivityLog(user_id=1, type=ActivityType.MESSAGE_SENT, channel_id=555)
    assert log.points_value == 0
    assert log.metadata == {}


def test_ticket_defaults():
    ticket = Ticket(author_id=1, subject="Help!")
    assert ticket.status == TicketStatus.OPEN
    assert ticket.priority == TicketPriority.MEDIUM


def test_ticket_event_nullable_fields():
    event = TicketEvent(ticket_id=1, actor_id=999)
    assert event.message_content is None
    assert event.system_note is None
    assert event.is_internal is False
