"""SpaceScope: a space-themed, MongoDB-backed launch-log dashboard."""

import os
import random
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from pymongo import MongoClient
from pymongo.errors import PyMongoError

st.set_page_config(page_title="SpaceScope", page_icon="🚀", layout="wide")

MISSING_LABEL = "N/A"
FILTER_KEYS = (
    "filter_organization",
    "filter_vehicle",
    "filter_mission",
    "filter_flight",
    "filter_site",
    "filter_category",
    "filter_year",
    "search_query",
    "table_page",
)


def starfield(count: int, seed: int) -> str:
    rng = random.Random(seed)
    return ",".join(
        f"{rng.randint(0, 2000)}px {rng.randint(0, 1600)}px #fff"
        for _ in range(count)
    )


st.markdown(
    f"""
    <style>
    .stApp {{
        background: radial-gradient(ellipse at 50% 115%, #172d4d 0%, #0c1427 45%, #070a16 100%);
        color: #edf4ff;
    }}
    header[data-testid="stHeader"] {{ background: transparent; }}
    [data-testid="stAppViewContainer"] {{ background: transparent; }}
    .block-container {{ max-width: 1440px; padding: 1.2rem 2rem 3rem; position: relative; z-index: 1; }}
    section[data-testid="stSidebar"] {{
        background: rgba(7, 12, 27, .96);
        border-right: 1px solid rgba(125, 211, 252, .18);
    }}
    .stars, .stars::before, .stars::after {{
        position: fixed; inset: 0; display: block; pointer-events: none;
        background: transparent; border-radius: 50%; z-index: 0;
    }}
    .stars {{ width: 1px; height: 1px; box-shadow: {starfield(150, 7)}; animation: drift 120s linear infinite; }}
    .stars::before {{ content: ""; width: 2px; height: 2px; box-shadow: {starfield(55, 12)}; animation: drift 85s linear infinite; }}
    .stars::after {{ content: ""; width: 3px; height: 3px; box-shadow: {starfield(18, 19)}; animation: twinkle 4s ease-in-out infinite; }}
    @keyframes drift {{ to {{ transform: translateY(-900px); }} }}
    @keyframes twinkle {{ 50% {{ opacity: .3; }} }}
    .spacecraft {{
        position: fixed; left: -3rem; z-index: 0; pointer-events: none;
        opacity: .32; filter: drop-shadow(0 0 8px rgba(125, 211, 252, .5));
    }}
    .craft-one {{ top: 24%; font-size: 1.5rem; animation: fly 95s linear infinite; }}
    .craft-two {{ top: 73%; font-size: 1.2rem; animation: fly 125s linear 30s infinite; }}
    @keyframes fly {{ to {{ transform: translateX(110vw) rotate(7deg); }} }}
    .hero {{ text-align: center; padding: .5rem 0 1.35rem; }}
    .hero h1 {{
        margin: 0; font-size: clamp(2.2rem, 5vw, 3.8rem); font-weight: 850;
        letter-spacing: .1em; color: #e6f7ff;
        text-shadow: 0 0 28px rgba(56, 189, 248, .28);
    }}
    .hero p {{ color: #b6c5dc; margin: .45rem 0 0; }}
    .kpi {{
        min-height: 108px; padding: 17px 19px; border-radius: 15px;
        border: 1px solid rgba(125, 211, 252, .2);
        background: linear-gradient(145deg, rgba(22, 39, 66, .92), rgba(12, 19, 36, .92));
        box-shadow: 0 12px 28px rgba(0, 0, 0, .16);
    }}
    .kpi-label {{ color: #b3c2da; font-size: .67rem; letter-spacing: .045em; text-transform: uppercase; }}
    .kpi-value {{ color: #f1f8ff; font-size: clamp(1.45rem, 2.2vw, 2rem); font-weight: 800; margin-top: 8px; }}
    h2, h3 {{ color: #e6f4ff !important; }}
    div[data-testid="stPlotlyChart"] {{
        border: 1px solid rgba(148, 163, 184, .16);
        border-radius: 14px; background: rgba(10, 16, 31, .55); padding: 6px;
    }}
    div[data-testid="stDataFrame"] {{ border: 1px solid rgba(148, 163, 184, .2); border-radius: 12px; }}
    div[data-testid="stAlert"] {{
        background: rgba(18, 38, 65, .92);
        border: 1px solid rgba(125, 211, 252, .22);
    }}
    div[data-testid="stAlert"] p {{ color: #e6f0ff; }}
    @media (max-width: 720px) {{
        .block-container {{ padding: 1rem .8rem 2rem; }}
    }}
    </style>
    <div class="stars"></div>
    <div class="spacecraft craft-one">🚀</div><div class="spacecraft craft-two">🛰️</div>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=300, show_spinner="Connecting to mission control...")
def get_launches(mongo_uri: str, database: str) -> pd.DataFrame:
    """Cache one collection read; all dashboard filtering then happens in memory."""
    with MongoClient(mongo_uri, serverSelectionTimeoutMS=5000) as client:
        client.admin.command("ping")
        records = list(client[database]["launches"].find({}, {"_id": 0}))
    return pd.DataFrame(records)


def clear_all_filters() -> None:
    for key in FILTER_KEYS:
        st.session_state[key] = 1 if key == "table_page" else ("" if key == "search_query" else [])


def clear_search() -> None:
    st.session_state["search_query"] = ""
    st.session_state["table_page"] = 1


def clean_text(series: pd.Series) -> pd.Series:
    text = series.astype("string").str.strip()
    empty = text.str.lower().isin({"", "-", "?", "none", "null", "nan", "n/a"})
    return text.mask(empty, pd.NA)


def distinct_options(frame: pd.DataFrame, column: str) -> list[str]:
    if column not in frame:
        return []
    values = clean_text(frame[column]).dropna().unique().tolist()
    return sorted(values, key=str.casefold)


def number_of_distinct(frame: pd.DataFrame, column: str) -> int | None:
    if column not in frame:
        return None
    return int(clean_text(frame[column]).nunique(dropna=True))


def style_chart(fig, height: int = 340, show_legend: bool = False):
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(l=12, r=16, t=35, b=12),
        font=dict(color="#d8e5f5"),
        showlegend=show_legend,
    )
    return fig


def show_donut_chart(frame: pd.DataFrame, column: str, color: str, height: int = 365):
    values = clean_text(frame[column]).dropna()
    if values.empty:
        st.info(f"{column.replace('_', ' ').title()} values are not available for these records.")
        return
    counts = values.value_counts()
    top = counts.head(8)
    remainder = int(counts.iloc[8:].sum())
    if remainder:
        top.loc["Other values"] = remainder
    summary = top.rename_axis("label").reset_index(name="records")
    fig = px.pie(
        summary,
        names="label",
        values="records",
        hole=.58,
        color_discrete_sequence=px.colors.sequential.Teal if color == "#49d8b5" else [color],
        custom_data=["records"],
        labels={"records": "Launch records", "label": column.replace("_", " ").title()},
    )
    fig.update_traces(
        textposition="inside",
        textinfo="percent",
        hovertemplate="%{label}<br>%{value:,} launch records<br>%{percent}<extra></extra>",
        marker=dict(line=dict(color="rgba(7, 10, 22, .85)", width=2)),
    )
    fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-.08, xanchor="center", x=.5))
    st.plotly_chart(style_chart(fig, height, show_legend=True), width="stretch")


mongo_uri = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
database = os.environ.get("MONGO_DB", "spacescope")

try:
    launches = get_launches(mongo_uri, database)
except PyMongoError as error:
    st.error("MongoDB is unavailable. Check MongoDB is running and verify `MONGO_URI`.")
    st.caption(f"Connection error type: {type(error).__name__}")
    st.stop()

if launches.empty:
    st.markdown('<div class="hero"><h1>🚀 SPACESCOPE</h1><p>Your window to the launch universe</p></div>', unsafe_allow_html=True)
    st.info("No records are stored yet. Run `python load_data.py` from the project folder to import the dataset.")
    st.stop()

if "company" not in launches:
    st.error("The MongoDB collection is missing the organization field. Run `python load_data.py` to normalize the source data.")
    st.stop()

for column in ("rocket", "mission", "flight", "site", "pad", "category", "launch_code", "fail_code", "source_launch_label", "source_julian_day", "orbital_payload", "destination", "apogee", "date", "year", "outcome"):
    if column not in launches:
        launches[column] = pd.NA

for column in ("company", "rocket", "mission", "flight", "site", "pad", "category", "launch_code", "fail_code", "source_launch_label"):
    launches[column] = clean_text(launches[column])

launches["date"] = pd.to_datetime(launches["date"], errors="coerce")
launches["year"] = pd.to_numeric(launches["year"], errors="coerce")
calendar_year = launches["date"].dt.year
unreliable_date = calendar_year.lt(1940) | calendar_year.gt(datetime.now().year + 1)
launches["date"] = launches["date"].mask(unreliable_date)
launches["year"] = launches["year"].mask(unreliable_date)

year_caption = "dates not available" if launches["date"].notna().sum() == 0 else (
    f"{int(launches['date'].dt.year.min())}–{int(launches['date'].dt.year.max())}"
)
st.markdown(
    f"""
    <div class="hero">
      <h1>🚀 SPACESCOPE</h1>
      <p>Launch-log analytics · {year_caption} · Hugging Face dataset</p>
    </div>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## 🛰️ Flight controls")
    st.caption(f"{len(launches):,} source records")
    st.button("↺ Reset all filters", on_click=clear_all_filters, width="stretch")

    organizations = distinct_options(launches, "company")
    vehicles = distinct_options(launches, "rocket")
    missions = distinct_options(launches, "mission")
    flights = distinct_options(launches, "flight")
    sites = distinct_options(launches, "site")
    categories = distinct_options(launches, "category")

    selected_organizations = st.multiselect("Organization", organizations, key="filter_organization")
    selected_vehicles = st.multiselect("Vehicle", vehicles, key="filter_vehicle")
    selected_missions = st.multiselect("Mission label", missions, key="filter_mission")
    selected_flights = st.multiselect("Flight identifier", flights, key="filter_flight")
    selected_sites = st.multiselect("Launch site code", sites, key="filter_site")
    selected_categories = st.multiselect("Category", categories, key="filter_category")

    available_years = sorted(launches["date"].dropna().dt.year.unique().tolist())
    selected_years = []
    if available_years:
        selected_years = st.multiselect(
            "Launch year",
            [int(year) for year in available_years],
            key="filter_year",
        )
    else:
        st.caption("No reliable calendar dates in the source; date filtering is unavailable.")
    st.caption("Mission outcomes are not supplied reliably by this dataset.")

filtered = launches.copy()
filter_values = {
    "company": selected_organizations,
    "rocket": selected_vehicles,
    "mission": selected_missions,
    "flight": selected_flights,
    "site": selected_sites,
    "category": selected_categories,
}
for column, selected in filter_values.items():
    if selected:
        filtered = filtered[clean_text(filtered[column]).isin(selected)]
if selected_years:
    filtered = filtered[filtered["date"].dt.year.isin(selected_years)]

st.subheader("📊 Mission overview")

search_left, search_right = st.columns([4, 1])
with search_left:
    search_query = st.text_input(
        "Search organization, vehicle, mission, flight, or launch site",
        placeholder="Try an organization, vehicle, mission, or site",
        key="search_query",
    )
with search_right:
    st.button("Clear", help="Clear the mission log search", on_click=clear_search, width="stretch")

if search_query.strip():
    search_columns = ("company", "rocket", "mission", "flight", "site", "pad", "category", "source_launch_label")
    matches = pd.Series(False, index=filtered.index)
    for column in search_columns:
        values = clean_text(filtered[column])
        matches |= values.str.contains(search_query.strip(), case=False, na=False, regex=False)
    filtered = filtered[matches]

active_filters = []
for label, selected in (
    ("Organization", selected_organizations),
    ("Vehicle", selected_vehicles),
    ("Mission", selected_missions),
    ("Flight", selected_flights),
    ("Launch site code", selected_sites),
    ("Category", selected_categories),
    ("Year", selected_years),
):
    if selected:
        active_filters.append(f"**{label}:** {', '.join(map(str, selected[:4]))}{'…' if len(selected) > 4 else ''}")
if search_query.strip():
    active_filters.append(f"**Search:** {search_query.strip()}")
if active_filters:
    st.caption("Active filters · " + " · ".join(active_filters))
else:
    st.caption("Showing all stored records.")

if "orbital_payload" not in filtered:
    filtered["orbital_payload"] = pd.NA
filtered["orbital_payload"] = pd.to_numeric(filtered["orbital_payload"], errors="coerce")

total_records = len(launches)
matched_records = len(filtered)
quality_fields = {
    "Organization": "company",
    "Vehicle": "rocket",
    "Mission label": "mission",
    "Flight": "flight",
    "Launch site": "site",
    "Category": "category",
}
if matched_records:
    complete_mask = pd.Series(True, index=filtered.index)
    for field in quality_fields.values():
        complete_mask &= clean_text(filtered[field]).notna()
    complete_percentage = complete_mask.mean() * 100
    missing_dates = int(filtered["date"].isna().sum())
    missing_vehicles = int(clean_text(filtered["rocket"]).isna().sum())
else:
    complete_percentage = 0.0
    missing_dates = 0
    missing_vehicles = 0

kpis = [
    ("🚀", "Total launch records", f"{total_records:,}", "All records in MongoDB"),
    ("🔎", "Matching filters", f"{matched_records:,}", "Records after filters and search"),
    ("🏢", "Organizations", f"{number_of_distinct(filtered, 'company') or 0:,}", "Distinct organization names"),
    ("🛰️", "Vehicle types", f"{number_of_distinct(filtered, 'rocket') or 0:,}", "Distinct non-missing vehicle names"),
    ("📋", "Mission labels", f"{number_of_distinct(filtered, 'mission') or 0:,}", "Distinct labels; not unique mission IDs"),
    ("📅", "Missing dates", f"{missing_dates:,}", f"{missing_dates / matched_records * 100:.1f}% of matching records" if matched_records else "No matching records"),
    ("🛠️", "Missing vehicles", f"{missing_vehicles:,}", f"{missing_vehicles / matched_records * 100:.1f}% of matching records" if matched_records else "No matching records"),
    ("✅", "Complete records", f"{complete_percentage:.1f}%", "Organization, vehicle, mission, flight, site and category present"),
]

tabs = st.tabs(
    ["Overview", "Organization Analytics", "Vehicle Analytics", "Mission Trends", "Data Quality", "Mission Log"]
)

with tabs[0]:
    st.subheader("🚀 Mission overview")
    st.caption("KPI values update with the selected filters. Total records always refers to the full MongoDB collection.")
    for start_index in (0, 4):
        columns = st.columns(4)
        for column, (icon, label, value, detail) in zip(columns, kpis[start_index : start_index + 4]):
            column.markdown(
                f'<div class="kpi"><div class="kpi-label">{icon} {label}</div>'
                f'<div class="kpi-value">{value}</div><div class="kpi-label">{detail}</div></div>',
                unsafe_allow_html=True,
            )

    if filtered.empty:
        st.info("No records match the current filters. Use Reset all filters to restore the full dataset.")
    else:
        org_col, vehicle_col = st.columns(2)
        with org_col:
            st.markdown("#### Launch records by organization")
            org_counts = clean_text(filtered.company).dropna().value_counts().head(10).sort_values()
            fig = px.bar(
                org_counts,
                x=org_counts.values,
                y=org_counts.index,
                orientation="h",
                labels={"x": "Launch records", "y": "Organization"},
                color_discrete_sequence=["#8b9cff"],
            )
            fig.update_traces(hovertemplate="%{y}<br>%{x:,} records<extra></extra>")
            st.plotly_chart(style_chart(fig, 360), width="stretch")
        with vehicle_col:
            st.markdown("#### Top recorded vehicle types")
            vehicle_counts = clean_text(filtered.rocket).dropna().value_counts().head(10).sort_values()
            fig = px.bar(
                vehicle_counts,
                x=vehicle_counts.values,
                y=vehicle_counts.index,
                orientation="h",
                labels={"x": "Launch records", "y": "Vehicle"},
                color_discrete_sequence=["#49d8b5"],
            )
            fig.update_traces(hovertemplate="%{y}<br>%{x:,} records<extra></extra>")
            st.plotly_chart(style_chart(fig, 360), width="stretch")

with tabs[1]:
    st.subheader("🏢 Organization Analytics")
    control_col, top_col = st.columns([2, 1])
    with control_col:
        organization_chart = st.selectbox(
            "Organization chart type",
            ["Bar chart", "Horizontal bar chart", "Pie chart", "Donut chart"],
            key="organization_chart_type",
        )
    with top_col:
        organization_limit = st.selectbox("Organizations to show", [5, 10, 20], index=1, key="organization_top_n")
    all_org_values = clean_text(filtered.company).dropna().value_counts()
    org_values = all_org_values.head(organization_limit)
    if org_values.empty:
        st.info("Organization data is unavailable for the current selection.")
    else:
        org_plot = org_values.rename_axis("Organization").reset_index(name="Launch records")
        if organization_chart in {"Pie chart", "Donut chart"}:
            top = all_org_values.head(organization_limit - 1 if len(all_org_values) > organization_limit else organization_limit)
            other = int(all_org_values.sum() - top.sum())
            if other:
                top.loc["Other organizations"] = other
            pie_data = top.rename_axis("Organization").reset_index(name="Launch records")
            fig = px.pie(
                pie_data,
                names="Organization",
                values="Launch records",
                hole=.58 if organization_chart == "Donut chart" else 0,
                color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig.update_traces(
                textposition="inside",
                textinfo="percent",
                hovertemplate="%{label}<br>%{value:,} launch records<br>%{percent}<extra></extra>",
            )
            fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-.08, xanchor="center", x=.5))
        else:
            horizontal = organization_chart == "Horizontal bar chart"
            org_plot = org_plot.sort_values("Launch records", ascending=horizontal)
            fig = px.bar(
                org_plot,
                x="Launch records" if horizontal else "Organization",
                y="Organization" if horizontal else "Launch records",
                orientation="h" if horizontal else "v",
                color_discrete_sequence=["#8b9cff"],
                labels={"Launch records": "Launch records", "Organization": "Organization"},
            )
            fig.update_traces(hovertemplate="%{x}<br>%{y:,} records<extra></extra>" if not horizontal else "%{y}<br>%{x:,} records<extra></extra>")
        st.plotly_chart(style_chart(fig, 480, show_legend=organization_chart in {"Pie chart", "Donut chart"}), width="stretch")
        st.caption(
            f"Showing up to {organization_limit} organizations within the filtered records. "
            "Pie and donut charts group remaining organizations into Other organizations."
        )

    st.markdown("#### Organization × mission category")
    categorized = filtered.dropna(subset=["company", "category"])
    if categorized.empty:
        st.info("No organization/category combinations are available for this selection.")
    else:
        top_orgs = categorized.company.value_counts().head(10).index
        top_categories = categorized.category.value_counts().head(8).index
        hierarchy = categorized[
            categorized.company.isin(top_orgs) & categorized.category.isin(top_categories)
        ].groupby(["company", "category"], observed=True).size().rename("Records").reset_index()
        st.caption("Comparison charts include the 10 most-recorded organizations and 8 most-recorded categories.")
        tree_col, stacked_col = st.columns(2)
        with tree_col:
            fig = px.treemap(
                hierarchy,
                path=["company", "category"],
                values="Records",
                color="company",
                color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig.update_traces(hovertemplate="%{label}<br>%{value:,} records<extra></extra>")
            st.plotly_chart(style_chart(fig, 430), width="stretch")
        with stacked_col:
            comparison = st.selectbox(
                "Category comparison style",
                ["Stacked", "Grouped"],
                key="organization_category_stacking",
            )
            fig = px.bar(
                hierarchy,
                x="company",
                y="Records",
                color="category",
                barmode="stack" if comparison == "Stacked" else "group",
                labels={"company": "Organization", "Records": "Launch records", "category": "Mission category"},
                color_discrete_sequence=px.colors.qualitative.Safe,
            )
            fig.update_layout(xaxis_tickangle=-35, legend_title_text="Mission category")
            st.plotly_chart(style_chart(fig, 430, show_legend=True), width="stretch")

with tabs[2]:
    st.subheader("🛰️ Vehicle Analytics")
    vehicle_control, vehicle_limit_col = st.columns([2, 1])
    with vehicle_control:
        vehicle_chart = st.selectbox(
            "Vehicle chart type",
            ["Horizontal bar chart", "Bar chart", "Donut chart"],
            key="vehicle_chart_type",
        )
    with vehicle_limit_col:
        vehicle_limit = st.selectbox("Vehicles to show", [5, 10, 20], index=1, key="vehicle_top_n")
    all_vehicle_values = clean_text(filtered.rocket).dropna().value_counts()
    vehicle_values = all_vehicle_values.head(vehicle_limit)
    if vehicle_values.empty:
        st.info("Vehicle names are unavailable for the current selection.")
    else:
        vehicle_data = vehicle_values.rename_axis("Vehicle").reset_index(name="Launch records")
        if vehicle_chart == "Donut chart":
            pie_values = all_vehicle_values.head(
                vehicle_limit - 1 if len(all_vehicle_values) > vehicle_limit else vehicle_limit
            ).copy()
            other_vehicles = int(all_vehicle_values.sum() - pie_values.sum())
            if other_vehicles:
                pie_values.loc["Other vehicles"] = other_vehicles
            vehicle_data = pie_values.rename_axis("Vehicle").reset_index(name="Launch records")
            fig = px.pie(vehicle_data, names="Vehicle", values="Launch records", hole=.58,
                         color_discrete_sequence=px.colors.qualitative.Safe)
            fig.update_traces(textposition="inside", textinfo="percent",
                              hovertemplate="%{label}<br>%{value:,} records<br>%{percent}<extra></extra>")
            fig.update_layout(legend=dict(orientation="h", yanchor="top", y=-.08, xanchor="center", x=.5))
        else:
            horizontal = vehicle_chart == "Horizontal bar chart"
            vehicle_data = vehicle_data.sort_values("Launch records", ascending=horizontal)
            fig = px.bar(
                vehicle_data,
                x="Launch records" if horizontal else "Vehicle",
                y="Vehicle" if horizontal else "Launch records",
                orientation="h" if horizontal else "v",
                color_discrete_sequence=["#49d8b5"],
                labels={"Launch records": "Launch records", "Vehicle": "Vehicle"},
            )
            fig.update_traces(hovertemplate="%{y}<br>%{x:,} records<extra></extra>" if horizontal else "%{x}<br>%{y:,} records<extra></extra>")
        st.plotly_chart(style_chart(fig, 460, show_legend=vehicle_chart == "Donut chart"), width="stretch")

    st.markdown("#### Recorded orbital-payload values")
    payload = pd.to_numeric(filtered["orbital_payload"], errors="coerce").dropna()
    payload = payload[payload > 0]
    if payload.empty:
        st.info("No positive orbital-payload values are available for this selection.")
    else:
        fig = px.histogram(
            payload,
            nbins=40,
            labels={"value": "Recorded orbital-payload value", "count": "Launch records"},
            color_discrete_sequence=["#f5b85c"],
        )
        fig.update_layout(bargap=.08)
        fig.update_traces(hovertemplate="Payload value: %{x}<br>Records: %{y}<extra></extra>")
        st.plotly_chart(style_chart(fig, 360), width="stretch")
        st.caption("Only positive source values are plotted. Units and measurement conventions are not specified in this dataset.")

with tabs[3]:
    st.subheader("🕰️ Mission Trends")
    dated = filtered.dropna(subset=["date"]).copy()
    if dated.empty:
        st.info(
            "A time-series chart cannot be produced: the source `launch_date` values "
            "are mostly labels and the sparse `launch_jd` values are inconsistent. "
            "The dashboard preserves these source fields without converting them "
            "into fabricated calendar dates."
        )
    else:
        interval = st.selectbox("Trend interval", ["Year", "Month"], key="trend_interval")
        if interval == "Year":
            dated["period"] = dated.date.dt.year
        else:
            dated["period"] = dated.date.dt.to_period("M").astype(str)
        trend = dated.groupby("period").size().rename("Launch records").reset_index()
        trend["Cumulative records"] = trend["Launch records"].cumsum()
        trend_type = st.selectbox("Trend visualization", ["Line", "Area"], key="trend_type")
        y_value = "Launch records" if trend_type == "Line" else "Cumulative records"
        fig = px.line(trend, x="period", y=y_value, markers=True,
                      labels={"period": interval, y_value: y_value})
        if trend_type == "Area":
            fig.update_traces(fill="tozeroy")
        st.plotly_chart(style_chart(fig, 440), width="stretch")

    numeric_pairs = [
        ("orbital_payload", "destination"),
        ("orbital_payload", "apogee"),
    ]
    def has_usable_numeric_range(field: str) -> bool:
        if field not in filtered:
            return False
        values = pd.to_numeric(filtered[field], errors="coerce").dropna()
        return len(values) >= 30 and values.nunique() >= 3 and int(values.ne(0).sum()) >= 30

    reliable_pairs = [
        (x, y) for x, y in numeric_pairs
        if has_usable_numeric_range(x) and has_usable_numeric_range(y)
    ]
    if reliable_pairs:
        x_field, y_field = reliable_pairs[0]
        scatter = filtered[[x_field, y_field, "company"]].copy()
        scatter[x_field] = pd.to_numeric(scatter[x_field], errors="coerce")
        scatter[y_field] = pd.to_numeric(scatter[y_field], errors="coerce")
        scatter = scatter.dropna().head(5000)
        fig = px.scatter(scatter, x=x_field, y=y_field, color="company",
                         labels={x_field: x_field.replace("_", " ").title(),
                                 y_field: y_field.replace("_", " ").title()})
        st.plotly_chart(style_chart(fig, 440, show_legend=True), width="stretch")
    else:
        st.info(
            "A scatter plot needs two reliable numerical measures. The source has "
            "orbital-payload values, but `apogee` is almost entirely missing and "
            "`destination` is nearly constant; plotting them together would be misleading."
        )

with tabs[4]:
    st.subheader("🧹 Data Quality")
    quality_rows = []
    complete_mask = pd.Series(True, index=filtered.index)
    for label, field in quality_fields.items():
        available = clean_text(filtered[field]).notna()
        missing_count = int((~available).sum())
        available_count = int(available.sum())
        complete_mask &= available
        quality_rows.append(
            {
                "Field": label,
                "Available": available_count,
                "Missing": missing_count,
                "Missing (%)": missing_count / len(filtered) * 100 if len(filtered) else 0,
            }
        )
    for label, available in (
        ("Reliable calendar date", filtered["date"].notna()),
        ("Standardized mission outcome", clean_text(filtered["outcome"]).notna()),
    ):
        missing_count = int((~available).sum())
        quality_rows.append(
            {
                "Field": label,
                "Available": int(available.sum()),
                "Missing": missing_count,
                "Missing (%)": missing_count / len(filtered) * 100 if len(filtered) else 0,
            }
        )
    quality = pd.DataFrame(quality_rows)
    if len(filtered):
        quality_chart = quality.sort_values("Missing (%)")
        fig = px.bar(
            quality_chart,
            x="Missing (%)",
            y="Field",
            orientation="h",
            color="Missing (%)",
            color_continuous_scale=["#49d8b5", "#f5b85c", "#e87991"],
            hover_data={"Missing": True, "Available": True, "Missing (%)": ":.1f"},
            labels={"Missing (%)": "Missing values (%)"},
        )
        fig.update_layout(coloraxis_showscale=False, xaxis=dict(range=[0, 100], ticksuffix="%"))
        st.plotly_chart(style_chart(fig, 390), width="stretch")
    st.dataframe(quality, width="stretch", hide_index=True)
    complete_count = int(complete_mask.sum())
    st.metric(
        "Records with all six core fields",
        f"{complete_count:,} / {len(filtered):,}",
        f"{complete_count / len(filtered) * 100:.1f}% complete" if len(filtered) else "No matching records",
    )
    st.info(
        "Core fields are organization, vehicle, mission label, flight, launch site, "
        "and category. Source dates, outcomes, and country are not included in this "
        "completeness percentage because reliable values are not provided."
    )
    st.markdown("#### Source-code frequency")
    code_left, code_right = st.columns(2)
    for container, field, title in (
        (code_left, "launch_code", "Launch codes"),
        (code_right, "fail_code", "Failure codes"),
    ):
        with container:
            st.markdown(f"##### {title}")
            counts = clean_text(filtered[field]).dropna().value_counts().head(15)
            if counts.empty:
                st.info("No source code values available.")
            else:
                st.dataframe(counts.rename_axis("Source code").reset_index(name="Records"),
                             width="stretch", hide_index=True)

with tabs[5]:
    st.subheader("📡 Mission Log")
    st.caption(f"{len(filtered):,} matching records")
    if filtered.empty:
        st.info("No records match the current filters. Use Reset all filters to restore the full dataset.")
    else:
        table_columns = [
            ("date", "Date"),
            ("company", "Organization"),
            ("rocket", "Vehicle"),
            ("mission", "Mission"),
            ("flight", "Flight"),
            ("site", "Launch site"),
            ("pad", "Launch pad"),
            ("category", "Category"),
            ("source_launch_label", "Source launch label"),
            ("source_julian_day", "Source Julian-day value"),
            ("launch_code", "Launch code"),
            ("fail_code", "Failure code"),
        ]
        visible_columns = [(field, label) for field, label in table_columns if field in filtered]
        sort_options = {
            label: field
            for field, label in visible_columns
            if field not in {"source_launch_label", "source_julian_day"}
            and (field != "date" or filtered[field].notna().any())
        }
        default_sort = "Organization" if "Organization" in sort_options else next(iter(sort_options))
        sort_left, sort_right, page_size_col = st.columns([2, 1, 1])
        with sort_left:
            sort_label = st.selectbox("Sort records by", list(sort_options),
                                      index=list(sort_options).index(default_sort), key="table_sort_field")
        with sort_right:
            sort_direction = st.selectbox("Order", ["Descending", "Ascending"], key="table_sort_order")
        with page_size_col:
            page_size = st.selectbox("Rows per page", [25, 50, 100], index=1, key="table_page_size")

        sort_field = sort_options[sort_label]
        sort_column = filtered[sort_field]
        if sort_field in {"company", "rocket", "mission", "flight", "site", "pad", "category", "launch_code", "fail_code"}:
            sort_column = clean_text(sort_column).str.casefold()
        sorted_filtered = filtered.assign(_missing=sort_column.isna(), _sort=sort_column).sort_values(
            ["_missing", "_sort"],
            ascending=[True, sort_direction == "Ascending"],
            na_position="last",
            kind="stable",
        )
        page_count = max(1, (len(sorted_filtered) + page_size - 1) // page_size)
        st.session_state["table_page"] = min(
            max(1, st.session_state.get("table_page", 1)), page_count
        )
        page = st.number_input("Page", min_value=1, max_value=page_count, step=1, key="table_page")
        start = (int(page) - 1) * page_size
        page_frame = sorted_filtered.iloc[start : start + page_size]
        display_frame = pd.DataFrame(index=page_frame.index)
        for field, label in visible_columns:
            values = page_frame[field]
            if field == "date":
                values = pd.to_datetime(values, errors="coerce").dt.strftime("%Y-%m-%d")
            else:
                values = clean_text(values)
            display_frame[label] = values.fillna(MISSING_LABEL)
        st.dataframe(display_frame, width="stretch", hide_index=True, height=460)
        st.caption(
            f"Page {int(page)} of {page_count} · records {start + 1:,}–"
            f"{min(start + page_size, len(sorted_filtered)):,} of {len(sorted_filtered):,}"
        )

st.caption(
    "Data source: juliensimon/space-launch-log on Hugging Face. "
    "Reliable calendar dates, standardized outcomes, and country values are not available."
)
