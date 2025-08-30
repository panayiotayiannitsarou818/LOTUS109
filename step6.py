
# ==========================================
# step6_FINAL.py (embedded, no external step6 import)
# - Embeds the original Step 6 algorithm from step6.py
# - Adds column "ΒΗΜΑ6_ΣΕΝΑΡΙΟ_N" at Excel column P
# - Public API:
#     * apply_step6_final(df, ...) -> {"df": DataFrame, "summary": dict}
#     * run_step6_final(df) -> DataFrame
# ==========================================

import re
import pandas as pd

# ---- Embedded original step6.py BELOW ----
# filename: step_6_final_check_and_fix_100_PERCENT_COMPLIANT.py
from __future__ import annotations
"""
Βήμα 6: Τελικός Ποιοτικός και Ποσοτικός Έλεγχος
100% σύμφωνος με προδιαγραφές - ΠΛΗΡΕΙΣ διορθώσεις:
1. Έλεγχος απαραβίαστων περιορισμών Βημάτων 1-2 ΣΕ ΣΧΕΣΗ ΜΕ ΤΗ ΒΑΣΗ (όχι between swaps)
2. Σωστός έλεγχος φιλιών που ΕΠΙΤΡΕΠΕΙ προϋπάρχουσες σπασμένες δυάδες σε swaps
3. Πλήρης audit trail με Population αιτία
"""
_IDCOL = "ID"
import itertools
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np

# --------------------------
# Constants / Config
# --------------------------
BOY = "Α"           # Αγόρι
GIRL = "Κ"          # Κορίτσι
GOOD = "Ν"          # Καλή Γνώση/Ζωηρότητα/Ιδιαιτερότητα/Παιδί Εκπαιδευτικού
NOTGOOD = "Ο"       # Όχι Καλή

MAX_PER_CLASS = 25
TARGET_POP_DIFF = 2
TARGET_GENDER_DIFF = 3
TARGET_LANG_DIFF = 3

MAX_ITER = 5

# Αποδεκτές τιμές για στήλη ΒΗΜΑ_ΤΟΠΟΘΕΤΗΣΗΣ
STEP4_MARKERS = {4, "4", "Βήμα 4", "Step4", "Step4_Group", "Β4", "Β4_Δυάδα"}
STEP5_MARKERS = {5, "5", "Βήμα 5", "Step5", "Step5_Solo", "Β5", "Β5_Μεμονωμένος"}

# Στήλες απαραβίαστων περιορισμών Βημάτων 1-2
PROTECTED_COLS = {
    "ΖΩΗΡΟΣ": "Ζωηρότητα",
    "ΙΔΙΑΙΤΕΡΟΤΗΤΑ": "Ιδιαιτερότητα", 
    "ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ": "Παιδιά Εκπαιδευτικών"
}

# Baseline snapshot στήλες για σύγκριση με Βήματα 1-2 ανά κατηγορία
BASELINE_MAPPING = {
    "ΖΩΗΡΟΣ": ["ΤΜΗΜΑ_ΒΗΜΑ2", "ΤΜΗΜΑ_ΠΡΙΝ_ΒΗΜΑ6", "ΤΜΗΜΑ"],
    "ΙΔΙΑΙΤΕΡΟΤΗΤΑ": ["ΤΜΗΜΑ_ΒΗΜΑ2", "ΤΜΗΜΑ_ΠΡΙΝ_ΒΗΜΑ6", "ΤΜΗΜΑ"], 
    "ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ": ["ΤΜΗΜΑ_ΒΗΜΑ1", "ΤΜΗΜΑ_ΠΡΙΝ_ΒΗΜΑ6", "ΤΜΗΜΑ"]
}

# --------------------------
# Utility Functions
# --------------------------
def _classes(df: pd.DataFrame, class_col: str) -> List[str]:
    """Επιστρέφει τα μοναδικά τμήματα."""
    cls = list(df[class_col].dropna().unique())
    if len(cls) < 2:
        raise ValueError("Απαιτούνται τουλάχιστον 2 τμήματα.")
    return cls

def _metrics(df: pd.DataFrame, class_col: str, gender_col: str, lang_col: str, group_col: str = "GROUP_ID") -> Dict[str, Any]:
    """
    Υπολογίζει μετρικές ανά τμήμα και συνολικές αποκλίσεις.
    
    Returns:
        Dict με 'per_class', 'deltas', 'extremes', 'broken_friendships_per_class'
    """
    per_class = {}
    broken_per_class = {}
    
    for c, sub in df.groupby(class_col):
        per_class[c] = dict(
            total=len(sub),
            boys=(sub[gender_col] == BOY).sum(),
            girls=(sub[gender_col] == GIRL).sum(),
            good=(sub[lang_col] == GOOD).sum(),
        )
        
        # Υπολογισμός σπασμένων φιλιών ανά τμήμα
        if group_col in df.columns:
            # Βρίσκω όλες τις δυάδες που έχουν τουλάχιστον ένα μέλος σε αυτό το τμήμα
            groups_in_class = sub.dropna(subset=[group_col])[group_col].unique()
            broken_count = 0
            for gid in groups_in_class:
                # Ελέγχω αν η δυάδα είναι σπασμένη (μέλη σε >1 τμήματα)
                group_classes = df[df[group_col] == gid][class_col].nunique()
                if group_classes > 1:
                    broken_count += 1
            broken_per_class[c] = broken_count
        else:
            broken_per_class[c] = 0
    
    if not per_class:
        return {"per_class": {}, "deltas": {}, "extremes": {}, "broken_friendships_per_class": {}}
    
    totals = [v["total"] for v in per_class.values()]
    boys   = [v["boys"]  for v in per_class.values()]
    girls  = [v["girls"] for v in per_class.values()]
    good   = [v["good"]  for v in per_class.values()]
    
    deltas = dict(
        pop   = (max(totals) - min(totals)) if totals else 0,
        boys  = (max(boys)   - min(boys))   if boys   else 0,
        girls = (max(girls)  - min(girls))  if girls  else 0,
        gender= max((max(boys)-min(boys)) if boys else 0, (max(girls)-min(girls)) if girls else 0),
        lang  = (max(good)   - min(good))  if good   else 0,
    )
    
    def argmax(metric: str) -> Optional[str]:
        return max(per_class.keys(), key=lambda k: per_class[k][metric]) if per_class else None
    
    def argmin(metric: str) -> Optional[str]:
        return min(per_class.keys(), key=lambda k: per_class[k][metric]) if per_class else None
    
    extremes = dict(
        pop_high = argmax("total"),  pop_low  = argmin("total"),
        boys_high= argmax("boys"),   boys_low = argmin("boys"),
        girls_high=argmax("girls"),  girls_low= argmin("girls"),
        lang_high= argmax("good"),   lang_low = argmin("good"),
    )
    
    return {
        "per_class": per_class, 
        "deltas": deltas, 
        "extremes": extremes,
        "broken_friendships_per_class": broken_per_class
    }

