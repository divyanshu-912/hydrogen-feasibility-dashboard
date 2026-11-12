"""
Hydrogen Retrofit vs BEV — Feasibility Dashboard
==================================================
B.Tech subject project (Industry 4.0 & IoT).

Run with:  streamlit run app.py

All figures on this dashboard are read directly from the project's own
files (data/dataset.csv, data/tco_analysis.xlsx, data/feasibility_comparison.xlsx)
via data_loader.py, or computed live from data/dataset.csv via ml.py.
See README.md for the one place where a source file (analysis_results.xlsx)
was not supplied and what was done instead.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio

import data_loader as dl
import ml

st.set_page_config(
    page_title="H2 Retrofit vs BEV — Feasibility Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# Styling
# ----------------------------------------------------------------------
H2_COLOR = "#E4572E"   # warm orange-red for hydrogen retrofit
BEV_COLOR = "#2E86AB"  # blue for BEV
NEUTRAL = "#6B7280"

pio.templates["h2bev"] = go.layout.Template(layout=dict(
    font=dict(family="Inter, Segoe UI, system-ui, sans-serif", size=13, color="#C9CFDA"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    colorway=[H2_COLOR, BEV_COLOR, "#F2A541", "#7BC8A4", "#9B8AE6", "#8A94A6"],
    title=dict(font=dict(size=15, color="#F1F3F8"), x=0.0, xanchor="left"),
    margin=dict(l=48, r=20, t=56, b=44),
    xaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.12)",
               linecolor="rgba(255,255,255,0.15)", ticks="outside", tickcolor="rgba(255,255,255,0.15)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.06)", zerolinecolor="rgba(255,255,255,0.12)",
               linecolor="rgba(255,255,255,0.15)"),
    legend=dict(bgcolor="rgba(0,0,0,0)", orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hoverlabel=dict(bgcolor="#1B2233", bordercolor="#2B3550", font=dict(color="#F1F3F8")),
    bargap=0.25,
))
pio.templates.default = "plotly_dark+h2bev"

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    :root {
        --bg: #0B0F17; --panel: #131926; --panel-2: #181F2F; --line: #232C42;
        --text: #E6E9EF; --muted: #8E98AB; --h2: #E4572E; --bev: #2E86AB; --gold: #D9B45B;
    }
    html, body, [class*="css"], .stApp { font-family: 'Inter', 'Segoe UI', system-ui, sans-serif; }
    .block-container { padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1280px; }

    h1 { font-weight: 700; letter-spacing: -0.02em; font-size: 2.1rem !important; margin-bottom: 0.2rem; }
    h2, h3 { font-weight: 600; letter-spacing: -0.01em; }
    h3 { font-size: 1.15rem !important; }
    h2 { margin-top: 1.6rem; padding-bottom: 0.35rem; border-bottom: 1px solid var(--line); }
    [data-testid="stCaptionContainer"] { color: var(--muted); }

    /* sidebar */
    [data-testid="stSidebar"] { background: var(--panel); border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] h1 { font-size: 1.25rem !important; letter-spacing: -0.01em;
        border-left: 4px solid var(--h2); padding-left: 10px; }
    [data-testid="stSidebar"] [role="radiogroup"] { gap: 2px; }
    [data-testid="stSidebar"] [role="radiogroup"] label {
        padding: 8px 12px; border-radius: 8px; border: 1px solid transparent;
        transition: background .15s, border-color .15s; width: 100%; }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover { background: var(--panel-2); }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
        background: var(--panel-2); border-color: var(--line); box-shadow: inset 3px 0 0 var(--h2); }
    [data-testid="stSidebar"] [role="radiogroup"] label > div:first-child { display: none; }

    /* kpi cards */
    .kpi-card {
        background: linear-gradient(180deg, var(--panel-2) 0%, var(--panel) 100%);
        border-radius: 12px; padding: 16px 18px; border: 1px solid var(--line);
        box-shadow: 0 1px 2px rgba(0,0,0,.35); min-height: 118px;
        transition: transform .15s ease, border-color .15s ease;
    }
    .kpi-card:hover { transform: translateY(-2px); border-color: #34415f; }
    .kpi-label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.09em; font-weight: 600; }
    .kpi-value { font-size: 1.65rem; font-weight: 700; color: var(--text); margin-top: 4px; letter-spacing: -0.02em; }
    .kpi-sub   { font-size: 0.75rem; color: var(--muted); margin-top: 2px; }

    .key-finding {
        background: linear-gradient(135deg, rgba(228,87,46,.14) 0%, rgba(19,25,38,.9) 70%);
        border: 1px solid rgba(228,87,46,.35); border-left: 4px solid var(--h2);
        border-radius: 12px; padding: 18px 24px; margin: 18px 0;
    }
    .key-finding h3 { margin: 0 0 6px 0; font-size: 0.78rem !important; text-transform: uppercase;
        letter-spacing: 0.14em; color: var(--h2); border: none; padding: 0; }
    .badge-h2 { color: var(--h2); font-weight: 700; }
    .badge-bev { color: var(--bev); font-weight: 700; }
    .synthetic-note {
        background: rgba(217,180,91,.08); border: 1px solid rgba(217,180,91,.28);
        border-left: 3px solid var(--gold); padding: 10px 14px;
        border-radius: 8px; font-size: 0.84rem; color: #E3D5A8; margin-bottom: 12px;
    }

    /* widgets */
    [data-testid="stExpander"] { border: 1px solid var(--line); border-radius: 10px; background: var(--panel); }
    [data-testid="stExpander"] summary { font-weight: 500; }
    [data-testid="stDataFrame"] { border: 1px solid var(--line); border-radius: 10px; overflow: hidden; }
    .stDownloadButton button, .stButton button {
        background: var(--panel-2); border: 1px solid var(--line); border-radius: 8px;
        color: var(--text); font-weight: 500; transition: border-color .15s, color .15s; }
    .stDownloadButton button:hover, .stButton button:hover { border-color: var(--h2); color: var(--h2); }
    [data-testid="stPlotlyChart"] { background: transparent; border: 1px solid var(--line);
        border-radius: 12px; padding: 6px 4px; }
    [data-testid="stMetric"] { background: var(--panel); border: 1px solid var(--line);
        border-radius: 10px; padding: 12px 14px; }
    hr { border-color: var(--line); }
    #MainMenu, footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


def kpi_card(label, value, sub=""):
    st.markdown(
        f"""<div class="kpi-card">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{sub}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def synthetic_note(text):
    st.markdown(f'<div class="synthetic-note">{text}</div>', unsafe_allow_html=True)


