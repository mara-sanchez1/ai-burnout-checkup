import pandas as pd
import altair as alt
alt.themes.enable("default")
import streamlit as st
from pathlib import Path

# ---------- Page config ----------
st.set_page_config(
    page_title="AI Usage & Burnout Checkup",
    page_icon="📊",
    layout="wide",
)

# ---------- CSS ----------
def load_css(file_name: str = "styles_streamlit.css") -> None:
    css_path = Path(__file__).parent / file_name
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css()

# ---------- Theme constants ----------
COLORS = {
    "bg_sidebar": "#F4C9A7",
    "text_dark": "#4A2C18",
    "accent_1": "#C45A1A",
    "accent_2": "#E38D53",
    "card_bg": "#FFFFFF",
    "border_soft": "#E6E6E6",
    "alert_red": "#B4442A",
    "medium_brown": "#9C5A2C",
    "light_orange": "#E9A56D",
    "deep_maroon": "#7A3A2A",
    "soft_gold": "#D9A441",
}

DEADLINE_PRESSURE_MAP = {"Low": 1, "Medium": 2, "High": 3}
DEADLINE_COLORS = ["#D9A441", "#E38D53", "#B4442A"]
AI_BAND_COLORS = ["#D9A441", "#E38D53", "#7A3A2A"]


# ---------- Data loading ----------
@st.cache_data
def load_dashboard_data() -> pd.DataFrame:
    features = pd.read_csv("data/ai_productivity_features.csv")
    targets = pd.read_csv("data/ai_productivity_targets.csv")

    df = features.merge(targets, on="Employee_ID")

    df["workload_score"] = (
        df["manual_work_hours_per_week"]
        + df["meeting_hours_per_week"]
        + df["deadline_pressure_level"].map(DEADLINE_PRESSURE_MAP)
    )

    df["workload_band"] = pd.qcut(
        df["workload_score"],
        q=3,
        labels=["Low", "Medium", "High"],
        duplicates="drop",
    )

    df["ai_band"] = pd.qcut(
        df["ai_tool_usage_hours_per_week"],
        q=3,
        labels=["Low", "Moderate", "High"],
        duplicates="drop",
    )

    return df


# ---------- Helpers ----------
def get_filter_choices(df: pd.DataFrame):
    return {
        "job_role_choices": ["All"] + sorted(df["job_role"].dropna().unique().tolist()),
        "ai_band_choices": ["All"] + sorted(df["ai_band"].dropna().astype(str).unique().tolist()),
        "deadline_choices": sorted(df["deadline_pressure_level"].dropna().unique().tolist()),
    }



def get_slider_ranges(df: pd.DataFrame):
    return {
        "experience": (
            int(df["experience_years"].min()),
            int(df["experience_years"].max()),
        ),
        "ai_usage": (
            int(df["ai_tool_usage_hours_per_week"].min()),
            int(df["ai_tool_usage_hours_per_week"].max()),
        ),
        "manual_hours": (
            int(df["manual_work_hours_per_week"].min()),
            int(df["manual_work_hours_per_week"].max()),
        ),
        "tasks_automated": (
            int(df["tasks_automated_percent"].min()),
            int(df["tasks_automated_percent"].max()),
        ),
    }



def get_baselines(df: pd.DataFrame):
    return {
        "median_burnout": float(df["burnout_risk_score"].median()),
        "median_productivity": float(df["productivity_score"].median()),
        "median_wlb": float(df["work_life_balance_score"].median()),
        "high_burnout_rate": float((df["burnout_risk_level"] == "High").mean()),
    }



def apply_dashboard_filters(
    df: pd.DataFrame,
    job_role,
    ai_band,
    experience,
    ai_usage,
    manual_hours,
    tasks_automated,
    deadline_pressure,
) -> pd.DataFrame:
    d = df.copy()

    if "All" not in job_role:
        d = d[d["job_role"].isin(job_role)]

    if "All" not in ai_band:
        d = d[d["ai_band"].astype(str).isin(ai_band)]

    d = d[
        (d["experience_years"] >= experience[0])
        & (d["experience_years"] <= experience[1])
    ]

    d = d[
        (d["ai_tool_usage_hours_per_week"] >= ai_usage[0])
        & (d["ai_tool_usage_hours_per_week"] <= ai_usage[1])
    ]

    d = d[
        (d["manual_work_hours_per_week"] >= manual_hours[0])
        & (d["manual_work_hours_per_week"] <= manual_hours[1])
    ]

    d = d[
        (d["tasks_automated_percent"] >= tasks_automated[0])
        & (d["tasks_automated_percent"] <= tasks_automated[1])
    ]

    d = d[d["deadline_pressure_level"].isin(deadline_pressure)]

    return d



