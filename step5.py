# -*- coding: utf-8 -*-
"""
step5_FINAL_RELAXED.py

Βήμα 5 (Τοποθέτηση υπολοίπων μαθητών) με ενσωματωμένα τα χαλαρά «σκληρά» όρια:
- Εύρος πληθυσμού (max−min) ≤ 4  → αλλιώς ΑΠΟΡΡΙΠΤΕΤΑΙ
- Διαφορά "Ν" (Καλή Γνώση Ελληνικών) ≤ 6 → αλλιώς ΑΠΟΡΡΙΠΤΕΤΑΙ
- Διαφορά φύλου (αγόρια) ≤ 6 και (κορίτσια) ≤ 6 → αλλιώς ΑΠΟΡΡΙΠΤΕΤΑΙ

Διατηρείται η υπάρχουσα λογική penalty χωρίς αλλαγές.
Γράφει αποτέλεσμα σε στήλες **ΒΗΜΑ5_ΣΕΝΑΡΙΟ_N** και, όταν είναι μόνο μία, τη μετακινεί στη στήλη O.
"""

from __future__ import annotations
import random, re
from typing import List, Dict, Tuple, Any, Optional
import pandas as pd

# ---------------------------- Ρυθμίσεις/Όρια Βήματος 5 (Χαλαρά) ----------------------------

STEP5_CAP: int = 25                 # μέγιστο μαθητών ανά τμήμα
STEP5_POP_DIFF_MAX: int = 4         # εύρος πληθυσμού ≤ 4
STEP5_GOOD_DIFF_MAX: int = 6        # Δ Ν (Καλή Γνώση) ≤ 6
STEP5_GENDER_DIFF_MAX: int = 6      # Δ φύλου (αγόρια) ≤ 6 και (κορίτσια) ≤ 6

# ---------------------------- Βοηθητικά ----------------------------

def _auto_num_classes(df: pd.DataFrame, override: Optional[int] = None) -> int:
    """Αυτόματος υπολογισμός αριθμού τμημάτων (25 μαθητές/τμήμα, min=2)."""
    import math
    n = len(df)
    k = max(2, math.ceil(n/25))
    return int(k if override is None else override)

YES_TOKENS = {"Ν", "ΝΑΙ", "YES", "Y", "TRUE", "1"}
NO_TOKENS  = {"Ο", "ΟΧΙ", "NO", "N", "FALSE", "0"}

def _norm_str(x: Any) -> str:
    return str(x).strip().upper()

def _is_yes(x: Any) -> bool:
    return _norm_str(x) in YES_TOKENS

def _parse_list_cell(x: Any) -> List[str]:
    if isinstance(x, list):
        return [str(t).strip() for t in x if str(t).strip()]
    s = "" if pd.isna(x) else str(x)
    s = s.strip()
    if not s or s.upper() == "NAN":
        return []
    try:
        v = eval(s, {}, {})
        if isinstance(v, list):
            return [str(t).strip() for t in v if str(t).strip()]
    except Exception:
        pass
    parts = re.split(r"[,\|\;/·\n]+", s)
    return [p.strip() for p in parts if p.strip()]

def _is_good_greek(row: pd.Series) -> bool:
    """Έλεγχος καλής γνώσης ελληνικών (backward/forward compatible)."""
    if "ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ" in row:
        return _is_yes(row.get("ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ"))
    if "ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ" in row:
        return _norm_str(row.get("ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ")) in {"ΚΑΛΗ", "GOOD", "Ν"}
    return False

def _get_class_labels(df: pd.DataFrame, scenario_col: str) -> List[str]:
    """Επιστρέφει τα labels των τμημάτων (Α1, Α2, ...)."""
    labs = sorted([str(v) for v in df[scenario_col].dropna().unique()
                   if re.match(r"^Α\d+$", str(v))])
    return labs or [f"Α{i+1}" for i in range(2)]

