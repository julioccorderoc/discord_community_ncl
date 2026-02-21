from datetime import datetime, timedelta, timezone

import pandas as pd

from src.database.client import supabase

# Cost per million tokens (Gemini 2.0 Flash Lite blended estimate).
_COST_PER_1M_TOKENS_USD = 0.075


def get_activity_last_n_days(n: int) -> pd.DataFrame:
    """Fetch all activity_logs rows from the last N days. Returns a DataFrame."""
    cutoff = (datetime.now(timezone.utc) - timedelta(days=n)).isoformat()
    response = (
        supabase.table("activity_logs")
        .select("user_id, points_value, created_at")
        .gte("created_at", cutoff)
        .execute()
    )
    if not response.data:
        return pd.DataFrame(columns=["user_id", "points_value", "created_at"])
    df = pd.DataFrame(response.data)
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    return df


def get_weekly_scores() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Return (this_week_df, last_week_df) — daily score totals for each period.
    Each DataFrame has columns: date (date), score (float).
    Score = sum(points_value) / 2.0 per day.
    """
    df = get_activity_last_n_days(14)
    if df.empty:
        empty = pd.DataFrame(columns=["date", "score"])
        return empty, empty
    df["date"] = df["created_at"].dt.date
    daily = df.groupby("date")["points_value"].sum().reset_index()
    daily["score"] = daily["points_value"] / 2.0
    daily = daily.drop(columns=["points_value"])
    cutoff = datetime.now(timezone.utc).date() - timedelta(days=7)
    this_week = daily[daily["date"] >= cutoff].copy()
    last_week = daily[daily["date"] < cutoff].copy()
    return this_week, last_week


def get_all_users() -> pd.DataFrame:
    """Fetch all discord_users. Returns DataFrame with discord_id, username, last_seen_at."""
    response = (
        supabase.table("discord_users")
        .select("discord_id, username, guild_join_date, last_seen_at")
        .execute()
    )
    if not response.data:
        return pd.DataFrame(columns=["discord_id", "username", "guild_join_date", "last_seen_at"])
    df = pd.DataFrame(response.data)
    df["last_seen_at"] = pd.to_datetime(df["last_seen_at"], utc=True)
    return df


def get_rising_stars(limit: int = 10) -> pd.DataFrame:
    """
    Top N users by engagement score in the last 7 days.
    Returns DataFrame: username, score (float), activity_count (int).
    """
    df = get_activity_last_n_days(7)
    if df.empty:
        return pd.DataFrame(columns=["username", "score", "activity_count"])
    users_df = get_all_users()
    grouped = df.groupby("user_id").agg(
        total_points=("points_value", "sum"),
        activity_count=("points_value", "count"),
    ).reset_index()
    grouped["score"] = grouped["total_points"] / 2.0
    merged = grouped.merge(
        users_df[["discord_id", "username"]],
        left_on="user_id",
        right_on="discord_id",
        how="left",
    )
    merged["username"] = merged["username"].fillna("Unknown")
    return (
        merged[["username", "score", "activity_count"]]
        .sort_values("score", ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )


def get_churn_risks(
    active_window_days: int = 30,
    silent_threshold_days: int = 7,
    limit: int = 10,
) -> pd.DataFrame:
    """
    Users who were active within `active_window_days` but have been silent
    for at least `silent_threshold_days`.
    Returns DataFrame: username, last_active (date), days_silent (int).
    """
    df = get_activity_last_n_days(active_window_days)
    if df.empty:
        return pd.DataFrame(columns=["username", "last_active", "days_silent"])
    users_df = get_all_users()
    last_active = df.groupby("user_id")["created_at"].max().reset_index()
    last_active.columns = ["user_id", "last_active"]
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=silent_threshold_days)
    silent = last_active[last_active["last_active"] < cutoff].copy()
    silent["days_silent"] = (now - silent["last_active"]).dt.days
    merged = silent.merge(
        users_df[["discord_id", "username"]],
        left_on="user_id",
        right_on="discord_id",
        how="left",
    )
    merged["username"] = merged["username"].fillna("Unknown")
    merged["last_active"] = merged["last_active"].dt.date
    return (
        merged[["username", "last_active", "days_silent"]]
        .sort_values("days_silent", ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )


# ── EPIC-006: Admin Dashboard helpers ─────────────────────────────────────────

def check_supabase_health() -> bool:
    """Return True if Supabase responds to a lightweight ping, False otherwise."""
    try:
        supabase.table("discord_users").select("discord_id").limit(1).execute()
        return True
    except Exception:
        return False


def get_ai_audit_logs(limit: int = 50) -> pd.DataFrame:
    """Last N rows from ai_audit_logs, newest first.

    Returns DataFrame with columns:
      created_at, user_id, command_name, tokens_used, processing_time_ms, input_prompt
    """
    response = (
        supabase.table("ai_audit_logs")
        .select("created_at, user_id, command_name, tokens_used, processing_time_ms, input_prompt")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    if not response.data:
        return pd.DataFrame(columns=[
            "created_at", "user_id", "command_name", "tokens_used",
            "processing_time_ms", "input_prompt",
        ])
    df = pd.DataFrame(response.data)
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    return df


def get_ai_cost_summary() -> dict:
    """Token totals and estimated USD cost for the current calendar month.

    Returns dict with keys: total_tokens (int), estimated_cost_usd (float), call_count (int).
    """
    now = datetime.now(timezone.utc)
    cycle_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
    response = (
        supabase.table("ai_audit_logs")
        .select("tokens_used")
        .gte("created_at", cycle_start)
        .execute()
    )
    if not response.data:
        return {"total_tokens": 0, "estimated_cost_usd": 0.0, "call_count": 0}
    tokens = [row["tokens_used"] for row in response.data if row.get("tokens_used") is not None]
    total_tokens = sum(tokens)
    return {
        "total_tokens": total_tokens,
        "estimated_cost_usd": (total_tokens / 1_000_000) * _COST_PER_1M_TOKENS_USD,
        "call_count": len(response.data),
    }
