# -*- coding: utf-8 -*-
"""
Step 2 — Ζωηροί & Ιδιαιτερότητες (Fixed v3, **patched**)
- Η στήλη εξόδου του Βήματος 2 ΜΕΤΟΝΟΜΑΖΕΤΑΙ σε «ΒΗΜΑ2_ΣΕΝΑΡΙΟ_{k}»
  όπου k είναι ο αριθμός από το step1_col_name (π.χ. ΒΗΜΑ1_ΣΕΝΑΡΙΟ_2 -> k=2).
- Όλα τα υπόλοιπα παραμένουν συμβατά.
- ΠΡΟΣΘΗΚΗ: run_step2() wrapper function για pages compatibility
"""
from typing import List, Dict, Tuple, Any, Set, Optional
import pandas as pd
import random
import re

def _auto_num_classes(df, override=None):
    import math
    n = len(df)
    # Keep a safe minimum of 2 to match downstream assumptions
    k = max(2, math.ceil(n/25))
    return int(k if override is None else override)

from step_2_helpers_FIXED import (
    normalize_columns, parse_friends_cell, scope_step2, mutual_pairs_in_scope
)

RANDOM_SEED = 42
random.seed(RANDOM_SEED)


def _pair_conflict_penalty(aZ, aI, bZ, bI) -> int:
    if aI and bI:
        return 5
    if (aI and bZ) or (bI and aZ):
        return 4
    if aZ and bZ:
        return 3
    return 0


def _count_ped_conflicts(df: pd.DataFrame, col: str) -> int:
    cnt = 0
    by_class = {}
    for _, r in df.iterrows():
        cl = r.get(col)
        if pd.isna(cl):
            continue
        by_class.setdefault(str(cl), []).append(r)
    for _cl, rows in by_class.items():
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                aZ = str(rows[i].get("ΖΩΗΡΟΣ", "")).strip() == "Ν"
                aI = str(rows[i].get("ΙΔΙΑΙΤΕΡΟΤΗΤΑ", "")).strip() == "Ν"
                bZ = str(rows[j].get("ΖΩΗΡΟΣ", "")).strip() == "Ν"
                bI = str(rows[j].get("ΙΔΙΑΙΤΕΡΟΤΗΤΑ", "")).strip() == "Ν"
                if _pair_conflict_penalty(aZ, aI, bZ, bI) > 0:
                    cnt += 1
    return cnt


def _sum_conflicts(df: pd.DataFrame, col: str) -> int:
    s = 0
    by_class = {}
    for _, r in df.iterrows():
        cl = r.get(col)
        if pd.isna(cl):
            continue
        by_class.setdefault(str(cl), []).append(r)
    for _cl, rows in by_class.items():
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                aZ = str(rows[i].get("ΖΩΗΡΟΣ", "")).strip() == "Ν"
                aI = str(rows[i].get("ΙΔΙΑΙΤΕΡΟΤΗΤΑ", "")).strip() == "Ν"
                bZ = str(rows[j].get("ΖΩΗΡΟΣ", "")).strip() == "Ν"
                bI = str(rows[j].get("ΙΔΙΑΙΤΕΡΟΤΗΤΑ", "")).strip() == "Ν"
                s += _pair_conflict_penalty(aZ, aI, bZ, bI)
    return s



def _mutual_pairs_all(df: pd.DataFrame) -> list[tuple[str, str]]:
    """Return all fully mutual friendship pairs (a,b) with a<b across the whole dataframe."""
    def _split_tokens(s):
        if pd.isna(s):
            return []
        return [t.strip() for t in re.split(r"[,\n;/]+", str(s)) if t.strip()]
    friends = {}
    for _, r in df.iterrows():
        n = str(r.get("ΟΝΟΜΑ", "")).strip()
        friends[n] = set(_split_tokens(r.get("ΦΙΛΟΙ", "")))
    pairs = set()
    for a in friends:
        for b in friends[a]:
            if a != b and a in friends.get(b, set()):
                pairs.add(tuple(sorted((a, b))))
    return sorted(pairs)

