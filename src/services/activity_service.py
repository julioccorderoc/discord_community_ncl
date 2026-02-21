import asyncio
from datetime import datetime, timezone
from typing import Optional

from src.database.client import supabase
from src.models.schemas import ActivityType

# Points stored at 2× scale so reactions (0.5) fit in INT.
# Score = SUM(points_value) / 2.0 at query time.
POINTS: dict[ActivityType, int] = {
    ActivityType.MESSAGE_SENT: 2,
    ActivityType.REACTION_ADD: 1,
    ActivityType.THREAD_CREATE: 2,
}


def calculate_score(points_values: list[int]) -> float:
    """Convert raw stored points (2× scale) to the canonical score."""
    return sum(points_values) / 2.0


def upsert_user(
    discord_id: int,
    username: str,
    avatar_url: Optional[str],
    guild_join_date: Optional[datetime],
) -> None:
    supabase.table("discord_users").upsert(
        {
            "discord_id": discord_id,
            "username": username,
            "avatar_url": avatar_url,
            "guild_join_date": guild_join_date.isoformat() if guild_join_date else None,
            "last_seen_at": datetime.now(timezone.utc).isoformat(),
        },
        on_conflict="discord_id",
    ).execute()


def log_activity(
    user_id: int,
    activity_type: ActivityType,
    channel_id: int,
    metadata: Optional[dict] = None,
) -> None:
    supabase.table("activity_logs").insert(
        {
            "user_id": user_id,
            "type": activity_type.value,
            "channel_id": channel_id,
            "points_value": POINTS[activity_type],
            "metadata": metadata or {},
        }
    ).execute()