def how_to_read(title, body_md):
    with st.expander(f"How to read this: {title}"):
        st.markdown(body_md)


# ----------------------------------------------------------------------
# Cached data loading
# ----------------------------------------------------------------------
@st.cache_data
def get_dataset():
    return dl.load_dataset()


@st.cache_data
def get_tco():
    return dl.load_tco_assumptions(), dl.load_tco_calculation(), dl.load_tco_year_by_year(), dl.load_tco_sensitivity()


@st.cache_data
def get_feasibility():
    stages, overall = dl.load_wtw_efficiency()
    infra = dl.load_infrastructure()
    safety = dl.load_safety()
    final_cmp = dl.load_final_comparison()
    crit, total, gap, verdict, why = dl.load_final_score()
    return stages, overall, infra, safety, final_cmp, crit, total, gap, verdict, why


@st.cache_data
def get_consistency():
    return dl.run_consistency_check()


@st.cache_data
def get_ml_results():
    df = get_dataset()
    return {vt: ml.train_and_evaluate(df, vt) for vt in ["H2_Retrofit", "BEV"]}


df_full = get_dataset()
tco_assump, tco_calc, tco_year, (tco_sens1, tco_sens2) = get_tco()
wtw_stages, wtw_overall, infra_df, safety_df, final_cmp_df, score_crit, score_total, score_gap, score_verdict, score_why = get_feasibility()
consistency_issues, consistency_confirms = get_consistency()
ml_results = get_ml_results()

# ----------------------------------------------------------------------
# Sidebar navigation
# ----------------------------------------------------------------------
st.sidebar.title("H2 Retrofit vs BEV")
st.sidebar.caption("B.Tech Feasibility Dashboard — Industry 4.0 & IoT")

PAGES = [
    "1. Executive Overview",
    "2. IoT Data Explorer",
    "3. EDA & Correlation",
    "4. Machine Learning",
    "5. Economic & TCO Analysis",
    "6. Energy Efficiency / WTW",
    "7. Safety & Infrastructure",
    "8. Final Feasibility",
]
page = st.sidebar.radio("Navigate", PAGES, label_visibility="collapsed")

with st.sidebar.expander("About this data"):
    st.markdown(
        "**Dataset type:** Synthetic IoT-style vehicle telemetry generated "
        "for academic analysis.\n\nNo physical IoT device or real vehicle "
        "telemetry was used. All monetary and technical figures come from "
        "the project's own spreadsheets."
    )

if consistency_issues:
    with st.sidebar.expander("Data consistency check: issues found", expanded=True):
        for iss in consistency_issues:
            st.write(f"**{iss['what']}** ({iss['where']})")
            st.write(iss["values"])
else:
    with st.sidebar.expander("Data consistency check: all clear"):
        for c in consistency_confirms:
            st.write("• " + c)

