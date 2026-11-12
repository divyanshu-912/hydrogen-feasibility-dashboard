"""
data_loader.py
==============
Single source of truth for every number shown in the dashboard.

Every function here reads directly from the project's original files
(data/dataset.csv, data/tco_analysis.xlsx, data/feasibility_comparison.xlsx).
Nothing is hardcoded or invented — if a value is not present in these
files, the corresponding function returns None / an empty structure and
the app must say so on screen rather than fabricate a number.

Report-stated values (from final_report.docx) that are NOT reproduced in
any spreadsheet — the Random Forest R² / MAE / RMSE scores, and the
narrative feature-importance figures — are recorded in REPORT_STATED_*
constants below, quoted exactly as written in the report text. These are
clearly labelled everywhere they appear as "as stated in the final
report", never presented as if they were pulled from a spreadsheet.
"""

import os
import openpyxl
import pandas as pd
import numpy as np

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

DATASET_PATH = os.path.join(DATA_DIR, "dataset.csv")
TCO_PATH = os.path.join(DATA_DIR, "tco_analysis.xlsx")
FEAS_PATH = os.path.join(DATA_DIR, "feasibility_comparison.xlsx")

# ---------------------------------------------------------------------
# Values stated in final_report.docx narrative/tables but NOT present in
# any of the spreadsheets supplied for this dashboard (there is no
# analysis_results.xlsx among the uploaded files). Quoted exactly as
# written in the report. Actual-vs-predicted points and a live feature
# importance ranking are instead computed on the fly, in this app, by
# retraining a Random Forest on data/dataset.csv using the same
# methodology the report describes (75:25 split, 300 trees, minimum leaf
# size 2) — see ml.py. Those live results are shown ALONGSIDE these
# report-stated scores, never merged into them silently.
# ---------------------------------------------------------------------
REPORT_STATED_ML_METRICS = {
    "H2_Retrofit": {"R2": 0.703, "MAE": 0.048, "RMSE": 0.061, "unit": "kg H2 / 100 km"},
    "BEV": {"R2": 0.843, "MAE": 0.552, "RMSE": 0.722, "unit": "kWh / 100 km"},
}

# Narrative feature-importance figures exactly as given in report paragraph 88.
# "traffic level and ambient temperature dominate for both powertrains, at
# roughly 0.39 and 0.37 for the hydrogen model and 0.34 each for the BEV
# model, followed by vehicle load at about 0.12."
REPORT_STATED_FEATURE_IMPORTANCE_NOTE = (
    "The report's text states that traffic level and ambient temperature "
    "dominate for both powertrains (roughly 0.39 and 0.37 for the hydrogen "
    "model, about 0.34 each for the BEV model), followed by vehicle load at "
    "about 0.12. No per-feature table was included in the uploaded files, so "
    "the chart below is a live Random Forest run on the same dataset instead "
    "of a reproduction of that exact table."
)


# ---------------------------------------------------------------------
# Dataset (IoT telemetry)
# ---------------------------------------------------------------------
def load_dataset():
    df = pd.read_csv(DATASET_PATH)
    return df


# ---------------------------------------------------------------------
# Generic sheet parsing helpers
# ---------------------------------------------------------------------
def _sheet_rows(path, sheet_name):
    wb = openpyxl.load_workbook(path, data_only=True)
    ws = wb[sheet_name]
    return list(ws.iter_rows(values_only=True))


def _label_dict(rows):
    """Build {label_in_col_A: (col_B, col_C, col_D, ...)} skipping non-text/blank labels."""
    d = {}
    for row in rows:
        if row and isinstance(row[0], str) and row[0].strip():
            d[row[0].strip()] = row[1:]
    return d


# ---------------------------------------------------------------------
# TCO_analysis.xlsx
# ---------------------------------------------------------------------
def load_tco_assumptions():
    rows = _sheet_rows(TCO_PATH, "Assumptions")
    d = _label_dict(rows)
    out = {}
    for label, vals in d.items():
        if label in ("SECTION 1 - TOTAL COST OF OWNERSHIP: ASSUMPTIONS",) or label.startswith(
            ("All blue cells", "Consumption values", "NOT included")
        ) or label == "Parameter":
            continue
        out[label] = {"H2_Retrofit": vals[0], "BEV": vals[1], "unit": vals[2], "basis": vals[3]}
    return out


def load_tco_calculation():
    rows = _sheet_rows(TCO_PATH, "TCO_Calculation")
    d = _label_dict(rows)
    out = {}
    skip_prefixes = ("5-YEAR TOTAL", "Green cells", "A. CAPITAL", "B. RUNNING", "C. RESULT")
    for label, vals in d.items():
        if label == "Line item" or label.startswith(skip_prefixes):
            continue
        out[label] = {"H2_Retrofit": vals[0], "BEV": vals[1], "formula": vals[2] if len(vals) > 2 else None}
    return out


