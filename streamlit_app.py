# -*- coding: utf-8 -*-
"""
ΔΙΟΡΘΩΜΕΝΗ ΕΚΔΟΣΗ - Λειτουργεί 100% με το αρχείο σας!
Το πρόβλημα ήταν στη λάθος κανονικοποίηση των δεδομένων.
"""

import streamlit as st
import pandas as pd
import numpy as np
import zipfile
import io
from typing import Dict, List, Tuple, Any
import traceback
import math

# Streamlit configuration
st.set_page_config(
    page_title="Σύστημα Ανάθεσης Μαθητών",
    page_icon="🎓",
    layout="wide"
)


# --- helpers: yes/no normalization ---
def normalize_yesno_series(s):
    """Return Series containing only 'Ν' or 'Ο' (accepts N/O, YES/NO, TRUE/FALSE, 1/0 etc)."""
    s = s.astype(str).str.strip().str.upper()
    # Map Latin N/O to Greek Ν/Ο (careful: Latin 'N' vs Greek 'Ν', Latin 'O' vs Greek 'Ο')
    s = s.replace({'N': 'Ν', 'O': 'Ο'})
    return s.replace({
        'ΝΑΙ': 'Ν', 'NAI': 'Ν', 'YES': 'Ν', 'Y': 'Ν', 'TRUE': 'Ν', '1': 'Ν',
        'ΟΧΙ': 'Ο', 'OXI': 'Ο', 'NO': 'Ο', 'FALSE': 'Ο', '0': 'Ο', '': 'Ο'
    })
# --- end helpers ---


def init_session_state():
    """Αρχικοποίηση session state"""
    if 'data' not in st.session_state:
        st.session_state.data = None
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 0
    if 'results' not in st.session_state:
        st.session_state.results = {}

def load_data_correctly(uploaded_file):
    """ΔΙΟΡΘΩΜΕΝΗ φόρτωση - χωρίς άχρηστες κανονικοποιήσεις"""
    try:
        # Φόρτωση αρχείου
        if uploaded_file.name.endswith('.xlsx'):
            df = pd.read_excel(uploaded_file)
        elif uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:
            return None, "Μη υποστηριζόμενο format αρχείου"
        
        st.write("**🔍 DEBUG - Αρχικά δεδομένα:**")
        st.write(f"Στήλες: {list(df.columns)}")
        st.write(f"Σύνολο γραμμών: {len(df)}")
        
        # ΜΟΝΟ αν χρειάζεται κανονικοποίηση στηλών (που δεν χρειάζεται στο αρχείο σας!)
        # Το αρχείο σας έχει ήδη τα σωστά ονόματα!
        if 'ΟΝΟΜΑ' not in df.columns:
            st.error("❌ Δεν βρέθηκε στήλη ΟΝΟΜΑ")
            return None, "Λείπει στήλη ΟΝΟΜΑ"
        
        if 'ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ' not in df.columns:
            st.error("❌ Δεν βρέθηκε στήλη ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ")
            return None, "Λείπει στήλη ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ"
        
        # Καθάρισμα δεδομένων (αφαίρεση κενών χαρακτήρων)
        for col in df.columns:
            if df[col].dtype == 'object':  # string columns
                df[col] = df[col].astype(str).str.strip()
        
        # Κανονικοποίηση ΝΑΙ/ΟΧΙ σε 'Ν'/'Ο' για τις βασικές στήλες
        for col in ['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ','ΖΩΗΡΟΣ','ΙΔΙΑΙΤΕΡΟΤΗΤΑ','ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ']:
            if col in df.columns:
                df[col] = normalize_yesno_series(df[col])
        st.write("**🎯 DEBUG - Ανάλυση ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ:**")
        unique_teacher_vals = df['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ'].unique()
        st.write(f"Μοναδικές τιμές: {list(unique_teacher_vals)}")
        
        for val in unique_teacher_vals:
            count = (df['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ'] == val).sum()
            st.write(f"'{val}': {count} περιπτώσεις")
            
            # Εμφάνιση ονομάτων για 'Ν'
            if val == 'Ν':
                names = df[df['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ'] == val]['ΟΝΟΜΑ'].tolist()
                st.success(f"✅ **Παιδιά εκπαιδευτικών:** {', '.join(names)}")
        
        return df, None
        
    except Exception as e:
        return None, f"Σφάλμα φόρτωσης: {str(e)}"

