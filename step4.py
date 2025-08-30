# -*- coding: utf-8 -*-
"""
Step 4 – Fully mutual groups placement (ΠΛΗΡΩΣ ΔΙΟΡΘΩΜΕΝΗ ΕΚΔΟΣΗ)
Αλλαγές: 
- ΜΟΝΟ δυάδες (όχι τριάδες) σύμφωνα με έγγραφο
- gender_diff_max=3 (αυστηρότερο όριο)  
- Αποκλεισμός "σπασμένων φιλιών" από προηγούμενα βήματα
- Πλήρης κατηγοριοποίηση με "Μικτής Γνώσης" για μονόφυλες ομάδες
- ΠΡΑΓΜΑΤΙΚΗ στρατηγική εναλλαγής κατηγοριών
- ideal_per_class διανομή λαμβάνοντας υπόψη ήδη τοποθετημένες ομάδες
- Export σε ΒΗΜΑ4_ΣΕΝΑΡΙΟ_1..5 στήλες
- ΠΡΟΣΘΗΚΗ: wrapper function run_step4() για compatibility με σελίδες
"""

import itertools
from collections import defaultdict
from copy import deepcopy
import pandas as pd
import math
from typing import List, Dict, Tuple, Optional, Set

def _auto_num_classes(df: pd.DataFrame, override: Optional[int] = None) -> int:
    """Αυτόματος υπολογισμός αριθμού τμημάτων βάσει αριθμού μαθητών."""
    n = len(df)
    k = max(2, math.ceil(n/25))
    return int(k if override is None else override)

# -------------------- Utilities --------------------

def is_fully_mutual(group: List[str], df: pd.DataFrame) -> bool:
    """Επιστρέφει True αν κάθε ζεύγος στη 'group' είναι αμοιβαίοι φίλοι."""
    if len(group) < 2:
        return False
        
    for name in group:
        try:
            friends = set(df.loc[df['ΟΝΟΜΑ'] == name, 'ΦΙΛΟΙ'].values[0])
        except (IndexError, KeyError):
            return False
        
        for other in group:
            if other == name:
                continue
            if other not in friends:
                return False
    
    # Έλεγχος συμμετρίας
    for a, b in itertools.permutations(group, 2):
        try:
            fa = set(df.loc[df['ΟΝΟΜΑ'] == a, 'ΦΙΛΟΙ'].values[0])
            if b not in fa:
                return False
        except (IndexError, KeyError):
            return False
    return True

def has_broken_friendship(name: str, df: pd.DataFrame) -> bool:
    """
    Έλεγχος αν μαθητής έχει σπασμένες φιλίες από προηγούμενα βήματα.
    Υποθέτει ότι υπάρχει στήλη 'ΣΠΑΣΜΕΝΕΣ_ΦΙΛΙΕΣ' (True/False).
    """
    if 'ΣΠΑΣΜΕΝΕΣ_ΦΙΛΙΕΣ' not in df.columns:
        return False
    
    try:
        return bool(df.loc[df['ΟΝΟΜΑ'] == name, 'ΣΠΑΣΜΕΝΕΣ_ΦΙΛΙΕΣ'].values[0])
    except (IndexError, KeyError):
        return False

def create_fully_mutual_groups(df: pd.DataFrame, assigned_column: str) -> List[List[str]]:
    """
    Δημιουργία ΜΟΝΟ ΔΥΑΔΩΝ (όχι τριάδων) μεταξύ μη-τοποθετημένων μαθητών.
    Αποκλεισμός μαθητών με σπασμένες φιλίες από προηγούμενα βήματα.
    """
    unassigned = df[df[assigned_column].isna()].copy()
    
    # Φιλτράρισμα μαθητών χωρίς φίλους
    unassigned = unassigned[
        unassigned['ΦΙΛΟΙ'].map(lambda x: isinstance(x, list) and len(x) > 0)
    ]
    
    if len(unassigned) == 0:
        return []
    
    names = list(unassigned['ΟΝΟΜΑ'].astype(str).unique())
    
    # Αποκλεισμός μαθητών με σπασμένες φιλίες
    names_no_broken = [name for name in names if not has_broken_friendship(name, df)]
    
    # Επιπλέον φιλτράρισμα: αποκλεισμός μαθητών χωρίς αμοιβαίες φιλίες στο pool
    names_with_mutual = []
    for name in names_no_broken:
        try:
            friends = set(df.loc[df['ΟΝΟΜΑ'] == name, 'ΦΙΛΟΙ'].values[0])
            mutual_friends_in_pool = friends.intersection(set(names_no_broken))
            if len(mutual_friends_in_pool) > 0:
                names_with_mutual.append(name)
        except (IndexError, KeyError):
            continue
    
    names = names_with_mutual
    used = set()
    groups = []

    # ΜΟΝΟ ΔΥΑΔΕΣ (σύμφωνα με έγγραφο - όχι τριάδες)
    for g in itertools.combinations(names, 2):
        if set(g) & used:
            continue
        if is_fully_mutual(list(g), df):
            groups.append(list(g))
            used |= set(g)

    return groups