def _count_broken_pairs(df: pd.DataFrame, scenario_col: str) -> int:
    """Δυναμικός υπολογισμός σπασμένων πλήρως αμοιβαίων φιλιών."""
    by_class = dict(zip(df["ΟΝΟΜΑ"].astype(str).str.strip(), df[scenario_col].astype(str)))
    broken = set()
    for _, r in df.iterrows():
        if not _is_yes(r.get("ΠΛΗΡΩΣ_ΑΜΟΙΒΑΙΑ", False)):
            continue
        me = str(r["ΟΝΟΜΑ"]).strip()
        c_me = by_class.get(me)
        for fr in _parse_list_cell(r.get("ΦΙΛΟΙ", [])):
            if me < fr:  # Αποφυγή διπλής καταμέτρησης
                friend_row = df[df["ΟΝΟΜΑ"].astype(str).str.strip() == fr]
                if not friend_row.empty and _is_yes(friend_row.iloc[0].get("ΠΛΗΡΩΣ_ΑΜΟΙΒΑΙΑ", False)):
                    c_fr = by_class.get(fr)
                    if pd.notna(c_me) and pd.notna(c_fr) and c_me != c_fr:
                        broken.add((me, fr))
    return len(broken)

def _collect_counters(df: pd.DataFrame, scenario_col: str) -> Tuple[Dict[str,int], Dict[str,int], Dict[str,int], Dict[str,int]]:
    """Επιστρέφει (cnt, good, boys, girls) ως dict ανά τμήμα για έλεγχο ορίων/penalty."""
    labs = _get_class_labels(df, scenario_col)
    cnt   = {lab: int((df[scenario_col] == lab).sum()) for lab in labs}
    good  = {lab: int(df[df[scenario_col] == lab].apply(_is_good_greek, axis=1).sum()) for lab in labs}
    boys  = {lab: int(((df[scenario_col] == lab) & (df["ΦΥΛΟ"].astype(str).str.upper() == "Α")).sum()) for lab in labs}
    girls = {lab: int(((df[scenario_col] == lab) & (df["ΦΥΛΟ"].astype(str).str.upper() == "Κ")).sum()) for lab in labs}
    return cnt, good, boys, girls

# ---------------------------- Acceptance (Σκληρά όρια) ----------------------------

def accept_step5(cnt: Dict[str,int], good: Dict[str,int], boys: Dict[str,int], girls: Dict[str,int],
                 cap: int = STEP5_CAP,
                 pop_diff_max: int = STEP5_POP_DIFF_MAX,
                 good_diff_max: int = STEP5_GOOD_DIFF_MAX,
                 gender_diff_max: int = STEP5_GENDER_DIFF_MAX) -> bool:
    """Επιστρέφει True αν το σενάριο Βήματος 5 τηρεί τα χαλαρά «σκληρά» όρια."""
    # 1) Κανένα τμήμα > cap
    if any(v > cap for v in cnt.values()):
        return False
    # 2) Εύρος πληθυσμού ≤ 4
    if cnt and (max(cnt.values()) - min(cnt.values())) > pop_diff_max:
        return False
    # 3) Δ Ν (Καλή Γνώση) ≤ 6
    if good and (max(good.values()) - min(good.values())) > good_diff_max:
        return False
    # 4) Δ φύλου (αγόρια) ≤ 6
    if boys and (max(boys.values()) - min(boys.values())) > gender_diff_max:
        return False
    # 5) Δ φύλου (κορίτσια) ≤ 6
    if girls and (max(girls.values()) - min(girls.values())) > gender_diff_max:
        return False
    return True

# ---------------------------- Penalty ----------------------------

def calculate_penalty_score(df: pd.DataFrame, scenario_col: str,
                            num_classes: Optional[int] = None) -> int:
    """
    Υπολογισμός penalty score σύμφωνα με τις οδηγίες:
    - Γνώση Ελληνικών: +1 για κάθε διαφορά > 2
    - Πληθυσμός: +1 για κάθε διαφορά > 1
    - Φύλο: +1 για κάθε διαφορά > 1 (αγόρια ή κορίτσια)
    - Σπασμένη Φιλία: +5 για κάθε σπασμένη πλήρως αμοιβαία φιλία
    """
    labs = _get_class_labels(df, scenario_col)
    if num_classes is None:
        num_classes = _auto_num_classes(df, None)

    penalty = 0

    # 1. Ισορροπία Γνώσης Ελληνικών
    greek_counts = []
    for lab in labs:
        sub = df[df[scenario_col] == lab].copy()
        greek_counts.append(int(sub.apply(_is_good_greek, axis=1).sum()))
    if greek_counts:
        greek_diff = max(greek_counts) - min(greek_counts)
        penalty += max(0, greek_diff - 2)

    # 2. Ισορροπία Πληθυσμού
    class_sizes = [int((df[scenario_col] == lab).sum()) for lab in labs]
    if class_sizes:
        pop_diff = max(class_sizes) - min(class_sizes)
        penalty += max(0, pop_diff - 1)

    # 3. Ισορροπία Φύλου
    boys_counts = [int(((df[scenario_col] == lab) &
                        (df["ΦΥΛΟ"].astype(str).str.upper() == "Α")).sum())
                   for lab in labs]
    girls_counts = [int(((df[scenario_col] == lab) &
                         (df["ΦΥΛΟ"].astype(str).str.upper() == "Κ")).sum())
                    for lab in labs]
    if boys_counts:
        penalty += max(0, (max(boys_counts) - min(boys_counts)) - 1)
    if girls_counts:
        penalty += max(0, (max(girls_counts) - min(girls_counts)) - 1)

    # 4. Σπασμένες Πλήρως Αμοιβαίες Φιλίες
    if "ΣΠΑΣΜΕΝΗ_ΦΙΛΙΑ" in df.columns:
        broken_friendships = int(df["ΣΠΑΣΜΕΝΗ_ΦΙΛΙΑ"].map(_is_yes).sum())
    else:
        broken_friendships = _count_broken_pairs(df, scenario_col)
    penalty += 5 * broken_friendships

    return penalty

