
import pandas as pd
import numpy as np
import re
import argparse

MAX_CLASS_SIZE = 25

def parse_friends(cell):
    if pd.isna(cell):
        return set()
    parts = re.split(r'[,\n;|/]+', str(cell))
    return {p.strip() for p in parts if p.strip()}

def build_mutual_dyads(df, name_col='ΟΝΟΜΑ', friends_col='ΦΙΛΟΙ'):
    friend_map = {row[name_col]: parse_friends(row[friends_col]) for _, row in df.iterrows()}
    names = set(friend_map.keys())
    dyads = set()
    for a in names:
        for b in friend_map[a]:
            if b in names and a in friend_map.get(b, set()):
                dyads.add(tuple(sorted([a,b])))
    return sorted(list(dyads))

def step3_assign(sheet_df, scenario_num, max_class_size=MAX_CLASS_SIZE):
    col_b1 = f'ΒΗΜΑ1_ΣΕΝΑΡΙΟ_{scenario_num}'
    col_b2 = f'ΒΗΜΑ2_ΣΕΝΑΡΙΟ_{scenario_num}'
    col_b3 = f'ΒΗΜΑ3_ΣΕΝΑΡΙΟ_{scenario_num}'
    name_col = 'ΟΝΟΜΑ'

    # Start with immutable assignments from Step2 then Step1
    if col_b2 in sheet_df.columns:
        assigned = sheet_df[col_b2].copy()
    else:
        assigned = pd.Series([np.nan] * len(sheet_df))
    if col_b1 in sheet_df.columns:
        assigned = assigned.where(~assigned.isna(), sheet_df[col_b1])

    # Current class counts
    counts = assigned.value_counts(dropna=True).to_dict()

    # Mutual DYADS only (Triads are not allowed per 22 Aug 2025 rule)
    dyads = build_mutual_dyads(sheet_df, name_col=name_col, friends_col='ΦΙΛΟΙ')

    # Build index by name
    name_to_idx = {row[name_col]: i for i, row in sheet_df.reset_index().iterrows()}

    # Place the unplaced member of each dyad if the other is already placed and capacity allows
    for a, b in dyads:
        ia = name_to_idx.get(a)
        ib = name_to_idx.get(b)
        if ia is None or ib is None:
            continue
        class_a = assigned.iloc[ia]
        class_b = assigned.iloc[ib]
        # exactly one assigned
        if pd.isna(class_a) ^ pd.isna(class_b):
            target = class_a if not pd.isna(class_a) else class_b
            if pd.isna(target):
                continue
            counts.setdefault(target, 0)
            if counts[target] < max_class_size:
                if pd.isna(class_a):
                    assigned.iloc[ia] = target
                else:
                    assigned.iloc[ib] = target
                counts[target] += 1
            # else leave unassigned for Step5

    # Insert the new column at position 12 (Excel 'M')
    out_df = sheet_df.copy()
    if col_b3 in out_df.columns:
        out_df.drop(columns=[col_b3], inplace=True)
    insert_at = 12 if len(out_df.columns) >= 12 else len(out_df.columns)
    out_df[col_b3] = assigned.values
    cols = out_df.columns.tolist()
    new_cols = cols[:insert_at] + [col_b3] + cols[insert_at:]
    out_df = out_df[new_cols]
    return out_df

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--in', dest='in_path', required=True, help='Path to VIMA2 Excel (sheets S1,S2,S3).')
    parser.add_argument('--out', dest='out_path', required=True, help='Output Excel with ΒΗΜΑ3_ΣΕΝΑΡΙΟ_N in column M.')
    args = parser.parse_args()

    xls = pd.ExcelFile(args.in_path)
    with pd.ExcelWriter(args.out_path, engine='xlsxwriter') as writer:
        for sheet in xls.sheet_names:
            df = pd.read_excel(args.in_path, sheet_name=sheet)
            m = re.search(r'(\d+)', sheet)
            scen = int(m.group(1)) if m else 1
            out_df = step3_assign(df, scen)
            out_df.to_excel(writer, index=False, sheet_name=sheet)

if __name__ == '__main__':
    main()