def get_group_characteristics(group: List[str], df: pd.DataFrame) -> str:
    """
    Κατηγοριοποίηση ομάδας βάσει φύλου και γνώσης ελληνικών.
    ΔΙΟΡΘΩΜΕΝΗ ΕΚΔΟΣΗ: Πλήρης διαχείριση όλων των κατηγοριών.
    """
    sub = df[df['ΟΝΟΜΑ'].isin(group)]
    genders = set(sub['ΦΥΛΟ'])
    lang = set(sub['ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ'])
    
    # Μικτό φύλο ως ενιαία κατηγορία (αγνοεί Ν/Ο)
    if len(genders) > 1:
        return 'Ομάδες Μικτού Φύλου'
    
    # Μονό φύλο - συνδυασμός φύλου και γνώσης
    gtxt = 'Αγόρια' if 'Α' in genders else 'Κορίτσια'
    
    # ΔΙΟΡΘΩΣΗ: Πλήρης διαχείριση Μικτής Γνώσης
    if len(lang) == 1:
        ltxt = 'Καλή Γνώση' if 'Ν' in lang else 'Όχι Καλή Γνώση'
    else:
        ltxt = 'Μικτής Γνώσης'  # ΠΡΟΣΘΗΚΗ: Μικτής Γνώσης για μονόφυλες ομάδες
    
    return f'{ltxt} ({gtxt})'

def categorize_groups(groups: List[List[str]], df: pd.DataFrame) -> Dict[str, List[List[str]]]:
    """Ομαδοποίηση των ομάδων βάσει χαρακτηριστικών."""
    cat = defaultdict(list)
    for g in groups:
        cat[get_group_characteristics(g, df)].append(g)
    return cat

def get_opposite_category(category: str) -> str:
    """
    ΔΙΟΡΘΩΜΕΝΗ στρατηγική εναλλαγής - αντίθετη κατηγορία για ισορροπία.
    """
    opposites = {
        'Καλή Γνώση (Αγόρια)': 'Όχι Καλή Γνώση (Κορίτσια)',
        'Όχι Καλή Γνώση (Κορίτσια)': 'Καλή Γνώση (Αγόρια)',
        'Καλή Γνώση (Κορίτσια)': 'Όχι Καλή Γνώση (Αγόρια)',
        'Όχι Καλή Γνώση (Αγόρια)': 'Καλή Γνώση (Κορίτσια)',
        'Μικτής Γνώσης (Αγόρια)': 'Μικτής Γνώσης (Κορίτσια)',
        'Μικτής Γνώσης (Κορίτσια)': 'Μικτής Γνώσης (Αγόρια)',
        # Μικτό Φύλο δεν έχει αντίθετο - επιστρέφει None
        'Ομάδες Μικτού Φύλου': None,
    }
    return opposites.get(category, category)

def count_groups_by_category_per_class_strict(df: pd.DataFrame, assigned_column: str, classes: List[str], 
                                             step1_results: Optional[Any] = None,
                                             detected_pairs: Optional[List[Tuple[str, str]]] = None) -> Dict[str, Dict[str, int]]:
    """
    ΒΕΛΤΙΩΜΕΝΗ καταμέτρηση ομάδων που λαμβάνει υπόψη την ΠΡΑΓΜΑΤΙΚΗ δομή από τα προηγούμενα βήματα.
    
    Args:
        step1_results: Step1Results object από step1_immutable.py (για παιδιά εκπαιδευτικών)
        detected_pairs: List από (name1, name2) pairs που εντοπίστηκαν σε προηγούμενα βήματα
    """
    assigned = df[~df[assigned_column].isna()]
    groups_per_class = defaultdict(lambda: defaultdict(int))
    
    # ΒΗΜΑ 1: Καταμέτρηση παιδιών εκπαιδευτικών ως ατομικές "ομάδες"
    if step1_results is not None:
        # Για κάθε σενάριο του Βήματος 1
        for scenario in step1_results.scenarios:
            if scenario.column_name == assigned_column:
                # Αυτά τα παιδιά τοποθετήθηκαν ως individuals στο Βήμα 1
                for student_name, class_name in scenario.assignments.items():
                    if class_name in classes:
                        fake_group = [student_name]
                        category = get_group_characteristics(fake_group, df)
                        groups_per_class[class_name][category] += 1
                break
    
    # ΒΗΜΑ 2 & 3: Εντοπισμός πραγματικών ζευγαριών που διατηρήθηκαν
    processed_students = set()
    
    if detected_pairs:
        for name1, name2 in detected_pairs:
            if name1 in processed_students or name2 in processed_students:
                continue
            
            # Έλεγχος αν το ζεύγος βρίσκεται στο ίδιο τμήμα
            class1 = assigned[assigned['ΟΝΟΜΑ'] == name1][assigned_column]
            class2 = assigned[assigned['ΟΝΟΜΑ'] == name2][assigned_column]
            
            if not class1.empty and not class2.empty and class1.iloc[0] == class2.iloc[0]:
                class_name = str(class1.iloc[0])
                if class_name in classes:
                    # Αυτό είναι πραγματικό ζεύγος που διατηρήθηκε
                    pair_group = [name1, name2]
                    category = get_group_characteristics(pair_group, df)
                    groups_per_class[class_name][category] += 1
                    processed_students.update([name1, name2])
    
    # ΥΠΟΛΟΙΠΑ: Μεμονωμένοι μαθητές που δεν ανήκουν σε ζεύγη
    for class_name in classes:
        class_students = assigned[assigned[assigned_column] == class_name]
        for _, student in class_students.iterrows():
            student_name = str(student['ΟΝΟΜΑ']).strip()
            if student_name not in processed_students:
                # Αυτός ο μαθητής δεν ανήκει σε κανένα διατηρημένο ζεύγος
                fake_group = [student_name]
                category = get_group_characteristics(fake_group, df)
                groups_per_class[class_name][category] += 1
    
    return dict(groups_per_class)