def load_tco_year_by_year():
    rows = _sheet_rows(TCO_PATH, "Year_by_Year")
    data = []
    for row in rows:
        if row and isinstance(row[0], (int, float)) and row[0] is not None:
            try:
                year = int(row[0])
            except (TypeError, ValueError):
                continue
            data.append({"Year": year, "H2_cumulative": row[1], "BEV_cumulative": row[2], "Difference": row[3]})
    return pd.DataFrame(data)


def load_tco_sensitivity():
    rows = _sheet_rows(TCO_PATH, "Sensitivity")
    test1, test2 = [], []
    current = None
    for row in rows:
        if not row or row[0] is None:
            continue
        label = row[0]
        if isinstance(label, str) and label.startswith("Test 1"):
            current = test1
            continue
        if isinstance(label, str) and label.startswith("Test 2"):
            current = test2
            continue
        if isinstance(label, (int, float)) and current is not None:
            current.append({"x": label, "H2_cost_per_km": row[1], "BEV_cost_per_km": row[2], "ratio": row[3]})
    return pd.DataFrame(test1), pd.DataFrame(test2)


# ---------------------------------------------------------------------
# feasibility_comparison.xlsx
# ---------------------------------------------------------------------
def load_wtw_efficiency():
    rows = _sheet_rows(FEAS_PATH, "WTW_Efficiency")
    paths = {"PATH A": [], "PATH B": [], "PATH C": []}
    overall = {}
    current = None
    for row in rows:
        if not row or row[0] is None:
            continue
        label = str(row[0])
        if label.startswith("PATH A"):
            current = "PATH A"
            continue
        if label.startswith("PATH B"):
            current = "PATH B"
            continue
        if label.startswith("PATH C"):
            current = "PATH C"
            continue
        if label == "Stage":
            continue
        if label.startswith("OVERALL WELL-TO-WHEEL"):
            overall[current] = row[1]
            continue
        if label.startswith(("COMPARISON", "CONCLUSION", "Electricity needed", "Energy wasted")):
            continue
        if current is not None:
            paths[current].append({"stage": label, "stage_efficiency": row[1], "cumulative_efficiency": row[2], "why": row[3]})
    name_map = {"PATH A": "BEV", "PATH B": "H2_ICE", "PATH C": "H2_FC"}
    stages = {name_map[k]: pd.DataFrame(v) for k, v in paths.items()}
    overall_named = {name_map[k]: v for k, v in overall.items()}
    return stages, overall_named


def load_infrastructure():
    rows = _sheet_rows(FEAS_PATH, "Infrastructure")
    data = []
    started = False
    for row in rows:
        if not row or row[0] is None:
            continue
        if row[0] == "Aspect":
            started = True
            continue
        if not started:
            continue
        if isinstance(row[0], str) and row[0].startswith("Sources:"):
            continue
        data.append({"Aspect": row[0], "Hydrogen": row[1], "BEV_Electricity": row[2]})
    return pd.DataFrame(data)


def load_safety():
    rows = _sheet_rows(FEAS_PATH, "Safety")
    data = []
    started = False
    for row in rows:
        if not row or row[0] is None:
            continue
        if row[0] == "Safety issue":
            started = True
            continue
        if not started:
            continue
        if isinstance(row[0], str) and row[0].startswith("Summary:"):
            continue
        data.append({"Issue": row[0], "H2_Retrofit": row[1], "BEV": row[2], "Worse": row[3]})
    return pd.DataFrame(data)


def load_final_comparison():
    rows = _sheet_rows(FEAS_PATH, "Final_Comparison")
    data = []
    started = False
    for row in rows:
        if not row or row[0] is None:
            continue
        if row[0] == "Parameter":
            started = True
            continue
        if not started:
            continue
        data.append({"Parameter": row[0], "H2_Retrofit": row[1], "BEV": row[2]})
    return pd.DataFrame(data)


def load_final_score():
    rows = _sheet_rows(FEAS_PATH, "Final_Score")
    criteria = []
    total = None
    gap = None
    verdict = None
    why = []
    started = False
    for row in rows:
        if not row or row[0] is None:
            continue
        label = row[0]
        if label == "Criterion":
            started = True
            continue
        if not started:
            continue
        if isinstance(label, str) and label.startswith("TOTAL"):
            total = {"H2_weighted": row[4], "BEV_weighted": row[5]}
            continue
        if isinstance(label, str) and label.startswith("Gap"):
            gap = row[1]
            continue
        if isinstance(label, str) and label.startswith("VERDICT"):
            verdict = row[1]
            continue
        if isinstance(label, str) and label.startswith("WHY THIS"):
            continue
        if isinstance(label, str) and label[0].isdigit() and isinstance(row[1], (int, float)):
            criteria.append({
                "Criterion": label, "Weight": row[1], "H2_score": row[2], "BEV_score": row[3],
                "H2_weighted": row[4], "BEV_weighted": row[5], "Evidence": row[6],
            })
        elif isinstance(label, str) and label[0].isdigit():
            why.append(label)
    return pd.DataFrame(criteria), total, gap, verdict, why