def penalty_score(df: pd.DataFrame, class_col: str, gender_col: str, lang_col: str) -> int:
    """
    Υπολογίζει penalty score σύμφωνα με τις προδιαγραφές:
    - Πληθυσμός: +3 * max(0, Δπληθ - 1)
    - Γλώσσα:    +1 * max(0, Δγλώσσας - 2)
    - Φύλο:      +2 * (max(0, Δαγοριών-1) + max(0, Δκοριτσιών-1))
    """
    try:
        M = _metrics(df, class_col, gender_col, lang_col)
        d = M["deltas"]
        boys_over = max(0, d["boys"] - 1)
        girls_over = max(0, d["girls"] - 1)
        return 3 * max(0, d["pop"] - 1) + 1 * max(0, d["lang"] - 2) + 2 * (boys_over + girls_over)
    except Exception as e:
        print(f"Warning: penalty_score calculation failed: {e}")
        return 9999

def _is_step4(val) -> bool: 
    """Ελέγχει αν η τιμή αντιστοιχεί σε Βήμα 4."""
    return val in STEP4_MARKERS

def _is_step5(val) -> bool: 
    """Ελέγχει αν η τιμή αντιστοιχεί σε Βήμα 5."""
    return val in STEP5_MARKERS

def _find_baseline_col_for_category(df: pd.DataFrame, category_col: str) -> str:
    """Βρίσκει τη κατάλληλη baseline στήλη για κάθε κατηγορία περιορισμών."""
    if category_col in BASELINE_MAPPING:
        for baseline_col in BASELINE_MAPPING[category_col]:
            if baseline_col in df.columns:
                return baseline_col
    # Fallback στην τρέχουσα στήλη αν δε βρεθεί baseline
    return None

def _eligible_units(df: pd.DataFrame, class_col: str, step_col: str, group_col: str,
                    gender_col: str, lang_col: str) -> Tuple[Dict[str, List], Dict[str, List]]:
    """
    Επιστρέφει (singles, pairs):
    - singles[class] = IDs μεμονωμένων Βήματος 5
    - pairs[class]   = λίστα δυάδων Βήματος 4 με metadata
    
    ✅ ΔΙΟΡΘΩΣΗ: ΕΠΙΤΡΕΠΕΙ σπασμένες δυάδες σε swaps (δεν τις φιλτράρει)
    """
    classes = _classes(df, class_col)
    singles = {c: [] for c in classes}
    pairs   = {c: [] for c in classes}

    # Μεμονωμένοι: Βήμα 5, χωρίς group
    try:
        mask_solo = df[step_col].map(_is_step5) & (df[group_col].isna() | (df[group_col] == ""))
        for c, sub in df[mask_solo].groupby(class_col):
            singles[c] = sub[_IDCOL].tolist()
    except Exception as e:
        print(f"Warning: Error processing singles: {e}")

    # Δυάδες: Βήμα 4, με group δύο μελών
    try:
        df_pairs = df[df[step_col].map(_is_step4) & df[group_col].notna()].copy()
        if not df_pairs.empty:
            for gid, g in df_pairs.groupby(group_col):
                if len(g) != 2:
                    continue
                
                # ✅ ΔΙΟΡΘΩΣΗ: Δέχεται δυάδες σε διαφορετικά τμήματα (προϋπάρχουσες σπασμένες)
                classes_in_group = g[class_col].unique()
                
                genders = list(g[gender_col])
                langs   = list(g[lang_col])
                
                # Κατηγοριοποίηση φύλου
                if genders.count(BOY) == 2:   
                    gender_kind = BOY
                elif genders.count(GIRL) == 2:
                    gender_kind = GIRL
                else:                         
                    gender_kind = "ΜΙΚΤΟ"
                
                # Κατηγοριοποίηση γλώσσας
                if langs.count(GOOD) == 2:    
                    lang_kind = "NN"
                elif langs.count(NOTGOOD) == 2: 
                    lang_kind = "OO"
                else:                         
                    lang_kind = "N+O"
                
                is_split = len(classes_in_group) > 1
                
                # ✅ ΔΙΟΡΘΩΣΗ: Προσθέτει τη δυάδα σε ΟΛΑ τα τμήματα που συμμετέχει
                # και την κάνει eligible για swaps ανεξάρτητα αν είναι σπασμένη
                for class_name in classes_in_group:
                    pairs[class_name].append({
                        'group_id': gid, 
                        'ids': list(g[_IDCOL]), 
                        'gender_kind': gender_kind, 
                        'lang_kind': lang_kind,
                        'is_split': is_split,
                        'all_classes': list(classes_in_group)  # Για audit
                    })
                    
    except Exception as e:
        print(f"Warning: Error processing pairs: {e}")

    return singles, pairs

def _check_size_ok(df: pd.DataFrame, class_col: str) -> bool:
    """Ελέγχει ότι κανένα τμήμα δεν υπερβαίνει τα 25 άτομα."""
    try:
        return (df[class_col].value_counts() <= MAX_PER_CLASS).all()
    except Exception:
        return False