def calculate_ideal_distribution(total_groups_per_category: Dict[str, int], classes: List[str]) -> Dict[str, int]:
    """Υπολογισμός ιδανικού αριθμού ομάδων ανά τμήμα για κάθε κατηγορία."""
    ideal = {}
    num_classes = len(classes)
    
    for category, total_groups in total_groups_per_category.items():
        ideal[category] = math.ceil(total_groups / num_classes)
    
    return ideal

# -------------------- Scoring & acceptance --------------------

def _counts_from(df: pd.DataFrame, placed_dict: Dict[Tuple[str, ...], str], 
                assigned_column: str, classes: List[str]) -> Tuple[Dict[str, int], Dict[str, int], Dict[str, int], Dict[str, int]]:
    """Υπολογισμός τρεχουσών μετρήσεων συμπεριλαμβανομένων υποθετικών τοποθετήσεων."""
    cnt = {c: int((df[assigned_column] == c).sum()) for c in classes}
    good= {c: int(((df[assigned_column] == c) & (df['ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ']=='Ν')).sum()) for c in classes}
    boys= {c: int(((df[assigned_column] == c) & (df['ΦΥΛΟ']=='Α')).sum()) for c in classes}
    girls={c: int(((df[assigned_column] == c) & (df['ΦΥΛΟ']=='Κ')).sum()) for c in classes}
    
    # Εφαρμογή τοποθετημένων ομάδων
    for g, c in placed_dict.items():
        size = len(g)
        sub = df[df['ΟΝΟΜΑ'].isin(g)]
        cnt[c]   += size
        good[c]  += int((sub['ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ']=='Ν').sum())
        boys[c]  += int((sub['ΦΥΛΟ']=='Α').sum())
        girls[c] += int((sub['ΦΥΛΟ']=='Κ').sum())
    
    return cnt, good, boys, girls

def accept(cnt: Dict[str, int], good: Dict[str, int], boys: Dict[str, int], girls: Dict[str, int], 
          cap: int = 25, pop_diff_max: int = 2, good_diff_max: int = 4, gender_diff_max: int = 3) -> bool:
    """
    ΔΙΟΡΘΩΜΕΝΟ: gender_diff_max=3 (αυστηρότερο), σωστό max-min για k>2 τμήματα
    """
    if any(v > cap for v in cnt.values()): 
        return False
    if max(cnt.values()) - min(cnt.values()) > pop_diff_max: 
        return False
    if max(good.values()) - min(good.values()) > good_diff_max: 
        return False
    if max(boys.values()) - min(boys.values()) > gender_diff_max: 
        return False
    if max(girls.values()) - min(girls.values()) > gender_diff_max: 
        return False
    return True

def penalty(cnt: Dict[str, int], good: Dict[str, int], boys: Dict[str, int], girls: Dict[str, int], 
           classes: List[str]) -> int:
    """Υπολογισμός penalty score βάσει ανισορροπιών (διορθωμένο για k>2)."""
    penalties = []
    
    # Penalty πληθυσμού (πέρα από διαφορά 1)
    pop_diff = max(cnt.values()) - min(cnt.values())
    penalties.append(max(0, pop_diff - 1))
    
    # Penalty γνώσης ελληνικών (πέρα από διαφορά 2)  
    good_diff = max(good.values()) - min(good.values())
    penalties.append(max(0, good_diff - 2))
    
    # Penalty φύλου (πέρα από διαφορά 1 για κάθε φύλο)
    boys_diff = max(boys.values()) - min(boys.values())
    girls_diff = max(girls.values()) - min(girls.values())
    penalties.extend([max(0, boys_diff - 1), max(0, girls_diff - 1)])
    
    return sum(penalties)

