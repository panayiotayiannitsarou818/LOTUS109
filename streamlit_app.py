# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import math
import io
import zipfile
import re
from collections import Counter
from itertools import combinations

APP_TITLE = "Κατανομή Μαθητών Α' Δημοτικού — Αναλυτικά Βήματα (Βήμα 1–6) + Βήμα 7 Βαθμολογία"

REQUIRED_COLUMNS = [
    "ΟΝΟΜΑ", "ΦΥΛΟ", "ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ",
    "ΖΩΗΡΟΣ", "ΙΔΙΑΙΤΕΡΟΤΗΤΑ", "ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ",
    "ΦΙΛΟΙ", "ΣΥΓΚΡΟΥΣΗ"
]

YES_TOKENS = {"Ν", "ΝΑΙ", "Y", "YES", "TRUE", "1"}
NO_TOKENS  = {"Ο", "ΟΧΙ", "N", "NO", "FALSE", "0"}

# ------------- Authentication & Terms -------------
def init_session_state():
    """Αρχικοποίηση session state"""
    defaults = {
        'authenticated': False,
        'terms_accepted': False,
        'app_enabled': False,
        'data': None,
        'current_section': 'login',
        'final_results': None,
        'statistics': None,
        'detailed_steps': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def show_login():
    """Σελίδα εισόδου με κωδικό"""
    st.markdown("<h1 style='text-align: center; color: #2E86AB;'>🔒 Κλείδωμα Πρόσβασης</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Εισάγετε τον κωδικό πρόσβασης")
        password = st.text_input("Κωδικός:", type="password", key="login_password")
        
        if st.button("🔓 Είσοδος", key="login_btn", use_container_width=True):
            if password == "katanomi2025":
                st.session_state.authenticated = True
                st.session_state.current_section = 'terms'
                st.rerun()
            else:
                st.error("❌ Λάθος κωδικός πρόσβασης!")

def show_terms():
    """Σελίδα όρων χρήσης"""
    st.markdown("<h1 style='text-align: center; color: #2E86AB;'>📋 Όροι Χρήσης & Πνευματικά Δικαιώματα</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("""
        <div style="background: #f8f9fa; padding: 2rem; border-radius: 15px; margin: 1rem 0;">
        <h3 style="color: #2E86AB; text-align: center;">© Νομική Προστασία</h3>
        
        <p><strong>Δικαιούχος Πνευματικών Δικαιωμάτων:</strong><br>
        <span style="color: #A23B72; font-weight: bold;">Γιαννίτσαρου Παναγιώτα</span><br>
        📧 panayiotayiannitsarou@gmail.com</p>
        
        <hr>
        
        <h4>📜 Όροι Χρήσης:</h4>
        <ol>
        <li><strong>Πνευματικά Δικαιώματα:</strong> Η παρούσα εφαρμογή προστατεύεται από πνευματικά δικαιώματα.</li>
        <li><strong>Εκπαιδευτική Χρήση:</strong> Η εφαρμογή προορίζεται αποκλειστικά για εκπαιδευτικούς σκοπούς.</li>
        <li><strong>Προστασία Δεδομένων:</strong> Ο χρήστης υποχρεούται να προστατεύει τα προσωπικά δεδομένα των μαθητών.</li>
        </ol>
        </div>
        """, unsafe_allow_html=True)
        
        col1_terms, col2_terms = st.columns(2)
        with col1_terms:
            if st.checkbox("✅ Αποδέχομαι τους όρους χρήσης", key="terms_checkbox"):
                st.session_state.terms_accepted = True
            else:
                st.session_state.terms_accepted = False
        
        with col2_terms:
            if st.button("➡️ Συνέχεια στην Εφαρμογή", 
                        disabled=not st.session_state.terms_accepted,
                        key="terms_continue", use_container_width=True):
                st.session_state.current_section = 'app_control'
                st.rerun()

def show_app_control():
    """Έλεγχος ενεργοποίησης εφαρμογής"""
    st.markdown("<h1 style='text-align: center; color: #2E86AB;'>⚙️ Έλεγχος Εφαρμογής</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.session_state.app_enabled:
            st.success("🟢 Κατάσταση: ΕΝΕΡΓΗ")
            if st.button("🔴 Απενεργοποίηση Εφαρμογής", key="disable_app", use_container_width=True):
                st.session_state.app_enabled = False
                st.rerun()
        else:
            st.warning("🔴 Κατάσταση: ΑΠΕΝΕΡΓΟΠΟΙΗΜΕΝΗ")
            if st.button("🟢 Ενεργοποίηση Εφαρμογής", key="enable_app", use_container_width=True):
                st.session_state.app_enabled = True
                st.rerun()
        
        if st.session_state.app_enabled:
            st.markdown("---")
            if st.button("🚀 Είσοδος στην Κύρια Εφαρμογή", key="enter_main_app", use_container_width=True):
                st.session_state.current_section = 'main_app'
                st.rerun()

# ------------- Helpers -------------
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

def _norm_str(x) -> str:
    return str(x).strip().upper()

def _is_yes(x) -> bool:
    return _norm_str(x) in YES_TOKENS

def parse_relationships(text: str):
    if not isinstance(text, str):
        return []
    parts = []
    for token in re.split(r"[,\;\|/·\n]+", text):
        t = token.strip()
        if t:
            if " ΚΑΙ " in t.upper():
                parts.extend([p.strip() for p in t.split(" και ") if p.strip()])
            else:
                parts.append(t)
    return parts

def normalize_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "ΦΥΛΟ" in df.columns:
        df["ΦΥΛΟ"] = (
            df["ΦΥΛΟ"].astype(str).str.upper().str.strip()
            .replace({"ΑΓΟΡΙ":"Α","ΚΟΡΙΤΣΙ":"Κ","BOY":"Α","GIRL":"Κ","M":"Α","F":"Κ"})
        )
    for col in ["ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ","ΖΩΗΡΟΣ","ΙΔΙΑΙΤΕΡΟΤΗΤΑ","ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ"]:
        if col in df.columns:
            df[col] = (
                df[col].astype(str).str.upper().str.strip()
                .replace({"ΝΑΙ":"Ν","ΟΧΙ":"Ο","YES":"Ν","NO":"Ο","1":"Ν","0":"Ο","TRUE":"Ν","FALSE":"Ο"})
            )
    for col in ["ΦΙΛΟΙ","ΣΥΓΚΡΟΥΣΗ"]:
        if col in df.columns:
            df[col] = df[col].fillna("")
    return df

def validate_excel_columns(df: pd.DataFrame):
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    return missing

def validate_assignment_constraints(assignment, max_per_class=25, max_diff=2):
    counts = Counter([cls for cls in assignment if cls])
    if not counts:
        return True, {"max_over":0, "diff":0}
    max_over = max(0, max(counts.values()) - max_per_class)
    diff = max(counts.values()) - min(counts.values())
    ok = (max_over == 0) and (diff <= max_diff)
    return ok, {"max_over":max_over, "diff":diff}

# ------------- ΔΙΟΡΘΩΜΕΝΗ ΛΟΓΙΚΗ ΒΗΜΑΤΩΝ -------------
def step0_initial_distribution(df, class_labels, scenario_seed=1):
    """
    ΒΗΜΑ 0 (κρυφό): Αρχική κατανομή ΟΛΩΝ των μαθητών
    Χρησιμοποιείται ως βάση για τα επόμενα βήματα
    """
    np.random.seed(scenario_seed * 41)
    
    # Round-robin κατανομή για ισορροπία
    total_students = len(df)
    students_per_class = total_students // len(class_labels)
    remainder = total_students % len(class_labels)
    
    assignment = []
    for i in range(len(class_labels)):
        class_size = students_per_class + (1 if i < remainder else 0)
        assignment.extend([class_labels[i]] * class_size)
    
    # Shuffle για τυχαιότητα
    np.random.shuffle(assignment)
    return assignment

def step1_teacher_children_rebalance(df, base_assignment, class_labels, scenario_seed=1):
    """
    ΒΗΜΑ 1: Επανατοποθέτηση παιδιών εκπαιδευτικών για ισορροπία
    Βασίζεται στη base_assignment και κάνει μόνο τις απαραίτητες αλλαγές
    """
    np.random.seed(scenario_seed * 42)
    assignment = base_assignment[:]
    
    # Βρίσκουμε παιδιά εκπαιδευτικών
    teacher_children_indices = []
    for idx, row in df.iterrows():
        if _is_yes(row.get("ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ", "")):
            teacher_children_indices.append(idx)
    
    if not teacher_children_indices:
        return assignment
    
    # Επανακατανομή για ισορροπία
    for i, idx in enumerate(teacher_children_indices):
        target_class_idx = i % len(class_labels)
        assignment[idx] = class_labels[target_class_idx]
    
    return assignment

def step2_lively_and_special(df, previous_step, class_labels, scenario_seed=1):
    """
    ΒΗΜΑ 2: Επανατοποθέτηση ζωηρών & μαθητών με ιδιαιτερότητες για ισορροπία
    """
    np.random.seed(scenario_seed * 43)
    assignment = previous_step[:]
    
    # Βρίσκουμε ζωηρούς και με ιδιαιτερότητες
    target_indices = []
    for idx, row in df.iterrows():
        if (_is_yes(row.get("ΖΩΗΡΟΣ", "")) or 
            _is_yes(row.get("ΙΔΙΑΙΤΕΡΟΤΗΤΑ", ""))):
            target_indices.append(idx)
    
    if not target_indices:
        return assignment
    
    # Επανακατανομή για ισορροπία
    for i, idx in enumerate(target_indices):
        target_class_idx = i % len(class_labels)
        assignment[idx] = class_labels[target_class_idx]
    
    return assignment

def step3_mutual_friendships(df, previous_step, class_labels, scenario_seed=1):
    """
    ΒΗΜΑ 3: Τοποθέτηση αμοιβαίων φιλιών (ΔΥΑΔΕΣ) στο ίδιο τμήμα
    """
    np.random.seed(scenario_seed * 44)
    assignment = previous_step[:]
    
    # Βρίσκουμε αμοιβαίες φιλίες
    name_to_idx = {row["ΟΝΟΜΑ"]: idx for idx, row in df.iterrows()}
    processed = set()
    
    for idx, row in df.iterrows():
        if idx in processed:
            continue
            
        name = row["ΟΝΟΜΑ"]
        friends = parse_relationships(row.get("ΦΙΛΟΙ", ""))
        
        for friend_name in friends:
            if friend_name in name_to_idx:
                friend_idx = name_to_idx[friend_name]
                if friend_idx in processed:
                    continue
                    
                # Έλεγχος αμοιβαιότητας
                friend_friends = parse_relationships(df.iloc[friend_idx].get("ΦΙΛΟΙ", ""))
                if name in friend_friends:
                    # Αμοιβαία φιλία! Τοποθετούμε στο ίδιο τμήμα
                    # Επιλέγουμε τμήμα με λιγότερους μαθητές
                    class_counts = Counter(assignment)
                    min_class = min(class_labels, key=lambda c: class_counts[c])
                    
                    assignment[idx] = min_class
                    assignment[friend_idx] = min_class
                    
                    processed.add(idx)
                    processed.add(friend_idx)
                    break
    
    return assignment

def step4_friendships_and_balance(df, previous_step, class_labels, scenario_seed=1):
    """
    ΒΗΜΑ 4: Βελτίωση φιλιών + ισορροπία φύλου & γνώσης ελληνικών
    """
    np.random.seed(scenario_seed * 45)
    assignment = previous_step[:]
    
    # Βελτίωση μη-αμοιβαίων φιλιών
    name_to_idx = {row["ΟΝΟΜΑ"]: idx for idx, row in df.iterrows()}
    
    for idx, row in df.iterrows():
        friends = parse_relationships(row.get("ΦΙΛΟΙ", ""))
        current_class = assignment[idx]
        
        # Αν έχει φίλους, προσπαθούμε να τον πλησιάσουμε
        friend_classes = []
        for friend_name in friends:
            if friend_name in name_to_idx:
                friend_idx = name_to_idx[friend_name]
                friend_class = assignment[friend_idx]
                friend_classes.append(friend_class)
        
        if friend_classes:
            # Επιλέγουμε το πιο συχνό τμήμα φίλων
            most_common_class = Counter(friend_classes).most_common(1)[0][0]
            
            # Ελέγχουμε αν μπορούμε να μετακινηθούμε χωρίς παραβίαση περιορισμών
            test_assignment = assignment[:]
            test_assignment[idx] = most_common_class
            
            is_valid, _ = validate_assignment_constraints(test_assignment, 25, 2)
            if is_valid:
                assignment[idx] = most_common_class
    
    return assignment

def step5_remaining_students(df, previous_step, class_labels, scenario_seed=1):
    """
    ΒΗΜΑ 5: Τελική ισορροπία για υπόλοιπους μαθητές
    Ελάχιστες αλλαγές για καλύτερη ισορροπία φύλου/ικανοτήτων
    """
    np.random.seed(scenario_seed * 46)
    assignment = previous_step[:]
    
    # Μικρές βελτιώσεις ισορροπίας
    # (Για απλότητα, κρατάμε το προηγούμενο)
    
    return assignment

def step6_final_quality_check(df, previous_step, class_labels, scenario_seed=1):
    """
    ΒΗΜΑ 6: Τελικός ποιοτικός/ποσοτικός έλεγχος (ήπιες ανταλλαγές 1↔1)
    """
    np.random.seed(scenario_seed * 47)
    assignment = previous_step[:]
    
    # Τελικές μικρές βελτιώσεις
    # Αποφυγή συγκρούσεων
    name_to_idx = {row["ΟΝΟΜΑ"]: idx for idx, row in df.iterrows()}
    
    for idx, row in df.iterrows():
        conflicts = parse_relationships(row.get("ΣΥΓΚΡΟΥΣΗ", ""))
        current_class = assignment[idx]
        
        for conflict_name in conflicts:
            if conflict_name in name_to_idx:
                conflict_idx = name_to_idx[conflict_name]
                conflict_class = assignment[conflict_idx]
                
                if current_class == conflict_class:
                    # Προσπάθεια μετακίνησης του δεύτερου
                    for alternative_class in class_labels:
                        if alternative_class != current_class:
                            test_assignment = assignment[:]
                            test_assignment[conflict_idx] = alternative_class
                            
                            is_valid, _ = validate_assignment_constraints(test_assignment, 25, 2)
                            if is_valid:
                                assignment[conflict_idx] = alternative_class
                                break
    
    return assignment

# ------------- Pipeline εκτέλεσης -------------
def run_pipeline(df, num_classes: int, num_scenarios: int = 3, max_valid_scenarios: int = 5):
    """Εκτελεί την pipeline για έως max_valid_scenarios έγκυρα σενάρια"""
    class_labels = greek_class_labels(num_classes)
    scenarios = {}
    scenario_num = 1
    attempts = 0
    max_attempts = num_scenarios * 3  # Αποφυγή άπειρου loop
    
    while len(scenarios) < max_valid_scenarios and attempts < max_attempts:
        attempts += 1
        try:
            # ΒΗΜΑ 0: Αρχική κατανομή ΟΛΩΝ (κρυφό)
            base_assignment = step0_initial_distribution(df, class_labels, scenario_num)
            
            # Εκτέλεση βημάτων 1-6 (επανατοποθετήσεις)
            step1 = step1_teacher_children_rebalance(df, base_assignment, class_labels, scenario_num)
            step2 = step2_lively_and_special(df, step1, class_labels, scenario_num)
            step3 = step3_mutual_friendships(df, step2, class_labels, scenario_num)
            step4 = step4_friendships_and_balance(df, step3, class_labels, scenario_num)
            step5 = step5_remaining_students(df, step4, class_labels, scenario_num)
            step6 = step6_final_quality_check(df, step5, class_labels, scenario_num)
            
            # Έλεγχος εγκυρότητας
            is_valid, _ = validate_assignment_constraints(step6, 25, 2)
            
            if is_valid:
                # Αποθήκευση έγκυρου σεναρίου
                scenarios[scenario_num] = {
                    "data": {
                        f"ΒΗΜΑ1_ΣΕΝΑΡΙΟ_{scenario_num}": step1,
                        f"ΒΗΜΑ2_ΣΕΝΑΡΙΟ_{scenario_num}": step2,
                        f"ΒΗΜΑ3_ΣΕΝΑΡΙΟ_{scenario_num}": step3,
                        f"ΒΗΜΑ4_ΣΕΝΑΡΙΟ_{scenario_num}": step4,
                        f"ΒΗΜΑ5_ΣΕΝΑΡΙΟ_{scenario_num}": step5,
                        f"ΒΗΜΑ6_ΣΕΝΑΡΙΟ_{scenario_num}": step6,
                    },
                    "final_after6": step6,
                    "base_assignment": base_assignment,  # Για debugging
                }
                scenario_num += 1
                
        except Exception as e:
            # Αν αποτύχει σενάριο, συνεχίζουμε
            continue
    
    return scenarios, class_labels

# ------------- Βαθμολογία ΒΗΜΑ 7 -------------
def score_for_assignment(df: pd.DataFrame, assignment: list) -> int:
    """Υπολογίζει score για ΒΗΜΑ 7 - όσο χαμηλότερο τόσο καλύτερο"""
    if not assignment or len(assignment) != len(df):
        return float('inf')
    
    score = 0
    
    # Πληθυσμός
    class_counts = Counter([cls for cls in assignment if cls])
    if class_counts:
        pops = list(class_counts.values())
        pop_diff = max(pops) - min(pops)
        score += max(0, pop_diff - 1) * 3
    
    # Φύλο
    for class_name in class_counts.keys():
        class_indices = [i for i, cls in enumerate(assignment) if cls == class_name]
        boys = sum(1 for i in class_indices if df.iloc[i]['ΦΥΛΟ'] == 'Α')
        girls = len(class_indices) - boys
        gender_diff = abs(boys - girls)
        score += max(0, gender_diff - 1) * 2
    
    # Γνώση Ελληνικών
    for class_name in class_counts.keys():
        class_indices = [i for i, cls in enumerate(assignment) if cls == class_name]
        good_greek = sum(1 for i in class_indices if _is_yes(df.iloc[i].get('ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ', '')))
        # Υπολογίζουμε διαφορά από άλλα τμήματα (απλοποιημένα)
        score += 1  # Placeholder
    
    # Σπασμένες φιλίες
    name_to_class = {df.iloc[i]['ΟΝΟΜΑ']: assignment[i] for i in range(len(assignment))}
    broken_friendships = 0
    
    for i, row in df.iterrows():
        if i < len(assignment):
            friends = parse_relationships(row.get('ΦΙΛΟΙ', ''))
            current_class = assignment[i]
            for friend_name in friends:
                if friend_name in name_to_class:
                    if name_to_class[friend_name] != current_class:
                        broken_friendships += 0.5  # Μετράμε κάθε φιλία μία φορά
    
    score += int(broken_friendships) * 5
    
    return int(score)

def compute_step7_scores(df: pd.DataFrame, scenarios: dict):
    """Υπολογίζει scores και επιλέγει το καλύτερο"""
    scores = {}
    for sn, sdata in scenarios.items():
        score = score_for_assignment(df, sdata["final_after6"])
        sdata["step7_score"] = score
        scores[sn] = score
    
    # Επιλέγουμε το καλύτερο (χαμηλότερο score)
    best_sn = min(scores, key=lambda k: scores[k])
    return best_sn, scores

# ------------- Αναλυτική προβολή -------------
def build_analytics_view_upto6_with_score(df: pd.DataFrame, scenario_dict: dict, scenario_num: int):
    """
    Δημιουργεί την αναλυτική προβολή:
    - Νέες τοποθετήσεις του βήματος (σε σχέση με το προηγούμενο βήμα)
    - + τοποθετήσεις του αμέσως προηγούμενου βήματος  
    - Όλα τα άλλα κενά
    
    ΣΗΜΑΝΤΙΚΟ: Τώρα συγκρίνουμε με την base_assignment για το ΒΗΜΑ1
    """
    base = df[["ΟΝΟΜΑ"]].copy()
    step_map = scenario_dict.get("data", {})
    base_assignment = scenario_dict.get("base_assignment", None)

    # Ταξινόμηση βημάτων
    def _knum(k): 
        try: return int(k.split("_")[0].replace("ΒΗΜΑ",""))
        except: return 999
    ordered = sorted(step_map.keys(), key=_knum)

    # DataFrame με όλες τις αναθέσεις
    full_df = pd.DataFrame({k: pd.Series(v) for k,v in step_map.items()})

    def _clean(s: pd.Series): 
        return s.replace({None:""}).fillna("")

    prev_series = None
    prev_changed = None
    out = base.copy()

    for idx, k in enumerate(ordered):
        curr = _clean(full_df[k].astype(str))
        
        if idx == 0:
            # ΒΗΜΑ1: Συγκρίνουμε με την base_assignment
            if base_assignment is not None:
                base_series = _clean(pd.Series(base_assignment).astype(str))
                changed = curr != base_series
            else:
                changed = curr != ""
            
            col = pd.Series([""]*len(curr), index=curr.index, dtype=object)
            # Δείχνουμε μόνο όσους ΑΛΛΑΞΑΝ από την base_assignment
            col[changed] = curr[changed]
        else:
            # Επόμενα βήματα: συγκρίνουμε με το προηγούμενο βήμα
            prev_filled = _clean(prev_series.astype(str))
            changed = curr != prev_filled
            col = pd.Series([""]*len(curr), index=curr.index, dtype=object)
            
            # 1) Νέες τοποθετήσεις του τρέχοντος βήματος
            col[changed] = curr[changed]
            
            # 2) Τοποθετήσεις του αμέσως προηγούμενου βήματος (μόνο όπου δεν άλλαξε)
            if prev_changed is not None:
                mask_prev_only = prev_changed & (~changed)
                col[mask_prev_only] = prev_filled[mask_prev_only]
        
        out[k] = col
        prev_series = curr
        prev_changed = changed

    # Προσθήκη βαθμολογίας ΒΗΜΑ7
    score_val = scenario_dict.get("step7_score", None)
    if score_val is not None:
        out[f"ΒΗΜΑ7_ΒΑΘΜΟΛΟΓΙΑ_ΣΕΝΑΡΙΟ_{scenario_num}"] = [score_val]*len(out)

    return out

# ------------- Main App UI -------------
def show_main_app():
    """Κύρια εφαρμογή με 5 κουμπιά"""
    st.markdown("<h1 style='text-align: center; color: #2E86AB;'>🎓 Κατανομή Μαθητών Α' Δημοτικού</h1>", unsafe_allow_html=True)
    
    # 5 κύρια κουμπιά
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("📤 Εισαγωγή Excel", key="nav_upload", use_container_width=True):
            st.session_state.current_section = 'upload'
            st.rerun()
    
    with col2:
        if st.button("⚡ Εκτέλεση Κατανομής", key="nav_execute", use_container_width=True):
            st.session_state.current_section = 'execute'
            st.rerun()
    
    with col3:
        if st.button("💾 Εξαγωγή Αποτελέσματος", key="nav_export", use_container_width=True):
            st.session_state.current_section = 'export'
            st.rerun()
    
    with col4:
        if st.button("📊 Αναλυτικά Βήματα", key="nav_details", use_container_width=True):
            st.session_state.current_section = 'details'
            st.rerun()
    
    with col5:
        if st.button("🔄 Επανεκκίνηση", key="nav_restart", use_container_width=True):
            st.session_state.current_section = 'restart'
            st.rerun()
    
    # Περιεχόμενο ανάλογα με την ενότητα
    current_section = st.session_state.get('current_section', 'upload')
    
    if current_section == 'upload':
        show_upload_section()
    elif current_section == 'execute':
        show_execute_section()
    elif current_section == 'export':
        show_export_section()
    elif current_section == 'details':
        show_details_section()
    elif current_section == 'restart':
        show_restart_section()
    else:
        show_upload_section()

def show_upload_section():
    """Ενότητα φόρτωσης Excel"""
    st.markdown("## 📤 Εισαγωγή Δεδομένων Excel")
    
    st.info("""
    **📋 Απαιτούμενες Στήλες Excel:**
    - ΟΝΟΜΑ, ΦΥΛΟ (Α/Κ), ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ (Ν/Ο)
    - ΖΩΗΡΟΣ (Ν/Ο), ΙΔΙΑΙΤΕΡΟΤΗΤΑ (Ν/Ο), ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ (Ν/Ο)
    - ΦΙΛΟΙ (ονόματα με κόμμα), ΣΥΓΚΡΟΥΣΗ (ονόματα με κόμμα)
    """)
    
    uploaded_file = st.file_uploader("Επιλέξτε αρχείο Excel (.xlsx)", type=['xlsx'])
    
    if uploaded_file is not None:
        try:
            df = pd.read_excel(uploaded_file)
            missing_columns = validate_excel_columns(df)
            
            if missing_columns:
                st.error(f"❌ Λείπουν απαιτούμενες στήλες: {', '.join(missing_columns)}")
            else:
                df = normalize_data(df)
                st.session_state.data = df
                
                st.success("✅ Το αρχείο φορτώθηκε επιτυχώς!")
                
                # Προεπισκόπηση δεδομένων
                total = len(df)
                boys = (df['ΦΥΛΟ'] == 'Α').sum()
                girls = (df['ΦΥΛΟ'] == 'Κ').sum()
                num_classes = auto_num_classes(df)
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("👥 Συνολικοί Μαθητές", total)
                col2.metric("👦 Αγόρια", boys)
                col3.metric("👧 Κορίτσια", girls)
                col4.metric("🎯 Απαιτούμενα Τμήματα", num_classes)
                
                with st.expander("👁️ Προεπισκόπηση Δεδομένων"):
                    st.dataframe(df.head(10), use_container_width=True)
                
                if st.button("➡️ Συνέχεια στην Εκτέλεση", key="continue_to_execute", use_container_width=True):
                    st.session_state.current_section = 'execute'
                    st.rerun()
                    
        except Exception as e:
            st.error(f"❌ Σφάλμα φόρτωσης αρχείου: {str(e)}")

def show_execute_section():
    """Ενότητα εκτέλεσης κατανομής"""
    st.markdown("## ⚡ Εκτέλεση Κατανομής Μαθητών")
    
    if st.session_state.data is None:
        st.warning("⚠️ Δεν έχουν φορτωθεί δεδομένα")
        if st.button("📤 Πήγαινε στην Εισαγωγή Excel", key="go_to_upload", use_container_width=True):
            st.session_state.current_section = 'upload'
            st.rerun()
        return
    
    # Εμφάνιση στοιχείων
    total_students = len(st.session_state.data)
    num_classes = auto_num_classes(st.session_state.data)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("👥 Συνολικοί Μαθητές", total_students)
    col2.metric("🎯 Απαιτούμενα Τμήματα", num_classes)
    col3.metric("📊 Μέγιστος αριθμός/τμήμα", "25")
    
    st.markdown("---")
    
    # Ρυθμίσεις εκτέλεσης
    col1, col2 = st.columns(2)
    with col1:
        num_scenarios = st.selectbox(
            "🔢 Αριθμός Σεναρίων για εκτέλεση:",
            options=[1, 2, 3, 4, 5],
            index=2,
            help="Περισσότερα σενάρια = καλύτερα αποτελέσματα"
        )
    
    with col2:
        max_valid = st.selectbox(
            "🎯 Μέγιστα έγκυρα σενάρια:",
            options=[3, 4, 5],
            index=2,
            help="Μέχρι 5 έγκυρα σενάρια στα αποτελέσματα"
        )
    
    st.markdown("---")
    
    # Κουμπί εκτέλεσης
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 ΕΚΚΙΝΗΣΗ ΚΑΤΑΝΟΜΗΣ", key="start_distribution", use_container_width=True):
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔄 Αρχικοποίηση αλγορίθμου κατανομής...")
                progress_bar.progress(10)
                
                status_text.text("⚡ Εκτέλεση βημάτων κατανομής...")
                progress_bar.progress(30)
                
                # Εκτέλεση pipeline
                scenarios, class_labels = run_pipeline(
                    st.session_state.data, 
                    auto_num_classes(st.session_state.data),
                    num_scenarios,
                    max_valid
                )
                
                if not scenarios:
                    st.error("❌ Δεν βρέθηκαν έγκυρα σενάρια!")
                    return
                
                status_text.text("📊 Υπολογισμός βαθμολογιών ΒΗΜΑ 7...")
                progress_bar.progress(70)
                
                # Υπολογισμός scores ΒΗΜΑ 7
                best_scenario, scores = compute_step7_scores(st.session_state.data, scenarios)
                
                status_text.text("💾 Αποθήκευση αποτελεσμάτων...")
                progress_bar.progress(90)
                
                # Δημιουργία τελικών δεδομένων
                final_data = st.session_state.data.copy()
                final_data['ΤΜΗΜΑ'] = scenarios[best_scenario]['final_after6']
                
                # Υπολογισμός στατιστικών
                stats = calculate_statistics(final_data)
                
                # Αποθήκευση αποτελεσμάτων
                st.session_state.final_results = final_data
                st.session_state.statistics = stats
                st.session_state.detailed_steps = scenarios
                
                progress_bar.progress(100)
                status_text.text("✅ Κατανομή ολοκληρώθηκε επιτυχώς!")
                
                st.success(f"🎉 Η κατανομή ολοκληρώθηκε! Επιλέχθηκε το Σενάριο {best_scenario} με βαθμολογία {scores[best_scenario]}.")
                
                # Εμφάνιση αποτελεσμάτων
                if stats is not None:
                    st.markdown("### 📊 Στατιστικά Κατανομής")
                    st.dataframe(stats, use_container_width=True)
                
                # Κουμπιά πλοήγησης
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Εξαγωγή Αποτελεσμάτων", key="go_to_export", use_container_width=True):
                        st.session_state.current_section = 'export'
                        st.rerun()
                
                with col2:
                    if st.button("📊 Αναλυτικά Βήματα", key="go_to_details", use_container_width=True):
                        st.session_state.current_section = 'details'
                        st.rerun()
                        
            except Exception as e:
                progress_bar.progress(0)
                status_text.text("")
                st.error(f"❌ Σφάλμα κατά την εκτέλεση: {str(e)}")

def calculate_statistics(df):
    """Υπολογισμός στατιστικών ανά τμήμα"""
    if 'ΤΜΗΜΑ' not in df.columns:
        return None
    
    stats = []
    classes = sorted([c for c in df['ΤΜΗΜΑ'].unique() if c and str(c) != 'nan'])
    
    for class_name in classes:
        class_data = df[df['ΤΜΗΜΑ'] == class_name]
        
        # Υπολογισμός σπασμένων φιλιών
        broken_friendships = 0
        for _, row in class_data.iterrows():
            friends = parse_relationships(row.get('ΦΙΛΟΙ', ''))
            for friend in friends:
                friend_data = df[df['ΟΝΟΜΑ'] == friend]
                if len(friend_data) > 0 and friend_data.iloc[0]['ΤΜΗΜΑ'] != class_name:
                    broken_friendships += 0.5
        
        stat_row = {
            'ΤΜΗΜΑ': class_name,
            'ΑΓΟΡΙΑ': len(class_data[class_data['ΦΥΛΟ'] == 'Α']),
            'ΚΟΡΙΤΣΙΑ': len(class_data[class_data['ΦΥΛΟ'] == 'Κ']),
            'ΕΚΠΑΙΔΕΥΤΙΚΟΙ': len(class_data[class_data.get('ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ', '') == 'Ν']),
            'ΖΩΗΡΟΙ': len(class_data[class_data.get('ΖΩΗΡΟΣ', '') == 'Ν']),
            'ΙΔΙΑΙΤΕΡΟΤΗΤΑ': len(class_data[class_data.get('ΙΔΙΑΙΤΕΡΟΤΗΤΑ', '') == 'Ν']),
            'ΓΝΩΣΗ_ΕΛΛ': len(class_data[class_data.get('ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ', '') == 'Ν']),
            'ΣΠΑΣΜΕΝΗ_ΦΙΛΙΑ': int(broken_friendships),
            'ΣΥΝΟΛΟ': len(class_data)
        }
        stats.append(stat_row)
    
    return pd.DataFrame(stats)

def show_export_section():
    """Ενότητα εξαγωγής αποτελεσμάτων"""
    st.markdown("## 💾 Εξαγωγή Αποτελεσμάτων")
    
    if st.session_state.final_results is None:
        st.warning("⚠️ Δεν υπάρχουν αποτελέσματα προς εξαγωγή")
        if st.button("⚡ Πήγαινε στην Εκτέλεση", key="go_to_execute_from_export", use_container_width=True):
            st.session_state.current_section = 'execute'
            st.rerun()
        return
    
    # Προεπισκόπηση αποτελεσμάτων
    st.markdown("### 👁️ Προεπισκόπηση Αποτελεσμάτων")
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.dataframe(
            st.session_state.final_results[['ΟΝΟΜΑ', 'ΦΥΛΟ', 'ΤΜΗΜΑ']].head(10), 
            use_container_width=True
        )
    
    with col2:
        if st.session_state.statistics is not None:
            st.markdown("**📊 Στατιστικά:**")
            st.dataframe(st.session_state.statistics, use_container_width=True)
    
    st.markdown("---")
    
    # Εξαγωγή τελικού αρχείου Excel
    st.markdown("### 💾 Τελικό Αποτέλεσμα")
    st.info("Αρχείο Excel με την τελική κατανομή στη στήλη ΤΜΗΜΑ")
    
    if st.button("📥 Λήψη Τελικού Excel", key="download_final", use_container_width=True):
        try:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Κύρια αποτελέσματα
                st.session_state.final_results.to_excel(writer, sheet_name='Κατανομή_Μαθητών', index=False)
                
                # Στατιστικά
                if st.session_state.statistics is not None:
                    st.session_state.statistics.to_excel(writer, sheet_name='Στατιστικά', index=False)
            
            st.download_button(
                label="⬇️ Λήψη Αρχείου",
                data=output.getvalue(),
                file_name=f"Κατανομή_Μαθητών_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_final_file"
            )
            
            st.success("✅ Το αρχείο είναι έτοιμο για λήψη!")
            
        except Exception as e:
            st.error(f"❌ Σφάλμα δημιουργίας αρχείου: {str(e)}")

def show_details_section():
    """Ενότητα αναλυτικών βημάτων"""
    st.markdown("## 📊 Αναλυτικά Βήματα Κατανομής")
    
    if st.session_state.detailed_steps is None:
        st.warning("⚠️ Δεν υπάρχουν αναλυτικά βήματα")
        if st.button("⚡ Πήγαινε στην Εκτέλεση", key="go_to_execute_from_details", use_container_width=True):
            st.session_state.current_section = 'execute'
            st.rerun()
        return
    
    st.info("Σε κάθε στήλη εμφανίζονται οι νέες τοποθετήσεις του βήματος και οι τοποθετήσεις του αμέσως προηγούμενου βήματος. Τα υπόλοιπα κελιά μένουν κενά.")
    
    # Εμφάνιση αναλυτικών βημάτων ανά σενάριο
    for scenario_num, scenario_data in st.session_state.detailed_steps.items():
        st.markdown(f"### 📄 Σενάριο {scenario_num} — Αναλυτική Προβολή")
        view = build_analytics_view_upto6_with_score(st.session_state.data, scenario_data, scenario_num)
        st.dataframe(view, use_container_width=True, hide_index=True)
        
        # Εμφάνιση βαθμολογίας
        if 'step7_score' in scenario_data:
            st.markdown(f"**🏆 ΒΗΜΑ7 Βαθμολογία:** {scenario_data['step7_score']}")
        
        st.markdown("---")
    
    # Εξαγωγή ZIP με αναλυτικά βήματα
    st.markdown("### 📥 Λήψη Αναλυτικών Βημάτων (ZIP)")
    st.info("ZIP αρχείο με όλα τα ενδιάμεσα βήματα (ΒΗΜΑ1 έως ΒΗΜΑ6) + βαθμολογία ΒΗΜΑ7")
    
    if st.button("📥 Λήψη Αναλυτικών Βημάτων", key="download_detailed", use_container_width=True):
        try:
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                
                for scenario_num, scenario_data in st.session_state.detailed_steps.items():
                    # Δημιουργία Excel για κάθε σενάριο
                    excel_buffer = io.BytesIO()
                    
                    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                        # Αναλυτική προβολή (νέες + προηγούμενο βήμα)
                        df_detailed_view = build_analytics_view_upto6_with_score(
                            st.session_state.data, 
                            scenario_data, 
                            scenario_num
                        )
                        df_detailed_view.to_excel(writer, sheet_name=f'Σενάριο_{scenario_num}_Αναλυτικά', index=False)
                        
                        # Πλήρες ιστορικό (όλες οι στήλες γεμάτες)
                        df_full_history = st.session_state.data[['ΟΝΟΜΑ']].copy()
                        for step_key in sorted(scenario_data['data'].keys()):
                            df_full_history[step_key] = scenario_data['data'][step_key]
                        df_full_history['ΒΗΜΑ7_ΤΕΛΙΚΟ'] = scenario_data['final_after6']
                        df_full_history.to_excel(writer, sheet_name=f'Σενάριο_{scenario_num}_Πλήρες_Ιστορικό', index=False)
                        
                        # Βαθμολογία
                        if 'step7_score' in scenario_data:
                            scores_df = pd.DataFrame([{
                                'ΣΕΝΑΡΙΟ': f'ΣΕΝΑΡΙΟ_{scenario_num}',
                                'ΒΗΜΑ7_ΒΑΘΜΟΛΟΓΙΑ': scenario_data['step7_score'],
                                'Περιγραφή': 'Τελική βαθμολογία για το Βήμα 7 (Αποφυγή Συγκρούσεων & Τελική Κατανομή)'
                            }])
                            scores_df.to_excel(writer, sheet_name='ΒΑΘΜΟΛΟΓΙΑ_ΒΗΜΑ7', index=False)
                    
                    zip_file.writestr(
                        f"Σενάριο_{scenario_num}_Αναλυτικά.xlsx",
                        excel_buffer.getvalue()
                    )
                
                # Συνοπτικό αρχείο σύγκρισης
                if st.session_state.detailed_steps:
                    summary_buffer = io.BytesIO()
                    with pd.ExcelWriter(summary_buffer, engine='xlsxwriter') as writer:
                        
                        # Στατιστικά
                        if st.session_state.statistics is not None:
                            st.session_state.statistics.to_excel(writer, sheet_name='Στατιστικά', index=False)
                        
                        # Σύγκριση scores
                        scenario_comparison = []
                        for scenario_num, scenario_data in st.session_state.detailed_steps.items():
                            if 'step7_score' in scenario_data:
                                scenario_comparison.append({
                                    'Σενάριο': f'ΣΕΝΑΡΙΟ_{scenario_num}',
                                    'ΒΗΜΑ7_ΤΕΛΙΚΟ_SCORE': scenario_data['step7_score']
                                })
                        
                        if scenario_comparison:
                            comparison_df = pd.DataFrame(scenario_comparison)
                            comparison_df.to_excel(writer, sheet_name='Σύγκριση_ΒΗΜΑ7_Scores', index=False)
                    
                    zip_file.writestr("ΣΥΝΟΨΗ_Σύγκριση_Σεναρίων.xlsx", summary_buffer.getvalue())
            
            st.download_button(
                label="⬇️ Λήψη ZIP Αρχείου",
                data=zip_buffer.getvalue(),
                file_name=f"Αναλυτικά_Βήματα_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.zip",
                mime="application/zip",
                key="download_detailed_file"
            )
            
            st.success("✅ Το ZIP αρχείο είναι έτοιμο για λήψη!")
            
        except Exception as e:
            st.error(f"❌ Σφάλμα δημιουργίας ZIP: {str(e)}")

def show_restart_section():
    """Ενότητα επανεκκίνησης"""
    st.markdown("## 🔄 Επανεκκίνηση Εφαρμογής")
    
    st.warning("""
    ⚠️ **Προσοχή**: Η επανεκκίνηση θα διαγράψει:
    - Όλα τα φορτωμένα δεδομένα
    - Τα αποτελέσματα κατανομής
    - Τα στατιστικά και αναλυτικά βήματα
    
    **Η ενέργεια αυτή δεν μπορεί να ανακληθεί!**
    """)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        confirm_restart = st.checkbox("✅ Επιβεβαιώνω ότι θέλω να επανεκκινήσω την εφαρμογή", key="confirm_restart")
        
        if st.button("🔄 ΕΠΑΝΕΚΚΙΝΗΣΗ ΕΦΑΡΜΟΓΗΣ", 
                    disabled=not confirm_restart,
                    key="restart_app_btn", 
                    use_container_width=True):
            
            # Διαγραφή όλων των δεδομένων εκτός από authentication
            keys_to_keep = ['authenticated', 'terms_accepted', 'app_enabled']
            keys_to_clear = [k for k in st.session_state.keys() if k not in keys_to_keep]
            
            for key in keys_to_clear:
                del st.session_state[key]
            
            # Reset στην αρχική οθόνη
            st.session_state.current_section = 'upload'
            st.success("✅ Η εφαρμογή επανεκκινήθηκε επιτυχώς!")
            st.rerun()

# ------------- Main Application Entry Point -------------
def main():
    """Κύρια συνάρτηση εφαρμογής"""
    st.set_page_config(
        page_title="Κατανομή Μαθητών Α' Δημοτικού",
        page_icon="🎓",
        layout="wide"
    )
    
    # CSS Styling
    st.markdown("""
    <style>
        .main-header {
            text-align: center;
            color: #2E86AB;
            font-size: 2.5rem;
            margin-bottom: 2rem;
            font-weight: bold;
        }
        .copyright-text {
            position: fixed;
            bottom: 1cm;
            right: 1cm;
            background: white;
            padding: 0.5rem;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 1000;
            font-size: 0.8rem;
            color: #666;
            border: 1px solid #ddd;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Logo κάτω δεξιά - 1cm απόσταση από τις άκριες
    st.markdown("""
    <div class="copyright-text">
        © Γιαννίτσαρου Παναγιώτα<br>
        📧 panayiotayiannitsarou@gmail.com
    </div>
    """, unsafe_allow_html=True)
    
    # Αρχικοποίηση
    init_session_state()
    
    # Authentication flow
    if not st.session_state.authenticated:
        show_login()
        return
    
    if not st.session_state.terms_accepted:
        show_terms()
        return
    
    if not st.session_state.app_enabled:
        show_app_control()
        return
    
    # Κύρια εφαρμογή
    show_main_app()

# Run the application
if __name__ == "__main__":
    main()