def _step2_rule_broken_pairs(df: pd.DataFrame, step1_col: str, step2_col_tmp: str) -> int:
    """
    Κανόνας Βήματος 2 για «Σπασμένες_Φιλίες»:
      Σύνολο που μας απασχολεί = (ΜΗ τοποθετημένοι Ζ/Ι) ∪ (ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ == 'Ν').
      Μετράμε αμοιβαίες δυάδες (πλήρως) που ανήκουν σε αυτό το σύνολο και καταλήγουν σε διαφορετικά τμήματα, όπου:
        - για παιδί εκπ/κού παίρνουμε την τάξη από το Βήμα 1 (step1_col)
        - για μη-τοποθετημένο (Ζ/Ι) παίρνουμε την τάξη από το προσωρινό Βήμα 2 (step2_col_tmp)
    """
    is_teacher = df["ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ"].astype(str).str.strip().str.upper().eq("Ν")
    is_z = df["ΖΩΗΡΟΣ"].astype(str).str.strip().str.upper().eq("Ν")
    is_i = df["ΙΔΙΑΙΤΕΡΟΤΗΤΑ"].astype(str).str.strip().str.upper().eq("Ν")
    not_placed_step1 = df[step1_col].isna()
    in_set = (is_teacher) | (not_placed_step1 & (is_z | is_i))

    name_to_inset = dict(zip(df["ΟΝΟΜΑ"].astype(str), in_set))
    by_name = df.set_index("ΟΝΟΜΑ")

    def cls_for(name: str) -> str:
        # teacher kid => step1 class; else => step2 temp class; if missing, fall back to step1
        if name_to_inset.get(name, False) and str(by_name.at[name, "ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ"]).strip().upper() == "Ν":
            return str(by_name.at[name, step1_col]).strip()
        c2 = by_name.at[name, step2_col_tmp] if step2_col_tmp in by_name.columns else None
        c1 = by_name.at[name, step1_col]
        return str(c2 if (pd.notna(c2) and str(c2).strip()) else c1).strip()

    broken = 0
    for a, b in _mutual_pairs_all(df):
        if not (name_to_inset.get(a, False) and name_to_inset.get(b, False)):
            continue
        ca, cb = cls_for(a), cls_for(b)
        if ca and cb and ca != cb:
            broken += 1
    return int(broken)


def _broken_mutual_pairs(df: pd.DataFrame, col: str, scope: Set[str]) -> int:
    pairs = mutual_pairs_in_scope(df, scope)
    name2class = {
        str(r["ΟΝΟΜΑ"]).strip(): str(r.get(col))
        for _, r in df.iterrows()
        if pd.notna(r.get(col))
    }
    return sum(1 for a, b in pairs if name2class.get(a) != name2class.get(b))


def _compute_targets_global(
    df: pd.DataFrame, step1_col: str, class_labels: List[str]
) -> Dict[str, Dict[str, int]]:
    """
    Υπολογίζει ΤΕΛΙΚΟΥΣ στόχους για σύνολο Ζ/Ι μετά το Βήμα 2 (δηλ. step1 + to_place).
    - final_totals = Z_step1_total + Z_to_place_total (και αντίστοιχα για Ι).
    - Τελικός στόχος ανά τμήμα: q ή q+1 όπου q,r = divmod(final_total, num_classes).
    """
    Z_step1 = {cl: 0 for cl in class_labels}
    I_step1 = {cl: 0 for cl in class_labels}
    Z_total_step1 = 0
    I_total_step1 = 0
    for _, r in df.iterrows():
        cl = r.get(step1_col)
        z = str(r.get("ΖΩΗΡΟΣ", "")).strip() == "Ν"
        i = str(r.get("ΙΔΙΑΙΤΕΡΟΤΗΤΑ", "")).strip() == "Ν"
        if not pd.isna(cl):
            if z:
                Z_step1[str(cl)] += 1
                Z_total_step1 += 1
            if i:
                I_step1[str(cl)] += 1
                I_total_step1 += 1

    to_place = df[pd.isna(df[step1_col])]
    Z_to_place = int((to_place["ΖΩΗΡΟΣ"].astype(str).str.strip() == "Ν").sum())
    I_to_place = int((to_place["ΙΔΙΑΙΤΕΡΟΤΗΤΑ"].astype(str).str.strip() == "Ν").sum())

    Z_final_total = Z_total_step1 + Z_to_place
    I_final_total = I_total_step1 + I_to_place

    def _qmax(total):
        q, r = divmod(total, len(class_labels))
        return {"q": q, "max": q + (1 if r > 0 else 0)}

    return {
        "Z": _qmax(Z_final_total),
        "I": _qmax(I_final_total),
        "Z_step1": Z_step1,
        "I_step1": I_step1,
    }