# -------------------- Enhanced Algorithm with IMPROVED Category Strategy --------------------

def apply_step4_with_enhanced_strategy(df: pd.DataFrame, assigned_column: str = 'ΒΗΜΑ3_ΣΕΝΑΡΙΟ_1', 
                                      num_classes: Optional[int] = None, max_results: int = 5, 
                                      max_nodes: int = None, exhaustive: bool = False) -> List[Tuple[Dict[Tuple[str, ...], str], int]]:
    """
    ΠΛΗΡΩΣ ΔΙΟΡΘΩΜΕΝΗ ΕΚΔΟΣΗ με πραγματική στρατηγική εναλλαγής κατηγοριών.
    """
    num_classes = _auto_num_classes(df, num_classes)
    classes = [f'Α{i+1}' for i in range(num_classes)]
    
    # Βασικές μετρήσεις από ήδη τοποθετημένους μαθητές
    base_cnt = {c: int((df[assigned_column]==c).sum()) for c in classes}
    base_good= {c: int(((df[assigned_column]==c) & (df['ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ']=='Ν')).sum()) for c in classes}
    base_boys= {c: int(((df[assigned_column]==c) & (df['ΦΥΛΟ']=='Α')).sum()) for c in classes}
    base_girls={c: int(((df[assigned_column]==c) & (df['ΦΥΛΟ']=='Κ')).sum()) for c in classes}

    # Δημιουργία αμοιβαίων ομάδων φιλίας από μη-τοποθετημένους μαθητές (ΜΟΝΟ ΔΥΑΔΕΣ)
    groups = create_fully_mutual_groups(df, assigned_column)
    if not groups:
        return []

    # Κατηγοριοποίηση ομάδων για στρατηγική
    categorized_groups = categorize_groups(groups, df)
    
    # Καταμέτρηση υπάρχουσων ομάδων ανά κατηγορία ανά τμήμα (από Βήματα 1-3)
    # ΒΕΛΤΙΩΣΗ: Εντοπισμός διατηρημένων ζευγαριών από προηγούμενα βήματα
    detected_pairs = []
    assigned_students = df[~df[assigned_column].isna()]
    
    # Εντοπισμός ζευγαριών που ήδη βρίσκονται στο ίδιο τμήμα
    for class_name in classes:
        class_students = assigned_students[assigned_students[assigned_column] == class_name]['ΟΝΟΜΑ'].tolist()
        
        # Έλεγχος όλων των συνδυασμών για αμοιβαίες φιλίες
        for i, student1 in enumerate(class_students):
            for student2 in class_students[i+1:]:
                if is_fully_mutual([student1, student2], df):
                    detected_pairs.append((student1, student2))
    
    existing_groups_per_class = count_groups_by_category_per_class_strict(
        df, assigned_column, classes, detected_pairs=detected_pairs
    )
    
    # Υπολογισμός συνολικών ομάδων ανά κατηγορία (υπάρχουσες + νέες)
    total_groups_per_category = {}
    for category, group_list in categorized_groups.items():
        existing_total = sum(existing_groups_per_class[c].get(category, 0) for c in classes)
        total_groups_per_category[category] = existing_total + len(group_list)
    
    # Υπολογισμός ιδανικής διανομής ανά κατηγορία
    ideal_per_category = calculate_ideal_distribution(total_groups_per_category, classes)
    
    print(f"📊 Ιδανική κατανομή ανά κατηγορία: {ideal_per_category}")
    print(f"📋 Υπάρχουσες ομάδες ανά τμήμα: {dict(existing_groups_per_class)}")

    # Επιπεδοποίηση ομάδων με προτεραιότητα βάσει ανάγκης κατηγοριών
    def group_priority_with_category_balance(g: List[str]) -> Tuple[int, int, int]:
        category = get_group_characteristics(g, df)
        
        # Υπολογισμός πόσο χρειάζεται αυτή η κατηγορία σε όλα τα τμήματα
        current_total = sum(existing_groups_per_class[c].get(category, 0) for c in classes)
        ideal_total = ideal_per_category.get(category, 1)
        need_score = max(0, ideal_total - current_total)  # Μεγαλύτερο = περισσότερο χρειάζεται
        
        sub = df[df['ΟΝΟΜΑ'].isin(g)]
        boys = int((sub['ΦΥΛΟ']=='Α').sum())
        girls= int((sub['ΦΥΛΟ']=='Κ').sum())
        
        # Προτεραιότητα: need_score desc, size desc, gender balance desc
        return (-need_score, -len(g), -abs(boys-girls))
    
    all_groups = []
    for group_list in categorized_groups.values():
        all_groups.extend(group_list)
    
    groups = sorted(all_groups, key=group_priority_with_category_balance)

    results = []
    nodes = 0
    placed = {}
    
    # Παρακολούθηση τελευταίας τοποθετημένης κατηγορίας ανά τμήμα για εναλλαγή
    last_category_per_class = {c: None for c in classes}

    def get_preferred_class_for_group(group: List[str], cnt: Dict[str, int], 
                                     good: Dict[str, int], boys: Dict[str, int], girls: Dict[str, int]) -> List[str]:
        """
        ΒΕΛΤΙΩΜΕΝΗ στρατηγική: Καθορισμός προτιμώμενης σειράς τμημάτων βάσει:
        1. ideal_per_class διανομής ανά κατηγορία (ΝΕΟ!)
        2. Στρατηγικής εναλλαγής κατηγοριών
        3. Load balancing
        """
        category = get_group_characteristics(group, df)
        
        # Έναρξη με load balancing
        order = sorted(classes, key=lambda c: (cnt[c], good[c], boys[c]+girls[c]))
        
        # ΒΕΛΤΙΩΣΗ 1: Εφαρμογή ideal_per_class στην τοποθέτηση
        ideal_preferred = []
        alternation_preferred = []
        other_classes = []
        
        opposite_category = get_opposite_category(category)
        ideal_for_category = ideal_per_category.get(category, 1)
        
        for c in order:
            current_groups_in_category = existing_groups_per_class[c].get(category, 0)
            
            # Προσθέτουμε τις ήδη τοποθετημένες ομάδες αυτής της κατηγορίας σε αυτό το placement
            groups_placed_here = sum(1 for placed_group, placed_class in placed.items() 
                                   if placed_class == c and 
                                   get_group_characteristics(list(placed_group), df) == category)
            
            current_total = current_groups_in_category + groups_placed_here
            
            # ΠΡΟΤΕΡΑΙΟΤΗΤΑ 1: Τμήματα που υπολείπονται από τον ιδανικό αριθμό
            if current_total < ideal_for_category:
                ideal_preferred.append(c)
            # ΠΡΟΤΕΡΑΙΟΤΗΤΑ 2: Εναλλαγή κατηγοριών (αν δεν υπολείπεται ιδανικός)
            # ΔΙΟΡΘΩΣΗ: Μόνο όταν υπάρχει και ταιριάζει η ακριβώς αντίθετη κατηγορία
            elif opposite_category is not None and last_category_per_class[c] == opposite_category:
                alternation_preferred.append(c)
            else:
                other_classes.append(c)
        
        # Επιστροφή με σειρά προτεραιότητας: ideal → alternation → load balancing
        final_order = ideal_preferred + alternation_preferred + other_classes
        
        # DEBUG: Εκτύπωση στρατηγικής για debugging
        if len(final_order) > 0:
            print(f"🎯 Ομάδα {group} ({category}) → Προτιμώμενη σειρά: {final_order[:3]}")
        
        return final_order

    def dfs(idx: int, cnt: Dict[str, int], good: Dict[str, int], 
            boys: Dict[str, int], girls: Dict[str, int]) -> None:
        nonlocal nodes
        nodes += 1
        
        # Έλεγχος ορίων μόνο αν δεν είναι exhaustive mode
        if not exhaustive and max_nodes and nodes > max_nodes:
            return
        
        # Γρήγορος έλεγχος χωρητικότητας
        if any(v > 25 for v in cnt.values()):
            return

        # Base case: όλες οι ομάδες επεξεργάστηκαν
        if idx == len(groups):
            if accept(cnt, good, boys, girls):
                p = penalty(cnt, good, boys, girls, classes)
                results.append((deepcopy(placed), p))
            return

        # Τρέχουσα ομάδα προς τοποθέτηση
        g = groups[idx]
        category = get_group_characteristics(g, df)
        sub = df[df['ΟΝΟΜΑ'].isin(g)]
        gsize = len(g)
        ggood = int((sub['ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ']=='Ν').sum())
        gboys = int((sub['ΦΥΛΟ']=='Α').sum())
        ggirls= int((sub['ΦΥΛΟ']=='Κ').sum())

        # Λήψη προτιμώμενης σειράς τμημάτων χρησιμοποιώντας στρατηγική κατηγοριών
        preferred_order = get_preferred_class_for_group(g, cnt, good, boys, girls)

        for c in preferred_order:
            # Προσομοίωση τοποθέτησης
            cnt[c]   += gsize
            good[c]  += ggood
            boys[c]  += gboys
            girls[c] += ggirls
            placed[tuple(g)] = c
            
            # Ενημέρωση παρακολούθησης εναλλαγής
            old_category = last_category_per_class[c]
            last_category_per_class[c] = category

            # Pruning μόνο αν δεν είναι exhaustive mode
            if exhaustive or (max(cnt.values()) - min(cnt.values())) <= 2:
                dfs(idx+1, cnt, good, boys, girls)

            # Backtrack
            last_category_per_class[c] = old_category
            placed.pop(tuple(g), None)
            cnt[c]   -= gsize
            good[c]  -= ggood
            boys[c]  -= gboys
            girls[c] -= ggirls

            # Early termination μόνο αν δεν είναι exhaustive mode
            if not exhaustive and len(results) >= max_results:
                return

    # Έναρξη DFS
    dfs(0, base_cnt.copy(), base_good.copy(), base_boys.copy(), base_girls.copy())

    # Ταξινόμηση βάσει penalty score (καλύτερα πρώτα)
    results_sorted = sorted(results, key=lambda t: t[1])[:max_results]
    return results_sorted