def _check_protected_constraints(df_baseline: pd.DataFrame, df_after: pd.DataFrame, 
                                class_col: str, step_col: str) -> bool:
    """
    ✅ ΔΙΟΡΘΩΣΗ: Ελέγχει ότι δεν αλλάζει η κατανομή Ζωηρών/Ιδιαιτερότητας/Παιδιών εκπαιδευτικών
    ανά τμήμα με ΣΩΣΤΗ BASELINE ΑΝΑ ΚΑΤΗΓΟΡΙΑ:
    - ΖΩΗΡΟΣ & ΙΔΙΑΙΤΕΡΟΤΗΤΑ: έναντι Βήματος 2
    - ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ: έναντι Βήματος 1
    """
    try:
        for col_name, description in PROTECTED_COLS.items():
            if col_name not in df_baseline.columns or col_name not in df_after.columns:
                continue
                
            # ✅ ΚΡΙΣΙΜΗ ΔΙΟΡΘΩΣΗ: Baseline ανά κατηγορία
            baseline_class_col = _find_baseline_col_for_category(df_baseline, col_name)
            if baseline_class_col is None:
                print(f"Warning: No baseline found for {col_name}, using current class column")
                baseline_class_col = class_col
                
            baseline_counts = df_baseline.groupby(baseline_class_col)[col_name].apply(
                lambda x: (x == GOOD).sum()
            ).to_dict()
            
            after_counts = df_after.groupby(class_col)[col_name].apply(
                lambda x: (x == GOOD).sum()
            ).to_dict()
            
            # Έλεγχος ότι δεν άλλαξε η κατανομή για κάθε τμήμα
            for class_name in set(baseline_counts.keys()) | set(after_counts.keys()):
                baseline_val = baseline_counts.get(class_name, 0)
                after_val = after_counts.get(class_name, 0)
                if baseline_val != after_val:
                    return False
                
        return True
    except Exception as e:
        print(f"Warning: Error checking protected constraints: {e}")
        return False

def _check_friendship_constraints(df_before: pd.DataFrame, df_after: pd.DataFrame, 
                                 class_col: str, group_col: str) -> bool:
    """
    ✅ ΔΙΟΡΘΩΣΗ: Ελέγχει τις φιλίες σύμφωνα με προδιαγραφές:
    1. Μη αύξηση αριθμού σπασμένων φιλιών (σε σχέση με το Βήμα 5)
    2. Απαγόρευση επανένωσης προϋπάρχουσων σπασμένων φιλιών
    3. Δεν επιτρέπεται διάσπαση ήδη ενωμένων δυάδων
    
    ΔΕΝ απαιτεί όλες οι δυάδες να είναι ενωμένες - επιτρέπει προϋπάρχουσες σπασμένες.
    """
    try:
        if group_col not in df_before.columns or group_col not in df_after.columns:
            return True
            
        def get_group_status(df):
            """
            Επιστρέφει dict: {group_id: {'classes': set, 'is_split': bool}}
            """
            groups_with_data = df.dropna(subset=[group_col])
            if groups_with_data.empty:
                return {}
                
            result = {}
            for gid, group_df in groups_with_data.groupby(group_col):
                classes = set(group_df[class_col])
                result[gid] = {
                    'classes': classes,
                    'is_split': len(classes) > 1
                }
            return result
        
        before_groups = get_group_status(df_before)
        after_groups = get_group_status(df_after)
        
        # Βρίσκουμε όλες τις δυάδες που υπήρχαν πριν ή μετά
        all_group_ids = set(before_groups.keys()) | set(after_groups.keys())
        
        split_before_count = sum(1 for g in before_groups.values() if g['is_split'])
        split_after_count = sum(1 for g in after_groups.values() if g['is_split'])
        
        # 1. Μη αύξηση αριθμού σπασμένων φιλιών
        if split_after_count > split_before_count:
            return False
        
        # 2. Έλεγχος για επανενώσεις και νέες διασπάσεις
        for gid in all_group_ids:
            before_status = before_groups.get(gid, {'classes': set(), 'is_split': False})
            after_status = after_groups.get(gid, {'classes': set(), 'is_split': False})
            
            was_split = before_status['is_split']
            is_now_split = after_status['is_split']
            
            # Απαγόρευση επανένωσης: προϋπάρχουσα σπασμένη δεν γίνεται ενωμένη
            if was_split and not is_now_split and len(after_status['classes']) > 0:
                return False
                
            # Απαγόρευση νέας διάσπασης: ενωμένη δεν γίνεται σπασμένη
            if not was_split and is_now_split:
                return False
                
        return True
        
    except Exception as e:
        print(f"Warning: Error checking friendship constraints: {e}")
        return False

# --------------------------
# Swap Operations
# --------------------------
def _apply_swap(df: pd.DataFrame, class_col: str,
                fromA_ids: List[str], to_class_B: str,
                fromB_ids: List[str], to_class_A: str,
                reason: str, swap_idx: int,
                step_col: str, group_col: str) -> pd.DataFrame:
    """Εφαρμόζει ανταλλαγή μεταξύ δύο τμημάτων."""
    df = df.copy()
    
    # Εφαρμογή ανταλλαγής
    if fromA_ids:
        df.loc[df[_IDCOL].isin(fromA_ids), class_col] = to_class_B
    if fromB_ids:
        df.loc[df[_IDCOL].isin(fromB_ids), class_col] = to_class_A

    # Audit trail
    swap_id = f"SWAP_{swap_idx}"
    moved_ids = list(fromA_ids) + list(fromB_ids)
    if moved_ids:
        mask = df[_IDCOL].isin(moved_ids)
        df.loc[mask, "ΒΗΜΑ6_ΚΙΝΗΣΗ"] = swap_id
        df.loc[mask, "ΑΙΤΙΑ_ΑΛΛΑΓΗΣ"] = reason
        df.loc[mask, "ΠΗΓΗ_ΒΗΜΑ"] = np.where(
            df.loc[mask, group_col].notna(), 
            "Β4_Δυάδα", 
            "Β5_Μεμονωμένος"
        )
    
    return df