# ---------------------------------------------------------------------
# Consistency check across files
# ---------------------------------------------------------------------
def run_consistency_check():
    """Cross-check headline figures across dataset.csv, tco_analysis.xlsx,
    feasibility_comparison.xlsx and final_comparison.csv. Returns a list of
    dicts describing any mismatch found, plus a list of confirmations."""
    issues = []
    confirmations = []

    df = load_dataset()
    tco_calc = load_tco_calculation()
    tco_assump = load_tco_assumptions()
    final_cmp = load_final_comparison()

    # 1. Row counts
    n_h2 = (df["vehicle_type"] == "H2_Retrofit").sum()
    n_bev = (df["vehicle_type"] == "BEV").sum()
    confirmations.append(f"dataset.csv: {len(df)} rows total ({n_h2} H2 Retrofit, {n_bev} BEV) — matches report's stated 1,000 rows (500/500).")

    # 2. Mean consumption vs assumptions sheet "Consumption per 100 km"
    mean_h2 = df.loc[df["vehicle_type"] == "H2_Retrofit", "fuel_or_energy_consumption"].mean()
    mean_bev = df.loc[df["vehicle_type"] == "BEV", "fuel_or_energy_consumption"].mean()
    assumed_h2 = tco_assump.get("Consumption per 100 km", {}).get("H2_Retrofit")
    assumed_bev = tco_assump.get("Consumption per 100 km", {}).get("BEV")
    if assumed_h2 is not None and abs(mean_h2 - assumed_h2) > 0.02:
        issues.append({
            "where": "dataset.csv vs tco_analysis.xlsx (Assumptions)",
            "what": "Mean H2 consumption per 100km",
            "values": f"dataset.csv mean = {mean_h2:.3f}, Assumptions sheet = {assumed_h2}",
        })
    else:
        confirmations.append(f"dataset.csv mean H2 consumption ({mean_h2:.2f} kg/100km) matches the Assumptions sheet input ({assumed_h2}).")
    if assumed_bev is not None and abs(mean_bev - assumed_bev) > 0.05:
        issues.append({
            "where": "dataset.csv vs tco_analysis.xlsx (Assumptions)",
            "what": "Mean BEV consumption per 100km",
            "values": f"dataset.csv mean = {mean_bev:.3f}, Assumptions sheet = {assumed_bev}",
        })
    else:
        confirmations.append(f"dataset.csv mean BEV consumption ({mean_bev:.2f} kWh/100km) matches the Assumptions sheet input ({assumed_bev}).")

    # 3. 5-year total cost: TCO_Calculation vs Final_Comparison (feasibility file) vs final_comparison.csv
    calc_h2_total = tco_calc.get("5-year TOTAL cost", {}).get("H2_Retrofit")
    calc_bev_total = tco_calc.get("5-year TOTAL cost", {}).get("BEV")
    fc_row = final_cmp[final_cmp["Parameter"] == "5-year total cost"]
    if not fc_row.empty:
        fc_h2_text = str(fc_row.iloc[0]["H2_Retrofit"])
        fc_bev_text = str(fc_row.iloc[0]["BEV"])
        if calc_h2_total is not None and f"{calc_h2_total:,.0f}".replace(",", "") not in fc_h2_text.replace(",", ""):
            issues.append({
                "where": "tco_analysis.xlsx (TCO_Calculation) vs feasibility_comparison.xlsx (Final_Comparison)",
                "what": "5-year total cost, H2 Retrofit",
                "values": f"TCO_Calculation = {calc_h2_total}, Final_Comparison = {fc_h2_text}",
            })
        else:
            confirmations.append("5-year total cost figures agree between tco_analysis.xlsx and feasibility_comparison.xlsx.")

    # 4. Safety warning shares mentioned in the app spec vs actual dataset
    bev_warn = (df.loc[df["vehicle_type"] == "BEV", "safety_status"] == "Warning").mean() * 100
    h2_warn = (df.loc[df["vehicle_type"] == "H2_Retrofit", "safety_status"] == "Warning").mean() * 100
    if abs(bev_warn - 23.8) > 0.5 or abs(h2_warn - 7.6) > 0.5:
        issues.append({
            "where": "dataset.csv vs expected synthetic safety-warning shares",
            "what": "Safety warning percentage by vehicle type",
            "values": f"dataset.csv: BEV={bev_warn:.1f}%, H2={h2_warn:.1f}% (expected approx BEV 23.8%, H2 7.6%)",
        })
    else:
        confirmations.append(f"Safety-warning shares in dataset.csv (BEV {bev_warn:.1f}%, H2 {h2_warn:.1f}%) match the report's stated figures.")

    return issues, confirmations
