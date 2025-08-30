# -*- coding: utf-8 -*-
# step2_export_only_L_FIXED.py
# Version: 2025-08-29
# Διορθώσεις που περιέχονται:
# 1) ΕΓΓΥΗΣΗ θέσεων: K = ΒΗΜΑ1_ΣΕΝΑΡΙΟ_N, L = ΒΗΜΑ2_ΣΕΝΑΡΙΟ_N (με padding/fillers όπου χρειάζεται)
# 2) Multi-sheet export: δημιουργεί ΚΑΙ sheet «ΣΠΑΣΜΕΝΕΣ_ΦΙΛΙΕΣ_ΒΗΜΑ2» (ανά S{sid})
# 3) Συμβατότητα: export_step2_only_L(...) παραμένει ως alias προς το νέο export (με K/L εγγυήσεις)
#
# Χρήση:
#   import step2_export_only_L_FIXED as exporter
#   exporter.export_step2_KL(df, "out.xlsx", step1_col_name="ΒΗΜΑ1_ΣΕΝΑΡΙΟ_3", step2_col_name="ΒΗΜΑ2_ΣΕΝΑΡΙΟ_3")
#   exporter.export_step2_sheets_KL({3: (df, "ΒΗΜΑ1_ΣΕΝΑΡΙΟ_3", "ΒΗΜΑ2_ΣΕΝΑΡΙΟ_3")}, "out_multi.xlsx")

from __future__ import annotations

import re
import numpy as np
import pandas as pd

# --- Προσπάθεια import helpers, αλλιώς ασφαλές fallback ---
try:
    from step_2_helpers_FIXED import mutual_pairs_in_scope, scope_step2
except Exception:
    import ast
    import pandas as _pd
    import re as _re
    SAFE_SEP = _re.compile(r"[,\|\;/·\n]+")

    def _parse_friends_cell(x):
        if isinstance(x, list):
            return [str(s).strip() for s in x if str(s).strip()]
        if _pd.isna(x):
            return []
        s = str(x).strip()
        if not s:
            return []
        try:
            v = ast.literal_eval(s)
            if isinstance(v, list):
                return [str(t).strip() for t in v if str(t).strip()]
        except Exception:
            pass
        parts = SAFE_SEP.split(s)
        return [p.strip() for p in parts if p.strip() and p.strip().lower() != "nan"]

    def _are_mutual_friends(df: _pd.DataFrame, a: str, b: str) -> bool:
        ra = df[df["ΟΝΟΜΑ"].astype(str) == str(a)]
        rb = df[df["ΟΝΟΜΑ"].astype(str) == str(b)]
        if ra.empty or rb.empty:
            return False
        fa = set(_parse_friends_cell(ra.iloc[0].get("ΦΙΛΟΙ", "")))
        fb = set(_parse_friends_cell(rb.iloc[0].get("ΦΙΛΟΙ", "")))
        return (str(b).strip() in fa) and (str(a).strip() in fb)

    def scope_step2(df: _pd.DataFrame, step1_col: str):
        s = set()
        for _, r in df.iterrows():
            placed = _pd.notna(r.get(step1_col))
            z = str(r.get("ΖΩΗΡΟΣ", "")).strip() == "Ν"
            i = str(r.get("ΙΔΙΑΙΤΕΡΟΤΗΤΑ", "")).strip() == "Ν"
            pk = str(r.get("ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ", "")).strip() == "Ν"
            if (not placed and (z or i)) or (placed and pk):
                s.add(str(r.get("ΟΝΟΜΑ", "")).strip())
        return s

    def mutual_pairs_in_scope(df: _pd.DataFrame, scope):
        scope = {str(x).strip() for x in scope if str(x).strip()}
        pairs = []
        names = sorted(scope)
        for i, a in enumerate(names):
            for b in names[i + 1 :]:
                if _are_mutual_friends(df, a, b):
                    pairs.append((a, b))
        return pairs

# --- Utilities ---
def _scenario_id_from_col(col_name: str) -> int | None:
    m = re.search(r"ΣΕΝΑΡΙΟ[_\s]*(\d+)", str(col_name))
    return int(m.group(1)) if m else None

