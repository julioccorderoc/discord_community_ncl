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


# ── EPIC-013: Community Health Dashboard helpers ───────────────────────────────

def get_member_events(days: int = 30) -> pd.DataFrame:
    """Rows from member_events for the last N days.

    Columns: user_id, event_type, created_at.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    response = (
        supabase.table("member_events")
        .select("user_id, event_type, created_at")
        .gte("created_at", cutoff)
        .execute()
    )
    if not response.data:
        return pd.DataFrame(columns=["user_id", "event_type", "created_at"])
    df = pd.DataFrame(response.data)
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True)
    return df


def get_member_growth_summary(days: int = 30) -> pd.DataFrame:
    """Daily net member growth for the last N days.

    Columns: date, joins, leaves, net.
    """
    df = get_member_events(days)
    if df.empty:
        return pd.DataFrame(columns=["date", "joins", "leaves", "net"])
    df["date"] = df["created_at"].dt.date
    joins = df[df["event_type"] == "join"].groupby("date").size().rename("joins")
    leaves = df[df["event_type"] == "leave"].groupby("date").size().rename("leaves")
    summary = pd.DataFrame({"joins": joins, "leaves": leaves}).fillna(0).astype(int)
    summary["net"] = summary["joins"] - summary["leaves"]
    return summary.reset_index()


def get_server_size_metrics(days: int = 30) -> dict:
    """Current member count and delta vs N days ago (based on first_seen_at).

    Returns dict with keys: current (int), baseline (int), delta (int).
    """
    response = (
        supabase.table("discord_users")
        .select("first_seen_at")
        .execute()
    )
    if not response.data:
        return {"current": 0, "baseline": 0, "delta": 0}
    df = pd.DataFrame(response.data)
    df["first_seen_at"] = pd.to_datetime(df["first_seen_at"], utc=True)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    current = len(df)
    baseline = len(df[df["first_seen_at"] <= cutoff])
    return {"current": current, "baseline": baseline, "delta": current - baseline}


def get_presence_stats(days: int = 7) -> dict:
    """Summary stats for presence sessions started in the last N days.

    Returns dict with keys: avg_duration_seconds (int), total_sessions (int),
    unique_active_members (int). Only closed sessions count toward avg_duration_seconds.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    response = (
        supabase.table("presence_sessions")
        .select("user_id, duration_seconds")
        .gte("started_at", cutoff)
        .execute()
    )
    if not response.data:
        return {"avg_duration_seconds": 0, "total_sessions": 0, "unique_active_members": 0}
    df = pd.DataFrame(response.data)
    closed = df.dropna(subset=["duration_seconds"])
    return {
        "avg_duration_seconds": int(closed["duration_seconds"].mean()) if not closed.empty else 0,
        "total_sessions": len(df),
        "unique_active_members": df["user_id"].nunique(),
    }


def get_peak_hours(days: int = 7) -> pd.DataFrame:
    """Average online members by hour of day (UTC) over the last N days.

    Columns: hour (0-23), avg_members (float).
    For each session, counts one member as 'online' for every clock-hour the session spans.
    Sessions are capped at 24 h to guard against runaway iteration on stale rows.
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    now = datetime.now(timezone.utc)
    response = (
        supabase.table("presence_sessions")
        .select("started_at, ended_at")
        .gte("started_at", cutoff)
        .execute()
    )
    hour_counts = [0] * 24
    if response.data:
        cap = timedelta(hours=24)
        for row in response.data:
            start = datetime.fromisoformat(row["started_at"])
            end = datetime.fromisoformat(row["ended_at"]) if row["ended_at"] else now
            end = min(end, now, start + cap)
            current = start.replace(minute=0, second=0, microsecond=0)
            while current < end:
                hour_counts[current.hour] += 1
                current += timedelta(hours=1)
    return pd.DataFrame({
        "hour": list(range(24)),
        "avg_members": [count / max(days, 1) for count in hour_counts],
    })


def get_top_presence_members(limit: int = 10, days: int = 7) -> pd.DataFrame:
    """Top N members by total online time (sum of duration_seconds) in the last N days.

    Columns: username, total_seconds (int).
    Only counts closed sessions (duration_seconds IS NOT NULL).
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    response = (
        supabase.table("presence_sessions")
        .select("user_id, duration_seconds")
        .gte("started_at", cutoff)
        .execute()
    )
    if not response.data:
        return pd.DataFrame(columns=["username", "total_seconds"])
    df = pd.DataFrame(response.data)
    df = df.dropna(subset=["duration_seconds"])
    if df.empty:
        return pd.DataFrame(columns=["username", "total_seconds"])
    grouped = df.groupby("user_id")["duration_seconds"].sum().reset_index()
    grouped.columns = ["user_id", "total_seconds"]
    users_df = get_all_users()
    merged = grouped.merge(
        users_df[["discord_id", "username"]],
        left_on="user_id",
        right_on="discord_id",
        how="left",
    )
    merged["username"] = merged["username"].fillna("Unknown")
    return (
        merged[["username", "total_seconds"]]
        .sort_values("total_seconds", ascending=False)
        .head(limit)
        .reset_index(drop=True)
    )


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