def _determine_reason(df_before: pd.DataFrame, class_col: str, gender_col: str, 
                     lang_col: str, objective: str) -> str:
    """
    Καθορίζει την αιτία ανταλλαγής βάσει στόχου και τρέχουσας κατάστασης.
    """
    metrics = _metrics(df_before, class_col, gender_col, lang_col)
    deltas = metrics["deltas"]
    
    within_targets = (
        deltas["pop"] <= TARGET_POP_DIFF and
        deltas["gender"] <= TARGET_GENDER_DIFF and 
        deltas["lang"] <= TARGET_LANG_DIFF
    )
    
    if within_targets and objective == "BOTH":
        return "Population"  # Βελτίωση penalty εντός στόχων
    elif objective == "LANG":
        return "Language"
    elif objective == "GENDER":
        return "Gender" 
    else:
        # Μικτή κατάσταση - προτεραιότητα στο φύλο
        return "Gender" if deltas["gender"] >= deltas["lang"] else "Language"

def _rank_candidates(df_before: pd.DataFrame, df_baseline: pd.DataFrame,
                     class_col: str, gender_col: str, lang_col: str,
                     step_col: str, group_col: str,
                     candidates: List, objective: str) -> List:
    """
    Κατατάσσει υποψήφιες ανταλλαγές βάσει στόχου με πλήρεις ελέγχους συμμόρφωσης.
    ✅ ΔΙΟΡΘΩΣΗ: Περιλαμβάνει έλεγχο baseline constraints.
    """
    base_M = _metrics(df_before, class_col, gender_col, lang_col)
    base_d = base_M["deltas"]
    base_pen = penalty_score(df_before, class_col, gender_col, lang_col)
    ranked = []

    for (fromA, classA, fromB, classB, base_reason) in candidates:
        try:
            # Καθορισμός σωστής αιτίας
            reason = _determine_reason(df_before, class_col, gender_col, lang_col, objective)
            
            tmp = _apply_swap(df_before, class_col, fromA, classB, fromB, classA, 
                            reason, 9999, step_col=step_col, group_col=group_col)
            
            # 1. Έλεγχος μεγέθους τμημάτων
            if not _check_size_ok(tmp, class_col):
                continue
                
            # 2. ✅ ΔΙΟΡΘΩΣΗ: Έλεγχος απαραβίαστων περιορισμών με baseline ανά κατηγορία
            if not _check_protected_constraints(df_baseline, tmp, class_col, step_col):
                continue
                
            # 3. Έλεγχος φιλιών (σπασμένες/επανενώσεις)
            if not _check_friendship_constraints(df_before, tmp, class_col, group_col):
                continue
                
            M = _metrics(tmp, class_col, gender_col, lang_col)
            d = M["deltas"]
            
            # 4. Πληθυσμιακός έλεγχος (αυστηροποίηση)
            if d["pop"] > TARGET_POP_DIFF:
                continue
            if base_d["pop"] <= TARGET_POP_DIFF and d["pop"] > base_d["pop"]:
                continue

            pen = penalty_score(tmp, class_col, gender_col, lang_col)
            dlang_gain   = base_d["lang"]   - d["lang"]
            dgender_gain = base_d["gender"] - d["gender"]
            pen_gain     = base_pen - pen

            # 5. Έλεγχος μη-επιδείνωσης του άλλου δείκτη
            if objective == "LANG"   and dgender_gain < 0: 
                continue
            if objective == "GENDER" and dlang_gain   < 0: 
                continue
            if objective == "BOTH"   and (dlang_gain < 0 or dgender_gain < 0): 
                continue

            # Κατάταξη βάσει στόχου
            if objective in ("GENDER", "BOTH"):
                key = (-dgender_gain, -dlang_gain, -pen_gain, len(fromA) + len(fromB))
            else:
                key = (-dlang_gain, -dgender_gain, -pen_gain, len(fromA) + len(fromB))
                
            ranked.append((key, fromA, classA, fromB, classB, reason))
            
        except Exception as e:
            print(f"Warning: Error evaluating candidate swap: {e}")
            continue

    ranked.sort(key=lambda x: x[0])
    return [(fromA, classA, fromB, classB, reason) for _, fromA, classA, fromB, classB, reason in ranked]