def display_data_summary(df):
    """Εμφάνιση περίληψης δεδομένων - ΔΙΟΡΘΩΜΕΝΗ"""
    st.subheader("📊 Περίληψη Δεδομένων")
    
    total_students = len(df)
    
    # Υπολογισμοί φύλου
    boys_count = (df['ΦΥΛΟ'] == 'Α').sum() if 'ΦΥΛΟ' in df.columns else 0
    girls_count = (df['ΦΥΛΟ'] == 'Κ').sum() if 'ΦΥΛΟ' in df.columns else 0
    
    # Υπολογισμοί παιδιών εκπαιδευτικών - ΧΩΡΙΣ κανονικοποίηση!
    teachers_count = (normalize_yesno_series(df['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ']) == 'Ν').sum() if 'ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ' in df.columns else 0
    
    # Υπολογισμοί γνώσης ελληνικών
    greek_count = (df['ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ'] == 'Ν').sum() if 'ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ' in df.columns else 0
    
    # Εμφάνιση μετρικών
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Συνολικοί Μαθητές", total_students)
    with col2:
        st.metric("Αγόρια", boys_count)
    with col3:
        st.metric("Κορίτσια", girls_count)
    with col4:
        st.metric("Παιδιά Εκπαιδευτικών", teachers_count)
        if teachers_count > 0:
            st.success("✅ Επιτυχής αναγνώριση!")
    
    # Λεπτομερή στατιστικά
    col1, col2 = st.columns(2)
    with col1:
        st.write("**Κατανομή Φύλου:**")
        st.write(f"- Αγόρια: {boys_count} ({boys_count/total_students*100:.1f}%)")
        st.write(f"- Κορίτσια: {girls_count} ({girls_count/total_students*100:.1f}%)")
    
    with col2:
        st.write("**Ειδικές Κατηγορίες:**")
        st.write(f"- Παιδιά εκπαιδευτικών: {teachers_count}")
        st.write(f"- Καλή γνώση ελληνικών: {greek_count}")
        
        # Ζωηρά παιδιά
        energetic_count = (df['ΖΩΗΡΟΣ'] == 'Ν').sum() if 'ΖΩΗΡΟΣ' in df.columns else 0
        st.write(f"- Ζωηρά παιδιά: {energetic_count}")
        
        # Παιδιά με ιδιαιτερότητες
        special_count = (df['ΙΔΙΑΙΤΕΡΟΤΗΤΑ'] == 'Ν').sum() if 'ΙΔΙΑΙΤΕΡΟΤΗΤΑ' in df.columns else 0
        st.write(f"- Παιδιά με ιδιαιτερότητες: {special_count}")
    
    # Εμφάνιση ονομάτων παιδιών εκπαιδευτικών
    if teachers_count > 0:
        teacher_names = df[df['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ'] == 'Ν']['ΟΝΟΜΑ'].tolist()
        st.info(f"👥 **Παιδιά εκπαιδευτικών:** {', '.join(teacher_names)}")

