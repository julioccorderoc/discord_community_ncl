import plotly.graph_objects as go
import streamlit as st

import src.config as config
from src.services.ai_service import check_gemini_health
from src.services.dashboard_service import (
    check_supabase_health,
    get_ai_audit_logs,
    get_ai_cost_summary,
    get_churn_risks,
    get_member_growth_summary,
    get_peak_hours,
    get_presence_stats,
    get_rising_stars,
    get_server_size_metrics,
    get_top_presence_members,
    get_weekly_scores,
)

_COST_RATE_PER_1M = "0.075"  # Gemini 2.0 Flash Lite blended estimate

st.set_page_config(page_title="NCL Community OS", page_icon="📊", layout="wide")
st.title("NCL Community OS — Manager Dashboard")

tab1, tab2, tab3, tab4 = st.tabs(["📈 Impact Pulse", "📋 The Lists", "🔐 Admin", "🏥 Community Health"])

# ── Tab 1: Impact Pulse ────────────────────────────────────────────────────────
with tab1:
    st.subheader("Engagement Score — This Week vs. Last Week")

    @st.cache_data(ttl=60)
    def load_weekly():
        return get_weekly_scores()

    this_week, last_week = load_weekly()

    if this_week.empty and last_week.empty:
        st.info("No activity data yet. Send some messages in Discord and refresh.")
    else:
        fig = go.Figure()
        if not last_week.empty:
            fig.add_trace(go.Scatter(
                x=last_week["date"].astype(str),
                y=last_week["score"],
                mode="lines+markers",
                name="Last Week",
                line=dict(dash="dash", color="gray"),
            ))
        if not this_week.empty:
            fig.add_trace(go.Scatter(
                x=this_week["date"].astype(str),
                y=this_week["score"],
                mode="lines+markers",
                name="This Week",
                line=dict(color="#5865F2"),
            ))
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Engagement Score",
            legend=dict(orientation="h"),
            margin=dict(l=0, r=0, t=30, b=0),
        )
        st.plotly_chart(fig, use_container_width=True)

# ── Tab 2: The Lists ───────────────────────────────────────────────────────────
with tab2:
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🌟 Rising Stars")
        st.caption("Top 10 by score — last 7 days")

        @st.cache_data(ttl=60)
        def load_rising_stars():
            return get_rising_stars(limit=10)

        stars = load_rising_stars()
        if stars.empty:
            st.info("No activity in the last 7 days.")
        else:
            st.dataframe(
                stars.rename(columns={
                    "username": "Member",
                    "score": "Score",
                    "activity_count": "Actions",
                }),
                use_container_width=True,
                hide_index=True,
            )

    with col2:
        st.subheader("⚠️ Churn Risks")
        st.caption("Active in last 30 days, silent for 7+ days")

        @st.cache_data(ttl=60)
        def load_churn_risks():
            return get_churn_risks(limit=10)

        risks = load_churn_risks()
        if risks.empty:
            st.info("No churn risks detected.")
        else:
            st.dataframe(
                risks.rename(columns={
                    "username": "Member",
                    "last_active": "Last Active",
                    "days_silent": "Days Silent",
                }),
                use_container_width=True,
                hide_index=True,
            )

# ── Tab 3: Admin ───────────────────────────────────────────────────────────────
with tab3:
    st.subheader("Admin Mode")

    if not config.ADMIN_PASSWORD:
        st.warning("ADMIN_PASSWORD is not set. Configure it in your .env file to enable this panel.")
        st.stop()

    password = st.text_input("Enter admin password", type="password", key="admin_pw")

    if password != config.ADMIN_PASSWORD:
        if password:
            st.error("Incorrect password.")
        st.stop()

    st.success("Admin mode active.")
    st.divider()

    # ── Health Check Panel ─────────────────────────────────────────────────────
    st.subheader("🩺 System Health")

    def _status_badge(ok: bool) -> str:
        return "🟢 Healthy" if ok else "🔴 Unreachable"

    h_col1, h_col2, h_col3 = st.columns(3)

    with h_col1:
        st.metric("Discord Gateway", _status_badge(True))
        st.caption("Always healthy while the dashboard is running.")

    with h_col2:
        supabase_ok = check_supabase_health()
        st.metric("Supabase", _status_badge(supabase_ok))

    with h_col3:
        gemini_ok = check_gemini_health()
        st.metric("Gemini API", _status_badge(gemini_ok))

    st.divider()

    # ── Cost Ledger ────────────────────────────────────────────────────────────
    st.subheader("💰 AI Cost Ledger — Current Billing Cycle")

    @st.cache_data(ttl=300)
    def load_cost_summary():
        return get_ai_cost_summary()

    cost = load_cost_summary()
    c_col1, c_col2, c_col3 = st.columns(3)
    c_col1.metric("Total Tokens", f"{cost['total_tokens']:,}")
    c_col2.metric("Estimated Cost", f"${cost['estimated_cost_usd']:.4f}")
    c_col3.metric("Total Calls", cost["call_count"])
    st.caption(
        f"Cost estimate based on ~${_COST_RATE_PER_1M}/1M tokens (Gemini 2.0 Flash Lite blended rate). "
        "Actual billing may vary."
    )

    st.divider()

    # ── Log Stream ─────────────────────────────────────────────────────────────
    st.subheader("📜 Recent AI Audit Logs")
    st.caption("Last 50 entries — refreshes every 30 s")

    @st.cache_data(ttl=30)
    def load_audit_logs():
        return get_ai_audit_logs(limit=50)

    logs_df = load_audit_logs()
    if logs_df.empty:
        st.info("No audit log entries yet. Use /audit in Discord to populate this table.")
    else:
        st.dataframe(
            logs_df.rename(columns={
                "created_at": "Timestamp",
                "user_id": "User ID",
                "command_name": "Command",
                "tokens_used": "Tokens",
                "processing_time_ms": "Latency (ms)",
                "input_prompt": "Input",
            }),
            use_container_width=True,
            hide_index=True,
        )

    st.divider()

    # ── Panic Button ───────────────────────────────────────────────────────────
    st.subheader("🚨 Panic Controls")

    if st.button("🧹 Flush Cache", help="Clears all cached data — next load will re-fetch from DB."):
        st.cache_data.clear()
        st.success("Cache cleared. All data will reload on next interaction.")