# --------------------------
# Candidate Generation
# --------------------------
def _enum_LANG(df: pd.DataFrame, class_col: str, gender_col: str, lang_col: str,
               step_col: str, group_col: str, top_k: int = 2) -> List:
    """
    Παράγει υποψήφιες ανταλλαγές για διόρθωση γλώσσας.
    ✅ ΔΙΟΡΘΩΣΗ: ΔΕΝ φιλτράρει σπασμένες δυάδες - τις επιτρέπει σε swaps.
    """
    M = _metrics(df, class_col, gender_col, lang_col)
    per_class = M["per_class"]
    
    # Ταξινόμηση τμημάτων κατά 'good' γλώσσα
    classes_sorted = sorted(per_class.keys(), key=lambda c: per_class[c]["good"], reverse=True)
    highs = classes_sorted[:top_k]
    lows  = list(reversed(classes_sorted))[:top_k]

    singles, pairs = _eligible_units(df, class_col, step_col, group_col, gender_col, lang_col)
    candidates = []
    
    try:
        for high in highs:
            for low in lows:
                if high == low: 
                    continue
                
                # 1↔1 (Καλή Γνώση ↔ Όχι Καλή)
                singles_high_good = df[df[_IDCOL].isin(singles[high]) & (df[lang_col] == GOOD)][_IDCOL].tolist()
                singles_low_not   = df[df[_IDCOL].isin(singles[low])  & (df[lang_col] == NOTGOOD)][_IDCOL].tolist()
                
                for i in singles_high_good:
                    for j in singles_low_not:
                        candidates.append(([i], high, [j], low, "Language"))
                
                # ✅ ΔΙΟΡΘΩΣΗ: 2↔2 (NN ↔ OO) - ΧΩΡΙΣ φιλτράρισμα σπασμένων δυάδων
                pairs_high_NN = [p for p in pairs[high] if p["lang_kind"] == "NN"]
                pairs_low_OO  = [p for p in pairs[low]  if p["lang_kind"] == "OO"]
                
                for pNN in pairs_high_NN:
                    for pOO in pairs_low_OO:
                        candidates.append((pNN["ids"], high, pOO["ids"], low, "Language"))
                
                # ✅ ΔΙΟΡΘΩΣΗ: 2↔1+1 scenarios - ΧΩΡΙΣ φιλτράρισμα σπασμένων
                if pairs_high_NN and len(singles_low_not) >= 2:
                    for pNN in pairs_high_NN:
                        for two in itertools.combinations(singles_low_not, 2):
                            candidates.append((pNN["ids"], high, list(two), low, "Language"))
                
                # Αντίστροφα (OO ↔ Ν+Ν)
                pairs_high_OO = [p for p in pairs[high] if p["lang_kind"] == "OO"]
                singles_low_good = df[df[_IDCOL].isin(singles[low]) & (df[lang_col] == GOOD)][_IDCOL].tolist()
                
                if pairs_high_OO and len(singles_low_good) >= 2:
                    for pOO in pairs_high_OO:
                        for two in itertools.combinations(singles_low_good, 2):
                            candidates.append((list(two), low, pOO["ids"], high, "Language"))
                            
    except Exception as e:
        print(f"Warning: Error generating language candidates: {e}")
    
    return candidates

def _enum_GENDER(df: pd.DataFrame, class_col: str, gender_col: str, lang_col: str,
                 step_col: str, group_col: str, top_k: int = 2) -> List:
    """
    Παράγει υποψήφιες ανταλλαγές για διόρθωση φύλου.
    ✅ ΔΙΟΡΘΩΣΗ: ΔΕΝ φιλτράρει σπασμένες δυάδες - τις επιτρέπει σε swaps.
    """
    M = _metrics(df, class_col, gender_col, lang_col)
    per_class = M["per_class"]
    deltas = M["deltas"]
    
    # Καθορισμός target φύλου (το φύλο με μεγαλύτερη απόκλιση)
    target_gender = BOY if deltas["boys"] >= deltas["girls"] else GIRL
    opp_gender = GIRL if target_gender == BOY else BOY
    
    # Ταξινόμηση τμημάτων κατά πλήθος target φύλου
    metric = "boys" if target_gender == BOY else "girls"
    classes_sorted = sorted(per_class.keys(), key=lambda c: per_class[c][metric], reverse=True)
    highs = classes_sorted[:top_k]
    lows  = list(reversed(classes_sorted))[:top_k]

    singles, pairs = _eligible_units(df, class_col, step_col, group_col, gender_col, lang_col)
    candidates = []
    
    try:
        for high in highs:
            for low in lows:
                if high == low: 
                    continue
                
                # 1↔1 (target_gender ↔ opp_gender)
                ids_high_target = df[df[_IDCOL].isin(singles[high]) & (df[gender_col] == target_gender)][_IDCOL].tolist()
                ids_low_opp = df[df[_IDCOL].isin(singles[low]) & (df[gender_col] == opp_gender)][_IDCOL].tolist()
                
                for i in ids_high_target:
                    # Προτίμηση ίδιας γλώσσας
                    lang_i = df.loc[df[_IDCOL] == i, lang_col].iloc[0]
                    same_lang = df[
                        df[_IDCOL].isin(singles[low]) & 
                        (df[gender_col] == opp_gender) & 
                        (df[lang_col] == lang_i)
                    ][_IDCOL].tolist()
                    
                    for j in same_lang:
                        candidates.append(([i], high, [j], low, "Gender"))
                    for j in ids_low_opp:
                        candidates.append(([i], high, [j], low, "Gender"))
                
                # ✅ ΔΙΟΡΘΩΣΗ: 2↔2 - ΧΩΡΙΣ φιλτράρισμα σπασμένων δυάδων
                pairs_high_target = [p for p in pairs[high] if p["gender_kind"] == target_gender]
                pairs_low_opp = [p for p in pairs[low] if p["gender_kind"] == opp_gender]
                
                for p1 in pairs_high_target:
                    for p2 in pairs_low_opp:
                        candidates.append((p1["ids"], high, p2["ids"], low, "Gender"))
                
                # ✅ ΔΙΟΡΘΩΣΗ: 2↔1+1 - ΧΩΡΙΣ φιλτράρισμα σπασμένων δυάδων
                for p1 in pairs_high_target:
                    if len(ids_low_opp) >= 2:
                        for two in itertools.combinations(ids_low_opp, 2):
                            candidates.append((p1["ids"], high, list(two), low, "Gender"))
                            
    except Exception as e:
        print(f"Warning: Error generating gender candidates: {e}")
    
    return candidates

def _enum_BOTH(df: pd.DataFrame, class_col: str, gender_col: str, lang_col: str,
               step_col: str, group_col: str, top_k: int = 2) -> List:
    """Παράγει υποψήφιες ανταλλαγές για ταυτόχρονη διόρθωση."""
    candidates = []
    candidates += _enum_LANG(df, class_col, gender_col, lang_col, step_col, group_col, top_k=top_k)
    candidates += _enum_GENDER(df, class_col, gender_col, lang_col, step_col, group_col, top_k=top_k)
    return candidates