# ---------------------------- Βήμα 5 ----------------------------

def step5_place_remaining_students(df: pd.DataFrame, scenario_col: str,
                                   num_classes: Optional[int] = None,
                                   enforce_acceptance: bool = True) -> Tuple[pd.DataFrame, int]:
    """
    Βήμα 5: Τοποθέτηση υπολοίπων μαθητών χωρίς (πλήρως αμοιβαίες) φιλίες.
    Κριτήρια:
    1) Τμήμα με μικρότερο πληθυσμό (<25)
    2) Προτίμηση όσων κρατούν διαφορά πληθυσμού ≤2
    3) Καλύτερη ισορροπία φύλου σε ΟΛΑ τα τμήματα

    Αν enforce_acceptance=True, εφαρμόζεται στο τέλος ο έλεγχος «σκληρών» ορίων.
    """
    df = df.copy()
    labs = _get_class_labels(df, scenario_col)
    if num_classes is None:
        num_classes = _auto_num_classes(df, None)

    friends_list = (df["ΦΙΛΟΙ"].map(_parse_list_cell) if "ΦΙΛΟΙ" in df.columns else pd.Series([[]]*len(df)))
    fully_mutual = (df["ΠΛΗΡΩΣ_ΑΜΟΙΒΑΙΑ"].map(_is_yes) if "ΠΛΗΡΩΣ_ΑΜΟΙΒΑΙΑ" in df.columns else pd.Series([False]*len(df)))
    broken_friendship = (df["ΣΠΑΣΜΕΝΗ_ΦΙΛΙΑ"].map(_is_yes) if "ΣΠΑΣΜΕΝΗ_ΦΙΛΙΑ" in df.columns else pd.Series([False]*len(df)))

    mask_step5 = (
        df[scenario_col].isna() &
        ((friends_list.map(len) == 0) | (~fully_mutual) | (broken_friendship))
    )
    remaining_students = df[mask_step5].copy()

    for _, row in remaining_students.iterrows():
        name = str(row["ΟΝΟΜΑ"]).strip()
        gender = str(row["ΦΥΛΟ"]).strip().upper()

        class_sizes = {lab: int((df[scenario_col] == lab).sum()) for lab in labs}
        min_size = min(class_sizes.values()) if class_sizes else 0
        available_classes = [lab for lab, size in class_sizes.items() if size == min_size and size < STEP5_CAP]
        if not available_classes:
            continue

        if len(available_classes) == 1:
            chosen_class = available_classes[0]
        else:
            candidates_with_pop_diff = []
            for candidate in available_classes:
                new_sizes = {lab: int((df[scenario_col] == lab).sum()) + (1 if lab == candidate else 0)
                             for lab in labs}
                pop_diff = max(new_sizes.values()) - min(new_sizes.values())
                candidates_with_pop_diff.append((candidate, pop_diff))

            preferred_pool = [c for c, d in candidates_with_pop_diff if d <= 2]
            pool = preferred_pool if preferred_pool else [c for c, _ in candidates_with_pop_diff]

            if len(pool) == 1:
                chosen_class = pool[0]
            else:
                best_score = float('inf'); best_classes = []
                for candidate in pool:
                    boys_counts, girls_counts = [], []
                    for lab in labs:
                        boys_in = int(((df[scenario_col] == lab) & (df["ΦΥΛΟ"].astype(str).str.upper() == "Α")).sum())
                        girls_in = int(((df[scenario_col] == lab) & (df["ΦΥΛΟ"].astype(str).str.upper() == "Κ")).sum())
                        if lab == candidate:
                            if gender == "Α": boys_in += 1
                            elif gender == "Κ": girls_in += 1
                        boys_counts.append(boys_in); girls_counts.append(girls_in)
                    gender_diff = (max(boys_counts) - min(boys_counts)) + (max(girls_counts) - min(girls_counts))
                    if gender_diff < best_score:
                        best_score = gender_diff; best_classes = [candidate]
                    elif gender_diff == best_score:
                        best_classes.append(candidate)
                chosen_class = random.choice(best_classes)

        df.loc[df["ΟΝΟΜΑ"] == name, scenario_col] = chosen_class

    # Υπολογισμός penalty
    score = calculate_penalty_score(df, scenario_col, num_classes)

    # Έλεγχος «σκληρών» ορίων (αν ζητηθεί)
    if enforce_acceptance:
        cnt, good, boys, girls = _collect_counters(df, scenario_col)
        if not accept_step5(cnt, good, boys, girls):
            # Σενάριο απορρίπτεται ρητά
            raise ValueError("Απόρριψη Βήματος 5: υπέρβαση ορίων (Εύρος πληθυσμού, Δ Ν ή Δ φύλου).")

    return df, score