# =======================================================================
# PAGE 1 — EXECUTIVE OVERVIEW
# =======================================================================
if page == PAGES[0]:
    st.title("Executive Overview")
    st.caption("IoT-Based Data-Driven Feasibility Analysis of Hydrogen Retrofit Passenger Vehicles vs BEVs in India")

    synthetic_note("Synthetic+Real academic dataset — not real vehicle telemetry. No physical IoT device was used in this study.")

    n_obs = len(df_full)
    n_h2 = (df_full["vehicle_type"] == "H2_Retrofit").sum()
    n_bev = (df_full["vehicle_type"] == "BEV").sum()

    h2_score = score_total["H2_weighted"] if score_total else None
    bev_score = score_total["BEV_weighted"] if score_total else None
    h2_tco = tco_calc["5-year TOTAL cost"]["H2_Retrofit"]
    bev_tco = tco_calc["5-year TOTAL cost"]["BEV"]
    h2_wtw = wtw_overall.get("H2_ICE")
    bev_wtw = wtw_overall.get("BEV")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Observations", f"{n_obs:,}", f"{n_h2} H2 · {n_bev} BEV")
    with c2:
        kpi_card("Feasibility score", f"{h2_score:.2f} vs {bev_score:.2f}", "H2 Retrofit vs BEV, out of 10")
    with c3:
        kpi_card("5-yr Total Cost", f"₹{h2_tco/100000:.2f}L vs ₹{bev_tco/100000:.2f}L", "H2 Retrofit vs BEV")
    with c4:
        kpi_card("WTW Efficiency", f"{h2_wtw*100:.1f}% vs {bev_wtw*100:.1f}%", "H2-ICE vs BEV")

    st.divider()

    colA, colB = st.columns(2)

    with colA:
        st.subheader("Visual 1 — Overall Feasibility (out of 10)")
        fig = go.Figure(go.Bar(
            x=["H2 Retrofit", "BEV"], y=[h2_score, bev_score],
            marker_color=[H2_COLOR, BEV_COLOR], text=[f"{h2_score:.2f}", f"{bev_score:.2f}"],
            textposition="outside",
        ))
        fig.update_layout(yaxis_title="Weighted feasibility score (out of 10)", height=340, showlegend=False)
        st.plotly_chart(fig, width="stretch", theme=None)

        st.subheader("Visual 3 — Cost per km (5-year basis)")
        h2_cpk = tco_calc["TOTAL cost per km"]["H2_Retrofit"]
        bev_cpk = tco_calc["TOTAL cost per km"]["BEV"]
        fig3 = go.Figure(go.Bar(
            x=["H2 Retrofit", "BEV"], y=[h2_cpk, bev_cpk],
            marker_color=[H2_COLOR, BEV_COLOR], text=[f"₹{h2_cpk:.2f}", f"₹{bev_cpk:.2f}"],
            textposition="outside",
        ))
        fig3.update_layout(yaxis_title="₹ per km (total, 5-year basis)", height=340, showlegend=False)
        st.plotly_chart(fig3, width="stretch", theme=None)

        st.subheader("Visual 5 — Range")
        fig5 = go.Figure()
        fig5.add_trace(go.Bar(name="Min range", x=["H2 Retrofit", "BEV"], y=[250, 250], marker_color="rgba(0,0,0,0)"))
        fig5.add_trace(go.Bar(name="Range span", x=["H2 Retrofit", "BEV"], y=[100, 200],
                               base=[250, 250], marker_color=[H2_COLOR, BEV_COLOR]))
        fig5.update_layout(barmode="stack", yaxis_title="Range (km)", height=340, showlegend=False,
                            title="H2: approx 250–350 km · BEV: approx 250–450 km")
        st.plotly_chart(fig5, width="stretch", theme=None)

    with colB:
        st.subheader("Visual 2 — 5-Year Total Cost of Ownership")
        fig2 = go.Figure(go.Bar(
            x=["H2 Retrofit", "BEV"], y=[h2_tco, bev_tco],
            marker_color=[H2_COLOR, BEV_COLOR], text=[f"₹{h2_tco:,.0f}", f"₹{bev_tco:,.0f}"],
            textposition="outside",
        ))
        fig2.update_layout(yaxis_title="₹ (5-year total cost)", height=340, showlegend=False)
        st.plotly_chart(fig2, width="stretch", theme=None)

        st.subheader("Visual 4 — Well-to-Wheel Efficiency")
        fig4 = go.Figure(go.Bar(
            x=["H2 Retrofit (H2-ICE)", "BEV"], y=[h2_wtw*100, bev_wtw*100],
            marker_color=[H2_COLOR, BEV_COLOR], text=[f"{h2_wtw*100:.1f}%", f"{bev_wtw*100:.1f}%"],
            textposition="outside",
        ))
        fig4.update_layout(yaxis_title="Overall WTW efficiency (%)", height=340, showlegend=False)
        st.plotly_chart(fig4, width="stretch", theme=None)

        st.subheader("Visual 6 — Refuelling / Charging Time")
        fig6 = go.Figure(go.Bar(
            x=["H2 refuelling", "BEV fast charging", "BEV home charging"],
            y=[5, 52.5, 7*60],
            marker_color=[H2_COLOR, BEV_COLOR, BEV_COLOR],
            text=["~5 min", "45–60 min", "6–8 h"], textposition="outside",
        ))
        fig6.update_layout(yaxis_title="Minutes (log scale)", yaxis_type="log", height=340, showlegend=False)
        st.plotly_chart(fig6, width="stretch", theme=None)

    st.divider()
    st.markdown(
        f"""<div class="key-finding">
        <h3>Key finding</h3>
        <p style="font-size:1.05rem;">Under the assumptions and conditions considered in this study,
        <b>hydrogen retrofit of mainstream passenger vehicles is not feasible</b> compared with BEVs.</p>
        <p>The hydrogen retrofit option costs more to buy (₹{tco_calc['Initial cost (total)']['H2_Retrofit']:,.0f}
        vs ₹{tco_calc['Initial cost (total)']['BEV']:,.0f}), costs more to run
        (₹{tco_calc['Operating cost per km']['H2_Retrofit']:.2f}/km vs ₹{tco_calc['Operating cost per km']['BEV']:.2f}/km),
        delivers far less of the original grid electricity to the wheels ({h2_wtw*100:.1f}% vs {bev_wtw*100:.1f}%),
        and depends on almost no refuelling infrastructure in India today. It wins on exactly one criterion —
        refuelling time (~5 minutes vs 45 minutes to several hours) — which is not enough to offset the rest.</p>
        </div>""",
        unsafe_allow_html=True,
    )
    st.caption(
        "This conclusion is specific to retrofitting mainstream passenger vehicles to hydrogen under the "
        "assumptions of this study. It is not a claim that hydrogen technology is useless, or that fuel-cell "
        "hydrogen vehicles behave identically to a converted hydrogen-ICE retrofit."
    )