def _commit_best_swap_if_improves(df: pd.DataFrame, df_baseline: pd.DataFrame,
                                  class_col: str, gender_col: str, lang_col: str,
                                  step_col: str, group_col: str, objective: str, swap_idx: int) -> Tuple[pd.DataFrame, bool]:
    """
    Επιχειρεί να βρει και εφαρμόσει τη βέλτιστη ανταλλαγή με πλήρεις ελέγχους συμμόρφωσης.
    ✅ ΔΙΟΡΘΩΣΗ: Περιλαμβάνει baseline constraints checking.
    """
    
    # Παραγωγή υποψηφίων
    if objective == "LANG":
        candidates = _enum_LANG(df, class_col, gender_col, lang_col, step_col, group_col)
    elif objective == "GENDER":
        candidates = _enum_GENDER(df, class_col, gender_col, lang_col, step_col, group_col)
    else:  # BOTH
        candidates = _enum_BOTH(df, class_col, gender_col, lang_col, step_col, group_col)

    ranked = _rank_candidates(df, df_baseline, class_col, gender_col, lang_col, step_col, group_col, candidates, objective)
    if not ranked: 
        return df, False

    base_penalty = penalty_score(df, class_col, gender_col, lang_col)

    # Δοκιμή καλύτερης ανταλλαγής - ήδη φιλτραρισμένη από _rank_candidates
    for (fromA, classA, fromB, classB, reason) in ranked:
        try:
            tmp = _apply_swap(df, class_col, fromA, classB, fromB, classA, reason, swap_idx, step_col, group_col)
            
            # Όλοι οι έλεγχοι έχουν ήδη γίνει στο _rank_candidates
            # Απλά ελέγχουμε τη βελτίωση penalty
            new_penalty = penalty_score(tmp, class_col, gender_col, lang_col)
            if new_penalty < base_penalty:
                return tmp, True
                
        except Exception as e:
            print(f"Warning: Error applying swap: {e}")
            continue
    
    return df, False

# --------------------------
# Public API
# --------------------------
def apply_step6_to_step5_scenarios(step5_outputs: Dict[str, pd.DataFrame],
                                   *, class_col: str = "ΤΜΗΜΑ", id_col: str = "ID", 
                                   gender_col: str = "ΦΥΛΟ", lang_col: str = "ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ", 
                                   step_col: str = "ΒΗΜΑ_ΤΟΠΟΘΕΤΗΣΗΣ", group_col: str = "GROUP_ID", 
                                   max_iter: int = MAX_ITER) -> Dict[str, Dict]:
    """
    Εφαρμόζει το Βήμα 6 σε πολλαπλά σενάρια από το Βήμα 5.
    
    Args:
        step5_outputs: Dict με σενάρια {"ΣΕΝΑΡΙΟ_1": df5_1, ...}
        
    Returns:
        Dict με ίδια keys και values {"df": df6, "summary": {...}}
    """
    results = {}
    for name, df5 in step5_outputs.items():
        try:
            result = apply_step6(df5.copy(), class_col=class_col, id_col=id_col, 
                               gender_col=gender_col, lang_col=lang_col, 
                               step_col=step_col, group_col=group_col, max_iter=max_iter)
            results[name] = result
        except Exception as e:
            print(f"Error processing scenario {name}: {e}")
            results[name] = {"df": df5.copy(), "summary": {"status": "ERROR", "error": str(e)}}
    
    return results

