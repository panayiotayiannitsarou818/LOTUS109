
import streamlit as st
import pandas as pd
import numpy as np
import math
import io
import zipfile
import traceback
from datetime import datetime
from collections import defaultdict, Counter
from itertools import combinations

# Optional plotting libs (safe import)
try:
    import plotly.express as px
    PLOTLY_AVAILABLE = True
except Exception:
    PLOTLY_AVAILABLE = False

# ============== Page Setup & Styles ==============
st.set_page_config(page_title="Κατανομή Μαθητών Α' Δημοτικού", page_icon="🎓", layout="wide")

st.markdown("""
<style>
    .main-header { text-align:center; color:#2E86AB; font-size:2.2rem; margin:0 0 1rem; font-weight:700; }
    .step-header { background:linear-gradient(90deg,#2E86AB,#A23B72); color:#fff; padding:0.8rem 1rem; border-radius:12px; text-align:center; margin:1rem 0; font-weight:700; }
    .stats-container { background:#f8f9fa; padding:1rem; border-radius:14px; margin:1rem 0; box-shadow:0 2px 10px rgba(0,0,0,0.06); }
    .success-box { background:#d4edda; border:1px solid #c3e6cb; color:#155724; padding:0.8rem; border-radius:10px; margin:0.6rem 0; }
    .warning-box { background:#fff3cd; border:1px solid #ffeaa7; color:#856404; padding:0.8rem; border-radius:10px; margin:0.6rem 0; }
    .error-box { background:#f8d7da; border:1px solid #f5c6cb; color:#721c24; padding:0.8rem; border-radius:10px; margin:0.6rem 0; }
</style>
""", unsafe_allow_html=True)

# Fixed footer (1 cm from bottom-right)
st.markdown("""
<div style="position:fixed; bottom:1cm; right:1cm; background:white; padding:0.5rem 0.7rem; border-radius:10px; 
            box-shadow:0 2px 10px rgba(0,0,0,0.2); z-index:1000; font-size:0.8rem; color:#666; border:1px solid #ddd;">
    © Γιαννίτσαρου Παναγιώτα<br>📧 panayiotayiannitsarou@gmail.com
</div>
""", unsafe_allow_html=True)