# =======================================================================
# PAGE 2 — IoT DATA EXPLORER
# =======================================================================
elif page == PAGES[1]:
    st.title("IoT Data Explorer")
    synthetic_note(
        "Dataset type: Synthetic IoT-style vehicle telemetry generated for academic analysis. "
        "No physical IoT device or real vehicle telemetry was used."
    )

    st.sidebar.markdown("### Filters")
    vt_filter = st.sidebar.multiselect("Vehicle type", sorted(df_full["vehicle_type"].unique()), default=list(df_full["vehicle_type"].unique()))
    traffic_filter = st.sidebar.multiselect("Traffic level", sorted(df_full["traffic_level"].unique()), default=list(df_full["traffic_level"].unique()))
    safety_filter = st.sidebar.multiselect("Safety status", sorted(df_full["safety_status"].unique()), default=list(df_full["safety_status"].unique()))
    maint_filter = st.sidebar.multiselect("Maintenance status", sorted(df_full["maintenance_status"].unique()), default=list(df_full["maintenance_status"].unique()))

    df = df_full[
        df_full["vehicle_type"].isin(vt_filter)
        & df_full["traffic_level"].isin(traffic_filter)
        & df_full["safety_status"].isin(safety_filter)
        & df_full["maintenance_status"].isin(maint_filter)
    ]

    if df.empty:
        st.warning("No rows match the selected filters. Adjust the filters in the sidebar.")
    else:
        n_h2 = (df["vehicle_type"] == "H2_Retrofit").sum()
        n_bev = (df["vehicle_type"] == "BEV").sum()
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        with c1: kpi_card("Total obs.", f"{len(df):,}")
        with c2: kpi_card("H2 obs.", f"{n_h2:,}")
        with c3: kpi_card("BEV obs.", f"{n_bev:,}")
        with c4: kpi_card("Avg speed", f"{df['speed_kmph'].mean():.1f} km/h")
        with c5: kpi_card("Avg distance", f"{df['distance_km'].mean():.1f} km")
        with c6: kpi_card("Avg load", f"{df['vehicle_load'].mean():.0f} kg")
        st.caption(f"Average ambient temperature in current selection: {df['ambient_temperature'].mean():.1f} °C")

        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            fig = px.histogram(df, x="speed_kmph", color="vehicle_type", nbins=30, barmode="overlay",
                                color_discrete_map={"H2_Retrofit": H2_COLOR, "BEV": BEV_COLOR},
                                labels={"speed_kmph": "Average trip speed (km/h)"},
                                title="1. Speed distribution")
            fig.update_traces(opacity=0.65)
            st.plotly_chart(fig, width="stretch", theme=None)

            fig = px.histogram(df, x="fuel_or_energy_consumption", color="vehicle_type", nbins=30, barmode="overlay",
                                color_discrete_map={"H2_Retrofit": H2_COLOR, "BEV": BEV_COLOR},
                                labels={"fuel_or_energy_consumption": "Consumption (H2: kg/100km · BEV: kWh/100km)"},
                                title="3. Energy consumption distribution")
            fig.update_traces(opacity=0.65)
            st.plotly_chart(fig, width="stretch", theme=None)

            fig = px.histogram(df, x="safety_status", color="vehicle_type", barmode="group",
                                color_discrete_map={"H2_Retrofit": H2_COLOR, "BEV": BEV_COLOR},
                                title="5. Safety status distribution")
            st.plotly_chart(fig, width="stretch", theme=None)

        with col2:
            fig = px.histogram(df, x="distance_km", color="vehicle_type", nbins=30, barmode="overlay",
                                color_discrete_map={"H2_Retrofit": H2_COLOR, "BEV": BEV_COLOR},
                                labels={"distance_km": "Trip distance (km)"},
                                title="2. Distance distribution")
            fig.update_traces(opacity=0.65)
            st.plotly_chart(fig, width="stretch", theme=None)

            fig = px.histogram(df, x="traffic_level", color="vehicle_type", barmode="group",
                                category_orders={"traffic_level": ["Low", "Medium", "High"]},
                                color_discrete_map={"H2_Retrofit": H2_COLOR, "BEV": BEV_COLOR},
                                title="4. Traffic level distribution")
            st.plotly_chart(fig, width="stretch", theme=None)

            fig = px.histogram(df, x="maintenance_status", color="vehicle_type", barmode="group",
                                category_orders={"maintenance_status": ["OK", "Due", "Overdue"]},
                                color_discrete_map={"H2_Retrofit": H2_COLOR, "BEV": BEV_COLOR},
                                title="6. Maintenance status distribution")
            st.plotly_chart(fig, width="stretch", theme=None)

        how_to_read("distributions", """
- **X-axis** shows the value of the variable (e.g. speed in km/h); **Y-axis** shows how many trips fall in that range.
- Each bar is a "bucket" of observations — taller bars mean that value range is more common.
- Orange = H2 Retrofit, Blue = BEV, wherever both are shown together.
- Overlapping distributions mean the two vehicle types were driven under broadly similar conditions in this synthetic dataset — differences in outcome (cost, efficiency) come mainly from the powertrain, not from different driving patterns.
""")

        st.divider()
        st.subheader("Filtered data")
        st.dataframe(df, width="stretch", height=280)

        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button("Download filtered dataset (CSV)", df.to_csv(index=False).encode("utf-8"),
                                file_name="filtered_dataset.csv", mime="text/csv")
        with dl_col2:
            st.download_button("Download original dataset (CSV)", df_full.to_csv(index=False).encode("utf-8"),
                                file_name="dataset_original.csv", mime="text/csv")