def apply_step6(df: pd.DataFrame,
                *, class_col: str = "ΤΜΗΜΑ", id_col: str = "ID", 
                gender_col: str = "ΦΥΛΟ", lang_col: str = "ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ",
                step_col: str = "ΒΗΜΑ_ΤΟΠΟΘΕΤΗΣΗΣ", group_col: str = "GROUP_ID", 
                max_iter: int = MAX_ITER) -> Dict[str, Any]:
    """
    Εφαρμογή Βήματος 6: Τελικός Ποιοτικός και Ποσοτικός Έλεγχος.
    
    ✅ 100% σύμφωνος με προδιαγραφές:
    - Απαραβίαστοι περιορισμοί Βημάτων 1-2 σε σχέση με βάση (όχι between swaps)
    - Σωστός έλεγχος φιλιών που επιτρέπει προϋπάρχουσες σπασμένες δυάδες σε swaps
    - Πλήρης audit trail με Population αιτία
    
    Στόχοι:
    - Πληθυσμός: διαφορά ≤2
    - Φύλο: διαφορά ≤3  
    - Γλώσσα: διαφορά ≤3
    
    Κινούνται ΜΟΝΟ:
    - Δυάδες Β4 (αδιαίρετες, ΣΥΜΠΕΡΙΛΑΜΒΑΝΟΜΕΝΩΝ σπασμένων)
    - Μεμονωμένοι Β5
    
    Args:
        df: DataFrame με μαθητές μετά το Βήμα 5
        max_iter: Μέγιστος αριθμός επαναλήψεων
        
    Returns:
        Dict με "df" (βελτιωμένο DataFrame) και "summary" (στατιστικά)
    """
    # Αρχικοποίηση
    global _IDCOL
    _IDCOL = id_col
    
    # Δημιουργία snapshot πριν το Βήμα 6
    if "ΤΜΗΜΑ_ΠΡΙΝ_ΒΗΜΑ6" not in df.columns and class_col in df.columns:
        df["ΤΜΗΜΑ_ΠΡΙΝ_ΒΗΜΑ6"] = df[class_col]

    # Έλεγχος απαραίτητων στηλών
    required_cols = [id_col, class_col, gender_col, lang_col, step_col]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Λείπουν στήλες: {missing_cols}")
    
    # ✅ ΔΙΟΡΘΩΣΗ: Εντοπισμός baseline στηλών ανά κατηγορία για έλεγχο περιορισμών Βημάτων 1-2
    available_baselines = {}
    for category_col in PROTECTED_COLS.keys():
        if category_col in df.columns:
            baseline_col = _find_baseline_col_for_category(df, category_col)
            available_baselines[category_col] = baseline_col or class_col
    
    # Δημιουργία baseline snapshot για τους ελέγχους
    df_baseline = df.copy()
    
    # Προετοιμασία στηλών
    if group_col not in df.columns:
        df = df.copy()
        df[group_col] = np.nan
    else:
        # Διόρθωση: αντικατάσταση None με np.nan για συνέπεια
        df = df.copy()
        df[group_col] = df[group_col].replace([None, ""], np.nan)

    # Audit στήλες
    audit_cols = ["ΒΗΜΑ6_ΚΙΝΗΣΗ", "ΑΙΤΙΑ_ΑΛΛΑΓΗΣ", "ΠΗΓΗ_ΒΗΜΑ"]
    for col in audit_cols:
        if col not in df.columns:
            df[col] = None

    if available_baselines:
        print(f"Baseline mapping for protected constraints: {available_baselines}")

    # Έλεγχος διαθεσιμότητας προστατευόμενων στηλών
    available_protected = [col for col in PROTECTED_COLS.keys() if col in df.columns]
    if available_protected:
        print(f"Protecting constraints for: {', '.join(available_protected)}")

    # Κύριος αλγόριθμος
    iterations = 0
    status = "VALID"
    
    try:
        while iterations < max_iter:
            iterations += 1
            metrics = _metrics(df, class_col, gender_col, lang_col)
            deltas = metrics["deltas"]
            
            # Έλεγχος στόχων
            within_targets = (
                deltas["pop"] <= TARGET_POP_DIFF and
                deltas["gender"] <= TARGET_GENDER_DIFF and 
                deltas["lang"] <= TARGET_LANG_DIFF
            )

            # Καθορισμός στόχου με σειριακή προτεραιότητα για ταυτόχρονη απόκλιση
            if not within_targets:
                if deltas["gender"] > TARGET_GENDER_DIFF and deltas["lang"] > TARGET_LANG_DIFF:
                    # Γ: Ταυτόχρονη απόκλιση - προτεραιότητα στο φύλο
                    df_new, changed = _commit_best_swap_if_improves(
                        df, df_baseline, class_col, gender_col, lang_col, 
                        step_col, group_col, "GENDER", iterations
                    )
                    if not changed:
                        # Αν δεν βελτιώθηκε το φύλο, δοκίμασε γλώσσα
                        df_new, changed = _commit_best_swap_if_improves(
                            df, df_baseline, class_col, gender_col, lang_col, 
                            step_col, group_col, "LANG", iterations
                        )
                elif deltas["gender"] > TARGET_GENDER_DIFF:
                    # Β: Μόνο φύλο εκτός στόχου
                    df_new, changed = _commit_best_swap_if_improves(
                        df, df_baseline, class_col, gender_col, lang_col, 
                        step_col, group_col, "GENDER", iterations
                    )
                else:
                    # Α: Μόνο γλώσσα εκτός στόχου
                    df_new, changed = _commit_best_swap_if_improves(
                        df, df_baseline, class_col, gender_col, lang_col, 
                        step_col, group_col, "LANG", iterations
                    )
            else:
                # Εντός στόχων: συνέχεια βελτίωσης (θα καταγραφεί ως Population)
                df_new, changed = _commit_best_swap_if_improves(
                    df, df_baseline, class_col, gender_col, lang_col, 
                    step_col, group_col, "BOTH", iterations
                )
            
            if not changed:
                break
            df = df_new

    except Exception as e:
        print(f"Error in step 6 iterations: {e}")
        status = "ERROR"

    # Τελικός έλεγχος
    try:
        final_metrics = _metrics(df, class_col, gender_col, lang_col)
        final_penalty = penalty_score(df, class_col, gender_col, lang_col)
        final_deltas = final_metrics["deltas"]
        
        final_within_targets = (
            final_deltas["pop"] <= TARGET_POP_DIFF and
            final_deltas["gender"] <= TARGET_GENDER_DIFF and 
            final_deltas["lang"] <= TARGET_LANG_DIFF
        )
        
        if not final_within_targets and status != "ERROR":
            status = "Αδυναμία Διόρθωσης (Βήμα 6)"
            
    except Exception as e:
        print(f"Error in final metrics calculation: {e}")
        final_metrics = {"deltas": {}, "per_class": {}}
        final_penalty = 9999
        status = "ERROR"

    # Προετοιμασία εξόδων
    try:
        if "ΤΜΗΜΑ_ΜΕΤΑ_ΒΗΜΑ6" not in df.columns and class_col in df.columns:
            df["ΤΜΗΜΑ_ΜΕΤΑ_ΒΗΜΑ6"] = df[class_col]
            
        # Στήλη μεταβολής
        if "ΤΜΗΜΑ_ΠΡΙΝ_ΒΗΜΑ6" in df.columns and "ΤΜΗΜΑ_ΜΕΤΑ_ΒΗΜΑ6" in df.columns:
            df["ΜΕΤΑΒΟΛΗ_ΤΜΗΜΑΤΟΣ"] = np.where(
                df["ΤΜΗΜΑ_ΠΡΙΝ_ΒΗΜΑ6"].astype(str) == df["ΤΜΗΜΑ_ΜΕΤΑ_ΒΗΜΑ6"].astype(str),
                "STAY",
                df["ΤΜΗΜΑ_ΠΡΙΝ_ΒΗΜΑ6"].astype(str) + "→" + df["ΤΜΗΜΑ_ΜΕΤΑ_ΒΗΜΑ6"].astype(str)
            )
        
        # Βήμα 6 τμήμα
        df["ΒΗΜΑ6_ΤΜΗΜΑ"] = df.get("ΤΜΗΜΑ_ΜΕΤΑ_ΒΗΜΑ6", df.get(class_col))
        
        # Εντοπισμός σεναρίου από Βήμα 5
        import re
        scen_num = None
        for col in df.columns:
            match = re.match(r"ΒΗΜΑ5_ΣΕΝΑΡΙΟ_(\d+)__1$", str(col))
            if match:
                scen_num = match.group(1)
                break
        
        if scen_num and f"ΒΗΜΑ6_ΣΕΝΑΡΙΟ_{scen_num}__1" not in df.columns:
            df[f"ΒΗΜΑ6_ΣΕΝΑΡΙΟ_{scen_num}__1"] = df["ΒΗΜΑ6_ΤΜΗΜΑ"]
            
    except Exception as e:
        print(f"Warning: Error preparing output columns: {e}")

    summary = {
        "iterations": iterations,
        "final_deltas": final_metrics.get("deltas", {}),
        "per_class": final_metrics.get("per_class", {}),
        "broken_friendships_per_class": final_metrics.get("broken_friendships_per_class", {}),
        "final_penalty": final_penalty,
        "status": status,
        "targets": {
            "population": TARGET_POP_DIFF,
            "gender": TARGET_GENDER_DIFF, 
            "language": TARGET_LANG_DIFF
        },
        "protected_columns": available_protected,
        "baseline_mapping": available_baselines
    }

    return {"df": df, "summary": summary}