def _prereject(assign_map, next_name, next_cl, df, step1_col, class_labels, targets) -> bool:
    """Γρήγορο pruning πριν από απόπειρα ανάθεσης."""
    Zc = targets["Z_step1"].copy()
    Ic = targets["I_step1"].copy()
    tmp = assign_map.copy()
    if next_name and next_cl:
        tmp[next_name] = next_cl

    # Προσωρινή καταμέτρηση Ζ/Ι αν μπει το next
    for n, cl in tmp.items():
        row = df[df["ΟΝΟΜΑ"] == n].iloc[0]
        if str(row.get("ΖΩΗΡΟΣ", "")).strip() == "Ν":
            Zc[cl] += 1
        if str(row.get("ΙΔΙΑΙΤΕΡΟΤΗΤΑ", "")).strip() == "Ν":
            Ic[cl] += 1

    # Upper bounds per targets
    for cl in class_labels:
        if Zc[cl] > targets["Z"]["max"]:
            return False
        if Ic[cl] > targets["I"]["max"]:
            return False

    # Γρήγορος έλεγχος συγκρούσεων με fixed/partial της ίδιας τάξης
    if next_name and next_cl and "ΣΥΓΚΡΟΥΣΗ" in df.columns:
        mask_next = (df["ΟΝΟΜΑ"] == next_name)
        next_conf_cell = df.loc[mask_next, "ΣΥΓΚΡΟΥΣΗ"]
        toks_next = set(parse_friends_cell(next_conf_cell.values[0] if not next_conf_cell.empty else ""))

        fixed_same = df[(pd.notna(df[step1_col])) & (df[step1_col] == next_cl)]
        if any((n in toks_next) for n in fixed_same["ΟΝΟΜΑ"].astype(str).tolist()):
            return False

        for n2, cl2 in tmp.items():
            if cl2 != next_cl:
                continue
            mask_n2 = (df["ΟΝΟΜΑ"] == n2)
            n2_conf_cell = df.loc[mask_n2, "ΣΥΓΚΡΟΥΣΗ"]
            toks2 = set(parse_friends_cell(n2_conf_cell.values[0] if not n2_conf_cell.empty else ""))
            if (next_name in toks2) or (n2 in toks_next):
                return False
    return True


def _extract_step1_id(step1_col_name: str) -> int:
    """
    Επιστρέφει τον αριθμό k από «ΒΗΜΑ1_ΣΕΝΑΡΙΟ_k» ή «V1_ΣΕΝΑΡΙΟ_k».
    Αν δεν βρεθεί, επιστρέφει 1.
    """
    m = re.search(r'(?:ΒΗΜΑ1_|V1_)ΣΕΝΑΡΙΟ[_\s]*(\d+)', str(step1_col_name))
    if not m:
        return 1
    return int(m.group(1))


