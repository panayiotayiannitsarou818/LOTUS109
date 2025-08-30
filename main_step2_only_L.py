
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# main_step2_only_L.py (updated to KL)
# ------------------------------------
# Runner για το Βήμα 2 που δουλεύει με το υπάρχον step2.py και εξάγει:
# - **Στήλη K** = ΒΗΜΑ1_ΣΕΝΑΡΙΟ_N
# - **Στήλη L** = ΒΗΜΑ2_ΣΕΝΑΡΙΟ_N
# - Ένα **ξεχωριστό φύλλο** ανά σενάριο (S1, S2, ...) σε ενιαίο workbook,
#   καθώς και ατομικά αρχεία ανά σενάριο.
#
# Παραμένει συμβατό με παλιές κλήσεις/ονόματα.

from __future__ import annotations

import argparse
import os
import re
import pandas as pd

# Εσωτερικές εισαγωγές
import importlib.util
import sys
sys.path.append("/mnt/data")  # προσαρμογή για το τρέχον περιβάλλον

def _import_from_path(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

# Προσαρμόστε τα paths αν χρειάζεται
STEP2_PATH = os.path.join(os.path.dirname(__file__), "step2.py")
EXPORT_PATH = os.path.join(os.path.dirname(__file__), "step2_export_only_L.py")

step2 = _import_from_path("step2", STEP2_PATH)
exporter = _import_from_path("step2_export_only_L", EXPORT_PATH)

def _sid(c: str) -> int:
    m = re.search(r"ΣΕΝΑΡΙΟ[_\s]*(\d+)", str(c))
    return int(m.group(1)) if m else 0

def run_step2_with_lock(input_step1_workbook: str, outdir: str, num_classes: int = 2, combine: bool = True):
    """
    Διαβάζει το workbook του Βήματος 1 (με τις στήλες ΒΗΜΑ1_ΣΕΝΑΡΙΟ_*),
    τρέχει το Βήμα 2 για ΚΑΘΕ σενάριο και εξάγει αρχεία όπου:
    - K=ΒΗΜΑ1_ΣΕΝΑΡΙΟ_N
    - L=ΒΗΜΑ2_ΣΕΝΑΡΙΟ_N
    - Ένα φύλλο/σενάριο σε ένα ενιαίο workbook
    """
    os.makedirs(outdir, exist_ok=True)

    df_step1 = pd.read_excel(input_step1_workbook)
    step1_cols = [c for c in df_step1.columns if str(c).startswith("ΒΗΜΑ1_ΣΕΝΑΡΙΟ_")]
    step1_cols = sorted(step1_cols, key=_sid)

    per_scenario_outputs = []
    dfs_for_combined = {}

    for col in step1_cols:
        sid = _sid(col)

        results = step2.step2_apply_FIXED_v3(df_step1, step1_col_name=col, num_classes=num_classes, max_results=5)
        if not results:
            # pass-through (αν δεν επιστρέψει σενάρια)
            best_name, best_df, best_metrics = ("option_1", df_step1.copy(), {"penalty": None})
            # Βεβαιώσου ότι υπάρχει ένα ΒΗΜΑ2_ΣΕΝΑΡΙΟ_N (copy από ΒΗΜΑ1)
            s2_col = f"ΒΗΜΑ2_ΣΕΝΑΡΙΟ_{sid}"
            best_df[s2_col] = best_df[col]
        else:
            best_name, best_df, best_metrics = results[0]
            # Βρες την ακριβή στήλη ΒΗΜΑ2_ΣΕΝΑΡΙΟ_N
            s2_candidates = [c for c in best_df.columns if str(c).startswith("ΒΗΜΑ2_ΣΕΝΑΡΙΟ_")]
            s2_col = None
            for c in s2_candidates:
                if f"_{sid}" in str(c):
                    s2_col = c
                    break
            if s2_col is None:
                s2_col = s2_candidates[0] if s2_candidates else f"ΒΗΜΑ2_ΣΕΝΑΡΙΟ_{sid}"
                if s2_col not in best_df.columns:
                    best_df[s2_col] = best_df[col]

        # Εξαγωγή ατομικού αρχείου
        out_file = os.path.join(outdir, f"VIMA2_S{sid}_KL.xlsx")
        exporter.export_step2_KL(best_df, out_file, step1_col_name=col, step2_col_name=s2_col, sheet_name=f"S{sid}")
        per_scenario_outputs.append(out_file)

        # Συγκέντρωση για combined
        dfs_for_combined[sid] = (best_df, col, s2_col)

    # Ενιαίο workbook με ένα φύλλο ανά σενάριο
    combined_path = os.path.join(outdir, "VIMA2_ALL_SCENARIOS_KL.xlsx")
    exporter.export_step2_sheets_KL(dfs_for_combined, combined_path)

    return {
        "input": input_step1_workbook,
        "outputs": per_scenario_outputs,
        "combined": combined_path,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Workbook Βήματος 1 (π.χ. ΒΗΜΑ1_IMMUTABLE.xlsx)")
    ap.add_argument("--outdir", required=True, help="Φάκελος εξόδου")
    ap.add_argument("--num-classes", type=int, default=2)
    ap.add_argument("--combine", action="store_true", help="(ignored, πάντα TRUE στο νέο exporter)")
    args = ap.parse_args()

    info = run_step2_with_lock(args.input, args.outdir, num_classes=args.num_classes, combine=True)
    print("OK")
    print("Input:", info["input"])
    print("Outputs:")
    for p in info["outputs"]:
        print(" -", p)
    print("Combined:", info["combined"])

if __name__ == "__main__":
    main()
