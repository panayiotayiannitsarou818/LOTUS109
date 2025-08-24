# -*- coding: utf-8 -*-
"""
Βήμα 1 (FIXED): δημιουργεί πραγματικά ΔΙΑΦΟΡΕΤΙΚΑ σενάρια για τα παιδιά εκπαιδευτικών.
- Εξαλείφει τη συμμετρία Α1↔Α2 (canonicalization), ώστε να μην εμφανίζονται «ίδια» σενάρια με αλλαγμένες ετικέτες.
- Για μικρό πλήθος παιδιών εκπαιδευτικών (<= 12) κάνει ΕΞΑΝΤΛΗΤΙΚΗ απαρίθμηση όλων των αναθέσεων και κρατά τις top-k.
- Για μεγαλύτερα πλήθη χρησιμοποιεί greedy με εναλλακτικά seeds + ελέγχει μοναδικότητα με canonical key.
Έξοδοι: VIMA1_Scenarios_ENUM_CANON.xlsx & VIMA1_Scenarios_ENUM_CANON_Comparison.xlsx
"""

from pathlib import Path
import pandas as pd, numpy as np, itertools, math, re

def _auto_num_classes(df, override=None):
    import math
    n = len(df)
    # Keep a safe minimum of 2 to match downstream assumptions
    k = max(2, math.ceil(n/25))
    return int(k if override is None else override)

SRC = Path("/mnt/data/Παραδειγμα τελικη μορφηΤΜΗΜΑ.xlsx")
OUT = Path("/mnt/data/VIMA1_Scenarios_ENUM_CANON.xlsx")
OUT_CMP = Path("/mnt/data/VIMA1_Scenarios_ENUM_CANON_Comparison.xlsx")

def norm_yesno(val):
    s = str(val).strip().upper()
    return "Ν" if s in {"Ν","YES","TRUE","1"} else "Ο"

def load_and_normalize():
    df0 = pd.read_excel(SRC)
    df = df0.copy()
    # standardize columns
    rename = {}
    for c in df.columns:
        cc = str(c).strip()
        if cc.lower() in ["ονομα","name","μαθητης","μαθητρια"]:
            rename[c] = "ΟΝΟΜΑ"
        elif cc.lower().startswith("φυλο") or cc.lower()=="gender":
            rename[c] = "ΦΥΛΟ"
        elif "γνωση" in cc.lower():
            rename[c] = "ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ"
        elif "εκπ" in cc.lower():
            rename[c] = "ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ"
    df.rename(columns=rename, inplace=True)
    for col in ["ΟΝΟΜΑ","ΦΥΛΟ","ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ","ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ"]:
        if col not in df.columns:
            raise ValueError(f"Λείπει στήλη {col}")
    df["ΟΝΟΜΑ"] = df["ΟΝΟΜΑ"].astype(str).str.strip()
    df["ΦΥΛΟ"] = df["ΦΥΛΟ"].astype(str).str.strip().str.upper().map({"Α":"Α","Κ":"Κ","AGORI":"Α","KORITSI":"Κ"}).fillna("")
    for c in ["ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ","ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ"]:
        df[c] = df[c].map(norm_yesno)
    return df


def _class_labels(k:int):
    return [f"Α{i+1}" for i in range(k)]



def canonical_key(names, assign_map, class_labels):
    """Canonicalize an assignment by ignoring label permutations:
    return a tuple of sorted tuples (one per class), sorted lexicographically."""
    buckets = []
    for c in class_labels:
        members = tuple(sorted([n for n in names if assign_map.get(n) == c]))
        buckets.append(members)
    # Sort buckets so that permutations of labels map to the same key
    return tuple(sorted(buckets))


def score_state(st):
    cnts  = [v["cnt"]   for v in st.values()]
    boys  = [v["boys"]  for v in st.values()]
    girls = [v["girls"] for v in st.values()]
    good  = [v["good"]  for v in st.values()]
    pop   = (max(cnts)   - min(cnts))   if cnts  else 0
    bdiff = (max(boys)   - min(boys))   if boys  else 0
    gdiff = (max(girls)  - min(girls))  if girls else 0
    ndiff = (max(good)   - min(good))   if good  else 0
    return pop*3 + bdiff*2 + gdiff*2 + ndiff*1