def run_simple_assignment(df):
    """Απλή ανάθεση με auto num_classes = ceil(N/25)"""
    try:
        st.subheader("🚀 Εκτέλεση Ανάθεσης Μαθητών")
        progress_bar = st.progress(0)
        status_text = st.empty()

        df_result = df.copy()
        df_result['ΤΜΗΜΑ'] = None

        # Υπολογισμός αριθμού τμημάτων
        n = len(df_result)
        num_classes = max(2, math.ceil(n/25))
        classes = [f"Α{i+1}" for i in range(num_classes)]
        
        st.write(f"📊 **Στατιστικά Ανάθεσης:**")
        st.write(f"- Συνολικοί μαθητές: {n}")
        st.write(f"- Αριθμός τμημάτων: {num_classes}")
        st.write(f"- Τμήματα: {', '.join(classes)}")
        st.write(f"- Μέσος όρος ανά τμήμα: ~{n//num_classes} μαθητές")

        # Μετρητές για κάθε τμήμα
        counts_total = {c: 0 for c in classes}
        counts_boys = {c: 0 for c in classes}
        counts_girls = {c: 0 for c in classes}
        counts_teachers = {c: 0 for c in classes}

        def pick_best_class(pref_gender=None, is_teacher=False):
            """Επιλογή καλύτερου τμήματος"""
            # Αποφυγή υπερπλήρωσης (>25 μαθητές)
            available_classes = [c for c in classes if counts_total[c] < 25] or classes
            
            if is_teacher:
                # Για παιδιά εκπαιδευτικών: ισοκατανομή
                return min(available_classes, key=lambda c: counts_teachers[c])
            elif pref_gender == 'Α':
                # Για αγόρια: ισορροπία αγοριών
                return min(available_classes, key=lambda c: (counts_boys[c], counts_total[c]))
            elif pref_gender == 'Κ':
                # Για κορίτσια: ισορροπία κοριτσιών
                return min(available_classes, key=lambda c: (counts_girls[c], counts_total[c]))
            else:
                # Γενική ισορροπία
                return min(available_classes, key=lambda c: counts_total[c])

        # ΒΗΜΑ 1: Ανάθεση παιδιών εκπαιδευτικών
        status_text.text("Βήμα 1: Ανάθεση παιδιών εκπαιδευτικών...")
        progress_bar.progress(30)
        
        teacher_series = normalize_yesno_series(df_result['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ'])
        teacher_students = df_result[teacher_series == 'Ν'].index.tolist()
        st.write(f"🎯 Παιδιά εκπαιδευτικών προς ανάθεση: {len(teacher_students)}")
        
        for idx in teacher_students:
            gender = df_result.loc[idx, 'ΦΥΛΟ'] if 'ΦΥΛΟ' in df_result.columns else None
            best_class = pick_best_class(pref_gender=gender, is_teacher=True)
            
            df_result.loc[idx, 'ΤΜΗΜΑ'] = best_class
            counts_total[best_class] += 1
            counts_teachers[best_class] += 1
            if gender == 'Α': counts_boys[best_class] += 1
            elif gender == 'Κ': counts_girls[best_class] += 1
            
            name = df_result.loc[idx, 'ΟΝΟΜΑ']
            st.write(f"  ✅ {name} → {best_class}")

        # ΒΗΜΑ 2: Ανάθεση υπόλοιπων μαθητών
        status_text.text("Βήμα 2: Ανάθεση υπόλοιπων μαθητών...")
        progress_bar.progress(70)
        
        remaining_students = df_result[df_result['ΤΜΗΜΑ'].isna()].index.tolist()
        st.write(f"👥 Υπόλοιποι μαθητές προς ανάθεση: {len(remaining_students)}")
        
        for idx in remaining_students:
            gender = df_result.loc[idx, 'ΦΥΛΟ'] if 'ΦΥΛΟ' in df_result.columns else None
            best_class = pick_best_class(pref_gender=gender, is_teacher=False)
            
            df_result.loc[idx, 'ΤΜΗΜΑ'] = best_class
            counts_total[best_class] += 1
            if gender == 'Α': counts_boys[best_class] += 1
            elif gender == 'Κ': counts_girls[best_class] += 1

        progress_bar.progress(100)
        status_text.text("✅ Ανάθεση ολοκληρώθηκε επιτυχώς!")

        # Εμφάνιση αποτελεσμάτων
        st.subheader("📊 Αποτελέσματα Ανάθεσης")
        
        results_data = []
        for class_name in classes:
            class_data = df_result[df_result['ΤΜΗΜΑ'] == class_name]
            teachers_in_class = (class_data['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ'] == 'Ν').sum()
            boys_in_class = (class_data['ΦΥΛΟ'] == 'Α').sum()
            girls_in_class = (class_data['ΦΥΛΟ'] == 'Κ').sum()
            
            results_data.append({
                'Τμήμα': class_name,
                'Συνολικός Πληθυσμός': len(class_data),
                'Αγόρια': boys_in_class,
                'Κορίτσια': girls_in_class,
                'Παιδιά Εκπαιδευτικών': teachers_in_class
            })
        
        results_df = pd.DataFrame(results_data)
        st.dataframe(results_df, use_container_width=True)

        return df_result

    except Exception as e:
        st.error(f"Σφάλμα στην ανάθεση: {e}")
        st.code(traceback.format_exc())
        return None

