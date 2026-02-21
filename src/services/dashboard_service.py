from datetime import datetime, timedelta, timezone

import pandas as pd

from src.database.client import supabase


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