# =======================================================================
# PAGE 3 — EDA & CORRELATION
# =======================================================================
elif page == PAGES[2]:
    st.title("EDA & Correlation")

    h2_df = df_full[df_full["vehicle_type"] == "H2_Retrofit"]
    bev_df = df_full[df_full["vehicle_type"] == "BEV"]

    st.subheader("Chart 1 — Energy Consumption Distribution")
    col1, col2 = st.columns(2)
    with col1:
        fig = px.histogram(h2_df, x="fuel_or_energy_consumption", nbins=25, color_discrete_sequence=[H2_COLOR],
                            labels={"fuel_or_energy_consumption": "kg H2 / 100 km"}, title="H2 Retrofit consumption")
        st.plotly_chart(fig, width="stretch", theme=None)
    with col2:
        fig = px.histogram(bev_df, x="fuel_or_energy_consumption", nbins=25, color_discrete_sequence=[BEV_COLOR],
                            labels={"fuel_or_energy_consumption": "kWh / 100 km"}, title="BEV consumption")
        st.plotly_chart(fig, width="stretch", theme=None)
    st.caption("Shown as two separate charts with separate units (kg H2/100km vs kWh/100km) — these are physically different "
               "quantities and are never plotted on one shared numeric axis.")

    st.divider()
    st.subheader("Chart 2 — Traffic Level vs Consumption")
    traffic_means = df_full.groupby(["vehicle_type", "traffic_level"])["fuel_or_energy_consumption"].mean().reset_index()
    col1, col2 = st.columns(2)
    with col1:
        d = traffic_means[traffic_means["vehicle_type"] == "H2_Retrofit"]
        fig = px.bar(d, x="traffic_level", y="fuel_or_energy_consumption", color_discrete_sequence=[H2_COLOR],
                     category_orders={"traffic_level": ["Low", "Medium", "High"]},
                     labels={"fuel_or_energy_consumption": "Mean kg H2/100km"}, title="H2 Retrofit: consumption by traffic")
        st.plotly_chart(fig, width="stretch", theme=None)
    with col2:
        d = traffic_means[traffic_means["vehicle_type"] == "BEV"]
        fig = px.bar(d, x="traffic_level", y="fuel_or_energy_consumption", color_discrete_sequence=[BEV_COLOR],
                     category_orders={"traffic_level": ["Low", "Medium", "High"]},
                     labels={"fuel_or_energy_consumption": "Mean kWh/100km"}, title="BEV: consumption by traffic")
        st.plotly_chart(fig, width="stretch", theme=None)

    st.divider()
    st.subheader("Chart 3 — Speed vs H2 Consumption")
    fig = px.scatter(h2_df, x="speed_kmph", y="fuel_or_energy_consumption", color="traffic_level",
                      category_orders={"traffic_level": ["Low", "Medium", "High"]},
                      labels={"speed_kmph": "Average speed (km/h)", "fuel_or_energy_consumption": "Hydrogen consumption (kg H2/100 km)"},
                      title="Each point = one trip")
    st.plotly_chart(fig, width="stretch", theme=None)

    st.subheader("Chart 4 — Temperature vs BEV Consumption")
    fig = px.scatter(bev_df, x="ambient_temperature", y="fuel_or_energy_consumption", color="traffic_level",
                      category_orders={"traffic_level": ["Low", "Medium", "High"]},
                      labels={"ambient_temperature": "Ambient temperature (°C)", "fuel_or_energy_consumption": "BEV electricity consumption (kWh/100 km)"},
                      title="Each point = one trip")
    st.plotly_chart(fig, width="stretch", theme=None)

    st.divider()
    st.subheader("Chart 5 — Correlation Heatmaps")
    num_cols = ["speed_kmph", "distance_km", "ambient_temperature", "vehicle_load", "fuel_or_energy_consumption"]
    col1, col2 = st.columns(2)
    with col1:
        corr_h2 = h2_df[num_cols + ["hydrogen_pressure"]].corr()
        fig = px.imshow(corr_h2, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, title="H2 Retrofit — correlation matrix")
        st.plotly_chart(fig, width="stretch", theme=None)
    with col2:
        corr_bev = bev_df[num_cols + ["battery_soc", "battery_temperature"]].corr()
        fig = px.imshow(corr_bev, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, title="BEV — correlation matrix")
        st.plotly_chart(fig, width="stretch", theme=None)

    how_to_read("correlation heatmap", """
- Correlation ranges from **-1 to +1**.
- **+1** = strong positive relationship (both variables rise together).
- **0** = little or no *linear* relationship.
- **-1** = strong negative relationship (one rises as the other falls).
- Dark red = strong positive, dark blue = strong negative, pale colours = weak relationship.
- **Correlation does not prove causation** — it only shows that two variables move together in this dataset, not that one causes the other.
""")

    st.divider()
    st.subheader("Chart 6 — Box Plot: Consumption by Traffic Level")
    col1, col2 = st.columns(2)
    with col1:
        fig = px.box(h2_df, x="traffic_level", y="fuel_or_energy_consumption", color_discrete_sequence=[H2_COLOR],
                     category_orders={"traffic_level": ["Low", "Medium", "High"]},
                     labels={"fuel_or_energy_consumption": "kg H2/100km"}, title="H2 Retrofit")
        st.plotly_chart(fig, width="stretch", theme=None)
    with col2:
        fig = px.box(bev_df, x="traffic_level", y="fuel_or_energy_consumption", color_discrete_sequence=[BEV_COLOR],
                     category_orders={"traffic_level": ["Low", "Medium", "High"]},
                     labels={"fuel_or_energy_consumption": "kWh/100km"}, title="BEV")
        st.plotly_chart(fig, width="stretch", theme=None)
    st.caption("The box shows the median (middle line), the spread of the middle 50% of trips (box edges), and any points "
               "outside the whiskers are potential outliers.")

# =======================================================================
# PAGE 4 — MACHINE LEARNING
# =======================================================================
elif page == PAGES[3]:
    st.title("Machine Learning — Random Forest")

    st.info(
        "**Note on this page's data:** the file that would hold the original notebook's saved test-set "
        "predictions and feature-importance table (an `analysis_results.xlsx`) was not among the files "
        "uploaded for this dashboard. The charts and metrics below labelled **'Live run'** are computed in "
        "this app by retraining a Random Forest directly on `data/dataset.csv`, following the methodology "
        "described in the report (75:25 split, 300 trees, minimum leaf size 2). The report's own published "
        "scores (Table 3) are shown alongside for comparison — a different random split will not reproduce "
        "identical numbers."
    )

    st.subheader("Model performance")
    perf_rows = []
    for vt, label in [("H2_Retrofit", "H2 Retrofit"), ("BEV", "BEV")]:
        rep = dl.REPORT_STATED_ML_METRICS[vt]
        live = ml_results[vt]
        perf_rows.append({
            "Model": label, "Source": "Report (Table 3)", "R²": rep["R2"], "MAE": rep["MAE"], "RMSE": rep["RMSE"], "Unit": rep["unit"],
        })
        perf_rows.append({
            "Model": label, "Source": "Live run (this app)", "R²": round(live["r2"], 3), "MAE": round(live["mae"], 3),
            "RMSE": round(live["rmse"], 3), "Unit": rep["unit"],
        })
    st.dataframe(pd.DataFrame(perf_rows), width="stretch", hide_index=True)

    st.divider()
    st.subheader("Visual 1 — Actual vs Predicted (live run, test set)")
    col1, col2 = st.columns(2)
    for col, vt, label, color in [(col1, "H2_Retrofit", "H2 Retrofit", H2_COLOR), (col2, "BEV", "BEV", BEV_COLOR)]:
        with col:
            pred_df = ml_results[vt]["predictions"]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=pred_df["actual"], y=pred_df["predicted"], mode="markers",
                                      marker=dict(color=color, opacity=0.6), name="Test-set trips"))
            lo, hi = pred_df["actual"].min(), pred_df["actual"].max()
            fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="lines", line=dict(color="white", dash="dash"),
                                      name="Perfect prediction"))
            fig.update_layout(title=f"{label} — Actual vs Predicted", xaxis_title="Actual", yaxis_title="Predicted", height=380)
            st.plotly_chart(fig, width="stretch", theme=None)
    st.caption("Points closer to the dashed diagonal indicate better predictions. The BEV model (higher R²) should cluster tighter than the H2 model.")

    st.divider()
    st.subheader("Visual 2 — Feature Importance (live run)")
    st.caption(dl.REPORT_STATED_FEATURE_IMPORTANCE_NOTE)
    col1, col2 = st.columns(2)
    for col, vt, label, color in [(col1, "H2_Retrofit", "H2 Retrofit", H2_COLOR), (col2, "BEV", "BEV", BEV_COLOR)]:
        with col:
            imp = ml_results[vt]["importances"]
            fig = px.bar(x=imp.values, y=imp.index, orientation="h", color_discrete_sequence=[color],
                         labels={"x": "Importance", "y": "Feature"}, title=f"{label} — feature importance")
            fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=380)
            st.plotly_chart(fig, width="stretch", theme=None)
    st.caption("Traffic level and ambient temperature matter most for both powertrains — feature importance shows which "
               "variables the model relied on, not that they *cause* higher consumption.")

    how_to_read("ML metrics", """
- **R² (R-squared):** the share of variation in consumption that the model explains — closer to 1.0 is better. Neither model reaches 1.0 because random noise was deliberately built into the synthetic data.
- **MAE (Mean Absolute Error):** the average size of the prediction error, in the same unit as the target.
- **RMSE (Root Mean Squared Error):** similar to MAE, but penalises large errors more heavily than small ones.
- Feature importance does **not** prove causation — it shows which inputs the trees relied on most to reduce prediction error, not what physically drives fuel or energy use in the real world.
""")