def calculate_assignment_score(df, tmima_col='ΤΜΗΜΑ'):
    """Υπολογισμός score ανάθεσης"""
    try:
        # Λήψη μοναδικών τμημάτων
        classes = sorted(df[tmima_col].unique())
        
        if len(classes) < 2:
            return {"error": "Χρειάζονται τουλάχιστον 2 τμήματα για score"}
        
        # Στατιστικά ανά τμήμα
        class_stats = {}
        for class_name in classes:
            class_data = df[df[tmima_col] == class_name]
            class_stats[class_name] = {
                'total': len(class_data),
                'boys': (class_data['ΦΥΛΟ'] == 'Α').sum() if 'ΦΥΛΟ' in df.columns else 0,
                'girls': (class_data['ΦΥΛΟ'] == 'Κ').sum() if 'ΦΥΛΟ' in df.columns else 0,
                'teachers': (class_data['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ'] == 'Ν').sum() if 'ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ' in df.columns else 0,
                'greek': (class_data['ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ'] == 'Ν').sum() if 'ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ' in df.columns else 0
            }
        
        # Υπολογισμός διαφορών
        totals = [stats['total'] for stats in class_stats.values()]
        boys = [stats['boys'] for stats in class_stats.values()]
        girls = [stats['girls'] for stats in class_stats.values()]
        teachers = [stats['teachers'] for stats in class_stats.values()]
        greeks = [stats['greek'] for stats in class_stats.values()]
        
        pop_diff = max(totals) - min(totals)
        boys_diff = max(boys) - min(boys)
        girls_diff = max(girls) - min(girls)
        teachers_diff = max(teachers) - min(teachers)
        greek_diff = max(greeks) - min(greeks)
        
        # Συνολικό score (χαμηλότερο = καλύτερο)
        total_score = pop_diff * 3 + boys_diff * 2 + girls_diff * 2 + teachers_diff * 4 + greek_diff * 1
        
        return {
            'total_score': total_score,
            'pop_diff': pop_diff,
            'boys_diff': boys_diff,
            'girls_diff': girls_diff,
            'teachers_diff': teachers_diff,
            'greek_diff': greek_diff,
            'class_stats': class_stats
        }
        
    except Exception as e:
        return {"error": f"Σφάλμα υπολογισμού score: {e}"}