def step2_apply_FIXED_v3(
    df_in: pd.DataFrame,
    step1_col_name: str,
    num_classes: Optional[int] = None,
    *,
    seed: int = 42,
    max_results: int = 5,
) -> List[Tuple[str, pd.DataFrame, Dict[str, Any]]]:
    """
    Επιστρέφει έως max_results σενάρια ως (label, DataFrame, metrics).
    Το DataFrame περιέχει στήλες εισόδου + «ΒΗΜΑ2_ΣΕΝΑΡΙΟ_{k}» όπου k = id του ΒΗΜΑ1_ΣΕΝΑΡΙΟ_k.
    """
    random.seed(seed)
    df = normalize_columns(df_in).copy()
    num_classes = _auto_num_classes(df, num_classes)
    class_labels = [f"Α{i+1}" for i in range(num_classes)]
    scope = scope_step2(df, step1_col=step1_col_name)

    # Μόνο Ζ/Ι προς τοποθέτηση
    to_place = df[(pd.isna(df[step1_col_name])) & ((df["ΖΩΗΡΟΣ"] == "Ν") | (df["ΙΔΙΑΙΤΕΡΟΤΗΤΑ"] == "Ν"))]["ΟΝΟΜΑ"].astype(str).tolist()
    targets = _compute_targets_global(df, step1_col=step1_col_name, class_labels=class_labels)

    best: List[Tuple[pd.DataFrame, int, int, int, int]] = []
    assign: Dict[str, str] = {}

    # Σειρά δυσκολίας
    def deg(name: str) -> int:
        row = df[df["ΟΝΟΜΑ"] == name].iloc[0]
        return len(parse_friends_cell(row.get("ΣΥΓΚΡΟΥΣΗ", ""))) + len(parse_friends_cell(row.get("ΦΙΛΟΙ", "")))

    to_place_sorted = sorted(
        to_place,
        key=lambda n: (
            -(
                str(df.loc[df["ΟΝΟΜΑ"] == n, "ΖΩΗΡΟΣ"].values[0]).strip() == "Ν"
                and str(df.loc[df["ΟΝΟΜΑ"] == n, "ΙΔΙΑΙΤΕΡΟΤΗΤΑ"].values[0]).strip() == "Ν"
            ),
            -(str(df.loc[df["ΟΝΟΜΑ"] == n, "ΙΔΙΑΙΤΕΡΟΤΗΤΑ"].values[0]).strip() == "Ν"),
            -(str(df.loc[df["ΟΝΟΜΑ"] == n, "ΖΩΗΡΟΣ"].values[0]).strip() == "Ν"),
            -deg(n),
        ),
    )

    def backtrack(i: int) -> None:
        if i == len(to_place_sorted):
            cand = df.copy()
            cand_col = "ΒΗΜΑ2_TMP"
            cand[cand_col] = cand[step1_col_name]
            for n, cl in assign.items():
                cand.loc[cand["ΟΝΟΜΑ"] == n, cand_col] = cl

            # reject "όλοι στην ίδια τάξη"
            counts_new = {cl: 0 for cl in class_labels}
            for cl in assign.values():
                counts_new[cl] += 1
            if sum(counts_new.values()) > 0 and max(counts_new.values()) == sum(counts_new.values()):
                return

            # έλεγχος στόχων Ζ/Ι
            Zc = targets["Z_step1"].copy()
            Ic = targets["I_step1"].copy()
            for n, cl in assign.items():
                row = df[df["ΟΝΟΜΑ"] == n].iloc[0]
                if str(row.get("ΖΩΗΡΟΣ", "")).strip() == "Ν":
                    Zc[cl] += 1
                if str(row.get("ΙΔΙΑΙΤΕΡΟΤΗΤΑ", "")).strip() == "Ν":
                    Ic[cl] += 1
            for cl in class_labels:
                if not (targets["Z"]["q"] <= Zc[cl] <= targets["Z"]["max"]):
                    return
                if not (targets["I"]["q"] <= Ic[cl] <= targets["I"]["max"]):
                    return

            ped_cnt = _count_ped_conflicts(cand, cand_col)
            conf_sum = _sum_conflicts(cand, cand_col)
            broken = _step2_rule_broken_pairs(cand, step1_col_name, cand_col)
            total = conf_sum + 5 * broken
            best.append((cand, ped_cnt, broken, total, conf_sum))
            return

        name = to_place_sorted[i]
        for cl in class_labels:
            if not _prereject(assign, name, cl, df, step1_col_name, class_labels, targets):
                continue
            assign[name] = cl
            backtrack(i + 1)
            del assign[name]

    backtrack(0)

    # Αν δεν βρέθηκε τίποτα, «pass-through»
    if not best:
        tmp = df.copy()
        # Στήλη Β2: να πάρει id από το step1_col_name
        base_id = _extract_step1_id(step1_col_name)
        tmp[f"ΒΗΜΑ2_ΣΕΝΑΡΙΟ_{base_id}"] = tmp[step1_col_name]
        return [("option_1", tmp, {"ped_conflicts": None, "broken": None, "penalty": None})]

    # --- Επιλογή σεναρίων ---
    zero_ped = [x for x in best if x[1] == 0]
    selected = []

    # Για ρητή ορολογία «διατηρημένες φιλίες», υπολογίζουμε το σταθερό πλήθος συνολικών αμοιβαίων
    total_pairs = len(mutual_pairs_in_scope(df, scope))

    if zero_ped:
        # 1) λιγότερα broken
        min_broken = min(x[2] for x in zero_ped)
        tier1 = [x for x in zero_ped if x[2] == min_broken]
        # 2) χαμηλότερο συνολικό penalty
        min_total = min(x[3] for x in tier1)
        tier2 = [x for x in tier1 if x[3] == min_total]
        # 3) τυχαία αν > max_results
        if len(tier2) > max_results:
            random.shuffle(tier2)
            tier2 = tier2[:max_results]
        selected = tier2
    else:
        # ΌΛΑ έχουν παιδαγωγικές συγκρούσεις (Υποχρεωτική Τοποθέτηση)
        # 1) μικρότερο συνολικό penalty
        min_total = min(x[3] for x in best)
        tier1 = [x for x in best if x[3] == min_total]
        # 2) ΠΕΡΙΣΣΟΤΕΡΕΣ διατηρημένες φιλίες  ==  (total_pairs - broken) μέγιστο
        max_preserved = max(total_pairs - x[2] for x in tier1)
        tier2 = [x for x in tier1 if (total_pairs - x[2]) == max_preserved]
        # 3) τυχαία αν > max_results
        if len(tier2) > max_results:
            random.shuffle(tier2)
            tier2 = tier2[:max_results]
        selected = tier2

    # --- Κατασκευή αποτελεσμάτων ---
    results: List[Tuple[str, pd.DataFrame, Dict[str, Any]]] = []
    base_id = _extract_step1_id(step1_col_name)
    for k, (cand, ped_cnt, broken, total, conf_sum) in enumerate(selected, start=1):
        out = cand.copy()
        # ΠΑΝΤΑ οριστικοποιούμε τη στήλη ως «ΒΗΜΑ2_ΣΕΝΑΡΙΟ_{base_id}»
        final_col = f"ΒΗΜΑ2_ΣΕΝΑΡΙΟ_{base_id}"
        out[final_col] = out["ΒΗΜΑ2_TMP"]
        out.drop(columns=["ΒΗΜΑ2_TMP"], inplace=True)
        results.append(
            (
                f"option_{k}",
                out,
                {"ped_conflicts": int(ped_cnt), "broken": int(broken), "penalty": int(total)},
            )
        )
    return results