def _ensure_KL_positions(df: pd.DataFrame, step1_col_name: str, step2_col_name: str) -> pd.DataFrame:
    """
    Διασφαλίζει ότι:
    - Υπάρχουν στήλες ΒΗΜΑ1_ΣΕΝΑΡΙΟ_{sid} & ΒΗΜΑ2_ΣΕΝΑΡΙΟ_{sid} με αυτά ακριβώς τα ονόματα
    - Βρίσκονται στις θέσεις K (index 10) και L (index 11) αντίστοιχα
    - Γίνεται padding με fillers αν λείπουν στήλες πριν από την K
    """
    df2 = df.copy()

    sid = _scenario_id_from_col(step1_col_name) or _scenario_id_from_col(step2_col_name)
    if sid is None:
        for c in df2.columns:
            sid = _scenario_id_from_col(c)
            if sid is not None:
                break

    s1_target = f"ΒΗΜΑ1_ΣΕΝΑΡΙΟ_{sid}"
    s2_target = f"ΒΗΜΑ2_ΣΕΝΑΡΙΟ_{sid}"

    # Δημιουργία/μετονομασία στόχων
    if step1_col_name != s1_target:
        df2[s1_target] = df2[step1_col_name]
    if step2_col_name != s2_target:
        df2[s2_target] = df2[step2_col_name]

    # Καθαρισμός άλλων παρόμοιων στηλών
    to_drop = [c for c in df2.columns
               if (str(c).startswith("ΒΗΜΑ1_ΣΕΝΑΡΙΟ_") and c != s1_target)
               or (str(c).startswith("ΒΗΜΑ2_ΣΕΝΑΡΙΟ_") and c != s2_target)]
    if to_drop:
        df2 = df2.drop(columns=to_drop)

    # Αναδιάταξη ώστε οι στήλες-στόχοι να κάτσουν σε K/L
    cols = [c for c in df2.columns if c not in (s1_target, s2_target)]

    # Fillers μέχρι να υπάρξουν τουλάχιστον 10 στήλες πριν από K
    while len(cols) < 10:
        filler = f"_FILLER_{len(cols)}"
        df2[filler] = np.nan
        cols.append(filler)

    cols = cols[:10] + [s1_target, s2_target] + cols[10:]
    df2 = df2.reindex(columns=cols)
    return df2

def _count_broken_pairs(df: pd.DataFrame, step1_col_name: str, step2_col_name: str) -> int:
    """
    Υπολογίζει αριθμό «σπασμένων» πλήρως αμοιβαίων ΔΥΑΔΩΝ στο scope του Βήματος 2,
    με βάση την τοποθέτηση της στήλης ΒΗΜΑ2_ΣΕΝΑΡΙΟ_N (ή όποια δοθεί ως step2_col_name).
    """
    scope = scope_step2(df, step1_col=step1_col_name)
    pairs = mutual_pairs_in_scope(df, scope)
    name2class = {
        str(r["ΟΝΟΜΑ"]).strip(): str(r.get(step2_col_name))
        for _, r in df.iterrows()
        if pd.notna(r.get(step2_col_name))
    }
    broken = sum(1 for a, b in pairs if name2class.get(a) != name2class.get(b))
    return int(broken)

# --- Public API ---
def export_step2_KL(df: pd.DataFrame, output_file: str, step1_col_name: str, step2_col_name: str, sheet_name: str = "SCENARIO") -> str:
    """
    Εξαγωγή ΜΟΝΟ-φύλλου με εγγυημένες στήλες:
    - K = ΒΗΜΑ1_ΣΕΝΑΡΙΟ_N
    - L = ΒΗΜΑ2_ΣΕΝΑΡΙΟ_N
    """
    out = _ensure_KL_positions(df, step1_col_name=step1_col_name, step2_col_name=step2_col_name)
    with pd.ExcelWriter(output_file, engine="openpyxl") as wr:
        out.to_excel(wr, index=False, sheet_name=sheet_name)
    return output_file

def export_step2_sheets_KL(dfs_by_sid: dict[int, tuple[pd.DataFrame, str, str]], output_file: str) -> str:
    """
    Εξαγωγή ΠΟΛΥ-φύλλου (ένα ανά sid) ΚΑΙ σύνοψης:
    - Για κάθε sid γράφει sheet S{sid} με εγγυήσεις K/L.
    - Δημιουργεί sheet «ΣΠΑΣΜΕΝΕΣ_ΦΙΛΙΕΣ_ΒΗΜΑ2» με {ΣΕΝΑΡΙΟ, ΣΠΑΣΜΕΝΕΣ_ΦΙΛΙΕΣ}.
    """
    summary_rows = []
    with pd.ExcelWriter(output_file, engine="openpyxl") as wr:
        for sid, (df, s1_col, s2_col) in sorted(dfs_by_sid.items(), key=lambda kv: kv[0]):
            out = _ensure_KL_positions(df, s1_col, s2_col)
            sheet_name = f"S{sid}"
            out.to_excel(wr, index=False, sheet_name=sheet_name)

            # Σύνοψη «σπασμένων» για το sid
            try:
                broken = _count_broken_pairs(df, s1_col, s2_col)
            except Exception:
                broken = 0
            summary_rows.append({"ΣΕΝΑΡΙΟ": sheet_name, "ΣΠΑΣΜΕΝΕΣ_ΦΙΛΙΕΣ": int(broken)})

        if summary_rows:
            pd.DataFrame(summary_rows).to_excel(wr, index=False, sheet_name="ΣΠΑΣΜΕΝΕΣ_ΦΙΛΙΕΣ_ΒΗΜΑ2")
    return output_file