# ============== Session State ==============
def init_session_state():
    defaults = {
        "authenticated": False,
        "terms_accepted": False,
        "app_enabled": False,
        "data": None,
        "current_section": "login",
        "settings": {
            "max_students": 25,
            "max_diff": 2,
            "num_scenarios": 3,
            "auto_calc": True,
            "manual_classes": None,
            "include_details": True,
            "show_charts": PLOTLY_AVAILABLE,
        },
        "final_results": None,
        "statistics": None,
        "detailed_steps": None,
        "class_labels": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ============== Auth & Terms ==============
def show_login():
    st.markdown("<h1 class='main-header'>🔒 Κλείδωμα Πρόσβασης</h1>", unsafe_allow_html=True)
    pw = st.text_input("Κωδικός:", type="password")
    if st.button("🔓 Είσοδος", use_container_width=True):
        if pw == "katanomi2025":
            st.session_state.authenticated = True
            st.session_state.current_section = "terms"
            st.success("✅ Επιτυχής είσοδος.")
            st.rerun()
        else:
            st.error("❌ Λάθος κωδικός πρόσβασης.")

def show_terms():
    st.markdown("<h1 class='main-header'>📋 Όροι Χρήσης & Πνευματικά Δικαιώματα</h1>", unsafe_allow_html=True)
    st.markdown("""
    <div class="stats-container">
      <h3 style="text-align:center;color:#2E86AB;">© Νομική Προστασία</h3>
      <p><b>Δικαιούχος:</b> Γιαννίτσαρου Παναγιώτα — 📧 panayiotayiannitsarou@gmail.com</p>
      <ol>
        <li><b>Πνευματικά Δικαιώματα:</b> Απαγορεύεται αναπαραγωγή/τροποποίηση χωρίς άδεια.</li>
        <li><b>Εκπαιδευτική Χρήση:</b> Αποκλειστικά για κατανομή μαθητών.</li>
        <li><b>GDPR:</b> Προστασία προσωπικών δεδομένων μαθητών.</li>
        <li><b>Ευθύνη Χρήσης:</b> Πλήρης ευθύνη του χρήστη.</li>
        <li><b>Περιορισμοί:</b> Μη εμπορική εκμετάλλευση.</li>
      </ol>
      <div style="background:#e3f2fd;padding:0.6rem;border-radius:10px;text-align:center;"><b>⚠️ Η χρήση συνεπάγεται αποδοχή.</b></div>
    </div>
    """, unsafe_allow_html=True)
    accepted = st.checkbox("✅ Αποδέχομαι τους όρους")
    if st.button("➡️ Συνέχεια", disabled=not accepted, use_container_width=True):
        st.session_state.terms_accepted = True
        st.session_state.current_section = "app_control"
        st.rerun()

def show_app_control():
    st.markdown("<h1 class='main-header'>⚙️ Έλεγχος Εφαρμογής</h1>", unsafe_allow_html=True)
    if st.session_state.app_enabled:
        st.markdown("<div class='success-box'>🟢 Η εφαρμογή είναι ΕΝΕΡΓΗ.</div>", unsafe_allow_html=True)
        if st.button("🔴 Απενεργοποίηση", use_container_width=True):
            st.session_state.app_enabled = False
            st.rerun()
    else:
        st.markdown("<div class='warning-box'>🔴 Η εφαρμογή είναι ΑΠΕΝΕΡΓΟΠΟΙΗΜΕΝΗ.</div>", unsafe_allow_html=True)
        if st.button("🟢 Ενεργοποίηση", use_container_width=True):
            st.session_state.app_enabled = True
            st.rerun()
    if st.session_state.app_enabled:
        st.markdown("---")
        if st.button("🚀 Είσοδος στην Κύρια Εφαρμογή", use_container_width=True):
            st.session_state.current_section = "main_app"
            st.rerun()

# ============== Utilities ==============
REQUIRED_COLUMNS = [
    "ΟΝΟΜΑ", "ΦΥΛΟ", "ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ",
    "ΖΩΗΡΟΣ", "ΙΔΙΑΙΤΕΡΟΤΗΤΑ", "ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ",
    "ΦΙΛΟΙ", "ΣΥΓΚΡΟΥΣΗ", "ΤΜΗΜΑ"
]

def validate_excel_columns(df: pd.DataFrame):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    return missing

def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # Gender
    if "ΦΥΛΟ" in df.columns:
        df["ΦΥΛΟ"] = (
            df["ΦΥΛΟ"].astype(str).str.upper().str.strip()
            .replace({"ΑΓΟΡΙ":"Α","ΚΟΡΙΤΣΙ":"Κ","BOY":"Α","GIRL":"Κ","M":"Α","F":"Κ"})
        )
    # Yes/No cols
    for col in ["ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ","ΖΩΗΡΟΣ","ΙΔΙΑΙΤΕΡΟΤΗΤΑ","ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ"]:
        if col in df.columns:
            df[col] = (
                df[col].astype(str).str.upper().str.strip()
                .replace({"ΝΑΙ":"Ν","ΟΧΙ":"Ο","YES":"Ν","NO":"Ο","1":"Ν","0":"Ο","TRUE":"Ν","FALSE":"Ο"})
            )
    # Fill NA strings
    for col in ["ΦΙΛΟΙ","ΣΥΓΚΡΟΥΣΗ","ΤΜΗΜΑ"]:
        if col in df.columns:
            df[col] = df[col].fillna("")
    return df

def auto_num_classes(df: pd.DataFrame, override: int = None, min_classes: int = 2) -> int:
    if override is not None:
        try:
            return max(min_classes, int(override))
        except Exception:
            pass
    N = 0 if df is None else len(df)
    return max(min_classes, math.ceil(N/25))  # ΠΑΝΤΑ ≥2

def greek_class_labels(k: int):
    return [f"Α{i+1}" for i in range(k)]

def parse_relationships(text: str):
    if not isinstance(text, str):
        return []
    # split by commas / semicolons / greek "και"
    parts = []
    for token in text.replace(";", ",").split(","):
        t = token.strip()
        if t:
            # also split on ' και '
            if " και " in t:
                parts.extend([p.strip() for p in t.split(" και ") if p.strip()])
            else:
                parts.append(t)
    return parts

def build_step_columns_with_prev(dataframe, scenario_dict, scenario_num, base_columns=None):
    if base_columns is None:
        base_columns = ["ΟΝΟΜΑ"]
    df_out = dataframe[base_columns].copy()
    step_map = scenario_dict.get("data", {})
    def _step_num_from_key(k):
        try:
            return int(k.split("_")[0].replace("ΒΗΜΑ",""))
        except Exception:
            return 999
    ordered_keys = sorted(step_map.keys(), key=_step_num_from_key)
    full_steps_df = pd.DataFrame({k: pd.Series(v) for k, v in step_map.items()})
    def _clean_series(s): return s.replace({None:""}).fillna("")
    prev_series = None
    prev_changed_mask = None
    for idx, step_key in enumerate(ordered_keys):
        curr_series = _clean_series(full_steps_df[step_key].astype(str))
        if idx == 0:
            curr_changed_mask = curr_series != ""
            out_col = pd.Series([""]*len(curr_series), index=curr_series.index, dtype=object)
            out_col[curr_changed_mask] = curr_series[curr_changed_mask]
        else:
            prev_series_filled = _clean_series(prev_series.astype(str))
            curr_changed_mask = curr_series != prev_series_filled
            out_col = pd.Series([""]*len(curr_series), index=curr_series.index, dtype=object)
            out_col[curr_changed_mask] = curr_series[curr_changed_mask]
            if prev_changed_mask is not None:
                mask = prev_changed_mask & (~curr_changed_mask)
                out_col[mask] = prev_series_filled[mask]
        df_out[step_key] = out_col
        prev_series = curr_series
        prev_changed_mask = curr_changed_mask
    if "final" in scenario_dict:
        df_out["ΒΗΜΑ7_ΤΕΛΙΚΟ"] = scenario_dict["final"]
    return df_out

def validate_assignment_constraints(assignment, max_per_class=25, max_diff=2):
    counts = Counter([cls for cls in assignment if cls])
    if not counts:
        return True, {"max_over":0, "diff":0}
    max_over = max(0, max(counts.values()) - max_per_class)
    diff = max(counts.values()) - min(counts.values())
    ok = (max_over == 0) and (diff <= max_diff)
    return ok, {"max_over":max_over, "diff":diff}

def build_statistics(df: pd.DataFrame, assignment, class_labels):
    # Build a per-class statistics table
    stats = []
    for cls in class_labels:
        idxs = [i for i, c in enumerate(assignment) if c == cls]
        sub = df.iloc[idxs] if idxs else pd.DataFrame(columns=df.columns)
        boys = int((sub["ΦΥΛΟ"]=="Α").sum()) if "ΦΥΛΟ" in sub.columns else 0
        girls = int((sub["ΦΥΛΟ"]=="Κ").sum()) if "ΦΥΛΟ" in sub.columns else 0
        teachers_kids = int((sub["ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ"]=="Ν").sum()) if "ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ" in sub.columns else 0
        lively = int((sub["ΖΩΗΡΟΣ"]=="Ν").sum()) if "ΖΩΗΡΟΣ" in sub.columns else 0
        special = int((sub["ΙΔΙΑΙΤΕΡΟΤΗΤΑ"]=="Ν").sum()) if "ΙΔΙΑΙΤΕΡΟΤΗΤΑ" in sub.columns else 0
        good_gr = int((sub["ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ"]=="Ν").sum()) if "ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ" in sub.columns else 0
        stats.append({
            "Τμήμα": cls,
            "Μαθητές": len(idxs),
            "Αγόρια": boys,
            "Κορίτσια": girls,
            "Παιδιά Εκπ/κών": teachers_kids,
            "Ζωηροί": lively,
            "Ιδιαιτερότητα": special,
            "Καλή Γνώση Ελληνικών": good_gr,
        })
    return pd.DataFrame(stats)

def detailed_score_breakdown(df: pd.DataFrame, assignment, scenario_num):
    # Gender deviation (>1): +2 per unit beyond 1 (max pairwise deviation)
    class_labels = sorted(list(set([c for c in assignment if c])))
    per_class_idxs = {cls:[i for i,c in enumerate(assignment) if c==cls] for cls in class_labels}
    def count_boys(idxs): return sum(1 for i in idxs if df.iloc[i]["ΦΥΛΟ"]=="Α")
    def count_good_gr(idxs): return sum(1 for i in idxs if df.iloc[i]["ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ"]=="Ν")
    # population & gender
    pops = [len(v) for v in per_class_idxs.values()] or [0]
    max_pop_diff = max(pops) - min(pops) if pops else 0
    pop_pen = 3*max(0, max_pop_diff-1)  # (>1): +3/μονάδα

    boys_counts = [count_boys(v) for v in per_class_idxs.values()] or [0]
    girls_counts = [p-b for p,b in zip(pops, boys_counts)]
    # measure gender deviation as max|boys-girls| across classes minus 1 threshold
    gender_devs = [abs(b-g) for b,g in zip(boys_counts, girls_counts)] or [0]
    max_gender_dev = max(gender_devs) if gender_devs else 0
    gender_pen = 2*max(0, max_gender_dev-1)

    # Greek knowledge deviation (>2): +1 per unit beyond 2
    good_gr_counts = [count_good_gr(v) for v in per_class_idxs.values()] or [0]
    max_good_diff = (max(good_gr_counts)-min(good_gr_counts)) if good_gr_counts else 0
    greek_pen = max(0, max_good_diff-2) * 1

    # Special-pair conflicts (I-I : +5, I-Z : +4, Z-Z : +3) when in same class
    I_I = I_Z = Z_Z = 0
    for cls, idxs in per_class_idxs.items():
        for i, j in combinations(idxs, 2):
            row_i, row_j = df.iloc[i], df.iloc[j]
            isI_i = row_i["ΙΔΙΑΙΤΕΡΟΤΗΤΑ"]=="Ν"
            isI_j = row_j["ΙΔΙΑΙΤΕΡΟΤΗΤΑ"]=="Ν"
            isZ_i = row_i["ΖΩΗΡΟΣ"]=="Ν"
            isZ_j = row_j["ΖΩΗΡΟΣ"]=="Ν"
            if isI_i and isI_j: I_I += 1
            elif (isI_i and isZ_j) or (isZ_i and isI_j): I_Z += 1
            elif isZ_i and isZ_j: Z_Z += 1
    special_pen = I_I*5 + I_Z*4 + Z_Z*3

    # Broken mutual friendships (+5 per broken fully mutual pair)
    broken_friends = 0
    seen_pairs = set()
    names = df["ΟΝΟΜΑ"].tolist()
    name_to_index = {n:i for i,n in enumerate(names)}
    for i, row in df.iterrows():
        friends = parse_relationships(row.get("ΦΙΛΟΙ",""))
        for f in friends:
            if f in name_to_index:
                j = name_to_index[f]
                # mutual?
                fr_friends = parse_relationships(df.iloc[j].get("ΦΙΛΟΙ",""))
                pair = tuple(sorted([row["ΟΝΟΜΑ"], f]))
                if row["ΟΝΟΜΑ"] in fr_friends and pair not in seen_pairs:
                    if assignment[i] != assignment[j]:
                        broken_friends += 1
                    seen_pairs.add(pair)
    broken_pen = broken_friends * 5

    # Explicit external conflicts: if two names in each other's ΣΥΓΚΡΟΥΣΗ appear in same class, heavy penalty
    conflict_violations = 0
    for i, row in df.iterrows():
        conflicts = parse_relationships(row.get("ΣΥΓΚΡΟΥΣΗ",""))
        for c in conflicts:
            j = name_to_index.get(c, None)
            if j is not None and j > i:  # check pair once
                if assignment[i] == assignment[j] and assignment[i] is not None:
                    conflict_violations += 1
    conflict_pen = conflict_violations * 50

    total = gender_pen + pop_pen + greek_pen + special_pen + broken_pen + conflict_pen
    return {
        "ΣΕΝΑΡΙΟ": f"ΣΕΝΑΡΙΟ_{scenario_num}",
        "Δ_ΦΥΛΟ": float(gender_pen),
        "Δ_ΠΛΗΘΥΣΜΟΣ": float(pop_pen),
        "Δ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ": float(greek_pen),
        "ΠΑΙΔ_ΣΥΓΚΡ_Ι_Ι": int(I_I),
        "ΠΑΙΔ_ΣΥΓΚΡ_Ι_Ζ": int(I_Z),
        "ΠΑΙΔ_ΣΥΓΚΡ_Ζ_Ζ": int(Z_Z),
        "ΣΠΑΣΜΕΝΗ_ΦΙΛΙΑ": int(broken_friends),
        "ΣΥΓΚΡΟΥΣΕΙΣ": int(conflict_violations),
        "ΒΑΘΜΟΛΟΓΙΑ": float(total),
    }

# ============== Simple Baseline Allocation (fallback) ==============
def baseline_allocation(df: pd.DataFrame, class_labels):
    # round-robin ensures diff ≤1; with k=ceil(N/25) also ensures ≤25 per class
    N = len(df)
    assign = []
    k = len(class_labels)
    for idx in range(N):
        assign.append(class_labels[idx % k])
    return assign

def run_allocation_steps(df: pd.DataFrame, num_classes: int, num_scenarios: int = 3):
    """
    Placeholder pipeline that produces deterministic fair baseline scenarios.
    It builds step columns ΒΗΜΑ1..ΒΗΜΑ6 (with ΒΗΜΑ2 identical to ΒΗΜΑ1 so the
    'Νέες+Προηγούμενο' προβολή δουλεύει) και υπολογίζει ΒΗΜΑ7 βαθμολογία.
    """
    class_labels = greek_class_labels(num_classes)
    scenarios = {}
    for s in range(1, num_scenarios+1):
        # For variability across scenarios, rotate start index
        rotated_labels = class_labels[s-1:] + class_labels[:s-1]
        final_assignment = baseline_allocation(df, rotated_labels)

        # Build dummy steps
        steps = {}
        steps[f"ΒΗΜΑ1_ΣΕΝΑΡΙΟ_{s}"] = final_assignment[:]  # first placement
        steps[f"ΒΗΜΑ2_ΣΕΝΑΡΙΟ_{s}"] = final_assignment[:]  # no changes
        steps[f"ΒΗΜΑ3_ΣΕΝΑΡΙΟ_{s}"] = final_assignment[:]
        steps[f"ΒΗΜΑ4_ΣΕΝΑΡΙΟ_{s}"] = final_assignment[:]
        steps[f"ΒΗΜΑ5_ΣΕΝΑΡΙΟ_{s}"] = final_assignment[:]
        steps[f"ΒΗΜΑ6_ΣΕΝΑΡΙΟ_{s}"] = final_assignment[:]

        ok, info = validate_assignment_constraints(final_assignment, 25, 2)
        if not ok:
            st.warning(f"⚠️ Σενάριο {s}: Παραβίαση ορίων (>{25}/τμήμα ή διαφορά πληθυσμού>{2}). Προσπαθήστε με περισσότερα τμήματα.")

        # Statistics & scores
        stats = build_statistics(df, final_assignment, class_labels)
        score = detailed_score_breakdown(df, final_assignment, s)

        scenarios[s] = {
            "data": steps,
            "final": final_assignment,
            "final_score": score["ΒΑΘΜΟΛΟΓΙΑ"],
            "detailed_score": score,
            "statistics": stats
        }
    return scenarios, class_labels

# ============== UI Sections ==============
def display_data_summary(df):
    st.markdown("""<div class="stats-container"><h3 style="text-align:center;color:#2E86AB;">📊 Περίληψη Δεδομένων</h3></div>""", unsafe_allow_html=True)
    total = len(df)
    boys = int((df["ΦΥΛΟ"]=="Α").sum()) if "ΦΥΛΟ" in df.columns else 0
    girls = int((df["ΦΥΛΟ"]=="Κ").sum()) if "ΦΥΛΟ" in df.columns else 0
    teachers_kids = int((df["ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ"]=="Ν").sum()) if "ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ" in df.columns else 0
    lively = int((df["ΖΩΗΡΟΣ"]=="Ν").sum()) if "ΖΩΗΡΟΣ" in df.columns else 0
    special = int((df["ΙΔΙΑΙΤΕΡΟΤΗΤΑ"]=="Ν").sum()) if "ΙΔΙΑΙΤΕΡΟΤΗΤΑ" in df.columns else 0
    good_gr = int((df["ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ"]=="Ν").sum()) if "ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ" in df.columns else 0

    num_classes = auto_num_classes(df)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("👥 Συνολικοί Μαθητές", total)
    c2.metric("👦 Αγόρια", boys)
    c3.metric("👧 Κορίτσια", girls)
    c4.metric("🎯 Υπολογισμένα Τμήματα", num_classes)
    st.markdown("---")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("🏫 Παιδιά Εκπ/κών", teachers_kids)
    c2.metric("⚡ Ζωηροί", lively)
    c3.metric("🎨 Ιδιαιτερότητα", special)
    c4.metric("🇬🇷 Καλή Γνώση Ελλ.", good_gr)

def show_upload_section():
    st.markdown("<div class='step-header'>📥 Εισαγωγή Δεδομένων</div>", unsafe_allow_html=True)
    f = st.file_uploader("Ανέβασε Excel (.xlsx) ή CSV", type=["xlsx","csv"])
    if f is not None:
        try:
            if f.name.lower().endswith(".csv"):
                df = pd.read_csv(f)
            else:
                df = pd.read_excel(f)
            missing = validate_excel_columns(df)
            if missing:
                st.error("❌ Λείπουν στήλες: " + ", ".join(missing))
                return
            df = normalize_data(df)
            st.session_state.data = df
            st.success("✅ Το αρχείο φορτώθηκε και κανονικοποιήθηκε.")
            display_data_summary(df)
        except Exception as e:
            st.error(f"Σφάλμα φόρτωσης: {e}")
            st.code(traceback.format_exc())

def show_execute_section():
    st.markdown("<div class='step-header'>⚡ Εκτέλεση Κατανομής</div>", unsafe_allow_html=True)
    if st.session_state.data is None:
        st.warning("Ανέβασε πρώτα δεδομένα.")
        return

    sets = st.session_state.settings
    if sets.get("auto_calc", True):
        num_classes = auto_num_classes(st.session_state.data)
    else:
        num_classes = max(2, int(sets.get("manual_classes") or 2))

    st.info(f"Θα χρησιμοποιηθούν **{num_classes}** τμήματα (κανόνας: max(2, ⌈N/25⌉)).")

    num_scenarios = int(sets.get("num_scenarios", 3))
    if st.button("🚀 Εκτέλεση", use_container_width=True):
        scenarios, class_labels = run_allocation_steps(st.session_state.data, num_classes, num_scenarios)
        st.session_state.class_labels = class_labels
        # choose best by lowest score
        best_s = min(scenarios.keys(), key=lambda s: scenarios[s]["final_score"])
        best = scenarios[best_s]
        # persist unified results
        final_df = st.session_state.data.copy()
        final_df["ΤΜΗΜΑ"] = best["final"]
        st.session_state.final_results = final_df
        st.session_state.statistics = build_statistics(st.session_state.data, best["final"], class_labels)
        # all detailed
        st.session_state.detailed_steps = scenarios
        st.success(f"✅ Ολοκληρώθηκε. Επιλέχθηκε το ΣΕΝΑΡΙΟ {best_s} (μικρότερη βαθμολογία ΒΗΜΑ7).")

def show_details_section():
    st.markdown("<div class='step-header'>📊 Αναλυτικά Βήματα</div>", unsafe_allow_html=True)
    if st.session_state.detailed_steps is None:
        st.warning("Δεν υπάρχουν αναλυτικά βήματα. Εκτέλεσε πρώτα την κατανομή.")
        return
    st.info("Σε κάθε στήλη: Νέες τοποθετήσεις του βήματος + τοποθετήσεις του αμέσως προηγούμενου βήματος.")
    for scenario_num, scenario_data in st.session_state.detailed_steps.items():
        st.markdown(f"#### 📋 Σενάριο {scenario_num} — Αναλυτική Προβολή")
        df_view = build_step_columns_with_prev(st.session_state.data, scenario_data, scenario_num, base_columns=["ΟΝΟΜΑ"])
        st.dataframe(df_view, use_container_width=True, hide_index=True)
        if "final_score" in scenario_data:
            st.markdown(f"**🏆 ΒΗΜΑ7 Βαθμολογία:** {scenario_data['final_score']}")
        st.markdown("---")

def show_export_section():
    st.markdown("<div class='step-header'>💾 Εξαγωγή Αποτελεσμάτων</div>", unsafe_allow_html=True)
    if st.session_state.final_results is None:
        st.warning("Δεν υπάρχουν αποτελέσματα. Εκτέλεσε πρώτα την κατανομή.")
        return

    st.markdown("### 👁️ Προεπισκόπηση")
    col1, col2 = st.columns([2,1])
    with col1:
        st.dataframe(st.session_state.final_results[['ΟΝΟΜΑ','ΦΥΛΟ','ΤΜΗΜΑ']].head(10), use_container_width=True)
    with col2:
        if st.session_state.statistics is not None:
            st.markdown("**📊 Στατιστικά Κατανομής:**")
            st.dataframe(st.session_state.statistics, use_container_width=True)

    st.markdown("---")
    st.markdown("### 📁 Επιλογές Εξαγωγής")
    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### 💾 Τελικό Excel")
        if st.button("📥 Λήψη Τελικού Excel", use_container_width=True):
            try:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    st.session_state.final_results.to_excel(writer, sheet_name='Κατανομή_Μαθητών', index=False)
                    if st.session_state.statistics is not None:
                        st.session_state.statistics.to_excel(writer, sheet_name='Στατιστικά', index=False)
                st.download_button(
                    label="⬇️ Κατέβασε το Excel",
                    data=output.getvalue(),
                    file_name=f"Κατανομή_Μαθητών_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="dl_final_excel"
                )
            except Exception as e:
                st.error(f"Σφάλμα δημιουργίας αρχείου: {e}")

    with c2:
        st.markdown("#### 📦 Αναλυτικά Βήματα (ZIP)")
        if st.button("📥 Λήψη Αναλυτικών Βημάτων (ZIP)", use_container_width=True):
            try:
                if st.session_state.detailed_steps is None:
                    st.warning("Δεν υπάρχουν αναλυτικά βήματα.")
                    return
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # per-scenario files
                    for scenario_num, scenario_data in st.session_state.detailed_steps.items():
                        excel_buffer = io.BytesIO()
                        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                            # 1) Αναλυτική προβολή (Νέες + Προηγούμενο)
                            df_detailed_view = build_step_columns_with_prev(
                                st.session_state.data, scenario_data, scenario_num, base_columns=["ΟΝΟΜΑ"]
                            )
                            df_detailed_view.to_excel(writer, sheet_name=f"Σενάριο_{scenario_num}_Αναλυτικά", index=False)

                            # 2) Πλήρες Ιστορικό (ΒΗΜΑ1..ΒΗΜΑ6 πλήρη)
                            df_full_history = st.session_state.data[["ΟΝΟΜΑ"]].copy()
                            for step_key in sorted(scenario_data["data"].keys()):
                                df_full_history[step_key] = scenario_data["data"][step_key]
                            df_full_history["ΒΗΜΑ7_ΤΕΛΙΚΟ"] = scenario_data["final"]
                            df_full_history.to_excel(writer, sheet_name=f"Σενάριο_{scenario_num}_Πλήρες_Ιστορικό", index=False)

                            # 3) Αναλυτική Βαθμολογία ΒΗΜΑ7
                            if "detailed_score" in scenario_data:
                                pd.DataFrame([scenario_data["detailed_score"]]).to_excel(
                                    writer, sheet_name="ΒΑΘΜΟΛΟΓΙΑ_ΒΗΜΑ7_ΑΝΑΛΥΤΙΚΗ", index=False
                                )
                            else:
                                pd.DataFrame([{
                                    "ΣΕΝΑΡΙΟ": f"ΣΕΝΑΡΙΟ_{scenario_num}",
                                    "ΒΑΘΜΟΛΟΓΙΑ": scenario_data.get("final_score", 0)
                                }]).to_excel(writer, sheet_name="ΒΑΘΜΟΛΟΓΙΑ_ΒΗΜΑ7", index=False)

                        zip_file.writestr(f"ΣΕΝΑΡΙΟ_{scenario_num}_Αναλυτικά_Βήματα.xlsx", excel_buffer.getvalue())

                    # summary workbook
                    summary_buffer = io.BytesIO()
                    with pd.ExcelWriter(summary_buffer, engine='xlsxwriter') as writer:
                        if st.session_state.statistics is not None:
                            st.session_state.statistics.to_excel(writer, sheet_name="Στατιστικά", index=False)
                        # collect scenario scores
                        comp_rows = []
                        det_rows = []
                        for scenario_num, scenario_data in st.session_state.detailed_steps.items():
                            if "final_score" in scenario_data:
                                comp_rows.append({
                                    "Σενάριο": f"ΣΕΝΑΡΙΟ_{scenario_num}",
                                    "ΒΗΜΑ7_ΤΕΛΙΚΟ_SCORE": scenario_data["final_score"]
                                })
                            if "detailed_score" in scenario_data:
                                det_rows.append(scenario_data["detailed_score"])
                        if comp_rows:
                            pd.DataFrame(comp_rows).to_excel(writer, sheet_name="Σύγκριση_ΒΗΜΑ7_Scores", index=False)
                        if det_rows:
                            pd.DataFrame(det_rows).to_excel(writer, sheet_name="Αναλυτική_Σύγκριση_ΒΗΜΑ7", index=False)
                    zip_file.writestr("ΣΥΝΟΨΗ_Σύγκριση_Σεναρίων.xlsx", summary_buffer.getvalue())

                st.download_button(
                    label="⬇️ Κατέβασε το ZIP",
                    data=zip_buffer.getvalue(),
                    file_name=f"Αναλυτικά_Βήματα_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                    mime="application/zip",
                    key="dl_zip"
                )
                st.success("✅ Το ZIP ετοιμάστηκε.")
            except Exception as e:
                st.error(f"Σφάλμα δημιουργίας ZIP: {e}")
                st.code(traceback.format_exc())

def show_settings_section():
    st.markdown("<div class='step-header'>⚙️ Ρυθμίσεις</div>", unsafe_allow_html=True)
    sets = st.session_state.settings
    c1,c2 = st.columns(2)
    with c1:
        st.markdown("### 🎛️ Παράμετροι Κατανομής")
        sets["max_students"] = st.slider("Μέγιστο ανά τμήμα", 20, 30, sets.get("max_students",25), help="Προδιαγραφή: 25")
        sets["max_diff"] = st.slider("Μέγιστη διαφορά πληθυσμού", 1, 5, sets.get("max_diff",2), help="Προδιαγραφή: 2")
        sets["num_scenarios"] = st.selectbox("Αριθμός σεναρίων", [1,2,3,4,5], index=(sets.get("num_scenarios",3)-1))
        sets["auto_calc"] = st.checkbox("Αυτόματος υπολογισμός τμημάτων", value=sets.get("auto_calc",True))
        if not sets["auto_calc"]:
            sets["manual_classes"] = st.number_input("Χειροκίνητα τμήματα", min_value=2, max_value=10, value=sets.get("manual_classes") or 2)
    with c2:
        st.markdown("### 📁 Εξαγωγή & Εμφάνιση")
        sets["include_details"] = st.checkbox("Συμπερίληψη αναλυτικών βημάτων", value=sets.get("include_details",True))
        sets["show_charts"] = st.checkbox("Εμφάνιση γραφημάτων", value=sets.get("show_charts",PLOTLY_AVAILABLE))
        st.info("Η εμφάνιση γραφημάτων εξαρτάται από τη διαθεσιμότητα Plotly.")
    if st.button("💾 Αποθήκευση Ρυθμίσεων", use_container_width=True):
        st.success("✅ Αποθηκεύτηκαν.")

def show_restart_section():
    st.markdown("<div class='step-header'>🔄 Επανεκκίνηση</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class="warning-box">
        <b>Προσοχή:</b> Θα διαγραφούν δεδομένα, αποτελέσματα, στατιστικά & βήματα.
    </div>""", unsafe_allow_html=True)
    if st.checkbox("✅ Επιβεβαιώνω επανεκκίνηση"):
        if st.button("🔄 ΕΠΑΝΕΚΚΙΝΗΣΗ", use_container_width=True):
            keep = ["authenticated","terms_accepted","app_enabled"]
            for k in list(st.session_state.keys()):
                if k not in keep:
                    del st.session_state[k]
            st.session_state.current_section = "upload"
            st.success("✅ Επανεκκίνηση ολοκληρώθηκε.")
            st.rerun()

# ============== Main App ==============
def show_main_app():
    st.markdown("<h1 class='main-header'>🎓 Κατανομή Μαθητών Α' Δημοτικού</h1>", unsafe_allow_html=True)
    tabs = st.tabs(["📥 Εισαγωγή", "⚡ Εκτέλεση", "📊 Αναλυτικά", "💾 Εξαγωγή", "⚙️ Ρυθμίσεις", "🔄 Επανεκκίνηση"])
    with tabs[0]: show_upload_section()
    with tabs[1]: show_execute_section()
    with tabs[2]: show_details_section()
    with tabs[3]: show_export_section()
    with tabs[4]: show_settings_section()
    with tabs[5]: show_restart_section()

# ============== Controller ==============
def main():
    init_session_state()
    if not st.session_state.authenticated:
        show_login(); return
    if not st.session_state.terms_accepted:
        show_terms(); return
    if not st.session_state.app_enabled:
        show_app_control(); return
    show_main_app()
    st.markdown("""
    <div style="text-align:center;color:#666;font-size:0.9rem;margin-top:1.4rem;padding:0.8rem;border-top:1px solid #ddd;">
      © 2025 Γιαννίτσαρου Παναγιώτα — Όλα τα δικαιώματα κατοχυρωμένα
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