# =============================================================================
# WRAPPER FUNCTION ΓΙΑ PAGES COMPATIBILITY 
# =============================================================================

def run_step2(df: pd.DataFrame, step1_col: str = None, num_classes: int = 2) -> Dict[str, Any]:
    """
    Wrapper function για Βήμα 2 - Ζωηροί & Ιδιαιτερότητες
    Καλείται από το page2_vimata.py για compatibility με την υπάρχουσα δομή.
    
    Args:
        df: DataFrame από βήμα 1
        step1_col: Στήλη αποτελεσμάτων βήματος 1
        num_classes: Αριθμός τμημάτων
        
    Returns:
        Dict με "df", "scenarios", "meta"
    """
    try:
        # Auto-detect step1 column αν δεν δόθηκε
        if step1_col is None:
            step1_cols = [col for col in df.columns if col.startswith('ΒΗΜΑ1_ΣΕΝΑΡΙΟ_')]
            if step1_cols:
                step1_col = step1_cols[0]
            else:
                raise ValueError("Δεν βρέθηκε στήλη βήματος 1")
        
        # Κλήση κύριας function
        scenarios = step2_apply_FIXED_v3(
            df, 
            step1_col_name=step1_col,
            num_classes=num_classes,
            max_results=5
        )
        
        if not scenarios:
            return {
                "df": df,
                "scenarios": {},
                "meta": {"step": 2, "error": "Δεν βρέθηκαν σενάρια"}
            }
        
        # Παίρνουμε το καλύτερο σενάριο
        best_scenario_name, best_df, best_metrics = scenarios[0]
        
        # Format για compatibility με pages
        return {
            "df": best_df,
            "scenarios": {
                "total_scenarios": len(scenarios),
                "best_scenario": best_scenario_name,
                "ped_conflicts": best_metrics.get("ped_conflicts", 0),
                "broken_friendships": best_metrics.get("broken", 0),
                "penalty_score": best_metrics.get("penalty", 0)
            },
            "meta": {
                "step": 2,
                "description": "Ζωηροί & Ιδιαιτερότητες",
                "step1_column": step1_col,
                "all_scenarios": len(scenarios)
            }
        }
        
    except Exception as e:
        return {
            "df": df,
            "scenarios": {},
            "meta": {"step": 2, "error": str(e)}
        }


if __name__ == "__main__":
    print("Step 2 Module - Έτοιμο για import")
    print("Core function: step2_apply_FIXED_v3()")
    print("Wrapper function: run_step2() για pages compatibility")

# =============================================================================
# Exporter: "Νέα" Excel εξαγωγή για Βήμα 2 (ένα φύλλο ανά σενάριο)
# =============================================================================
def _letter_to_idx(letter: str) -> int:
    letter = str(letter).strip().upper()
    v = 0
    for ch in letter:
        if "A" <= ch <= "Z":
            v = v*26 + (ord(ch) - ord("A") + 1)
    return max(0, v-1)