# --------------------------
# Public Wrapper API
# --------------------------
def run_step6(df: pd.DataFrame) -> pd.DataFrame:
    """
    Wrapper function για το Βήμα 6 - API συνέπεια με άλλα βήματα.
    
    Εφαρμόζει τελικό ποιοτικό και ποσοτικό έλεγχο με στόχους:
    - Πληθυσμός: διαφορά ≤2
    - Φύλο: διαφορά ≤3  
    - Γλώσσα: διαφορά ≤3
    
    Args:
        df: DataFrame μετά το Βήμα 5
        
    Returns:
        DataFrame με βελτιωμένη κατανομή και audit trail
    """
    result = apply_step6(df)
    return result["df"]



# ---- End of embedded original step6.py ----

# --------------------------
# Helpers (FINAL wrapper)
# --------------------------
def _final_detect_step5_scenario_number(df: pd.DataFrame) -> str:
    """
    Tries to infer N from any column named:
    - 'ΒΗΜΑ5_ΣΕΝΑΡΙΟ_<N>'
    - 'ΒΗΜΑ5_ΣΕΝΑΡΙΟ_<N>__<k>'
    Falls back to "1" if none is found.
    """
    pattern = re.compile(r"ΒΗΜΑ5_ΣΕΝΑΡΙΟ_(\d+)(?:__\d+)?$")
    for col in df.columns:
        m = pattern.match(str(col))
        if m:
            return m.group(1)
    return "1"

def _final_place_col_at_letter(df: pd.DataFrame, col_name: str, values, letter: str = "P") -> pd.DataFrame:
    """
    Ensures `col_name` exists with `values` and is placed at the given Excel column letter.
    Column letters are 1-indexed visually (A=1), while pandas indices are 0-based.
    """
    df = df.copy()
    df[col_name] = values

    # Target zero-based index
    target_idx = ord(letter.upper()) - ord("A")

    cols = list(df.columns)
    # Move the column to target position
    if col_name in cols:
        cols.remove(col_name)
        # If target index is beyond current length, append at the end
        if target_idx >= len(cols):
            cols.append(col_name)
        else:
            cols.insert(target_idx, col_name)
        df = df[cols]
    return df

# --------------------------
# Public API (wrappers)
# --------------------------
def apply_step6_final(df: pd.DataFrame,
                      *, class_col: str = "ΤΜΗΜΑ", id_col: str = "ID",
                      gender_col: str = "ΦΥΛΟ", lang_col: str = "ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ",
                      step_col: str = "ΒΗΜΑ_ΤΟΠΟΘΕΤΗΣΗΣ", group_col: str = "GROUP_ID",
                      max_iter: int = 5):
    """
    Runs the embedded step6 algorithm (apply_step6) and then writes:
    'ΒΗΜΑ6_ΣΕΝΑΡΙΟ_N' at Excel column P.

    Returns: {"df": DataFrame, "summary": dict}
    """
    # Use the embedded apply_step6 from the original code block
    if "apply_step6" not in globals():
        raise RuntimeError("Embedded apply_step6 not found in this module.")
    result = apply_step6(
        df.copy(),
        class_col=class_col, id_col=id_col,
        gender_col=gender_col, lang_col=lang_col,
        step_col=step_col, group_col=group_col,
        max_iter=max_iter
    )

    out_df = result.get("df", df).copy()

    # Determine source column for the final class after Step 6
    # Prefer explicit 'ΤΜΗΜΑ_ΜΕΤΑ_ΒΗΜΑ6' if present, else fall back to current class_col
    src_col = "ΤΜΗΜΑ_ΜΕΤΑ_ΒΗΜΑ6" if "ΤΜΗΜΑ_ΜΕΤΑ_ΒΗΜΑ6" in out_df.columns else class_col

    # Detect scenario number and compose the final Step 6 scenario column name
    scen_num = _final_detect_step5_scenario_number(out_df)
    step6_col = f"ΒΗΜΑ6_ΣΕΝΑΡΙΟ_{scen_num}"

    # Place the column at Excel letter P
    out_df = _final_place_col_at_letter(out_df, step6_col, out_df[src_col], letter="P")

    # Update result and return
    result["df"] = out_df
    return result

def run_step6_final(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convenience wrapper that returns only the DataFrame.
    """
    return apply_step6_final(df)["df"]

if __name__ == "__main__":
    # Minimal smoke test (does not depend on real data)
    demo = pd.DataFrame({
        "ID": [1,2,3,4],
        "ΤΜΗΜΑ": ["Α1","Α1","Β1","Β1"],
        "ΦΥΛΟ": ["Α","Κ","Α","Κ"],
        "ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ": ["Ν","Ο","Ν","Ο"],
        "ΒΗΜΑ_ΤΟΠΟΘΕΤΗΣΗΣ": [5,5,5,5],
        "GROUP_ID": [None,None,None,None],
        "ΒΗΜΑ5_ΣΕΝΑΡΙΟ_1": ["Α1","Α1","Β1","Β1"]
    })
    df_out = run_step6_final(demo)
    print("OK. Columns:", list(df_out.columns))