# Συμβατότητα με παλαιό όνομα
def export_step2_only_L(df: pd.DataFrame, output_file: str, step1_col_name: str | None = None, step2_col_name: str | None = None, sheet_name: str = "SCENARIO") -> str:
    """
    Παλαιά συνάρτηση (alias). Πλέον επιβάλλει ΚΑΙ K/L.
    """
    if step1_col_name is None:
        s1s = [c for c in df.columns if str(c).startswith("ΒΗΜΑ1_ΣΕΝΑΡΙΟ_")]
        step1_col_name = s1s[0] if s1s else None
    if step2_col_name is None:
        s2s = [c for c in df.columns if str(c).startswith("ΒΗΜΑ2_ΣΕΝΑΡΙΟ_")]
        step2_col_name = s2s[0] if s2s else None
    if not step1_col_name or not step2_col_name:
        raise ValueError("Δώσε step1_col_name και step2_col_name ή βεβαιώσου ότι υπάρχουν στήλες ΒΗΜΑ1_ΣΕΝΑΡΙΟ_* / ΒΗΜΑ2_ΣΕΝΑΡΙΟ_* στο DataFrame.")
    return export_step2_KL(df, output_file, step1_col_name=step1_col_name, step2_col_name=step2_col_name, sheet_name=sheet_name)


def _count_broken_pairs(df: pd.DataFrame, step1_col_name: str, step2_col_name: str) -> int:
    """
    ΕΠΙΣΤΡΕΦΕΙ ΤΟ ΣΥΝΟΛΟ «Σπασμένων» πλήρως αμοιβαίων ΔΥΑΔΩΝ από ΒΗΜΑ 1 + ΒΗΜΑ 2.
    - Βήμα 1: αμοιβαίες δυάδες μεταξύ παιδιών εκπαιδευτικών (ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ=='Ν')
      που έχουν τάξη στο step1_col_name και ΔΙΑΦΟΡΕΤΙΚΕΣ τάξεις -> σπασμένες (μετρώνται 1 φορά ανά ζεύγος).
    - Βήμα 2 (όπως ορίζει ο κανόνας του Βήματος 2):
      Scope = (μη τοποθετημένοι Ζ/Ι) ∪ (ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ == 'Ν').
      Για κάθε αμοιβαία δυάδα (a,b) στο scope:
        * Παιδί εκπ/κού -> τάξη από Βήμα 1 (step1_col_name)
        * Μη-τοποθετημένος (Ζ/Ι) -> τάξη από Βήμα 2 (step2_col_name)
      Αν οι τάξεις διαφέρουν -> «σπασμένη».
    Επιστρέφεται: broken_step1 + broken_step2.
    """
    # --- helpers ---
    def yn(v): 
        return str(v).strip().upper() == "Ν"

    by_name = df.set_index("ΟΝΟΜΑ", drop=False)

    def cls_from_step1(name: str) -> str:
        if name not in by_name.index: 
            return ""
        c1 = by_name.loc[name].get(step1_col_name)
        return str(c1).strip() if pd.notna(c1) else ""

    def cls_from_step2(name: str) -> str:
        if name not in by_name.index: 
            return ""
        c2 = by_name.loc[name].get(step2_col_name)
        return str(c2).strip() if pd.notna(c2) else ""

    # ------------------
    # Part A: Broken pairs from STEP 1 (teacher-kids only)
    # ------------------
    teacher_scope = [n for n, row in by_name.iterrows() if yn(row.get("ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ", "")) and pd.notna(row.get(step1_col_name))]
    teacher_pairs = mutual_pairs_in_scope(df, teacher_scope)
    broken_step1 = 0
    for a, b in teacher_pairs:
        ca, cb = cls_from_step1(a), cls_from_step1(b)
        if ca and cb and ca != cb:
            broken_step1 += 1

    # ------------------
    # Part B: Broken pairs from STEP 2 scope (teacher-kids + unplaced Z/I)
    # ------------------
    scope = scope_step2(df, step1_col=step1_col_name)
    pairs = mutual_pairs_in_scope(df, scope)

    def cls_for_step2_rule(name: str) -> str:
        if name not in by_name.index:
            return ""
        row = by_name.loc[name]
        # Teacher kid -> class from Step 1
        if yn(row.get("ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ", "")):
            return cls_from_step1(name)
        # Not placed in Step 1 (Z/I) -> class from Step 2
        if pd.isna(row.get(step1_col_name)):
            return cls_from_step2(name)
        # Fallbacks: prefer Step 2 then Step 1
        c2 = cls_from_step2(name)
        if c2:
            return c2
        return cls_from_step1(name)

    broken_step2 = 0
    for a, b in pairs:
        ca, cb = cls_for_step2_rule(a), cls_for_step2_rule(b)
        if ca and cb and ca != cb:
            broken_step2 += 1

    # Σύνολο που ζητάς να αποτυπώνεται στη σύνοψη Βήματος 2
    return int(broken_step1 + broken_step2)