# =======================================================================
# PAGE 5 — ECONOMIC & TCO ANALYSIS
# =======================================================================
elif page == PAGES[4]:
    st.title("Economic & TCO Analysis")

    metrics = [
        ("Initial cost (total)", "Initial cost"),
        ("Annual energy cost", "Annual energy cost"),
        ("Annual maintenance", "Annual maintenance"),
        ("Annual operating cost", "Annual operating cost"),
        ("5-year operating cost", "Five-year operating cost"),
        ("5-year TOTAL cost", "Five-year total cost"),
        ("Operating cost per km", "Operating cost/km"),
        ("TOTAL cost per km", "Total cost/km"),
    ]
    cols = st.columns(4)
    for i, (key, label) in enumerate(metrics):
        v = tco_calc[key]
        with cols[i % 4]:
            unit = "₹/km" if "per km" in key else "₹"
            fmt = f"₹{v['H2_Retrofit']:.2f} vs ₹{v['BEV']:.2f}" if unit == "₹/km" else f"₹{v['H2_Retrofit']:,.0f} vs ₹{v['BEV']:,.0f}"
            kpi_card(label, fmt, "H2 Retrofit vs BEV")

    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Chart 1 — Initial Cost Comparison")
        capital_items = ["Base / donor vehicle", "Retrofit kit", "Certification / homologation", "Home infrastructure"]
        fig = go.Figure()
        fig.add_trace(go.Bar(name="H2 Retrofit", x=capital_items, y=[tco_calc[i]["H2_Retrofit"] for i in capital_items], marker_color=H2_COLOR))
        fig.add_trace(go.Bar(name="BEV", x=capital_items, y=[tco_calc[i]["BEV"] for i in capital_items], marker_color=BEV_COLOR))
        fig.update_layout(barmode="group", yaxis_title="₹", height=380)
        st.plotly_chart(fig, width="stretch", theme=None)

        st.subheader("Chart 3 — Cumulative Ownership Cost by Year")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=tco_year["Year"], y=tco_year["H2_cumulative"], mode="lines+markers", name="H2 Retrofit", line=dict(color=H2_COLOR)))
        fig.add_trace(go.Scatter(x=tco_year["Year"], y=tco_year["BEV_cumulative"], mode="lines+markers", name="BEV", line=dict(color=BEV_COLOR)))
        fig.update_layout(xaxis_title="Year", yaxis_title="Cumulative cost (₹)", height=380)
        st.plotly_chart(fig, width="stretch", theme=None)

    with col2:
        st.subheader("Chart 2 — Five-Year Cost Build-up")
        build_items = ["Initial cost (total)", "5-year operating cost"]
        fig = go.Figure()
        fig.add_trace(go.Bar(name="H2 Retrofit", x=["H2 Retrofit"], y=[tco_calc["Initial cost (total)"]["H2_Retrofit"]],
                              marker_color=H2_COLOR, text="Initial cost"))
        fig.add_trace(go.Bar(name="", x=["H2 Retrofit"], y=[tco_calc["5-year operating cost"]["H2_Retrofit"]],
                              base=[tco_calc["Initial cost (total)"]["H2_Retrofit"]], marker_color="#f2a679", text="5-yr operating"))
        fig.add_trace(go.Bar(name="", x=["BEV"], y=[tco_calc["Initial cost (total)"]["BEV"]], marker_color=BEV_COLOR, text="Initial cost"))
        fig.add_trace(go.Bar(name="", x=["BEV"], y=[tco_calc["5-year operating cost"]["BEV"]],
                              base=[tco_calc["Initial cost (total)"]["BEV"]], marker_color="#8fc1de", text="5-yr operating"))
        fig.update_layout(barmode="stack", yaxis_title="₹", height=380, showlegend=False)
        st.plotly_chart(fig, width="stretch", theme=None)

        st.subheader("Chart 4 — Operating Cost per km")
        fig = go.Figure(go.Bar(x=["H2 Retrofit", "BEV"],
                                y=[tco_calc["Operating cost per km"]["H2_Retrofit"], tco_calc["Operating cost per km"]["BEV"]],
                                marker_color=[H2_COLOR, BEV_COLOR],
                                text=[f"₹{tco_calc['Operating cost per km']['H2_Retrofit']:.2f}", f"₹{tco_calc['Operating cost per km']['BEV']:.2f}"],
                                textposition="outside"))
        fig.update_layout(yaxis_title="₹ per km", height=380, showlegend=False)
        st.plotly_chart(fig, width="stretch", theme=None)

    st.divider()
    st.subheader("Comparison Table")
    table_rows = []
    for key, label in metrics:
        v = tco_calc[key]
        table_rows.append({"Metric": label, "H2 Retrofit": v["H2_Retrofit"], "BEV": v["BEV"]})
    st.dataframe(pd.DataFrame(table_rows), width="stretch", hide_index=True)

    gap_5yr = tco_year["Difference"].iloc[-1]
    st.markdown(f"""
**Why does the cost gap increase over time?**
Both options start with a capital outlay, but the hydrogen retrofit's *annual operating cost*
(₹{tco_calc['Annual operating cost']['H2_Retrofit']:,.0f}) is more than double the BEV's
(₹{tco_calc['Annual operating cost']['BEV']:,.0f}), driven mainly by the higher energy cost per km.
That gap compounds every year: by year 5, the cumulative cost difference reaches
**₹{gap_5yr:,.0f}** in the BEV's favour (see Year_by_Year sheet).
""")

    with st.expander("Sensitivity analysis (from tco_analysis.xlsx)"):
        st.write("**Test 1 — varying the hydrogen price:**")
        st.dataframe(tco_sens1.rename(columns={"x": "H2 price (₹/kg)"}), width="stretch", hide_index=True)
        st.caption("Even at ₹250/kg, hydrogen fuel still costs more per km than BEV electricity.")
        st.write("**Test 2 — varying H2-ICE consumption (a real retrofit burns more than the dataset's fuel-cell-like mean):**")
        st.dataframe(tco_sens2.rename(columns={"x": "H2-ICE consumption (kg/100km)"}), width="stretch", hide_index=True)
        st.caption("1.15 kg/100km is the fuel-cell-like dataset mean; a real H2-ICE retrofit is nearer 2.4 kg/100km, which makes the economics roughly twice as bad.")

    how_to_read("TCO figures", """
- **Initial cost:** what it costs to acquire the vehicle and get it road-legal (donor vehicle, retrofit kit, certification, home charger).
- **Operating cost:** the recurring annual cost of running the vehicle (energy, maintenance, inspection, insurance).
- **Total cost:** initial cost + operating cost accumulated over the ownership period (5 years here).
- **Cost per km:** total or operating cost divided by distance driven — the number that is comparable across different usage levels.
""")

    st.download_button("Download final comparison table", final_cmp_df.to_csv(index=False).encode("utf-8"),
                        file_name="final_comparison_table.csv", mime="text/csv")

