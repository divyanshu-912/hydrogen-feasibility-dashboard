# Hydrogen Retrofit vs BEV — Feasibility Dashboard

**Project:** IoT-Based Data-Driven Feasibility Analysis of Hydrogen Retrofit Passenger Vehicles vs BEVs in India
**Type:** B.Tech subject project (Industry 4.0 & IoT), Group 3
**Technology:** Python, Streamlit, Pandas, Plotly, OpenPyXL, scikit-learn

## What this is

An interactive, browser-based dashboard that presents this project's analysis — dataset,
exploratory findings, Random Forest model, total-cost-of-ownership, well-to-wheel energy
efficiency, safety/infrastructure comparison, and the final weighted feasibility score —
so a faculty member can explore the study and understand why it concludes that hydrogen
retrofit of mainstream passenger vehicles is **not feasible** compared with BEVs, under
this study's assumptions.

## Folder structure

```
hydrogen_feasibility_dashboard/
│
├── app.py                          # Streamlit application (8 pages)
├── data_loader.py                  # Reads every number from the source files below
├── ml.py                           # Retrains the Random Forest live (see note below)
├── requirements.txt
├── README.md
│
└── data/
    ├── dataset.csv                 # Synthetic IoT-style telemetry (1,000 trips)
    ├── tco_analysis.xlsx           # 5-year TCO model, sensitivity analysis
    ├── feasibility_comparison.xlsx # WTW efficiency, infrastructure, safety, final score
    └── final_comparison.csv        # One-page final comparison table
```

## Installation & running

```bash
pip install -r requirements.txt
streamlit run app.py
```

The app opens in your browser (default: http://localhost:8501).

## Data sources and an important note on `analysis_results.xlsx`

Every number in this dashboard is read directly from the three files above via
`data_loader.py` — nothing is hardcoded or invented. A consistency check runs on
startup (visible in the sidebar) cross-checking headline figures across files; as of
this build, **no discrepancies were found**.

**One file requested in the original brief — `analysis_results.xlsx` — was not among the
files uploaded for this dashboard.** That file would have held the original notebook's
saved Random Forest test-set predictions and a feature-importance table. Rather than
fabricate those numbers, `ml.py` retrains a Random Forest **live, on `data/dataset.csv`**,
following the methodology the final report describes in section 8.2 (75:25 train/test
split, 300 trees, minimum leaf size 2, one model per vehicle type). The report's own
published R² / MAE / RMSE scores (Table 3) are shown **alongside** these live results on
the Machine Learning page, clearly labelled — a different random split naturally gives
slightly different numbers, and the app never conflates the two. The report's narrative
feature-importance figures (given as approximate values in its text, not a table) are
quoted on that page too, next to a live-computed feature-importance chart.

## Dashboard pages

1. **Executive Overview** — KPI cards and 6 headline visuals (feasibility, TCO, cost/km,
   WTW efficiency, range, refuelling time), plus the project's key finding.
2. **IoT Data Explorer** — the synthetic dataset with interactive filters (vehicle type,
   traffic, safety status, maintenance status) and 6 distribution charts.
3. **EDA & Correlation** — consumption distributions (kept in separate units), traffic vs
   consumption, two scatter plots, per-vehicle-type correlation heatmaps, and a box plot.
4. **Machine Learning** — Random Forest performance (report-stated and live), actual-vs-
   predicted plots, and feature importance, all with plain-language explanations.
5. **Economic & TCO Analysis** — the full 5-year total-cost-of-ownership build-up, year-
   by-year cumulative cost, and the report's sensitivity analysis.
6. **Energy Efficiency / WTW** — stage-by-stage energy pathways for BEV and H2-ICE
   retrofit (with the H2 fuel-cell pathway shown separately, for reference only).
7. **Safety & Infrastructure** — the qualitative safety comparison table, the synthetic
   safety-warning statistic (clearly flagged as not a real-world verdict), and the
   infrastructure comparison.
8. **Final Feasibility** — criterion-by-criterion scores, the overall weighted feasibility
   score, the scoring formula, and the study's final verdict.

## Important scope note

This project's conclusion is specifically about retrofitting hydrogen into **mainstream
passenger vehicles** under the assumptions and conditions studied here. It does **not**
claim hydrogen technology in general is infeasible, and it does **not** claim a hydrogen
fuel-cell vehicle behaves the same as a hydrogen-ICE retrofit — the fuel-cell pathway is
included on the WTW page only as a brief reference point.