def export_step4_scenarios(df: pd.DataFrame, results: List[Tuple[Dict[Tuple[str, ...], str], int]], 
                          assigned_column: str = 'ΒΗΜΑ3_ΣΕΝΑΡΙΟ_1') -> pd.DataFrame:
    """
    Export έως 5 σεναρίων ως νέες στήλες ΒΗΜΑ4_ΣΕΝΑΡΙΟ_1 έως 5.
    """
    df_result = df.copy()
    
    for i, (placed_dict, penalty_score) in enumerate(results[:5], 1):
        col_name = f'ΒΗΜΑ4_ΣΕΝΑΡΙΟ_{i}'
        
        # Έναρξη με υπάρχουσες τοποθετήσεις
        df_result[col_name] = df_result[assigned_column].copy()
        
        # Εφαρμογή νέων τοποθετήσεων
        for group_tuple, class_name in placed_dict.items():
            group_names = list(group_tuple)
            mask = df_result['ΟΝΟΜΑ'].isin(group_names)
            df_result.loc[mask, col_name] = class_name
        
        print(f"Σενάριο {i}: Penalty Score = {penalty_score}")
    
    return df_result

# -------------------- Main execution function --------------------

def run_step4_complete(df: pd.DataFrame, assigned_column: str = 'ΒΗΜΑ3_ΣΕΝΑΡΙΟ_1', 
                      num_classes: Optional[int] = None) -> pd.DataFrame:
    """
    Πλήρης εκτέλεση Βήμα 4 με στρατηγική εναλλαγής κατηγοριών και ιδανική διανομή.
    """
    print("🔍 Εκτέλεση Βήμα 4: Αμοιβαίες Φιλίες με Στρατηγική Εναλλαγής")
    print("="*65)
    
    # Έλεγχος αν υπάρχει στήλη ΣΠΑΣΜΕΝΕΣ_ΦΙΛΙΕΣ
    if 'ΣΠΑΣΜΕΝΕΣ_ΦΙΛΙΕΣ' not in df.columns:
        print("⚠️  Προσθήκη στήλης ΣΠΑΣΜΕΝΕΣ_ΦΙΛΙΕΣ (default: False)")
        df = df.copy()
        df['ΣΠΑΣΜΕΝΕΣ_ΦΙΛΙΕΣ'] = False
    
    # Εύρεση σεναρίων χρησιμοποιώντας βελτιωμένη στρατηγική
    results = apply_step4_with_enhanced_strategy(df, assigned_column, num_classes)
    
    if not results:
        print("❌ Δεν βρέθηκαν έγκυρα σενάρια τοποθέτησης.")
        return df
    
    print(f"✅ Βρέθηκαν {len(results)} σενάρια:")
    
    # Export σεναρίων σε DataFrame
    df_with_scenarios = export_step4_scenarios(df, results, assigned_column)
    
    # Εμφάνιση περίληψης
    for i, (_, penalty) in enumerate(results[:5], 1):
        col_name = f'ΒΗΜΑ4_ΣΕΝΑΡΙΟ_{i}'
        assigned_count = (~df_with_scenarios[col_name].isna()).sum()
        unassigned_count = df_with_scenarios[col_name].isna().sum()
        
        print(f"  Σενάριο {i}: Ποινή={penalty}, Τοποθετημένοι={assigned_count}, Μη-τοποθετημένοι={unassigned_count}")
    
    return df_with_scenarios