# ---------------------------- Συγκεντρωτικές ----------------------------

def apply_step5_to_all_scenarios(scenarios_dict: Dict[str, pd.DataFrame],
                                 scenario_col: str,
                                 num_classes: Optional[int] = None) -> Tuple[pd.DataFrame, int, str]:
    """
    Εφαρμογή Βήματος 5 σε dict σεναρίων και επιλογή βέλτιστου.
    Φιλτράρει ΟΣΑ αποτυγχάνουν στα «σκληρά» όρια.
    """
    if not scenarios_dict:
        raise ValueError("Δεν δόθηκαν σενάρια προς επεξεργασία")
    results = {}
    for scenario_name, scenario_df in scenarios_dict.items():
        try:
            updated_df, score = step5_place_remaining_students(scenario_df, scenario_col, num_classes, enforce_acceptance=True)
            results[scenario_name] = {"df": updated_df, "penalty_score": score}
        except Exception as e:
            print(f"Σενάριο {scenario_name} απορρίφθηκε στο Βήμα 5: {e}")
            continue
    if not results:
        raise ValueError("Κανένα αποδεκτό σενάριο στο Βήμα 5 βάσει ορίων.")
    min_score = min(v["penalty_score"] for v in results.values())
    best_scenarios = [k for k, v in results.items() if v["penalty_score"] == min_score]
    chosen_scenario = random.choice(best_scenarios)
    return results[chosen_scenario]["df"], results[chosen_scenario]["penalty_score"], chosen_scenario

# ---------------------------- Βοηθητικά για τελική στήλη O ----------------------------

def _extract_index_from_col(col: str, fallback: int = 1) -> int:
    """Εξάγει το N από ονόματα τύπου 'ΒΗΜΑ4_ΣΕΝΑΡΙΟ_N' ή 'ΣΕΝΑΡΙΟ_N'."""
    m = re.search(r"_ΣΕΝΑΡΙΟ_(\d+)$", str(col))
    return int(m.group(1)) if m else int(fallback)

def _move_column_to_letter_O(df: pd.DataFrame, colname: str, letter: str = "O") -> pd.DataFrame:
    """
    Μετακινεί ΜΟΝΟ τη στήλη `colname` στη θέση του γράμματος `letter` (0-based index).
    A→0, B→1, ..., O→14.
    """
    if colname not in df.columns:
        return df
    target_pos = ord(letter.upper()) - ord('A')
    cols = list(df.columns)
    cols.remove(colname)
    target_pos = max(0, min(target_pos, len(cols)))
    new_cols = cols[:target_pos] + [colname] + cols[target_pos:]
    return df[new_cols]

# ---------------------------- Κύρια συνάρτηση ----------------------------