# =======================================================================
# PAGE 6 — WELL-TO-WHEEL ENERGY EFFICIENCY
# =======================================================================
elif page == PAGES[5]:
    st.title("Well-to-Wheel Energy Efficiency")
    st.markdown(
        "**Well-to-Wheel (WTW)** traces energy from the original electricity source through all conversion "
        "stages until useful energy reaches the vehicle wheels. Both pathways below start from the **same "
        "1 unit of grid electricity**, so they are directly comparable."
    )
    st.latex(r"\eta_{total} = \eta_1 \times \eta_2 \times \dots \times \eta_n")

    st.divider()
    st.subheader("Visual 1 — Energy Remaining After Each Stage")
    col1, col2 = st.columns(2)
    with col1:
        d = wtw_stages["BEV"]
        fig = go.Figure(go.Bar(x=d["stage"], y=d["cumulative_efficiency"]*100, marker_color=BEV_COLOR,
                                text=[f"{v*100:.1f}%" for v in d["cumulative_efficiency"]], textposition="outside"))
        fig.update_layout(title="BEV pathway: Grid → Transmission → Charging → Battery → Motor/Inverter → Wheels",
                           yaxis_title="Energy remaining (%)", height=420, xaxis_tickangle=-30)
        st.plotly_chart(fig, width="stretch", theme=None)
    with col2:
        d = wtw_stages["H2_ICE"]
        fig = go.Figure(go.Bar(x=d["stage"], y=d["cumulative_efficiency"]*100, marker_color=H2_COLOR,
                                text=[f"{v*100:.1f}%" for v in d["cumulative_efficiency"]], textposition="outside"))
        fig.update_layout(title="H2-ICE Retrofit pathway: Grid → Electrolysis → Compression → Storage/dispensing → H2 engine → Wheels",
                           yaxis_title="Energy remaining (%)", height=420, xaxis_tickangle=-30)
        st.plotly_chart(fig, width="stretch", theme=None)

    st.divider()
    st.subheader("Visual 2 — Overall WTW Efficiency Comparison")
    fig = go.Figure(go.Bar(
        x=["BEV", "H2-ICE Retrofit"], y=[wtw_overall["BEV"]*100, wtw_overall["H2_ICE"]*100],
        marker_color=[BEV_COLOR, H2_COLOR],
        text=[f"{wtw_overall['BEV']*100:.1f}%", f"{wtw_overall['H2_ICE']*100:.1f}%"], textposition="outside",
    ))
    fig.update_layout(yaxis_title="Overall well-to-wheel efficiency (%)", height=380, showlegend=False)
    st.plotly_chart(fig, width="stretch", theme=None)

    ratio = wtw_overall["BEV"] / wtw_overall["H2_ICE"]
    st.markdown(f"""
**Biggest losses, per the report:** the BEV delivers about **{wtw_overall['BEV']*100:.1f}%** of the original
grid electricity to the wheels, while the hydrogen retrofit delivers about **{wtw_overall['H2_ICE']*100:.1f}%**.
The single biggest loss in the hydrogen chain is the **hydrogen internal combustion engine's thermal limit**
(only {wtw_stages['H2_ICE'].iloc[4]['stage_efficiency']*100:.0f}% efficient) — converting a petrol engine keeps
its poor thermal efficiency. In other words, the retrofit needs roughly **{ratio:.1f}× as much electricity**
to travel the same distance as a BEV.
""")

    with st.expander("Reference only: H2 Fuel Cell pathway (not the retrofit studied here)"):
        st.caption("FCEV technology is discussed only briefly for context — this study's subject is a hydrogen-ICE retrofit, not a fuel-cell vehicle.")
        d = wtw_stages["H2_FC"]
        fig = go.Figure(go.Bar(x=d["stage"], y=d["cumulative_efficiency"]*100, marker_color="#8a6fb0",
                                text=[f"{v*100:.1f}%" for v in d["cumulative_efficiency"]], textposition="outside"))
        fig.update_layout(title=f"H2 Fuel Cell pathway — overall {wtw_overall['H2_FC']*100:.1f}%", yaxis_title="Energy remaining (%)", height=380)
        st.plotly_chart(fig, width="stretch", theme=None)

    how_to_read("WTW efficiency", """
- **Energy pathway:** every conversion step energy passes through, from the power grid to the wheels.
- **Stage efficiency:** the fraction of energy that survives *that one step* (e.g. 0.90 = 90% survives, 10% is lost).
- **Overall efficiency:** the product of every stage's efficiency — multiplying fractions less than 1 together always gives a smaller number, which is why more conversion steps generally means more loss.
""")