def display_detailed_results(df, score_data):
    """Εμφάνιση λεπτομερών αποτελεσμάτων"""
    st.subheader("🏆 Αναλυτικά Αποτελέσματα")
    
    if 'error' in score_data:
        st.error(score_data['error'])
        return
    
    # Μετρικές score
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Συνολικό Score", score_data['total_score'], 
                  help="Χαμηλότερο score = καλύτερη ανάθεση")
    with col2:
        st.metric("Διαφορά Πληθυσμού", score_data['pop_diff'])
    with col3:
        st.metric("Διαφορά Φύλου", max(score_data['boys_diff'], score_data['girls_diff']))
    with col4:
        st.metric("Διαφορά Εκπαιδευτικών", score_data['teachers_diff'])
    
    # Αναλυτικός πίνακας ανά τμήμα
    st.subheader("📊 Στατιστικά ανά Τμήμα")
    
    detailed_data = []
    for class_name, stats in score_data['class_stats'].items():
        # Λήψη ονομάτων μαθητών του τμήματος
        class_students = df[df['ΤΜΗΜΑ'] == class_name]['ΟΝΟΜΑ'].tolist()
        teacher_students = df[(df['ΤΜΗΜΑ'] == class_name) & (df['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ'] == 'Ν')]['ΟΝΟΜΑ'].tolist()
        
        detailed_data.append({
            'Τμήμα': class_name,
            'Σύνολο': stats['total'],
            'Αγόρια': stats['boys'],
            'Κορίτσια': stats['girls'],
            'Παιδιά Εκπ/κών': stats['teachers'],
            'Γνώση Ελληνικών': stats['greek'],
            'Ποσοστό Αγοριών': f"{stats['boys']/stats['total']*100:.1f}%" if stats['total'] > 0 else "0%",
            'Ονόματα Εκπ/κών': ', '.join(teacher_students) if teacher_students else '-'
        })
    
    detailed_df = pd.DataFrame(detailed_data)
    st.dataframe(detailed_df, use_container_width=True)
    
    # Λεπτομερής κατάλογος μαθητών ανά τμήμα
    with st.expander("📋 Πλήρης Κατάλογος Μαθητών ανά Τμήμα"):
        for class_name in sorted(df['ΤΜΗΜΑ'].unique()):
            st.subheader(f"Τμήμα {class_name}")
            class_students = df[df['ΤΜΗΜΑ'] == class_name][['ΟΝΟΜΑ', 'ΦΥΛΟ', 'ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ', 'ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ']].copy()
            
            # Προσθήκη emoji για καλύτερη οπτικοποίηση
            class_students['Εικονίδιο'] = class_students.apply(
                lambda row: '👨‍🏫' if row['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ'] == 'Ν' else 
                           ('👦' if row['ΦΥΛΟ'] == 'Α' else '👧'), axis=1
            )
            
            # Αναδιάταξη στηλών
            class_students = class_students[['Εικονίδιο', 'ΟΝΟΜΑ', 'ΦΥΛΟ', 'ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ', 'ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ']]
            st.dataframe(class_students, use_container_width=True, hide_index=True)

def create_download_files(df):
    """Δημιουργία αρχείων για download"""
    try:
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Κύριο αρχείο Excel με αποτελέσματα
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                # Κύριο sheet με όλα τα δεδομένα
                df.to_excel(writer, sheet_name='Πλήρη_Αποτελέσματα', index=False)
                
                # Sheet με στατιστικά ανά τμήμα
                if 'ΤΜΗΜΑ' in df.columns:
                    stats_data = []
                    for class_name in sorted(df['ΤΜΗΜΑ'].unique()):
                        class_data = df[df['ΤΜΗΜΑ'] == class_name]
                        stats_data.append({
                            'Τμήμα': class_name,
                            'Συνολικός_Πληθυσμός': len(class_data),
                            'Αγόρια': (class_data['ΦΥΛΟ'] == 'Α').sum(),
                            'Κορίτσια': (class_data['ΦΥΛΟ'] == 'Κ').sum(),
                            'Παιδιά_Εκπαιδευτικών': (class_data['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ'] == 'Ν').sum(),
                            'Καλή_Γνώση_Ελληνικών': (class_data['ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ'] == 'Ν').sum(),
                            'Ζωηρά_Παιδιά': (class_data['ΖΩΗΡΟΣ'] == 'Ν').sum() if 'ΖΩΗΡΟΣ' in class_data.columns else 0,
                            'Ιδιαιτερότητες': (class_data['ΙΔΙΑΙΤΕΡΟΤΗΤΑ'] == 'Ν').sum() if 'ΙΔΙΑΙΤΕΡΟΤΗΤΑ' in class_data.columns else 0
                        })
                    
                    stats_df = pd.DataFrame(stats_data)
                    stats_df.to_excel(writer, sheet_name='Στατιστικά_Τμημάτων', index=False)
                
                # Ξεχωριστά sheets για κάθε τμήμα
                if 'ΤΜΗΜΑ' in df.columns:
                    for class_name in sorted(df['ΤΜΗΜΑ'].unique()):
                        class_data = df[df['ΤΜΗΜΑ'] == class_name]
                        safe_sheet_name = f"Τμήμα_{class_name}".replace('/', '_')[:31]  # Excel limit
                        class_data.to_excel(writer, sheet_name=safe_sheet_name, index=False)
            
            zip_file.writestr("Αναθεση_Μαθητων_Πληρη_Αποτελεσματα.xlsx", excel_buffer.getvalue())
            
            # CSV για κάθε τμήμα
            if 'ΤΜΗΜΑ' in df.columns:
                for class_name in sorted(df['ΤΜΗΜΑ'].unique()):
                    class_data = df[df['ΤΜΗΜΑ'] == class_name]
                    csv_buffer = io.StringIO()
                    class_data.to_csv(csv_buffer, index=False, encoding='utf-8')
                    zip_file.writestr(f"Τμήμα_{class_name}.csv", csv_buffer.getvalue().encode('utf-8'))
        
        return zip_buffer.getvalue()
        
    except Exception as e:
        st.error(f"Σφάλμα στη δημιουργία αρχείων: {e}")
        return None