# -------------------- WRAPPER FUNCTION για compatibility με σελίδες --------------------

def run_step4(df: pd.DataFrame) -> pd.DataFrame:
    """
    WRAPPER function για compatibility με τις σελίδες.
    Καλεί το run_step4_complete με default παραμέτρους.
    """
    return run_step4_complete(df)

# -------------------- Testing function --------------------

if __name__ == "__main__":
    print("Step 4 ΠΛΗΡΩΣ ΔΙΟΡΘΩΜΕΝΟ Module με Wrapper - Έτοιμο για import")
    print("Χρήση σελίδων: from step4 import run_step4")
    print("               df_result = run_step4(df)")
    print("Χρήση advanced: from step4 import run_step4_complete")
    print("                df_result = run_step4_complete(df, 'ΒΗΜΑ3_ΣΕΝΑΡΙΟ_1')")


# ================== FINAL WRAPPERS (ΜΟΝΟ ΒΗΜΑ4_ΣΕΝΑΡΙΟ_N στη στήλη N) ==================
import pandas as pd

def _excel_letter_to_index(letter: str) -> int:
    letter = letter.strip().upper()
    idx = 0
    for ch in letter:
        if not ('A' <= ch <= 'Z'):
            raise ValueError(f"Invalid Excel column letter: {letter}")
        idx = idx * 26 + (ord(ch) - ord('A') + 1)
    return idx - 1

