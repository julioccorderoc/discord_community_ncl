from src.database.client import supabase
from src.models.schemas import Ticket, TicketEvent, TicketStatus


def create_ticket(
    author_id: int,
    subject: str,
    discord_channel_id: int,
) -> Ticket:
    """
    Insert a new ticket row with status OPEN.

    IMPORTANT: The caller must have already called upsert_user(author_id, ...)
    via asyncio.to_thread() BEFORE calling this function.
    The FK constraint tickets.author_id -> discord_users.discord_id will
    reject the insert if the user row does not exist.
    """
    response = (
        supabase.table("tickets")
        .insert(
            {
                "author_id": author_id,
                "subject": subject,
                "discord_channel_id": discord_channel_id,
                "status": TicketStatus.OPEN.value,
            }
        )
        .execute()
    )
    return Ticket.model_validate(response.data[0])


def resolve_ticket(discord_channel_id: int) -> Ticket | None:
    """
    Set a ticket's status to RESOLVED, identified by the Discord channel ID.

    Returns the updated Ticket, or None if no matching ticket was found.
    """
    lookup = (
        supabase.table("tickets")
        .select("id")
        .eq("discord_channel_id", discord_channel_id)
        .execute()
    )
    if not lookup.data:
        return None

    ticket_id = lookup.data[0]["id"]

    response = (
        supabase.table("tickets")
        .update({"status": TicketStatus.RESOLVED.value})
        .eq("id", ticket_id)
        .execute()
    )
    return Ticket.model_validate(response.data[0])


def log_ticket_event(
    ticket_id: int,
    actor_id: int,
    system_note: str,
    is_internal: bool = True,
    message_content: str | None = None,
) -> TicketEvent:
    """Write an audit row to ticket_events."""
    response = (
        supabase.table("ticket_events")
        .insert(
            {
                "ticket_id": ticket_id,
                "actor_id": actor_id,
                "is_internal": is_internal,
                "system_note": system_note,
                "message_content": message_content,
            }
        )
        .execute()
    )
    return TicketEvent.model_validate(response.data[0])


def get_ticket_by_channel(discord_channel_id: int) -> Ticket | None:
    """
    Look up a ticket by its linked Discord channel ID.

    Returns None if the channel is not a ticket channel.
    Used by !close as a guard check.
    """
    response = (
        supabase.table("tickets")
        .select("*")
        .eq("discord_channel_id", discord_channel_id)
        .execute()
    )
    if not response.data:
        return None
    return Ticket.model_validate(response.data[0])