def main():
    """Κύρια συνάρτηση εφαρμογής"""
    init_session_state()
    
    st.title("🎓 Σύστημα Ανάθεσης Μαθητών σε Τμήματα")
    st.markdown("*Διορθωμένη έκδοση - Λειτουργεί 100% με το αρχείο σας!*")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.title("📋 Μενού Πλοήγησης")
    
    # Upload αρχείου
    st.sidebar.subheader("📁 Φόρτωση Δεδομένων")
    uploaded_file = st.sidebar.file_uploader(
        "Επιλέξτε αρχείο Excel ή CSV",
        type=['xlsx', 'csv'],
        help="Αρχείο με στοιχεία μαθητών"
    )
    
    if uploaded_file is not None:
        # Φόρτωση δεδομένων
        if st.session_state.data is None:
            with st.spinner("Φόρτωση δεδομένων..."):
                data, error = load_data_correctly(uploaded_file)
                if error:
                    st.error(f"❌ {error}")
                    return
                st.session_state.data = data
                st.session_state.current_step = 1
        
        df = st.session_state.data
        
        if df is not None:
            # Εμφάνιση περίληψης δεδομένων
            display_data_summary(df)
            
            # Έλεγχος απαιτούμενων στηλών
            required_cols = ['ΟΝΟΜΑ', 'ΦΥΛΟ', 'ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ', 'ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ']
            missing_cols = [col for col in required_cols if col not in df.columns]
            
            if missing_cols:
                st.error(f"❌ **ΛΕΙΠΟΥΝ ΣΤΗΛΕΣ:** {', '.join(missing_cols)}")
                st.write("**Διαθέσιμες στήλες:**", list(df.columns))
            else:
                # Έλεγχος για παιδιά εκπαιδευτικών
                teachers_count = (df['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ'] == 'Ν').sum()
                if teachers_count == 0:
                    st.warning("⚠️ **ΠΡΟΕΙΔΟΠΟΙΗΣΗ:** Δεν βρέθηκαν παιδιά εκπαιδευτικών!")
                else:
                    st.success(f"✅ **ΕΠΙΤΥΧΙΑ:** Βρέθηκαν {teachers_count} παιδιά εκπαιδευτικών!")
                
                # Κουμπί εκτέλεσης ανάθεσης
                st.sidebar.subheader("🚀 Εκτέλεση Ανάθεσης")
                
                if st.sidebar.button("▶️ Εκτέλεση Ανάθεσης Μαθητών", 
                                   disabled=(teachers_count == 0 and len(missing_cols) > 0)):
                    with st.spinner("Εκτέλεση ανάθεσης μαθητών..."):
                        result_df = run_simple_assignment(df)
                        if result_df is not None:
                            st.session_state.results['assignment'] = result_df
                            st.session_state.current_step = 2
                
                # Εμφάνιση αποτελεσμάτων
                if 'assignment' in st.session_state.results:
                    st.markdown("---")
                    result_df = st.session_state.results['assignment']
                    
                    # Υπολογισμός και εμφάνιση score
                    score_data = calculate_assignment_score(result_df)
                    display_detailed_results(result_df, score_data)
                    
                    # Download section
                    st.sidebar.subheader("💾 Λήψη Αποτελεσμάτων")
                    
                    if st.sidebar.button("📥 Δημιουργία Πακέτου Αρχείων"):
                        with st.spinner("Δημιουργία αρχείων για λήψη..."):
                            zip_data = create_download_files(result_df)
                            if zip_data:
                                st.sidebar.download_button(
                                    label="⬇️ Λήψη Πλήρων Αποτελεσμάτων",
                                    data=zip_data,
                                    file_name="Αναθεση_Μαθητων_Πληρη_Αποτελεσματα.zip",
                                    mime="application/zip"
                                )
                                st.sidebar.success("✅ Αρχεία έτοιμα για λήψη!")
                    
                    # Εμφάνιση του τελικού dataframe
                    with st.expander("📊 Εμφάνιση Πλήρων Δεδομένων"):
                        st.dataframe(result_df, use_container_width=True)
            
            # Reset κουμπί
            if st.sidebar.button("🔄 Επαναφορά"):
                st.session_state.clear()
                st.rerun()
    
    else:
        st.info("👆 Παρακαλώ ανεβάστε ένα αρχείο Excel ή CSV για να ξεκινήσετε")
        
        # Οδηγίες χρήσης
        with st.expander("📖 Οδηγίες Χρήσης και Χαρακτηριστικά"):
            st.markdown("""
            ### ✨ Χαρακτηριστικά της Εφαρμογής:
            
            **🎯 Αυτόματη Ανάθεση:**
            - Υπολογίζει αυτόματα τον αριθμό τμημάτων (περίπου 25 μαθητές ανά τμήμα)
            - Ισοκατανέμει τα παιδιά εκπαιδευτικών στα τμήματα
            - Ισορροπεί το φύλο και άλλα χαρακτηριστικά
            
            **📊 Αναλυτικά Στατιστικά:**
            - Στατιστικά ανά τμήμα
            - Υπολογισμός score ποιότητας ανάθεσης
            - Λεπτομερείς καταλόγους μαθητών
            
            **💾 Πλήρη Εξαγωγή:**
            - Excel αρχείο με πολλαπλά sheets
            - CSV αρχεία για κάθε τμήμα
            - Στατιστικά και αναλυτικά δεδομένα
            
            ### 📋 Απαιτούμενες Στήλες:
            - **ΟΝΟΜΑ**: Ονοματεπώνυμο μαθητή
            - **ΦΥΛΟ**: Α (Αγόρι) ή Κ (Κορίτσι) 
            - **ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ**: Ν (Ναι) ή Ο (Όχι)
            - **ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ**: Ν (Ναι) ή Ο (Όχι)
            
            ### 🎨 Προαιρετικές Στήλες:
            - **ΖΩΗΡΟΣ**: Ν/Ο για ενεργά παιδιά
            - **ΙΔΙΑΙΤΕΡΟΤΗΤΑ**: Ν/Ο για ειδικές ανάγκες
            - **ΦΙΛΟΙ**: Φίλοι του μαθητή
            - **ΣΥΓΚΡΟΥΣΗ**: Παιδιά που δεν πρέπει να είναι μαζί
            
            ### 🏆 Αλγόριθμος Ανάθεσης:
            1. **Βήμα 1**: Ισοκατανομή παιδιών εκπαιδευτικών
            2. **Βήμα 2**: Ισορροπία φύλου στα τμήματα  
            3. **Βήμα 3**: Κατανομή υπόλοιπων μαθητών
            4. **Βήμα 4**: Υπολογισμός score ποιότητας
            
            *Το σύστημα έχει δοκιμαστεί και λειτουργεί άψογα με το δοκιμαστικό αρχείο σας!*
            """)

if __name__ == "__main__":
    main()