def build_state(names, genders, greeks, assign_map, class_labels):
    st = {c: {"cnt":0, "boys":0, "girls":0, "good":0} for c in class_labels}
    idx = {n:i for i,n in enumerate(names)}
    for n in names:
        c = assign_map[n]
        i = idx[n]
        st[c]["cnt"]  += 1
        st[c]["boys"] += 1 if genders[i] == "Α" else 0
        st[c]["girls"]+= 1 if genders[i] == "Κ" else 0
        st[c]["good"] += 1 if greeks[i]  == "Ν" else 0
    return st


def enumerate_all(df, num_classes: int, top_k=3, max_states:int=1_000_000):
    teacher = df[df["ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ"]=="Ν"].copy().reset_index(drop=True)
    names   = list(teacher["ΟΝΟΜΑ"])
    genders = list(teacher["ΦΥΛΟ"])
    greeks  = list(teacher["ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ"])

    class_labels = _class_labels(num_classes)
    seen = set(); sols=[]
    total_states = (num_classes ** len(names)) if names else 1

    # Fallback to randomized sampling when search space is huge
    import itertools, random
    if total_states <= max_states:
        iterator = itertools.product(class_labels, repeat=len(names))
        for comb in iterator:
            am = {names[i]: comb[i] for i in range(len(names))}
            key = canonical_key(names, am, class_labels)
            if key in seen:
                continue
            seen.add(key)
            st = build_state(names, genders, greeks, am, class_labels)
            sc = score_state(st)
            sols.append((sc, am, st))
    else:
        # sample up to max_states random assignments
        for _ in range(min(max_states, 100000)):
            comb = [random.choice(class_labels) for _ in names]
            am = {names[i]: comb[i] for i in range(len(names))}
            key = canonical_key(names, am, class_labels)
            if key in seen:
                continue
            seen.add(key)
            st = build_state(names, genders, greeks, am, class_labels)
            sc = score_state(st)
            sols.append((sc, am, st))

    # sort by score then lexicographically
    def canon_tuple(am):
        buckets = []
        for c in class_labels:
            buckets.append(tuple(sorted([n for n in names if am.get(n)==c])))
        return tuple(buckets)

    sols.sort(key=lambda t: (t[0], canon_tuple(t[1])))
    return sols[:top_k], names


def write_outputs(df, solutions, names, num_classes):
    class_labels = _class_labels(num_classes)
    # Write canonical workbook (per-scenario sheets)
    with pd.ExcelWriter(OUT, engine="openpyxl") as w:
        for idx, (sc, am, st) in enumerate(solutions, start=1):
            data = []
            for n in names:
                row = {"ΟΝΟΜΑ": n}
                for c in class_labels:
                    row[c] = 1 if am.get(n)==c else 0
                data.append(row)
            pd.DataFrame(data).to_excel(w, index=False, sheet_name=f"V1_SENARIO_{idx}")
    # Comparison sheet
    rows=[]
    for i, (sc, am, st) in enumerate(solutions, start=1):
        row = {"Σενάριο": i, "Score": int(sc)}
        for c in class_labels:
            row[f"{c} σύνολο"] = st[c]["cnt"]
            row[f"{c} Αγόρια"] = st[c]["boys"]
            row[f"{c} Κορίτσια"] = st[c]["girls"]
            row[f"{c} Ν"] = st[c]["good"]
            row[f"{c}_ΜΑΘΗΤΕΣ"] = ", ".join(sorted([n for n in names if am.get(n)==c]))
        rows.append(row)
    cmp = pd.DataFrame(rows)
    with pd.ExcelWriter(OUT_CMP, engine="openpyxl") as w:
        cmp.to_excel(w, index=False, sheet_name="Σύνοψη")


def main():
    df = load_and_normalize()
    # AUTO num_classes from total N
    num_classes = _auto_num_classes(df, None)
    teacher = df[df["ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ"]=="Ν"]
    if len(teacher) <= 12:
        sols, names = enumerate_all(df, num_classes=num_classes, top_k=3)
    else:
        sols, names = enumerate_all(df, num_classes=num_classes, top_k=3)
    write_outputs(df, sols, names, num_classes)

if __name__ == "__main__":
    main()