def _move_column_to_letter(df: pd.DataFrame, col_name: str, letter: str = 'N') -> pd.DataFrame:
    if col_name not in df.columns:
        return df
    target_idx = _excel_letter_to_index(letter)
    cols = list(df.columns)
    cols.remove(col_name)
    insert_idx = min(max(0, target_idx), len(cols))
    cols.insert(insert_idx, col_name)
    return df[cols]

def export_step4_SINGLE_to_colN(df: pd.DataFrame, results, assigned_column: str, scenario_index: int,
                                excel_letter: str = 'N') -> pd.DataFrame:
    """
    Επιλέγει το σενάριο `scenario_index` από τα results (ή το καλύτερο αν δεν υπάρχει)
    και δημιουργεί ΜΟΝΟ τη στήλη ΒΗΜΑ4_ΣΕΝΑΡΙΟ_{scenario_index}, ξεκινώντας από τις τιμές
    του ΒΗΜΑ3_ΣΕΝΑΡΙΟ_{scenario_index}, εφαρμόζοντας τις νέες τοποθετήσεις των ομάδων.
    Τέλος, μετακινεί τη στήλη στη θέση Excel 'N'.
    """
    col_name = f'ΒΗΜΑ4_ΣΕΝΑΡΙΟ_{scenario_index}'
    df_out = df.copy()

    if not results:
        # Αν δεν υπάρχουν νέες ομάδες, τουλάχιστον αντιγράφουμε την προηγούμενη στήλη
        df_out[col_name] = df_out.get(assigned_column, pd.NA)
        return _move_column_to_letter(df_out, col_name, excel_letter)

    # Αν ζητήθηκε index > διαθέσιμων σεναρίων, πάρε το καλύτερο (πρώτο)
    idx = scenario_index - 1
    if idx < 0 or idx >= len(results):
        idx = 0

    placed_dict, _pen = results[idx]
    # Έναρξη με υπάρχουσες τοποθετήσεις από το ΒΗΜΑ3_ΣΕΝΑΡΙΟ_N
    df_out[col_name] = df_out.get(assigned_column, pd.NA)

    # Εφαρμογή νέων τοποθετήσεων ομάδων
    for group_tuple, class_name in placed_dict.items():
        group_names = list(group_tuple)
        mask = df_out['ΟΝΟΜΑ'].isin(group_names)
        df_out.loc[mask, col_name] = class_name

    # Μετακίνηση της στήλης στη θέση N
    return _move_column_to_letter(df_out, col_name, excel_letter)

def run_step4_FINAL(df: pd.DataFrame, scenario_index: int = 1, num_classes: int | None = None) -> pd.DataFrame:
    """
    Τρέχει τον ΙΔΙΟ αλγόριθμο με το step4.py (apply_step4_with_enhanced_strategy),
    αλλά επιστρέφει DataFrame με ΜΟΝΟ τη στήλη ΒΗΜΑ4_ΣΕΝΑΡΙΟ_{scenario_index},
    τοποθετημένη στη στήλη N.
    """
    assigned_column = f'ΒΗΜΑ3_ΣΕΝΑΡΙΟ_{scenario_index}'
    if 'ΣΠΑΣΜΕΝΕΣ_ΦΙΛΙΕΣ' not in df.columns:
        df = df.copy()
        df['ΣΠΑΣΜΕΝΕΣ_ΦΙΛΙΕΣ'] = False

    # Κλήση του αλγορίθμου από το αρχικό step4.py
    results = apply_step4_with_enhanced_strategy(df, assigned_column=assigned_column, num_classes=num_classes)

    # Εξαγωγή ΜΟΝΟ του ζητούμενου σεναρίου στη στήλη N
    return export_step4_SINGLE_to_colN(df, results, assigned_column, scenario_index, excel_letter='N')

# Backward-compat alias
def run_step4(df: pd.DataFrame, scenario_index: int = 1) -> pd.DataFrame:
    return run_step4_FINAL(df, scenario_index=scenario_index)


if __name__ == "__main__":
    print("step4_FINAL: Έτοιμο. Χρήση: run_step4_FINAL(df, scenario_index=1..5) → γράφει ΒΗΜΑ4_ΣΕΝΑΡΙΟ_N στη στήλη N.")


# =========================
# Excel Export Helpers (Sheets)
# =========================
import re
from typing import Iterable, Sequence, Optional

