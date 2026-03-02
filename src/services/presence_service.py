from datetime import datetime, timezone

from src.database.client import supabase


def open_presence_session(user_id: int, status: str) -> None:
    """Insert a new open presence session for the user."""
    supabase.table("presence_sessions").insert(
        {
            "user_id": user_id,
            "status": status,
        }
    ).execute()


def close_presence_session(user_id: int) -> None:
    """Close the user's open presence session, computing duration_seconds.

    No-op if the user has no open session (e.g. bot missed the open event).
    """
    now = datetime.now(timezone.utc)
    result = (
        supabase.table("presence_sessions")
        .select("id, started_at")
        .eq("user_id", user_id)
        .is_("ended_at", "null")
        .execute()
    )
    if not result.data:
        return
    session = result.data[0]
    started_at = datetime.fromisoformat(session["started_at"])
    duration = int((now - started_at).total_seconds())
    supabase.table("presence_sessions").update(
        {
            "ended_at": now.isoformat(),
            "duration_seconds": duration,
        }
    ).eq("id", session["id"]).execute()


def close_all_open_sessions() -> None:
    """Close all stale open sessions — called on bot startup after a restart.

    Any row with ended_at IS NULL is left over from a previous bot run.
    Sets ended_at = NOW() but does NOT write duration_seconds: the bot went
    down between the session opening and this cleanup, so we don't know when
    the user actually went offline. Leaving duration_seconds NULL excludes
    these rows from all duration-based aggregations in the dashboard.
    """
    now = datetime.now(timezone.utc)
    result = (
        supabase.table("presence_sessions")
        .select("id")
        .is_("ended_at", "null")
        .execute()
    )
    for session in result.data:
        supabase.table("presence_sessions").update(
            {"ended_at": now.isoformat()}
        ).eq("id", session["id"]).execute()