def run_step5_FINAL(df: pd.DataFrame,
                    base_col: Optional[str] = None,
                    base_prefix: str = "ΒΗΜΑ4_ΣΕΝΑΡΙΟ_",
                    out_prefix: str = "ΒΗΜΑ5_ΣΕΝΑΡΙΟ_",
                    force_letter: str = "O",
                    num_classes: Optional[int] = None,
                    enforce_acceptance: bool = True) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Τρέχει το Βήμα 5 πάνω σε μία ή περισσότερες στήλες βάσης (από Βήμα 4)
    και δημιουργεί αντίστοιχες στήλες **ΒΗΜΑ5_ΣΕΝΑΡΙΟ_N**.
    
    - Αν δοθεί `base_col`, επεξεργάζεται μόνο αυτή.
    - Αλλιώς ψάχνει όλες τις στήλες που ταιριάζουν με το `base_prefix` + N.
    - Αν προκύψει ΜΟΝΟ μία νέα στήλη, μετακινείται στη στήλη 'O'.
    - Αν enforce_acceptance=True, σενάρια που δεν τηρούν τα όρια απορρίπτονται (δεν γράφονται).

    Επιστρέφει: (updated_df, scores_dict) όπου scores_dict: {out_col: penalty_score}
    """
    df = df.copy()
    # Βρες τις στήλες βάσης
    if base_col is not None:
        base_cols = [base_col]
    else:
        base_cols = [c for c in df.columns if re.match(rf"^{re.escape(base_prefix)}\d+$", str(c))]
    if not base_cols:
        base_cols = [c for c in df.columns if re.match(r"^ΣΕΝΑΡΙΟ_\d+$", str(c))]
    if not base_cols:
        raise ValueError("Δεν βρέθηκαν στήλες βάσης σεναρίων για το Βήμα 5.")

    out_cols_made = []
    scores: Dict[str, int] = {}

    for base in base_cols:
        idx = _extract_index_from_col(base, fallback=1)
        out_col = f"{out_prefix}{idx}"

        # Δουλεύουμε σε προσωρινό df ώστε να ΜΗΝ τροποποιήσουμε την αρχική base στήλη
        working = df.copy()
        try:
            updated_df, score = step5_place_remaining_students(
                working, scenario_col=base, num_classes=num_classes, enforce_acceptance=enforce_acceptance
            )
        except Exception as e:
            # Απόρριψη σεναρίου: μην γράφεις στήλη
            print(f"Σενάριο {base} απορρίφθηκε στο Βήμα 5: {e}")
            continue

        # Γράψε αποτέλεσμα στην νέα στήλη out_col
        df[out_col] = updated_df[base]
        out_cols_made.append(out_col)
        scores[out_col] = score

    if not out_cols_made:
        raise ValueError("Κανένα αποδεκτό σενάριο στο Βήμα 5 για εγγραφή στήλης.")

    # Μετακίνησε ΜΟΝΟ αν δημιουργήθηκε μία στήλη
    if len(out_cols_made) == 1:
        df = _move_column_to_letter_O(df, out_cols_made[0], letter=force_letter)

    return df, scores

# ---------------------------- Συμβατότητα ----------------------------

def run_step5(df: pd.DataFrame) -> pd.DataFrame:
    """
    Backward-compatible wrapper: 
    - Αναζητά την ΠΡΩΤΗ στήλη που ξεκινά με 'ΣΕΝΑΡΙΟ_' και γράφει ΒΗΜΑ5_ΣΕΝΑΡΙΟ_1.
    - Μετακινεί τη νέα στήλη στη θέση 'O'.
    - Εφαρμόζει τα χαλαρά «σκληρά» όρια.
    """
    scenario_cols = [col for col in df.columns if col.startswith("ΣΕΝΑΡΙΟ_")]
    if not scenario_cols:
        raise ValueError("Δεν βρέθηκε στήλη σεναρίου (ΣΕΝΑΡΙΟ_Χ)")
    base = scenario_cols[0]
    out_df, _ = run_step5_FINAL(df, base_col=base, base_prefix="ΣΕΝΑΡΙΟ_", out_prefix="ΒΗΜΑ5_ΣΕΝΑΡΙΟ_",
                                force_letter="O", num_classes=None, enforce_acceptance=True)
    return out_df

# Compatibility alias
step5_filikoi_omades = step5_place_remaining_students

if __name__ == "__main__":
    # Δεν εκτελούμε τίποτα όταν τρέχει ως script.
    pass