# ── Tab 4: Community Health ────────────────────────────────────────────────────
with tab4:
    # ── Time range selector + top-line metrics ─────────────────────────────────
    growth_days = st.selectbox(
        "Time range",
        [30, 60, 90],
        format_func=lambda d: f"Last {d} days",
        key="growth_days",
    )

    @st.cache_data(ttl=300)
    def load_server_size(days: int):
        return get_server_size_metrics(days)

    @st.cache_data(ttl=300)
    def load_presence_stats():
        return get_presence_stats(days=7)

    size = load_server_size(growth_days)
    stats = load_presence_stats()

    avg_s = stats["avg_duration_seconds"]
    avg_fmt = f"{avg_s // 3600}h {(avg_s % 3600) // 60}m" if avg_s else "—"

    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Server Size", size["current"], delta=f"+{size['delta']} new")
    m_col1.caption(f"vs {size['baseline']} members {growth_days} days ago")
    m_col2.metric("Avg Session Duration (7d)", avg_fmt)
    m_col2.caption(f"{stats['total_sessions']} sessions · {stats['unique_active_members']} unique members")
    m_col3.metric("Active Members (7d)", stats["unique_active_members"])

    st.divider()

    # ── Member Growth chart ─────────────────────────────────────────────────────
    st.subheader("Member Growth")

    @st.cache_data(ttl=300)
    def load_growth_summary(days: int):
        return get_member_growth_summary(days)

    growth_df = load_growth_summary(growth_days)

    if growth_df.empty:
        st.info("No join/leave events recorded yet. This chart will populate once members join or leave the server.")
    else:
        fig_growth = go.Figure()
        fig_growth.add_trace(go.Scatter(
            x=growth_df["date"].astype(str),
            y=growth_df["joins"],
            mode="lines+markers",
            name="Joins",
            line=dict(color="#57F287"),
        ))
        fig_growth.add_trace(go.Scatter(
            x=growth_df["date"].astype(str),
            y=growth_df["leaves"],
            mode="lines+markers",
            name="Leaves",
            line=dict(color="#ED4245"),
        ))
        fig_growth.add_trace(go.Scatter(
            x=growth_df["date"].astype(str),
            y=growth_df["net"],
            mode="lines+markers",
            name="Net",
            line=dict(color="#5865F2"),
        ))
        fig_growth.update_layout(
            xaxis_title="Date",
            yaxis_title="Members",
            legend=dict(orientation="h"),
            margin=dict(l=0, r=0, t=30, b=0),
        )
        st.plotly_chart(fig_growth, use_container_width=True)

    st.divider()

    # ── Peak hours + Top presence members ──────────────────────────────────────
    ph_col, tm_col = st.columns(2)

    with ph_col:
        st.subheader("Peak Hours (UTC)")
        st.caption("Avg members online by hour of day — last 7 days")

        @st.cache_data(ttl=300)
        def load_peak_hours():
            return get_peak_hours(days=7)

        peak_df = load_peak_hours()
        if peak_df["avg_members"].sum() == 0:
            st.info("No presence data yet. This will populate once the bot has been tracking members online.")
        else:
            fig_peak = go.Figure(go.Bar(
                x=peak_df["hour"],
                y=peak_df["avg_members"],
                marker_color="#5865F2",
            ))
            fig_peak.update_layout(
                xaxis_title="Hour (UTC)",
                yaxis_title="Avg Members Online",
                xaxis=dict(tickmode="linear", tick0=0, dtick=1),
                margin=dict(l=0, r=0, t=10, b=0),
            )
            st.plotly_chart(fig_peak, use_container_width=True)

    with tm_col:
        st.subheader("Most Online This Week")
        st.caption("Top 10 by total online time — last 7 days")

        @st.cache_data(ttl=300)
        def load_top_presence():
            return get_top_presence_members(limit=10, days=7)

        top_df = load_top_presence()
        if top_df.empty:
            st.info("No closed presence sessions yet.")
        else:
            top_df["online_time"] = top_df["total_seconds"].apply(
                lambda s: f"{s // 3600}h {(s % 3600) // 60}m"
            )
            st.dataframe(
                top_df[["username", "online_time"]].rename(columns={
                    "username": "Member",
                    "online_time": "Online Time",
                }),
                use_container_width=True,
                hide_index=True,
            )