def percent_diff(value: float, baseline: float) -> float:
    if baseline == 0:
        return 0.0
    return (value - baseline) / baseline



def metric_delta_text(value: float, baseline: float) -> str:
    diff = percent_diff(value, baseline)
    if diff > 0:
        return f"▲ {abs(diff) * 100:.0f}% vs baseline"
    if diff < 0:
        return f"▼ {abs(diff) * 100:.0f}% vs baseline"
    return "→ 0% vs baseline"



def show_metric_card(title: str, value: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-title">{title}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def empty_chart(message: str, height: int = 320) -> alt.Chart:
    return (
        alt.Chart(pd.DataFrame({"text": [message]}))
        .mark_text(align="center", baseline="middle", size=14)
        .encode(text="text:N")
        .properties(height=height)
    )



def make_ai_vs_burnout_chart(d: pd.DataFrame, baseline_median_burnout: float) -> alt.Chart:
    if d.empty:
        return empty_chart("No data for current filters.")

    points = (
        alt.Chart(d)
        .mark_circle(opacity=0.7, size=80)
        .encode(
            x=alt.X("ai_tool_usage_hours_per_week:Q", title="AI tool usage (hrs/week)"),
            y=alt.Y("burnout_risk_score:Q", title="Burnout risk score"),
            color=alt.Color(
                "deadline_pressure_level:N",
                title="Deadline pressure",
                scale=alt.Scale(
                    domain=["Low", "Medium", "High"],
                    range=DEADLINE_COLORS,
                ),
            ),
            tooltip=[
                "job_role:N",
                "experience_years:Q",
                "ai_tool_usage_hours_per_week:Q",
                "manual_work_hours_per_week:Q",
                alt.Tooltip("burnout_risk_score:Q", format=".1f"),
            ],
        )
        .properties(height=320)
    )

    line = (
        alt.Chart(pd.DataFrame({"y": [baseline_median_burnout]}))
        .mark_rule(color=COLORS["alert_red"], strokeDash=[6, 4])
        .encode(y="y:Q")
    )

    return points + line



def make_burnout_by_role_chart(d: pd.DataFrame) -> alt.Chart:
    if d.empty:
        return empty_chart("No data for current filters.")

    summary = (
        d.groupby("job_role", as_index=False)["burnout_risk_score"]
        .mean()
        .rename(columns={"burnout_risk_score": "avg_burnout"})
        .sort_values("avg_burnout", ascending=False)
    )

    return (
        alt.Chart(summary)
        .mark_bar(color=COLORS["medium_brown"])
        .encode(
            x=alt.X("job_role:N", sort="-y", title="Job role", axis=alt.Axis(labelAngle=15)),
            y=alt.Y("avg_burnout:Q", title="Avg burnout risk score"),
            tooltip=["job_role:N", alt.Tooltip("avg_burnout:Q", format=".2f")],
        )
        .properties(height=320)
    )



def make_hours_breakdown_chart(d: pd.DataFrame) -> alt.Chart:
    if d.empty:
        return empty_chart("No data for current filters.")

    weekly_focus = d["focus_hours_per_day"] * 5.0
    breakdown = pd.DataFrame(
        {
            "category": ["Meetings", "Collaboration", "Deep work", "Manual work"],
            "hours": [
                float(d["meeting_hours_per_week"].mean()),
                float(d["collaboration_hours_per_week"].mean()),
                float(weekly_focus.mean()),
                float(d["manual_work_hours_per_week"].mean()),
            ],
        }
    )

    if breakdown["hours"].sum() <= 0:
        return empty_chart("No hours available for current filters.")

    return (
        alt.Chart(breakdown)
        .mark_arc(innerRadius=70)
        .encode(
            theta=alt.Theta("hours:Q"),
            color=alt.Color(
                "category:N",
                title=None,
                scale=alt.Scale(
                    domain=["Meetings", "Collaboration", "Deep work", "Manual work"],
                    range=[
                        COLORS["medium_brown"],
                        COLORS["light_orange"],
                        COLORS["deep_maroon"],
                        COLORS["soft_gold"],
                    ],
                ),
            ),
            tooltip=[
                alt.Tooltip("category:N", title="Category"),
                alt.Tooltip("hours:Q", title="Avg hours/week", format=".1f"),
            ],
        )
        .properties(height=320)
    )


# ---------- Main app ----------
df = load_dashboard_data()
choices = get_filter_choices(df)
ranges = get_slider_ranges(df)
baselines = get_baselines(df)

if "reset_filters" not in st.session_state:
    st.session_state.reset_filters = False

st.markdown("<h1 class='main-title'>AI Usage & Burnout Checkup</h1>", unsafe_allow_html=True)
st.markdown(
    "<p class='subtitle'>A simplified Streamlit version of the original dashboard.</p>",
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## Filters")

    if st.button("Reset filters", use_container_width=True):
        st.session_state.clear()
        st.rerun()

    job_role = st.multiselect(
        "Job role",
        options=choices["job_role_choices"],
        default=["All"],
    )

    ai_band = st.multiselect(
        "AI usage band",
        options=choices["ai_band_choices"],
        default=["All"],
    )

    experience = st.slider(
        "Experience (years)",
        min_value=ranges["experience"][0],
        max_value=ranges["experience"][1],
        value=ranges["experience"],
    )

    ai_usage = st.slider(
        "Weekly AI usage",
        min_value=ranges["ai_usage"][0],
        max_value=ranges["ai_usage"][1],
        value=ranges["ai_usage"],
    )

    manual_hours = st.slider(
        "Manual work hours",
        min_value=ranges["manual_hours"][0],
        max_value=ranges["manual_hours"][1],
        value=ranges["manual_hours"],
    )

    tasks_automated = st.slider(
        "Tasks automated (%)",
        min_value=ranges["tasks_automated"][0],
        max_value=ranges["tasks_automated"][1],
        value=ranges["tasks_automated"],
    )

    deadline_pressure = st.multiselect(
        "Deadline pressure",
        options=choices["deadline_choices"],
        default=choices["deadline_choices"],
    )

filtered_df = apply_dashboard_filters(
    df=df,
    job_role=job_role,
    ai_band=ai_band,
    experience=experience,
    ai_usage=ai_usage,
    manual_hours=manual_hours,
    tasks_automated=tasks_automated,
    deadline_pressure=deadline_pressure,
)

# ---------- KPI row ----------
col1, col2, col3, col4 = st.columns(4)

if filtered_df.empty:
    with col1:
        show_metric_card("Median Burnout Risk", "—")
    with col2:
        show_metric_card("High Burnout %", "—")
    with col3:
        show_metric_card("Median Productivity", "—")
    with col4:
        show_metric_card("Median Work-Life Balance", "—")
else:
    burnout_val = float(filtered_df["burnout_risk_score"].median())
    high_burnout_pct = float((filtered_df["burnout_risk_level"] == "High").mean())
    productivity_val = float(filtered_df["productivity_score"].median())
    wlb_val = float(filtered_df["work_life_balance_score"].median())

    with col1:
        show_metric_card(
            "Median Burnout Risk",
            f"{burnout_val:.1f}",
            metric_delta_text(burnout_val, baselines["median_burnout"]),
        )
    with col2:
        show_metric_card(
            "High Burnout %",
            f"{high_burnout_pct * 100:.1f}%",
            metric_delta_text(high_burnout_pct, baselines["high_burnout_rate"]),
        )
    with col3:
        show_metric_card(
            "Median Productivity",
            f"{productivity_val:.1f}",
            metric_delta_text(productivity_val, baselines["median_productivity"]),
        )
    with col4:
        show_metric_card(
            "Median Work-Life Balance",
            f"{wlb_val:.1f}",
            metric_delta_text(wlb_val, baselines["median_wlb"]),
        )

# ---------- Charts ----------
left1, right1 = st.columns(2)
with left1:
    st.markdown("### AI Usage vs Burnout")
    st.altair_chart(
        make_ai_vs_burnout_chart(filtered_df, baselines["median_burnout"]),
        use_container_width=True,
    )
with right1:
    st.markdown("### Burnout Risk by Job Role")
    st.altair_chart(make_burnout_by_role_chart(filtered_df), use_container_width=True)

left2, right2 = st.columns(2)
with left2:
    st.markdown("### Weekly Work Hours Breakdown")
    st.altair_chart(make_hours_breakdown_chart(filtered_df), use_container_width=True)
with right2:
    st.markdown("### Filtered Data Preview")
    st.dataframe(filtered_df, use_container_width=True, height=320)
    csv = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered data",
        data=csv,
        file_name="filtered_data.csv",
        mime="text/csv",
        use_container_width=True,
    )