def _reorder_with_targets(df: pd.DataFrame, base_first: list, step2_col: str, final_col: str or None,
                          place_step2_at="L", place_final_at="M") -> pd.DataFrame:
    base_present = [c for c in base_first if c in df.columns]
    others = [c for c in df.columns if c not in base_present and c != step2_col and c != final_col]
    ordered = base_present + others
    idxL = min(max(0, _letter_to_idx(place_step2_at)), len(ordered))
    if step2_col in df.columns:
        ordered.insert(idxL, step2_col)
    if final_col and final_col in df.columns:
        idxM = min(max(0, _letter_to_idx(place_final_at)), len(ordered))
        ordered.insert(idxM, final_col)
    seen = set()
    final = []
    for c in ordered:
        if c not in seen:
            final.append(c)
            seen.add(c)
    return df[final].copy()

def _drop_positions(df: pd.DataFrame, letters: list) -> pd.DataFrame:
    to_drop = []
    for L in letters:
        idx = _letter_to_idx(L)
        if idx < len(df.columns):
            to_drop.append(df.columns[idx])
    return df.drop(columns=to_drop, errors="ignore")

def _move_src_letter_to_dst_letter_then_drop(df: pd.DataFrame, src_letter: str, dst_letter: str, drop_letters: list) -> pd.DataFrame:
    def name_by_letter(df0, L):
        idx = _letter_to_idx(L)
        return df0.columns[idx] if idx < len(df0.columns) else None
    name_src = name_by_letter(df, src_letter)
    new_order = []
    for i, c in enumerate(df.columns):
        if i == _letter_to_idx(dst_letter):
            if name_src is not None:
                new_order.append(name_src)
            continue
        if c in [name_by_letter(df, L) for L in drop_letters]:
            continue
        new_order.append(c)
    seen = set()
    final_cols = []
    for c in new_order:
        if c not in seen:
            final_cols.append(c)
            seen.add(c)
    return df[final_cols].copy()

def export_step2_per_scenario_only(df_step1: pd.DataFrame,
                                   output_file: str = "VIMA2_PER_SCENARIO_ONLY_FINAL.xlsx",
                                   place_step2_at: str = "L",
                                   place_final_at: str = "M",
                                   apply_sheet_rules: bool = True,
                                   num_classes: int = 2) -> str:
    from step2_finalize import finalize_step2_assignments
    step1_cols = [c for c in df_step1.columns if str(c).startswith("ΒΗΜΑ1_ΣΕΝΑΡΙΟ_")]
    if not step1_cols:
        raise ValueError("Δεν βρέθηκαν στήλες 'ΒΗΜΑ1_ΣΕΝΑΡΙΟ_' στο df_step1.")
    base_cols = ['ΟΝΟΜΑ','ΦΥΛΟ','ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ','ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ','ΖΩΗΡΟΣ','ΙΔΙΑΙΤΕΡΟΤΗΤΑ','ΦΙΛΟΙ','ΣΥΓΚΡΟΥΣΗ']
    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        for step1_col in step1_cols:
            sid = _extract_step1_id(step1_col)
            scenarios = step2_apply_FIXED_v3(
                df_step1,
                step1_col_name=step1_col,
                num_classes=num_classes,
                max_results=5
            )
            if not scenarios:
                continue
            best_name, best_df, best_metrics = scenarios[0]
            step2_cols = [c for c in best_df.columns if str(c).startswith("ΒΗΜΑ2_ΣΕΝΑΡΙΟ_")]
            step2_col = None
            for c in step2_cols:
                if _extract_step1_id(c) == sid:
                    step2_col = c
                    break
            if step2_col is None and step2_cols:
                step2_col = step2_cols[0]
            final_df, stats = finalize_step2_assignments(best_df, step2_col)
            final_cols = [c for c in final_df.columns if str(c).startswith("ΤΕΛΙΚΟ_ΤΜΗΜΑ_ΣΕΝΑΡΙΟ_") and _extract_step1_id(c)==sid]
            final_col = final_cols[0] if final_cols else None
            df_out = _reorder_with_targets(final_df, base_cols, step2_col, final_col,
                                           place_step2_at=place_step2_at, place_final_at=place_final_at)
            if apply_sheet_rules:
                if sid == 1:
                    df_out = _drop_positions(df_out, ["M","N","O"])
                elif sid == 2:
                    df_out = _move_src_letter_to_dst_letter_then_drop(df_out, src_letter="N", dst_letter="K", drop_letters=["K","M","O"])
                elif sid == 3:
                    df_out = _move_src_letter_to_dst_letter_then_drop(df_out, src_letter="O", dst_letter="K", drop_letters=["K","M","N"])
            df_out.to_excel(writer, index=False, sheet_name=f"S{sid}")
    return output_file