def export_step4_scenarios_to_excel(
    df,
    output_path: str = "VIMA4_SCENARIOS.xlsx",
    scenario_indices: Sequence[int] = (1, 2, 3, 4, 5),
    engine: str = "openpyxl",
) -> str:
    """
    Τρέχει το ΒΗΜΑ 4 για κάθε ζητημένο σενάριο και γράφει
    ΚΑΘΕ σενάριο σε ΞΕΧΩΡΙΣΤΟ SHEET. Σε κάθε sheet:
      - εξασφαλίζει ότι υπάρχει η στήλη 'ΒΗΜΑ4_ΣΕΝΑΡΙΟ_{N}'
      - τη μετακινεί/κρατά στη θέση Excel Στήλη N (δηλ. γράμμα 'N')

    Parameters
    ----------
    df : pandas.DataFrame
        Το dataframe εισόδου (με τα ΒΗΜΑ3_ΣΕΝΑΡΙΟ_N κ.λπ.).
    output_path : str
        Το αρχείο εξόδου .xlsx.
    scenario_indices : Sequence[int]
        Ποια σενάρια (N) να παραχθούν (1..5).
    engine : str
        Writer engine για pandas ExcelWriter.

    Returns
    -------
    str
        Το path του αρχείου Excel που δημιουργήθηκε.
    """
    import pandas as pd

    # Lazy import to avoid circulars if used as module
    # run_step4_FINAL πρέπει να ορίζεται στο ίδιο αρχείο
    if "run_step4_FINAL" not in globals():
        raise RuntimeError("Η συνάρτηση run_step4_FINAL δεν βρέθηκε στο namespace. Φόρτωσε πρώτα το αρχείο που την ορίζει.")

    with pd.ExcelWriter(output_path, engine=engine) as writer:
        for idx in scenario_indices:
            _df = df.copy(deep=True)

            # Τρέχουμε το Βήμα 4 για το συγκεκριμένο σενάριο
            out_df = run_step4_FINAL(_df, scenario_index=idx)

            # Τοποθέτηση της βάσης ΒΗΜΑ3_ΣΕΝΑΡΙΟ_{idx} στη στήλη M (αν υπάρχει)
            step3_col = f"ΒΗΜΑ3_ΣΕΝΑΡΙΟ_{idx}"
            try:
                if step3_col in out_df.columns:
                    out_df = _move_column_to_letter(out_df, step3_col, "M")
            except Exception:
                pass

            # Αναμενόμενο όνομα στήλης αποτελέσματος
            colname = f"ΒΗΜΑ4_ΣΕΝΑΡΙΟ_{idx}"

            # Αν δεν υπάρχει, προσπαθούμε να την εντοπίσουμε με pattern
            if colname not in out_df.columns:
                candidates = [c for c in out_df.columns if re.fullmatch(r"ΒΗΜΑ4_ΣΕΝΑΡΙΟ_\d+", str(c) or "")]
                if len(candidates) == 1:
                    colname = candidates[0]
                elif len(candidates) > 1:
                    # Επιλέγουμε αυτή με το σωστό idx, αλλιώς την τελευταία
                    exact = [c for c in candidates if c.endswith(f"_{idx}")]
                    colname = exact[0] if exact else candidates[-1]
                else:
                    # Τελευταία γραμμή άμυνας: αν ο wrapper έγραψε μόνο σε 'ΤΜΗΜΑ' ή σε άτιτλη στήλη,
                    # απλά δημιουργούμε την ονομαστική στήλη-καθρέφτη (δεν αλλάζουμε δεδομένα)
                    if "ΤΜΗΜΑ" in out_df.columns:
                        out_df[colname] = out_df["ΤΜΗΜΑ"]
                    else:
                        # Δεν μπορούμε να μαντέψουμε — συνεχίζουμε χωρίς στήλη (δεν θα γίνει move)
                        pass

            # Μετακίνηση/διασφάλιση ότι η colname βρίσκεται στη Στήλη N
            try:
                out_df = _move_column_to_letter(out_df, colname, "N")
            except Exception:
                # Αν δεν υπάρχει, αγνοούμε τη μετακίνηση
                pass

            sheet_name = f"ΒΗΜΑ4_ΣΕΝΑΡΙΟ_{idx}"
            out_df.to_excel(writer, index=False, sheet_name=sheet_name)

    return str(output_path)


def export_step4_single_scenario_to_excel(
    df,
    scenario_index: int = 1,
    output_path: str = "VIMA4_SCENARIO_{idx}.xlsx",
    engine: str = "openpyxl",
) -> str:
    """
    Εξάγει ΜΟΝΟ ένα σενάριο σε ένα Excel (ένα sheet).
    Η στήλη 'ΒΗΜΑ4_ΣΕΝΑΡΙΟ_{N}' τοποθετείται στη στήλη N.

    Returns
    -------
    str : το path του αρχείου που δημιουργήθηκε
    """
    output_path = output_path.format(idx=scenario_index)
    return export_step4_scenarios_to_excel(
        df=df,
        output_path=output_path,
        scenario_indices=(scenario_index,),
        engine=engine,
    )
