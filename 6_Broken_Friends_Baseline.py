
import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Robust import: look for friends_utils.py one level up from /pages
sys.path.append(str(Path(__file__).resolve().parent.parent))
from friends_utils import detect_broken_mutuals, auto_rename_columns

st.title("Έλεγχος Σπασμένων Αμοιβαίων (Baseline Βημάτων 1+2)")

st.write("""
**Κανόνας:** Στα Βήματα 3–7 **δεν** επιτρέπονται **νέες** σπασμένες πλήρως αμοιβαίες δυάδες
σε σχέση με το baseline που προκύπτει από τα Βήματα 1+2.
""")

left, right = st.columns(2)

with left:
    step_number = st.number_input(
        "Tρέχον Βήμα", min_value=1, max_value=7, value=5, step=1,
        help="Για Βήματα 1–2: δεν απορρίπτονται σενάρια λόγω σπασμένων. Για 3–7: δεν επιτρέπονται ΝΕΕΣ σπασμένες."
    )
    current_file = st.file_uploader(
        "Workbook τρέχοντος Βήματος (xlsx, με πολλά φύλλα/σενάρια)",
        type=["xlsx"]
    )

with right:
    baseline_file = st.file_uploader(
        "Προαιρετικά: Αναφορά Baseline (από Βήματα 1+2)",
        type=["xlsx"],
        help=(
            "Αν περιέχει φύλλο 'SUMMARY' με στήλες ['ΣΕΝΑΡΙΟ', 'BROKEN_BASELINE'] "
            "ή ['BROKEN_MUTUAL_ΣΥΝΟΛΟ'] ή ['ΣΠΑΣΜΕΝΕΣ_ΔΥΑΔΕΣ'], θα χρησιμοποιηθεί ως baseline."
        )
    )

def load_baseline_map(xlpath_or_buf):
    if xlpath_or_buf is None:
        return {}
    try:
        xls = pd.ExcelFile(xlpath_or_buf)
        sheet_name = "SUMMARY" if "SUMMARY" in xls.sheet_names else xls.sheet_names[0]
        df = pd.read_excel(xlpath_or_buf, sheet_name=sheet_name)
        df.columns = [str(c).strip().upper() for c in df.columns]
        # find scenario column
        scen_col = "ΣΕΝΑΡΙΟ"
        if scen_col not in df.columns:
            for c in df.columns:
                if "ΣΕΝΑΡΙΟ" in c:
                    scen_col = c
                    break
        # choose baseline column
        base_col = None
        for c in ["BROKEN_BASELINE", "BROKEN_MUTUAL_ΣΥΝΟΛΟ", "ΣΠΑΣΜΕΝΕΣ_ΔΥΑΔΕΣ", "ΣΠΑΣΜΕΝΕΣ ΦΙΛΙΕΣ"]:
            if c in df.columns:
                base_col = c
                break
        if scen_col in df.columns and base_col:
            tmp = df[[scen_col, base_col]].copy()
            tmp.columns = ["ΣΕΝΑΡΙΟ", "BROKEN_BASELINE"]
            tmp["ΣΕΝΑΡΙΟ"] = tmp["ΣΕΝΑΡΙΟ"].astype(str)
            tmp["BROKEN_BASELINE"] = pd.to_numeric(tmp["BROKEN_BASELINE"], errors="coerce").fillna(0).astype(int)
            return dict(zip(tmp["ΣΕΝΑΡΙΟ"], tmp["BROKEN_BASELINE"]))
    except Exception as e:
        st.warning(f"Αδυναμία ανάγνωσης baseline: {e}")
    return {}

def scenario_is_valid(step: int, broken_current: int, broken_baseline: int) -> bool:
    # Βήματα 1–2: πάντα έγκυρα ως προς αυτό το κριτήριο
    if step in (1, 2):
        return True
    # Βήματα 3–7: δεν επιτρέπονται νέες σπασμένες
    return broken_current <= broken_baseline

baseline_map = load_baseline_map(baseline_file)

if current_file is None:
    st.info("Ανέβασε ένα workbook για έλεγχο.")
    st.stop()

xls = pd.ExcelFile(current_file)
rows = []
per_sheet_broken = {}
per_sheet_stats = {}

for sheet in xls.sheet_names:
    df_raw = pd.read_excel(current_file, sheet_name=sheet)
    df, _ = auto_rename_columns(df_raw)

    # πληθυσμοί ανά τμήμα
    if "ΤΜΗΜΑ" in df.columns:
        per_sheet_stats[sheet] = df.groupby("ΤΜΗΜΑ").size().rename("ΣΥΝΟΛΟ ΜΑΘΗΤΩΝ").to_frame()
    else:
        per_sheet_stats[sheet] = pd.DataFrame({"ΣΥΝΟΛΟ ΜΑΘΗΤΩΝ": []})

    broken_by_class, broken_list_df, mutual_total, broken_total = detect_broken_mutuals(df)
    baseline = int(baseline_map.get(str(sheet), 0))
    new_broken = max(0, int(broken_total) - baseline)
    valid = scenario_is_valid(step_number, broken_total, baseline)

    per_sheet_broken[sheet] = broken_list_df.copy()

    rows.append({
        "ΣΕΝΑΡΙΟ": sheet,
        "MUTUAL_ΣΥΝΟΛΟ": int(mutual_total),
        "BROKEN_BASELINE(Σ1+Σ2)": baseline,
        "BROKEN_CURRENT": int(broken_total),
        "NEW_BROKEN(>=0)": int(new_broken),
        "VALID_BY_RULE": "ΝΑΙ" if valid else "ΟΧΙ"
    })

summary = pd.DataFrame(rows).sort_values("ΣΕΝΑΡΙΟ")
st.subheader("Σύνοψη ανά σενάριο")
st.dataframe(summary, use_container_width=True)

st.download_button(
    "Κατέβασε SUMMARY (CSV)",
    data=summary.to_csv(index=False).encode("utf-8-sig"),
    file_name="broken_summary_with_baseline.csv",
    mime="text/csv"
)

st.divider()
st.subheader("Λίστες σπασμένων αμοιβαίων")
for scen, df_b in per_sheet_broken.items():
    st.markdown(f"**{scen}**")
    if df_b.empty:
        st.info("— καμία σπασμένη —")
    else:
        st.dataframe(df_b, use_container_width=True)

if st.button("Εξαγωγή αναφοράς Excel"):
    out_path = Path("broken_friends_report_v2.xlsx")
    with pd.ExcelWriter(out_path, engine="openpyxl") as w:
        summary.to_excel(w, index=False, sheet_name="SUMMARY")
        for scen, stats_df in per_sheet_stats.items():
            stats_df.to_excel(w, sheet_name=str(scen)[:31] or "STATS")
        for scen, broken_df in per_sheet_broken.items():
            name = (str(scen)[:25] + "_BROKEN") or "BROKEN"
            if broken_df.empty:
                pd.DataFrame({"info": ["— καμία σπασμένη —"]}).to_excel(w, index=False, sheet_name=name[:31])
            else:
                broken_df.to_excel(w, index=False, sheet_name=name[:31])
    st.success(f"Αποθηκεύτηκε: {out_path.as_posix()}")
    with open(out_path, "rb") as f:
        st.download_button("Download Excel report", data=f.read(),
                           file_name="broken_friends_report_v2.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