# =======================================================================
# PAGE 7 — SAFETY & INFRASTRUCTURE
# =======================================================================
elif page == PAGES[6]:
    st.title("Safety & Infrastructure")

    st.header("Section A — Safety")
    st.dataframe(safety_df, width="stretch", hide_index=True)

    bev_warn = (df_full.loc[df_full["vehicle_type"] == "BEV", "safety_status"] == "Warning").mean() * 100
    h2_warn = (df_full.loc[df_full["vehicle_type"] == "H2_Retrofit", "safety_status"] == "Warning").mean() * 100
    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure(go.Bar(x=["BEV", "H2 Retrofit"], y=[bev_warn, h2_warn], marker_color=[BEV_COLOR, H2_COLOR],
                                text=[f"{bev_warn:.1f}%", f"{h2_warn:.1f}%"], textposition="outside"))
        fig.update_layout(title="Synthetic monitoring: safety-warning share", yaxis_title="% of trips flagged 'Warning'", height=340)
        st.plotly_chart(fig, width="stretch", theme=None)
    with col2:
        st.warning(
            "This is a **synthetic monitoring statistic** based on the chosen simulation thresholds. "
            "It is **NOT** a real-world safety verdict and is **NOT** used to calculate the final "
            "feasibility score. Do not read a higher BEV warning share here as evidence that BEVs are "
            "physically less safe — the qualitative safety comparison (table above) is a separate, "
            "physics-based assessment."
        )

    st.divider()
    st.header("Section B — Infrastructure")
    st.dataframe(infra_df, width="stretch", hide_index=True)
    st.info("**Practical issue:** a BEV can be charged at home overnight. Hydrogen requires access to a "
            "hydrogen refuelling station, of which India has essentially none for private cars today.")

    how_to_read("this page", """
- The safety table is **qualitative** — based on the physical properties of each energy carrier, not a crash-test or simulation result.
- The infrastructure numbers come from the report's cited sources (Parliament data, NGHM pilot reporting) as of the report's writing — infrastructure figures change quickly and should be re-checked before a viva.
""")

# =======================================================================
# PAGE 8 — FINAL FEASIBILITY
# =======================================================================
elif page == PAGES[7]:
    st.title("Final Feasibility")

    st.subheader("Visual 1 — Criterion-wise Comparison")
    fig = go.Figure()
    fig.add_trace(go.Bar(name="H2 Retrofit", x=score_crit["Criterion"], y=score_crit["H2_score"], marker_color=H2_COLOR))
    fig.add_trace(go.Bar(name="BEV", x=score_crit["Criterion"], y=score_crit["BEV_score"], marker_color=BEV_COLOR))
    fig.update_layout(barmode="group", yaxis_title="Score (1–10, 10 = most feasible)", height=420, xaxis_tickangle=-25)
    st.plotly_chart(fig, width="stretch", theme=None)

    st.subheader("Visual 2 — Overall Feasibility Score")
    fig = go.Figure(go.Bar(x=["H2 Retrofit", "BEV"], y=[score_total["H2_weighted"], score_total["BEV_weighted"]],
                            marker_color=[H2_COLOR, BEV_COLOR],
                            text=[f"{score_total['H2_weighted']:.2f}/10", f"{score_total['BEV_weighted']:.2f}/10"],
                            textposition="outside"))
    fig.update_layout(yaxis_title="Weighted feasibility score (out of 10)", height=340, showlegend=False)
    st.plotly_chart(fig, width="stretch", theme=None)

    st.subheader("Visual 3 — Grouped Comparison (Radar alternative)")
    categories = score_crit["Criterion"].tolist()
    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(r=score_crit["H2_score"], theta=categories, fill="toself", name="H2 Retrofit", line_color=H2_COLOR))
    fig.add_trace(go.Scatterpolar(r=score_crit["BEV_score"], theta=categories, fill="toself", name="BEV", line_color=BEV_COLOR))
    fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), height=480)
    st.plotly_chart(fig, width="stretch", theme=None)
    st.caption("A radar chart is used here since the 8 criteria are of similar scale (1–10) and comparing the overall 'shape' aids readability. A grouped bar chart (Visual 1) is provided alongside for exact values.")

    st.divider()
    st.subheader("How the weighted score was calculated")
    st.latex(r"\text{Feasibility Score} = \sum (\text{weight} \times \text{criterion score})")
    st.markdown("""
- Each criterion (cost, efficiency, safety, etc.) has a **score** from 1–10 for each option.
- Each criterion has a **weight** reflecting its importance to a private owner (weights sum to 1.00).
- Weighted scores (`weight × score`) are added across all 8 criteria.
- The **final score is out of 10**.

This is a **transparent decision-support score created for this study; it is not a machine-learning prediction.**
""")
    st.dataframe(score_crit[["Criterion", "Weight", "H2_score", "BEV_score", "H2_weighted", "BEV_weighted", "Evidence"]],
                 width="stretch", hide_index=True)

    st.divider()
    st.markdown(f"""<div class="key-finding">
    <h3>Final Verdict</h3>
    <p>{score_verdict}</p>
    <p><b>Gap (BEV − H2): {score_gap:.2f} points</b> out of 10.</p>
    </div>""", unsafe_allow_html=True)

    st.subheader("Why this is the answer")
    for w in score_why:
        st.markdown(f"- {w}")
    st.markdown("**Hydrogen wins on exactly one criterion: refuelling time. That is not enough.**")

    st.caption(
        "This conclusion is about retrofitting hydrogen into private passenger cars in India under present "
        "conditions. It is not a conclusion that hydrogen is a useless technology — hydrogen retains genuine "
        "advantages for applications such as heavy, continuously-running vehicles where fast refuelling matters most."
    )

    st.download_button("Download summary results (final comparison table)",
                        final_cmp_df.to_csv(index=False).encode("utf-8"),
                        file_name="summary_results.csv", mime="text/csv")
