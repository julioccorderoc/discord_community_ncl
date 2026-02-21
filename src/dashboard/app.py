import plotly.graph_objects as go
import streamlit as st

from src.services.dashboard_service import (
    get_churn_risks,
    get_rising_stars,
    get_weekly_scores,
)

st.set_page_config(page_title="NCL Community OS", page_icon="📊", layout="wide")
st.title("NCL Community OS — Manager Dashboard")

tab1, tab2 = st.tabs(["📈 Impact Pulse", "📋 The Lists"])

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
