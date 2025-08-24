                        # Show scenario comparison with scores
                        if st.session_state.detailed_steps:
                            st.markdown("### 🏆 Σύγκριση Σεναρίων με Scores")
                            
                            scenario_comparison = []
                            for scenario_num, scenario_data in st.session_state.detailed_steps.items():
                                if 'scores' in scenario_data:
                                    scores = scenario_data['scores']
                                    scenario_comparison.append({
                                        'Σενάριο': f'ΣΕΝΑΡΙΟ_{scenario_num}',
                                        'Βήμα 1': scores.get('step1', 0),
                                        'Βήμα 2': scores.get('step2', 0),
                                        'Βήμα 3': scores.get('step3', 0),
                                        'Βήμα 4': scores.get('step4', 0),
                                        'Βήμα 5': scores.get('step5', 0),
                                        'Βήμα 6': scores.get('step6', 0),
                                        '🏆 ΤΕΛΙΚΟ SCORE': scores.get('final', 0)
                                    })
                            
                            if scenario_comparison:
                                comparison_df = pd.DataFrame(scenario_comparison)
                                
                                # Highlight best scenario (lowest score)
                                best_score = comparison_df['🏆 ΤΕΛΙΚΟ SCORE'].min()
                                best_scenario = comparison_df[comparison_df['🏆 ΤΕΛΙΚΟ SCORE'] == best_score]['Σενάριο'].iloc[0]
                                
                                st.success(f"🥇 **Καλύτερο Σενάριο:**# -*- coding: utf-8 -*-
"""
Streamlit App - Σύστημα Κατανομής Μαθητών Α' Δημοτικού
Ολοκληρωμένη εφαρμογή σύμφωνα με τις προδιαγραφές
Γιαννίτσαρου Παναγιώτα - panayiotayiannitsarou@gmail.com
"""

import streamlit as st
import pandas as pd
import numpy as np
import zipfile
import io
import math
from collections import defaultdict
import copy
import traceback
from datetime import datetime

# Προαιρετικά imports για γραφήματα
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

try:
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Ρύθμιση σελίδας
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
    
    .step-header {
        background: linear-gradient(90deg, #2E86AB, #A23B72);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 1rem 0;
        font-weight: bold;
    }
    
    .main-buttons {
        display: flex;
        justify-content: center;
        gap: 1rem;
        margin: 2rem 0;
        flex-wrap: wrap;
    }
    
    .main-button {
        background: #2E86AB;
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 10px;
        cursor: pointer;
        font-weight: bold;
        min-width: 180px;
        text-align: center;
    }
    
    .main-button:hover {
        background: #A23B72;
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    
    .stats-container {
        background: #f8f9fa;
        padding: 2rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .footer-logo {
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
    
    .copyright-text {
        text-align: center;
        color: #666;
        font-size: 0.9rem;
        margin-top: 2rem;
        padding: 1rem;
        border-top: 1px solid #ddd;
    }
    
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    .error-box {
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Footer Logo
st.markdown("""
<div class="footer-logo">
    © Γιαννίτσαρου Παναγιώτα<br>
    📧 panayiotayiannitsarou@gmail.com
</div>
""", unsafe_allow_html=True)

# Session State Initialization
def init_session_state():
    """Αρχικοποίηση session state"""
    defaults = {
        'authenticated': False,
        'terms_accepted': False,
        'app_enabled': False,
        'data': None,
        'current_section': 'login',
        'step_results': {},
        'final_results': None,
        'statistics': None,
        'detailed_steps': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Authentication System
def show_login():
    """Σελίδα εισόδου με κωδικό"""
    st.markdown("<h1 class='main-header'>🔐 Κλείδωμα Πρόσβασης</h1>", unsafe_allow_html=True)
    
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
        
        st.info("💡 Εισάγετε τον κωδικό πρόσβασης για να συνεχίσετε")

def show_terms():
    """Σελίδα όρων χρήσης"""
    st.markdown("<h1 class='main-header'>📋 Όροι Χρήσης & Πνευματικά Δικαιώματα</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        st.markdown("""
        <div class="stats-container">
        <h3 style="color: #2E86AB; text-align: center;">© Νομική Προστασία</h3>
        
        <p><strong>Δικαιούχος Πνευματικών Δικαιωμάτων:</strong><br>
        <span style="color: #A23B72; font-weight: bold;">Γιαννίτσαρου Παναγιώτα</span><br>
        📧 panayiotayiannitsarou@gmail.com</p>
        
        <hr>
        
        <h4>📜 Όροι Χρήσης:</h4>
        <ol>
        <li><strong>Πνευματικά Δικαιώματα:</strong> Η παρούσα εφαρμογή προστατεύεται από πνευματικά δικαιώματα. Απαγορεύεται η αναπαραγωγή, διανομή ή τροποποίηση χωρίς γραπτή άδεια.</li>
        
        <li><strong>Εκπαιδευτική Χρήση:</strong> Η εφαρμογή προορίζεται αποκλειστικά για εκπαιδευτικούς σκοπούς και την κατανομή μαθητών σε τμήματα.</li>
        
        <li><strong>Προστασία Δεδομένων:</strong> Ο χρήστης υποχρεούται να προστατεύει τα προσωπικά δεδομένα των μαθητών σύμφωνα με τη νομοθεσία GDPR.</li>
        
        <li><strong>Ευθύνη Χρήσης:</strong> Ο χρήστης αναλαμβάνει την πλήρη ευθύνη για τη σωστή και νόμιμη χρήση της εφαρμογής.</li>
        
        <li><strong>Περιορισμοί:</strong> Απαγορεύεται η εμπορική εκμετάλλευση ή η χρήση για σκοπούς εκτός του εκπαιδευτικού περιβάλλοντος.</li>
        </ol>
        
        <hr>
        
        <div style="background: #e3f2fd; padding: 1rem; border-radius: 10px; margin: 1rem 0;">
        <p style="color: #1976d2; font-weight: bold; text-align: center; margin: 0;">
        ⚠️ Η χρήση της εφαρμογής συνεπάγεται αυτόματη αποδοχή των παραπάνω όρων
        </p>
        </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.checkbox("✅ Αποδέχομαι τους όρους χρήσης και τα πνευματικά δικαιώματα", key="terms_checkbox"):
                st.session_state.terms_accepted = True
            else:
                st.session_state.terms_accepted = False
        
        with col2:
            if st.button("➡️ Συνέχεια στην Εφαρμογή", 
                        disabled=not st.session_state.terms_accepted,
                        key="terms_continue",
                        use_container_width=True):
                st.session_state.current_section = 'app_control'
                st.rerun()

def show_app_control():
    """Έλεγχος ενεργοποίησης εφαρμογής"""
    st.markdown("<h1 class='main-header'>⚙️ Έλεγχος Εφαρμογής</h1>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="stats-container">
        <h3 style="color: #2E86AB; text-align: center;">🎛️ Κεντρικός Έλεγχος Συστήματος</h3>
        </div>
        """, unsafe_allow_html=True)
        
        # Εμφάνιση τρέχουσας κατάστασης
        if st.session_state.app_enabled:
            st.markdown("""
            <div class="success-box">
            <h4>🟢 Κατάσταση: ΕΝΕΡΓΗ</h4>
            <p>Η εφαρμογή είναι ενεργοποιημένη και έτοιμη για χρήση.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="warning-box">
            <h4>🔴 Κατάσταση: ΑΠΕΝΕΡΓΟΠΟΙΗΜΕΝΗ</h4>
            <p>Η εφαρμογή είναι απενεργοποιημένη. Πατήστε το κουμπί για ενεργοποίηση.</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Toggle κουμπί
        if st.session_state.app_enabled:
            if st.button("🔴 Απενεργοποίηση Εφαρμογής", 
                        key="disable_app", 
                        use_container_width=True):
                st.session_state.app_enabled = False
                st.success("✅ Η εφαρμογή απενεργοποιήθηκε!")
                st.rerun()
        else:
            if st.button("🟢 Ενεργοποίηση Εφαρμογής", 
                        key="enable_app", 
                        use_container_width=True):
                st.session_state.app_enabled = True
                st.success("✅ Η εφαρμογή ενεργοποιήθηκε!")
                st.rerun()
        
        # Κουμπί συνέχειας
        if st.session_state.app_enabled:
            st.markdown("---")
            if st.button("🚀 Είσοδος στην Κύρια Εφαρμογή", 
                        key="enter_main_app",
                        use_container_width=True):
                st.session_state.current_section = 'main_app'
                st.rerun()

# Helper Functions
def auto_num_classes(df, override=None, min_classes=2):
    """Υπολογισμός αριθμού τμημάτων βάσει του τύπου ⌈N/25⌉"""
    if override is not None:
        try:
            return max(min_classes, int(override))
        except:
            pass
    
    if df is None or len(df) == 0:
        return min_classes
        
    N = len(df)
    calculated_classes = math.ceil(N / 25)
    
    # Ελάχιστα 2 τμήματα, εκτός αν έχουμε λιγότερους από 13 μαθητές
    if N < 13:
        return 1
    else:
        return max(min_classes, calculated_classes)

def validate_excel_columns(df):
    """Έλεγχος απαιτούμενων στηλών"""
    required_columns = [
        'ΟΝΟΜΑ', 'ΦΥΛΟ', 'ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ', 
        'ΖΩΗΡΟΣ', 'ΙΔΙΑΙΤΕΡΟΤΗΤΑ', 'ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ',
        'ΦΙΛΟΙ', 'ΣΥΓΚΡΟΥΣΗ', 'ΤΜΗΜΑ'
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    return missing_columns

def normalize_data(df):
    """Κανονικοποίηση δεδομένων"""
    df = df.copy()
    
    # Κανονικοποίηση φύλου
    if 'ΦΥΛΟ' in df.columns:
        df['ΦΥΛΟ'] = df['ΦΥΛΟ'].astype(str).str.upper().str.strip()
        gender_map = {'ΑΓΟΡΙ': 'Α', 'ΚΟΡΙΤΣΙ': 'Κ', 'BOY': 'Α', 'GIRL': 'Κ', 'M': 'Α', 'F': 'Κ'}
        df['ΦΥΛΟ'] = df['ΦΥΛΟ'].replace(gender_map).fillna('Α')
    
    # Κανονικοποίηση Ν/Ο στηλών
    yes_no_columns = ['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ', 'ΖΩΗΡΟΣ', 'ΙΔΙΑΙΤΕΡΟΤΗΤΑ', 'ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ']
    for col in yes_no_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()
            yn_map = {'ΝΑΙ': 'Ν', 'ΟΧΙ': 'Ο', 'YES': 'Ν', 'NO': 'Ο', '1': 'Ν', '0': 'Ο', 'TRUE': 'Ν', 'FALSE': 'Ο'}
            df[col] = df[col].replace(yn_map).fillna('Ο')
    
    return df

def display_data_summary(df):
    """Εμφάνιση περίληψης δεδομένων"""
    st.markdown("""
    <div class="stats-container">
    <h3 style="color: #2E86AB; text-align: center;">📊 Περίληψη Δεδομένων</h3>
    </div>
    """, unsafe_allow_html=True)
    
    total = len(df)
    boys = (df['ΦΥΛΟ'] == 'Α').sum() if 'ΦΥΛΟ' in df.columns else 0
    girls = (df['ΦΥΛΟ'] == 'Κ').sum() if 'ΦΥΛΟ' in df.columns else 0
    teachers_kids = (df['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ'] == 'Ν').sum() if 'ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ' in df.columns else 0
    active = (df['ΖΩΗΡΟΣ'] == 'Ν').sum() if 'ΖΩΗΡΟΣ' in df.columns else 0
    special = (df['ΙΔΙΑΙΤΕΡΟΤΗΤΑ'] == 'Ν').sum() if 'ΙΔΙΑΙΤΕΡΟΤΗΤΑ' in df.columns else 0
    good_greek = (df['ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ'] == 'Ν').sum() if 'ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ' in df.columns else 0
    
    num_classes = auto_num_classes(df)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Συνολικοί Μαθητές", total)
    col2.metric("👦 Αγόρια", boys)
    col3.metric("👧 Κορίτσια", girls)
    col4.metric("🎯 Απαιτούμενα Τμήματα", num_classes)
    
    st.markdown("---")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏫 Παιδιά Εκπαιδευτικών", teachers_kids)
    col2.metric("⚡ Ζωηροί", active)
    col3.metric("🎨 Ιδιαιτερότητες", special)
    col4.metric("🇬🇷 Καλή Γνώση Ελληνικών", good_greek)
    
    # Γράφημα κατανομής φύλου
    if PLOTLY_AVAILABLE and boys > 0 and girls > 0:
        fig = px.pie(
            values=[boys, girls], 
            names=['Αγόρια', 'Κορίτσια'],
            title="Κατανομή Φύλου",
            color_discrete_map={'Αγόρια': '#2E86AB', 'Κορίτσια': '#A23B72'}
        )
        st.plotly_chart(fig, use_container_width=True)

# Core Student Distribution Class
class StudentDistributor:
    def __init__(self, data):
        self.data = data.copy()
        self.num_classes = auto_num_classes(data)
        self.scenarios = {}
        
    def step1_population_balance(self, scenario_num):
        """Βήμα 1: Ισορροπία Πληθυσμού"""
        total_students = len(self.data)
        
        # Υπολογισμός αριθμού τμημάτων: ⌈N/25⌉
        self.num_classes = math.ceil(total_students / 25)
        
        # Δημιουργία base assignment
        students_per_class = total_students // self.num_classes
        remainder = total_students % self.num_classes
        
        assignment = []
        for i in range(self.num_classes):
            class_size = students_per_class + (1 if i < remainder else 0)
            # Δυναμικά ονόματα τμημάτων (Α1, Α2, Α3, κτλ ή ΤΜΗΜΑ_1, ΤΜΗΜΑ_2, κτλ)
            if self.num_classes <= 10:
                class_name = f'Α{i+1}'  # Α1, Α2, Α3...
            else:
                class_name = f'ΤΜΗΜΑ_{i+1}'  # ΤΜΗΜΑ_1, ΤΜΗΜΑ_2...
            assignment.extend([class_name] * class_size)
        
        np.random.seed(scenario_num * 42)  # Διαφορετικό seed για κάθε σενάριο
        np.random.shuffle(assignment)
        
        return assignment
    
    def step2_gender_balance(self, scenario_num, previous_step):
        """Βήμα 2: Ισορροπία Φύλου"""
        result = previous_step.copy()
        
        # Group by class
        classes = defaultdict(list)
        for idx, class_name in enumerate(result):
            if class_name:
                classes[class_name].append(idx)
        
        # Balance gender in each class
        for class_name, student_indices in classes.items():
            boys = [idx for idx in student_indices if self.data.iloc[idx]['ΦΥΛΟ'] == 'Α']
            girls = [idx for idx in student_indices if self.data.iloc[idx]['ΦΥΛΟ'] == 'Κ']
            
            target_boys = len(student_indices) // 2
            
            # Simple balancing - move excess to other classes
            if len(boys) > target_boys + 1:
                excess_boys = boys[target_boys + 1:]
                # Find classes that need boys
                for other_class, other_indices in classes.items():
                    if other_class != class_name and excess_boys:
                        other_boys = [idx for idx in other_indices if self.data.iloc[idx]['ΦΥΛΟ'] == 'Α']
                        if len(other_boys) < len(other_indices) // 2:
                            # Move one boy
                            boy_to_move = excess_boys.pop(0)
                            result[boy_to_move] = other_class
        
        return result
    
    def step3_teacher_children(self, scenario_num, previous_step):
        """Βήμα 3: Κατανομή Παιδιών Εκπαιδευτικών"""
        result = previous_step.copy()
        
        teacher_children = []
        for idx, row in self.data.iterrows():
            if row.get('ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ') == 'Ν':
                teacher_children.append(idx)
        
        # Δυναμικά ονόματα τμημάτων
        if self.num_classes <= 10:
            class_names = [f'Α{i+1}' for i in range(self.num_classes)]
        else:
            class_names = [f'ΤΜΗΜΑ_{i+1}' for i in range(self.num_classes)]
            
        # Distribute teacher children evenly across classes
        for i, child_idx in enumerate(teacher_children):
            target_class = class_names[i % self.num_classes]
            result[child_idx] = target_class
        
        return result
    
    def step4_active_students(self, scenario_num, previous_step):
        """Βήμα 4: Κατανομή Ζωηρών Μαθητών"""
        result = previous_step.copy()
        
        active_students = []
        for idx, row in self.data.iterrows():
            if row.get('ΖΩΗΡΟΣ') == 'Ν':
                active_students.append(idx)
        
        # Δυναμικά ονόματα τμημάτων
        if self.num_classes <= 10:
            class_names = [f'Α{i+1}' for i in range(self.num_classes)]
        else:
            class_names = [f'ΤΜΗΜΑ_{i+1}' for i in range(self.num_classes)]
            
        for i, student_idx in enumerate(active_students):
            target_class = class_names[i % self.num_classes]
            result[student_idx] = target_class
        
        return result
    
    def step5_special_needs(self, scenario_num, previous_step):
        """Βήμα 5: Κατανομή Μαθητών με Ιδιαιτερότητες"""
        result = previous_step.copy()
        
        special_students = []
        for idx, row in self.data.iterrows():
            if row.get('ΙΔΙΑΙΤΕΡΟΤΗΤΑ') == 'Ν':
                special_students.append(idx)
        
        # Δυναμικά ονόματα τμημάτων
        if self.num_classes <= 10:
            class_names = [f'Α{i+1}' for i in range(self.num_classes)]
        else:
            class_names = [f'ΤΜΗΜΑ_{i+1}' for i in range(self.num_classes)]
            
        for i, student_idx in enumerate(special_students):
            target_class = class_names[i % self.num_classes]
            result[student_idx] = target_class
        
        return result
    
    def parse_relationships(self, relationship_str):
        """Parse φιλίες/συγκρούσεις"""
        if pd.isna(relationship_str) or relationship_str == '':
            return []
        return [name.strip() for name in str(relationship_str).split(',')]
    
    def step6_friendships(self, scenario_num, previous_step):
        """Βήμα 6: Διατήρηση Φιλιών"""
        result = previous_step.copy()
        
        # Find mutual friendships
        friendships = {}
        for idx, row in self.data.iterrows():
            name = row['ΟΝΟΜΑ']
            friends = self.parse_relationships(row.get('ΦΙΛΟΙ', ''))
            friendships[name] = friends
        
        # Process mutual friendships
        processed = set()
        for name, friends in friendships.items():
            if name in processed:
                continue
            
            for friend in friends:
                if friend in friendships and name in friendships[friend]:
                    # Mutual friendship found
                    name_idx = self.data[self.data['ΟΝΟΜΑ'] == name].index
                    friend_idx = self.data[self.data['ΟΝΟΜΑ'] == friend].index
                    
                    if len(name_idx) > 0 and len(friend_idx) > 0:
                        name_idx = name_idx[0]
                        friend_idx = friend_idx[0]
                        
                        # Put friends in same class
                        result[friend_idx] = result[name_idx]
                        processed.add(name)
                        processed.add(friend)
                        break
        
        return result
    
    def step7_final_conflicts(self, scenario_num, previous_step):
        """Βήμα 7: Αποφυγή Συγκρούσεων & Τελική Κατανομή"""
        result = previous_step.copy()
        
        # Handle conflicts
        conflicts = []
        for idx, row in self.data.iterrows():
            name = row['ΟΝΟΜΑ']
            conflict_names = self.parse_relationships(row.get('ΣΥΓΚΡΟΥΣΗ', ''))
            for conflict in conflict_names:
                conflicts.append((name, conflict))
        
        # Δυναμικά ονόματα τμημάτων για εναλλακτικές επιλογές
        if self.num_classes <= 10:
            all_classes = [f'Α{i+1}' for i in range(self.num_classes)]
        else:
            all_classes = [f'ΤΜΗΜΑ_{i+1}' for i in range(self.num_classes)]
        
        # Resolve conflicts
        for name1, name2 in conflicts:
            name1_idx = self.data[self.data['ΟΝΟΜΑ'] == name1].index
            name2_idx = self.data[self.data['ΟΝΟΜΑ'] == name2].index
            
            if len(name1_idx) > 0 and len(name2_idx) > 0:
                name1_idx = name1_idx[0]
                name2_idx = name2_idx[0]
                
                if result[name1_idx] == result[name2_idx]:
                    # Move second person to different class
                    current_class = result[name1_idx]
                    available_classes = [cls for cls in all_classes if cls != current_class]
                    if available_classes:
                        result[name2_idx] = available_classes[0]
        
        return result
    
    def calculate_scenario_score(self, assignment):
        """Υπολογισμός συνολικού score για ένα σενάριο κατανομής"""
        if not assignment or len(assignment) != len(self.data):
            return float('inf')  # Worst possible score
        
        score = 0
        
        # 1. Population Balance Score (0-100 points)
        class_counts = defaultdict(int)
        for class_assignment in assignment:
            if class_assignment:
                class_counts[class_assignment] += 1
        
        if class_counts:
            populations = list(class_counts.values())
            pop_std = np.std(populations)
            max_pop = max(populations)
            
            # Penalty for classes > 25 students (heavy penalty)
            if max_pop > 25:
                score += (max_pop - 25) * 50
            
            # Penalty for population imbalance
            score += pop_std * 10
        
        # 2. Gender Balance Score (0-50 points)
        for class_name in class_counts.keys():
            class_indices = [i for i, cls in enumerate(assignment) if cls == class_name]
            boys = sum(1 for i in class_indices if self.data.iloc[i]['ΦΥΛΟ'] == 'Α')
            girls = len(class_indices) - boys
            gender_diff = abs(boys - girls)
            score += gender_diff * 2
        
        # 3. Special Categories Balance (0-30 points each)
        special_categories = ['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ', 'ΖΩΗΡΟΣ', 'ΙΔΙΑΙΤΕΡΟΤΗΤΑ', 'ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ']
        
        for category in special_categories:
            if category in self.data.columns:
                category_distribution = defaultdict(int)
                for class_name in class_counts.keys():
                    class_indices = [i for i, cls in enumerate(assignment) if cls == class_name]
                    category_count = sum(1 for i in class_indices 
                                       if self.data.iloc[i].get(category, 'Ο') == 'Ν')
                    category_distribution[class_name] = category_count
                
                if category_distribution:
                    cat_values = list(category_distribution.values())
                    cat_std = np.std(cat_values)
                    score += cat_std * 5
        
        # 4. Friendship Score (0-100 points)
        broken_friendships = 0
        processed_pairs = set()
        
        for idx, row in self.data.iterrows():
            if idx < len(assignment):
                name = row['ΟΝΟΜΑ']
                current_class = assignment[idx]
                friends = self.parse_relationships(row.get('ΦΙΛΟΙ', ''))
                
                for friend in friends:
                    friend_rows = self.data[self.data['ΟΝΟΜΑ'] == friend]
                    if len(friend_rows) > 0:
                        friend_idx = friend_rows.index[0]
                        if friend_idx < len(assignment):
                            friend_class = assignment[friend_idx]
                            
                            # Check if friendship is mutual
                            friend_friends = self.parse_relationships(
                                friend_rows.iloc[0].get('ΦΙΛΟΙ', '')
                            )
                            
                            pair = tuple(sorted([name, friend]))
                            if name in friend_friends and pair not in processed_pairs:
                                if current_class != friend_class:
                                    broken_friendships += 1
                                processed_pairs.add(pair)
        
        score += broken_friendships * 20
        
        # 5. Conflict Penalty (0-200 points)
        conflict_violations = 0
        for idx, row in self.data.iterrows():
            if idx < len(assignment):
                name = row['ΟΝΟΜΑ']
                current_class = assignment[idx]
                conflicts = self.parse_relationships(row.get('ΣΥΓΚΡΟΥΣΗ', ''))
                
                for conflict in conflicts:
                    conflict_rows = self.data[self.data['ΟΝΟΜΑ'] == conflict]
                    if len(conflict_rows) > 0:
                        conflict_idx = conflict_rows.index[0]
                        if conflict_idx < len(assignment):
                            conflict_class = assignment[conflict_idx]
                            if current_class == conflict_class:
                                conflict_violations += 1
        
        score += conflict_violations * 100  # Heavy penalty for conflicts
        
        return round(score, 2)
    
    def run_distribution(self, num_scenarios=3):
        """Εκτέλεση πλήρους κατανομής με score calculation"""
        scenario_scores = {}
        
        for scenario in range(1, num_scenarios + 1):
            scenario_data = {}
            
            # Execute all 7 steps
            step1 = self.step1_population_balance(scenario)
            scenario_data[f'ΒΗΜΑ1_ΣΕΝΑΡΙΟ_{scenario}'] = step1
            score1 = self.calculate_scenario_score(step1)
            
            step2 = self.step2_gender_balance(scenario, step1)
            scenario_data[f'ΒΗΜΑ2_ΣΕΝΑΡΙΟ_{scenario}'] = step2
            score2 = self.calculate_scenario_score(step2)
            
            step3 = self.step3_teacher_children(scenario, step2)
            scenario_data[f'ΒΗΜΑ3_ΣΕΝΑΡΙΟ_{scenario}'] = step3
            score3 = self.calculate_scenario_score(step3)
            
            step4 = self.step4_active_students(scenario, step3)
            scenario_data[f'ΒΗΜΑ4_ΣΕΝΑΡΙΟ_{scenario}'] = step4
            score4 = self.calculate_scenario_score(step4)
            
            step5 = self.step5_special_needs(scenario, step4)
            scenario_data[f'ΒΗΜΑ5_ΣΕΝΑΡΙΟ_{scenario}'] = step5
            score5 = self.calculate_scenario_score(step5)
            
            step6 = self.step6_friendships(scenario, step5)
            scenario_data[f'ΒΗΜΑ6_ΣΕΝΑΡΙΟ_{scenario}'] = step6
            score6 = self.calculate_scenario_score(step6)
            
            step7 = self.step7_final_conflicts(scenario, step6)
            final_score = self.calculate_scenario_score(step7)
            
            # Store scenario with all step scores
            self.scenarios[scenario] = {
                'data': scenario_data,
                'final': step7,
                'scores': {
                    'step1': score1,
                    'step2': score2,
                    'step3': score3,
                    'step4': score4,
                    'step5': score5,
                    'step6': score6,
                    'final': final_score
                }
            }
            
            scenario_scores[scenario] = final_score
        
        # Pick best scenario (lowest score is best)
        best_scenario = min(scenario_scores.keys(), key=lambda k: scenario_scores[k])
        final_assignment = self.scenarios[best_scenario]['final']
        
        # Add final assignment to data
        self.data['ΤΜΗΜΑ'] = final_assignment
        
        return self.data, self.scenarios
    
    def calculate_statistics(self):
        """Υπολογισμός στατιστικών ανά τμήμα"""
        if 'ΤΜΗΜΑ' not in self.data.columns:
            return None
        
        stats = []
        classes = self.data['ΤΜΗΜΑ'].unique()
        classes = [c for c in classes if c and str(c) != 'nan']
        
        for class_name in sorted(classes):
            class_data = self.data[self.data['ΤΜΗΜΑ'] == class_name]
            
            # Count broken friendships
            broken_friendships = 0
            for idx, row in class_data.iterrows():
                name = row['ΟΝΟΜΑ']
                friends = self.parse_relationships(row.get('ΦΙΛΟΙ', ''))
                for friend in friends:
                    friend_data = self.data[self.data['ΟΝΟΜΑ'] == friend]
                    if len(friend_data) > 0 and friend_data.iloc[0]['ΤΜΗΜΑ'] != class_name:
                        broken_friendships += 0.5  # Count each broken friendship once
            
            stat_row = {
                'ΤΜΗΜΑ': class_name,
                'ΑΓΟΡΙΑ': len(class_data[class_data['ΦΥΛΟ'] == 'Α']),
                'ΚΟΡΙΤΣΙΑ': len(class_data[class_data['ΦΥΛΟ'] == 'Κ']),
                'ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ': len(class_data[class_data.get('ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ', '') == 'Ν']),
                'ΖΩΗΡΟΙ': len(class_data[class_data.get('ΖΩΗΡΟΣ', '') == 'Ν']),
                'ΙΔΙΑΙΤΕΡΟΤΗΤΑ': len(class_data[class_data.get('ΙΔΙΑΙΤΕΡΟΤΗΤΑ', '') == 'Ν']),
                'ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ': len(class_data[class_data.get('ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ', '') == 'Ν']),
                'ΣΠΑΣΜΕΝΗ ΦΙΛΙΑ': int(broken_friendships),
                'Σύνολο': len(class_data)
            }
            stats.append(stat_row)
        
        return pd.DataFrame(stats)

# Main Application Functions
def show_main_app():
    """Κύρια εφαρμογή"""
    st.markdown("<h1 class='main-header'>🎓 Κατανομή Μαθητών Α' Δημοτικού</h1>", unsafe_allow_html=True)
    
    # Main Navigation Buttons
    st.markdown("""
    <div style="display: flex; justify-content: center; gap: 1rem; margin: 2rem 0; flex-wrap: wrap;">
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
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
    
    col4, col5, col6 = st.columns(3)
    with col4:
        if st.button("📊 Αναλυτικά Βήματα", key="nav_details", use_container_width=True):
            st.session_state.current_section = 'details'
            st.rerun()
    
    with col5:
        if st.button("🔄 Επανεκκίνηση", key="nav_restart", use_container_width=True):
            st.session_state.current_section = 'restart'
            st.rerun()
    
    with col6:
        if st.button("⚙️ Ρυθμίσεις", key="nav_settings", use_container_width=True):
            st.session_state.current_section = 'settings'
            st.rerun()
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Content based on current section
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
    elif current_section == 'settings':
        show_settings_section()
    else:
        show_upload_section()

def show_upload_section():
    """Ενότητα φόρτωσης Excel"""
    st.markdown("<div class='step-header'>📤 Εισαγωγή Δεδομένων Excel</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="stats-container">
        <h4 style="color: #2E86AB;">📋 Απαιτούμενες Στήλες Excel:</h4>
        <ul>
        <li><strong>ΟΝΟΜΑ</strong> - Όνομα μαθητή</li>
        <li><strong>ΦΥΛΟ</strong> - Α (Αγόρι) ή Κ (Κορίτσι)</li>
        <li><strong>ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ</strong> - Ν (Ναι) ή Ο (Όχι)</li>
        <li><strong>ΖΩΗΡΟΣ</strong> - Ν (Ναι) ή Ο (Όχι)</li>
        <li><strong>ΙΔΙΑΙΤΕΡΟΤΗΤΑ</strong> - Ν (Ναι) ή Ο (Όχι)</li>
        <li><strong>ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ</strong> - Ν (Ναι) ή Ο (Όχι)</li>
        <li><strong>ΦΙΛΟΙ</strong> - Ονόματα χωρισμένα με κόμμα</li>
        <li><strong>ΣΥΓΚΡΟΥΣΗ</strong> - Ονόματα χωρισμένα με κόμμα</li>
        <li><strong>ΤΜΗΜΑ</strong> - Αρχικά κενή</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Επιλέξτε αρχείο Excel (.xlsx)",
            type=['xlsx'],
            key="main_file_upload"
        )
        
        if uploaded_file is not None:
            try:
                with st.spinner("Φόρτωση και επικύρωση δεδομένων..."):
                    # Load Excel file
                    df = pd.read_excel(uploaded_file)
                    
                    # Validate columns
                    missing_columns = validate_excel_columns(df)
                    
                    if missing_columns:
                        st.markdown(f"""
                        <div class="error-box">
                        <h4>❌ Λείπουν απαιτούμενες στήλες:</h4>
                        <p>{', '.join(missing_columns)}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        # Normalize data
                        df = normalize_data(df)
                        st.session_state.data = df
                        
                        st.markdown("""
                        <div class="success-box">
                        <h4>✅ Το αρχείο φορτώθηκε επιτυχώς!</h4>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Display data summary
                        display_data_summary(df)
                        
                        # Preview data
                        with st.expander("👁️ Προεπισκόπηση Δεδομένων"):
                            st.dataframe(df.head(10), use_container_width=True)
                        
                        # Continue button
                        if st.button("➡️ Συνέχεια στην Εκτέλεση", key="continue_to_execute", use_container_width=True):
                            st.session_state.current_section = 'execute'
                            st.rerun()
                            
            except Exception as e:
                st.markdown(f"""
                <div class="error-box">
                <h4>❌ Σφάλμα φόρτωσης αρχείου:</h4>
                <p>{str(e)}</p>
                </div>
                """, unsafe_allow_html=True)

def show_execute_section():
    """Ενότητα εκτέλεσης κατανομής"""
    st.markdown("<div class='step-header'>⚡ Εκτέλεση Κατανομής Μαθητών</div>", unsafe_allow_html=True)
    
    if st.session_state.data is None:
        st.markdown("""
        <div class="warning-box">
        <h4>⚠️ Δεν έχουν φορτωθεί δεδομένα</h4>
        <p>Παρακαλώ φορτώστε πρώτα το αρχείο Excel από την ενότητα "Εισαγωγή Excel".</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("📤 Πήγαινε στην Εισαγωγή Excel", key="go_to_upload", use_container_width=True):
            st.session_state.current_section = 'upload'
            st.rerun()
        return
    
    # Display current data info
    total_students = len(st.session_state.data)
    num_classes = auto_num_classes(st.session_state.data)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("👥 Συνολικοί Μαθητές", total_students)
    col2.metric("🎯 Απαιτούμενα Τμήματα", num_classes)
    col3.metric("📊 Μέγιστος αριθμός/τμήμα", "25")
    
    st.markdown("---")
    
    # Execution settings
    col1, col2 = st.columns(2)
    with col1:
        num_scenarios = st.selectbox(
            "🔢 Αριθμός Σεναρίων:",
            options=[1, 2, 3, 4, 5],
            index=2,
            help="Περισσότερα σενάρια = καλύτερα αποτελέσματα (αλλά πιο αργή εκτέλεση)"
        )
    
    with col2:
        auto_export = st.checkbox(
            "📁 Αυτόματη εξαγωγή μετά την κατανομή",
            value=True,
            help="Θα δημιουργηθούν αυτόματα τα αρχεία εξαγωγής"
        )
    
    st.markdown("---")
    
    # Main execution button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 ΕΚΚΙΝΗΣΗ ΚΑΤΑΝΟΜΗΣ", key="start_distribution", use_container_width=True):
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("🔄 Αρχικοποίηση αλγορίθμου κατανομής...")
                progress_bar.progress(10)
                
                # Initialize distributor
                distributor = StudentDistributor(st.session_state.data)
                
                status_text.text("⚡ Εκτέλεση 7 βημάτων κατανομής...")
                progress_bar.progress(30)
                
                # Run distribution
                final_data, scenarios = distributor.run_distribution(num_scenarios)
                
                status_text.text("📊 Υπολογισμός στατιστικών...")
                progress_bar.progress(70)
                
                # Calculate statistics
                statistics = distributor.calculate_statistics()
                
                status_text.text("💾 Αποθήκευση αποτελεσμάτων...")
                progress_bar.progress(90)
                
                # Store results
                st.session_state.final_results = final_data
                st.session_state.statistics = statistics
                st.session_state.detailed_steps = scenarios
                
                progress_bar.progress(100)
                status_text.text("✅ Κατανομή ολοκληρώθηκε επιτυχώς!")
                
                st.success("🎉 Η κατανομή των μαθητών ολοκληρώθηκε με επιτυχία!")
                
                # Show results summary
                st.markdown("### 📊 Περίληψη Αποτελεσμάτων")
                
                if statistics is not None and len(statistics) > 0:
                    st.dataframe(statistics, use_container_width=True)
                    
                    # Visual statistics
                    if PLOTLY_AVAILABLE:
                        fig_students = px.bar(
                            statistics, 
                            x='ΤΜΗΜΑ', 
                            y='Σύνολο',
                            title='Πληθυσμός ανά Τμήμα',
                            color='Σύνολο',
                            color_continuous_scale='Blues'
                        )
                        st.plotly_chart(fig_students, use_container_width=True)
                        
                        fig_gender = px.bar(
                            statistics,
                            x='ΤΜΗΜΑ',
                            y=['ΑΓΟΡΙΑ', 'ΚΟΡΙΤΣΙΑ'],
                            title='Κατανομή Φύλου ανά Τμήμα',
                            barmode='group'
                        )
                        st.plotly_chart(fig_gender, use_container_width=True)
                
                # Navigation buttons
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("💾 Εξαγωγή Αποτελεσμάτων", key="go_to_export", use_container_width=True):
                        st.session_state.current_section = 'export'
                        st.rerun()
                
                with col2:
                    if st.button("📊 Αναλυτικά Βήματα", key="go_to_details", use_container_width=True):
                        st.session_state.current_section = 'details'
                        st.rerun()
                        
                # Auto export if enabled
                if auto_export:
                    st.session_state.current_section = 'export'
                    st.rerun()
                    
            except Exception as e:
                progress_bar.progress(0)
                status_text.text("")
                st.markdown(f"""
                <div class="error-box">
                <h4>❌ Σφάλμα κατά την εκτέλεση:</h4>
                <p>{str(e)}</p>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander("🔍 Τεχνικές Λεπτομέρειες Σφάλματος"):
                    st.code(traceback.format_exc())

def show_export_section():
    """Ενότητα εξαγωγής αποτελεσμάτων"""
    st.markdown("<div class='step-header'>💾 Εξαγωγή Αποτελεσμάτων</div>", unsafe_allow_html=True)
    
    if st.session_state.final_results is None:
        st.markdown("""
        <div class="warning-box">
        <h4>⚠️ Δεν υπάρχουν αποτελέσματα προς εξαγωγή</h4>
        <p>Παρακαλώ εκτελέστε πρώτα την κατανομή των μαθητών.</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("⚡ Πήγαινε στην Εκτέλεση", key="go_to_execute_from_export", use_container_width=True):
            st.session_state.current_section = 'execute'
            st.rerun()
        return
    
    # Results preview
    st.markdown("### 👁️ Προεπισκόπηση Αποτελεσμάτων")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        if st.session_state.final_results is not None:
            # Show sample of results
            st.dataframe(st.session_state.final_results[['ΟΝΟΜΑ', 'ΦΥΛΟ', 'ΤΜΗΜΑ']].head(10), use_container_width=True)
    
    with col2:
        if st.session_state.statistics is not None:
            st.markdown("**📊 Στατιστικά Κατανομής:**")
            st.dataframe(st.session_state.statistics, use_container_width=True)
    
    st.markdown("---")
    
    # Export options
    st.markdown("### 📁 Επιλογές Εξαγωγής")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 💾 Τελικό Αποτέλεσμα")
        st.info("Αρχείο Excel με την τελική κατανομή στη στήλη ΤΜΗΜΑ")
        
        if st.button("📥 Λήψη Τελικού Excel", key="download_final", use_container_width=True):
            try:
                # Create Excel file
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    # Main results sheet
                    st.session_state.final_results.to_excel(writer, sheet_name='Κατανομή_Μαθητών', index=False)
                    
                    # Statistics sheet
                    if st.session_state.statistics is not None:
                        st.session_state.statistics.to_excel(writer, sheet_name='Στατιστικά', index=False)
                
                # Download button
                st.download_button(
                    label="⬇️ Λήψη Αρχείου",
                    data=output.getvalue(),
                    file_name=f"Κατανομή_Μαθητών_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_final_file"
                )
                
                st.success("✅ Το αρχείο είναι έτοιμο για λήψη!")
                
            except Exception as e:
                st.error(f"❌ Σφάλμα δημιουργίας αρχείου: {str(e)}")
    
    with col2:
        st.markdown("#### 📊 Αναλυτικά Βήματα")
        st.info("ZIP αρχείο με όλα τα ενδιάμεσα βήματα (ΒΗΜΑ1 έως ΒΗΜΑ6)")
        
        if st.button("📥 Λήψη Αναλυτικών Βημάτων", key="download_detailed", use_container_width=True):
            try:
                if st.session_state.detailed_steps is None:
                    st.warning("⚠️ Δεν υπάρχουν αναλυτικά βήματα")
                    return
                
                with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    
                    for scenario_num, scenario_data in st.session_state.detailed_steps.items():
                        # Create Excel for this scenario
                        excel_buffer = io.BytesIO()
                        
                        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                            # Create DataFrame with all steps
                            df_detailed = st.session_state.data.copy()
                            
                            # Add all step columns
                            for step_name, assignments in scenario_data['data'].items():
                                df_detailed[step_name] = assignments
                            
                            # Add final result
                            df_detailed['ΒΗΜΑ7_ΤΕΛΙΚΟ'] = scenario_data['final']
                            
                            # Add scores as a separate column
                            if 'scores' in scenario_data:
                                scores = scenario_data['scores']
                                # Create score summary row at the end
                                score_row = [''] * len(df_detailed.columns)
                                score_indices = {
                                    f'ΒΗΜΑ1_ΣΕΝΑΡΙΟ_{scenario_num}': scores.get('step1', 0),
                                    f'ΒΗΜΑ2_ΣΕΝΑΡΙΟ_{scenario_num}': scores.get('step2', 0),
                                    f'ΒΗΜΑ3_ΣΕΝΑΡΙΟ_{scenario_num}': scores.get('step3', 0),
                                    f'ΒΗΜΑ4_ΣΕΝΑΡΙΟ_{scenario_num}': scores.get('step4', 0),
                                    f'ΒΗΜΑ5_ΣΕΝΑΡΙΟ_{scenario_num}': scores.get('step5', 0),
                                    f'ΒΗΜΑ6_ΣΕΝΑΡΙΟ_{scenario_num}': scores.get('step6', 0),
                                    'ΒΗΜΑ7_ΤΕΛΙΚΟ': scores.get('final', 0)
                                }
                                
                                # Add score column
                                df_detailed['SCORE_ΒΗΜΑΤΟΣ'] = ''
                                for col_name, score in score_indices.items():
                                    if col_name in df_detailed.columns:
                                        df_detailed.loc[0, 'SCORE_ΒΗΜΑΤΟΣ'] = f"Scores ανά βήμα →"
                                
                                # Create separate scores sheet
                                scores_df = pd.DataFrame([{
                                    'Βήμα': f'ΒΗΜΑ{i}',
                                    'Score': score,
                                    'Περιγραφή': desc
                                } for i, (score, desc) in enumerate([
                                    (scores.get('step1', 0), 'Ισορροπία Πληθυσμού'),
                                    (scores.get('step2', 0), 'Ισορροπία Φύλου'),
                                    (scores.get('step3', 0), 'Παιδιά Εκπαιδευτικών'),
                                    (scores.get('step4', 0), 'Ζωηροί Μαθητές'),
                                    (scores.get('step5', 0), 'Ιδιαιτερότητες'),
                                    (scores.get('step6', 0), 'Φιλίες'),
                                    (scores.get('final', 0), 'ΤΕΛΙΚΟ SCORE')
                                ], 1)])
                                
                                scores_df.to_excel(writer, sheet_name='SCORES', index=False)
                            
                            df_detailed.to_excel(writer, sheet_name=f'Σενάριο_{scenario_num}', index=False)
                        
                        zip_file.writestr(
                            f"ΣΕΝΑΡΙΟ_{scenario_num}_Αναλυτικά_Βήματα.xlsx",
                            excel_buffer.getvalue()
                        )
                    
                    # Add comprehensive summary with all scenarios comparison
                    if st.session_state.detailed_steps:
                        summary_buffer = io.BytesIO()
                        with pd.ExcelWriter(summary_buffer, engine='xlsxwriter') as writer:
                            
                            # Main statistics
                            if st.session_state.statistics is not None:
                                st.session_state.statistics.to_excel(writer, sheet_name='Στατιστικά', index=False)
                            
                            # Scenarios comparison with scores
                            scenario_comparison = []
                            for scenario_num, scenario_data in st.session_state.detailed_steps.items():
                                if 'scores' in scenario_data:
                                    scores = scenario_data['scores']
                                    scenario_comparison.append({
                                        'Σενάριο': f'ΣΕΝΑΡΙΟ_{scenario_num}',
                                        'Βήμα_1_Score': scores.get('step1', 0),
                                        'Βήμα_2_Score': scores.get('step2', 0),
                                        'Βήμα_3_Score': scores.get('step3', 0),
                                        'Βήμα_4_Score': scores.get('step4', 0),
                                        'Βήμα_5_Score': scores.get('step5', 0),
                                        'Βήμα_6_Score': scores.get('step6', 0),
                                        'ΤΕΛΙΚΟ_SCORE': scores.get('final', 0)
                                    })
                            
                            if scenario_comparison:
                                comparison_df = pd.DataFrame(scenario_comparison)
                                comparison_df.to_excel(writer, sheet_name='Σύγκριση_Scores', index=False)
                        
                        zip_file.writestr("ΣΥΝΟΨΗ_Σύγκριση_Σεναρίων.xlsx", summary_buffer.getvalue())
                
                # Download button
                st.download_button(
                    label="⬇️ Λήψη ZIP Αρχείου",
                    data=zip_buffer.getvalue(),
                    file_name=f"Αναλυτικά_Βήματα_{datetime.now().strftime('%Y%m%d_%H%M')}.zip",
                    mime="application/zip",
                    key="download_detailed_file"
                )
                
                st.success("✅ Το ZIP αρχείο είναι έτοιμο για λήψη!")
                
                # Show what's included in ZIP
                st.markdown("""
                **📁 Περιεχόμενα ZIP αρχείου:**
                - `ΣΕΝΑΡΙΟ_X_Αναλυτικά_Βήματα.xlsx` - Ένα αρχείο για κάθε σενάριο
                  - **Φύλλο "Σενάριο_X":** Όλα τα δεδομένα + στήλες ΒΗΜΑ1 έως ΒΗΜΑ6 + ΒΗΜΑ7_ΤΕΛΙΚΟ
                  - **Φύλλο "SCORES":** Αναλυτικά scores για κάθε βήμα
                - `ΣΥΝΟΨΗ_Σύγκριση_Σεναρίων.xlsx` - Συνολική σύγκριση
                  - **Φύλλο "Στατιστικά":** Τελικά στατιστικά κατανομής  
                  - **Φύλλο "Σύγκριση_Scores":** Πίνακας με όλα τα scores ανά σενάριο
                """)
                
            except Exception as e:
                st.error(f"❌ Σφάλμα δημιουργίας ZIP: {str(e)}")
                with st.expander("🔍 Τεχνικές Λεπτομέρειες"):
                    st.code(traceback.format_exc())

def show_details_section():
    """Ενότητα αναλυτικών βημάτων"""
    st.markdown("<div class='step-header'>📊 Αναλυτικά Βήματα Κατανομής</div>", unsafe_allow_html=True)
    
    if st.session_state.detailed_steps is None:
        st.markdown("""
        <div class="warning-box">
        <h4>⚠️ Δεν υπάρχουν αναλυτικά βήματα</h4>
        <p>Παρακαλώ εκτελέστε πρώτα την κατανομή των μαθητών.</p>
        </div>
        """, unsafe_allow_html=True)
        return
    
    # Step-by-step analysis
    st.markdown("### 🔍 Ανάλυση Βημάτων Κατανομής")
    
    step_descriptions = {
        'ΒΗΜΑ1': '🎯 Ισορροπία Πληθυσμού - Διαίρεση σε τμήματα ≤25 μαθητών',
        'ΒΗΜΑ2': '⚖️ Ισορροπία Φύλου - Κατανομή αγοριών/κοριτσιών', 
        'ΒΗΜΑ3': '🏫 Παιδιά Εκπαιδευτικών - Ισόποση κατανομή',
        'ΒΗΜΑ4': '⚡ Ζωηροί Μαθητές - Ισόποση κατανομή',
        'ΒΗΜΑ5': '🎨 Ιδιαιτερότητες - Ισόποση κατανομή', 
        'ΒΗΜΑ6': '👫 Φιλίες - Διατήρηση αμοιβαίων φιλιών',
        'ΒΗΜΑ7': '🚫 Συγκρούσεις - Αποφυγή συγκρούσεων & τελική κατανομή'
    }
    
    # Show scenarios
    for scenario_num, scenario_data in st.session_state.detailed_steps.items():
        with st.expander(f"📋 Σενάριο {scenario_num} - Αναλυτικά Βήματα"):
            
            # Show each step
            for step_num in range(1, 8):
                step_key = f'ΒΗΜΑ{step_num}_ΣΕΝΑΡΙΟ_{scenario_num}'
                if step_key in scenario_data['data'] or step_num == 7:
                    
                    st.markdown(f"#### {step_descriptions.get(f'ΒΗΜΑ{step_num}', f'Βήμα {step_num}')}")
                    
                    if step_num == 7:
                        # Final step
                        assignments = scenario_data['final']
                    else:
                        assignments = scenario_data['data'][step_key]
                    
                    # Count assignments per class
                    class_counts = defaultdict(int)
                    for assignment in assignments:
                        if assignment:
                            class_counts[assignment] += 1
                    
                    # Show distribution
                    if class_counts:
                        dist_df = pd.DataFrame([
                            {'Τμήμα': k, 'Μαθητές': v} 
                            for k, v in sorted(class_counts.items())
                        ])
                        
                        col1, col2 = st.columns([1, 2])
                        with col1:
                            st.dataframe(dist_df, use_container_width=True)
                        
                        with col2:
                            if PLOTLY_AVAILABLE and len(dist_df) > 0:
                                fig = px.bar(
                                    dist_df, 
                                    x='Τμήμα', 
                                    y='Μαθητές',
                                    title=f'Κατανομή Βήμα {step_num}'
                                )
                                st.plotly_chart(fig, use_container_width=True)
                    
                    st.markdown("---")

def show_restart_section():
    """Ενότητα επανεκκίνησης"""
    st.markdown("<div class='step-header'>🔄 Επανεκκίνηση Εφαρμογής</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("""
        <div class="warning-box">
        <h4>⚠️ Επανεκκίνηση Συστήματος</h4>
        <p>Η επανεκκίνηση θα διαγράψει:</p>
        <ul>
        <li>Όλα τα φορτωμένα δεδομένα</li>
        <li>Τα αποτελέσματα κατανομής</li>
        <li>Τα στατιστικά και αναλυτικά βήματα</li>
        </ul>
        <p><strong>Η ενέργεια αυτή δεν μπορεί να αναιρεθεί!</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Confirmation checkbox
        confirm_restart = st.checkbox(
            "✅ Επιβεβαιώνω ότι θέλω να επανεκκινήσω την εφαρμογή",
            key="confirm_restart"
        )
        
        # Restart button
        if st.button(
            "🔄 ΕΠΑΝΕΚΚΙΝΗΣΗ ΕΦΑΡΜΟΓΗΣ", 
            key="restart_app_btn",
            disabled=not confirm_restart,
            use_container_width=True
        ):
            # Clear all session state except authentication
            keys_to_keep = ['authenticated', 'terms_accepted', 'app_enabled']
            keys_to_clear = [k for k in st.session_state.keys() if k not in keys_to_keep]
            
            for key in keys_to_clear:
                del st.session_state[key]
            
            # Reset to main app
            st.session_state.current_section = 'upload'
            st.success("✅ Η εφαρμογή επανεκκινήθηκε επιτυχώς!")
            st.rerun()

def show_settings_section():
    """Ενότητα ρυθμίσεων"""
    st.markdown("<div class='step-header'>⚙️ Ρυθμίσεις Εφαρμογής</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("### 🎛️ Παράμετροι Κατανομής")
        
        # Maximum students per class
        max_students = st.slider(
            "Μέγιστος αριθμός μαθητών ανά τμήμα:",
            min_value=20,
            max_value=30,
            value=25,
            help="Σύμφωνα με τις προδιαγραφές: 25 μαθητές"
        )
        
        # Maximum difference between classes
        max_diff = st.slider(
            "Μέγιστη διαφορά πληθυσμού μεταξύ τμημάτων:",
            min_value=1,
            max_value=5,
            value=2,
            help="Σύμφωνα με τις προδιαγραφές: 2 μαθητές"
        )
        
        # Number of scenarios
        num_scenarios = st.selectbox(
            "Αριθμός σεναρίων για εκτέλεση:",
            options=[1, 2, 3, 4, 5],
            index=2,
            help="Περισσότερα σενάρια = καλύτερα αποτελέσματα"
        )
        
        # Auto-calculation of classes
        auto_calc = st.checkbox(
            "Αυτόματος υπολογισμός αριθμού τμημάτων",
            value=True,
            help="Υπολογίζει αυτόματα βάσει του τύπου ⌈N/25⌉"
        )
        
        if not auto_calc:
            manual_classes = st.number_input(
                "Χειροκίνητος αριθμός τμημάτων:",
                min_value=2,
                max_value=10,
                value=2
            )
    
    with col2:
        st.markdown("### 📊 Προτιμήσεις Εμφάνισης")
        
        # Chart preferences
        show_charts = st.checkbox(
            "Εμφάνιση γραφημάτων",
            value=PLOTLY_AVAILABLE,
            help="Γραφήματα για καλύτερη οπτικοποίηση των στατιστικών"
        )
        
        # Theme selection
        theme = st.selectbox(
            "Θέμα εφαρμογής:",
            options=["Μπλε (Προεπιλογή)", "Πράσινο", "Πορτοκαλί"],
            index=0
        )
        
        # Language
        language = st.selectbox(
            "Γλώσσα εφαρμογής:",
            options=["Ελληνικά", "English"],
            index=0,
            help="Προς το παρόν μόνο Ελληνικά"
        )
        
        # Debug mode
        debug_mode = st.checkbox(
            "Λειτουργία εντοπισμού σφαλμάτων",
            value=False,
            help="Εμφανίζει επιπλέον πληροφορίες για προχωρημένους χρήστες"
        )
        
        st.markdown("### 📁 Προτιμήσεις Εξαγωγής")
        
        # Export format
        export_format = st.multiselect(
            "Μορφές εξαγωγής:",
            options=["Excel (.xlsx)", "CSV (.csv)", "PDF Report"],
            default=["Excel (.xlsx)"],
            help="Επιλέξτε τις μορφές που θέλετε να εξάγετε"
        )
        
        # Include detailed steps
        include_details = st.checkbox(
            "Συμπερίληψη αναλυτικών βημάτων στην εξαγωγή",
            value=True
        )
    
    st.markdown("---")
    
    # Save settings
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("💾 Αποθήκευση Ρυθμίσεων", use_container_width=True):
            # Store settings in session state
            settings = {
                'max_students': max_students,
                'max_diff': max_diff,
                'num_scenarios': num_scenarios,
                'auto_calc': auto_calc,
                'manual_classes': manual_classes if not auto_calc else None,
                'show_charts': show_charts,
                'theme': theme,
                'language': language,
                'debug_mode': debug_mode,
                'export_format': export_format,
                'include_details': include_details
            }
            st.session_state.settings = settings
            st.success("✅ Οι ρυθμίσεις αποθηκεύτηκαν!")
    
    with col2:
        if st.button("🔄 Επαναφορά Προεπιλογών", use_container_width=True):
            if 'settings' in st.session_state:
                del st.session_state.settings
            st.success("✅ Επαναφορά στις προεπιλογές!")
            st.rerun()
    
    with col3:
        if st.button("📊 Πληροφορίες Συστήματος", use_container_width=True):
            st.markdown("### 🖥️ Πληροφορίες Συστήματος")
            
            system_info = {
                "Plotly Διαθέσιμο": "✅ Ναι" if PLOTLY_AVAILABLE else "❌ Όχι",
                "Matplotlib Διαθέσιμο": "✅ Ναι" if MATPLOTLIB_AVAILABLE else "❌ Όχι",
                "Pandas Έκδοση": pd.__version__,
                "Numpy Έκδοση": np.__version__,
                "Python Έκδοση": "3.x",
                "Streamlit": "✅ Ενεργό"
            }
            
            for key, value in system_info.items():
                st.write(f"**{key}:** {value}")

# Enhanced Statistical Analysis
def generate_detailed_statistics(data, statistics):
    """Δημιουργία αναλυτικών στατιστικών"""
    if data is None or statistics is None:
        return None
    
    detailed_stats = {
        'population_balance': {},
        'gender_balance': {},
        'special_categories': {},
        'friendships': {},
        'conflicts': {}
    }
    
    # Population balance analysis
    pop_std = statistics['ΣΥΝΟΛΟ'].std()
    pop_mean = statistics['ΣΥΝΟΛΟ'].mean()
    detailed_stats['population_balance'] = {
        'standard_deviation': pop_std,
        'mean': pop_mean,
        'balance_score': max(0, 10 - pop_std)  # Higher is better
    }
    
    # Gender balance analysis
    gender_diffs = abs(statistics['ΑΓΟΡΙΑ'] - statistics['ΚΟΡΙΤΣΙΑ'])
    gender_balance_score = max(0, 10 - gender_diffs.mean())
    detailed_stats['gender_balance'] = {
        'average_difference': gender_diffs.mean(),
        'balance_score': gender_balance_score
    }
    
    # Special categories balance
    special_cols = ['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ', 'ΖΩΗΡΟΙ', 'ΙΔΙΑΙΤΕΡΟΤΗΤΑ', 'ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ']
    for col in special_cols:
        if col in statistics.columns:
            col_std = statistics[col].std()
            detailed_stats['special_categories'][col] = {
                'standard_deviation': col_std,
                'balance_score': max(0, 10 - col_std)
            }
    
    # Friendship analysis
    total_broken = statistics['ΣΠΑΣΜΕΝΗ ΦΙΛΙΑ'].sum()
    friendship_score = max(0, 10 - total_broken)
    detailed_stats['friendships'] = {
        'total_broken': total_broken,
        'friendship_score': friendship_score
    }
    
    return detailed_stats
    
    return detailed_stats

def create_comprehensive_report(data, statistics, detailed_stats):
    """Δημιουργία περιεκτικής αναφοράς"""
    if not all([data is not None, statistics is not None, detailed_stats is not None]):
        return None
    
    report = []
    report.append("# 📊 ΑΝΑΦΟΡΑ ΚΑΤΑΝΟΜΗΣ ΜΑΘΗΤΩΝ Α' ΔΗΜΟΤΙΚΟΥ")
    report.append(f"**Ημερομηνία:** {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    report.append(f"**Συνολικοί Μαθητές:** {len(data)}")
    report.append(f"**Αριθμός Τμημάτων:** {len(statistics)}")
    report.append("")
    
    # Population Analysis
    report.append("## 👥 ΑΝΑΛΥΣΗ ΠΛΗΘΥΣΜΟΥ")
    pop_stats = detailed_stats['population_balance']
    report.append(f"- **Μέσος Όρος Μαθητών/Τμήμα:** {pop_stats['mean']:.1f}")
    report.append(f"- **Τυπική Απόκλιση:** {pop_stats['standard_deviation']:.2f}")
    report.append(f"- **Σκορ Ισορροπίας:** {pop_stats['balance_score']:.1f}/10")
    report.append("")
    
    # Gender Analysis
    report.append("## ⚖️ ΑΝΑΛΥΣΗ ΦΥΛΟΥ")
    gender_stats = detailed_stats['gender_balance']
    report.append(f"- **Μέση Διαφορά Φύλου:** {gender_stats['average_difference']:.1f}")
    report.append(f"- **Σκορ Ισορροπίας Φύλου:** {gender_stats['balance_score']:.1f}/10")
    report.append("")
    
    # Special Categories
    report.append("## 🎯 ΕΙΔΙΚΕΣ ΚΑΤΗΓΟΡΙΕΣ")
    for category, stats in detailed_stats['special_categories'].items():
        category_name = category.replace('_', ' ').title()
        report.append(f"### {category_name}")
        report.append(f"- **Τυπική Απόκλιση:** {stats['standard_deviation']:.2f}")
        report.append(f"- **Σκορ Ισορροπίας:** {stats['balance_score']:.1f}/10")
    report.append("")
    
    # Friendship Analysis
    report.append("## 👫 ΑΝΑΛΥΣΗ ΦΙΛΙΩΝ")
    friend_stats = detailed_stats['friendships']
    report.append(f"- **Συνολικές Σπασμένες Φιλίες:** {friend_stats['total_broken']}")
    report.append(f"- **Σκορ Φιλίας:** {friend_stats['friendship_score']:.1f}/10")
    report.append("")
    
    # Detailed Statistics Table
    report.append("## 📋 ΑΝΑΛΥΤΙΚΟΣ ΠΙΝΑΚΑΣ")
    report.append(statistics.to_string())
    report.append("")
    
    # Recommendations
    report.append("## 💡 ΣΥΣΤΑΣΕΙΣ")
    
    if pop_stats['balance_score'] < 7:
        report.append("- ⚠️ Βελτίωση ισορροπίας πληθυσμού απαιτείται")
    
    if gender_stats['balance_score'] < 7:
        report.append("- ⚠️ Βελτίωση ισορροπίας φύλου απαιτείται")
    
    if friend_stats['total_broken'] > 5:
        report.append("- ⚠️ Πολλές σπασμένες φιλίες - εξετάστε αναδιάταξη")
    
    if all([pop_stats['balance_score'] >= 8, gender_stats['balance_score'] >= 8, friend_stats['total_broken'] <= 2]):
        report.append("- ✅ Εξαιρετική κατανομή! Όλοι οι δείκτες είναι εντός των επιθυμητών ορίων")
    
    return '\n'.join(report)

# Main Application Controller
def main():
    """Κύρια συνάρτηση εφαρμογής"""
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
    
    # Main application
    show_main_app()
    
    # Copyright notice
    st.markdown("""
    <div class="copyright-text">
    © 2024 Γιαννίτσαρου Παναγιώτα - Σύστημα Κατανομής Μαθητών Α' Δημοτικού<br>
    📧 panayiotayiannitsarou@gmail.com | Όλα τα δικαιώματα κατοχυρωμένα
    </div>
    """, unsafe_allow_html=True)

# Additional utility functions
def export_to_multiple_formats(data, statistics, formats=['xlsx']):
    """Εξαγωγή σε πολλαπλές μορφές"""
    exports = {}
    
    if 'xlsx' in formats:
        # Excel export
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
            data.to_excel(writer, sheet_name='Κατανομή_Μαθητών', index=False)
            if statistics is not None:
                statistics.to_excel(writer, sheet_name='Στατιστικά', index=False)
        exports['xlsx'] = excel_buffer.getvalue()
    
    if 'csv' in formats:
        # CSV export
        csv_buffer = io.StringIO()
        data.to_csv(csv_buffer, index=False, encoding='utf-8')
        exports['csv'] = csv_buffer.getvalue().encode('utf-8')
    
    return exports

def validate_data_integrity(data):
    """Έλεγχος ακεραιότητας δεδομένων"""
    issues = []
    
    # Check for duplicate names
    if data['ΟΝΟΜΑ'].duplicated().any():
        duplicates = data[data['ΟΝΟΜΑ'].duplicated()]['ΟΝΟΜΑ'].tolist()
        issues.append(f"Διπλότυπα ονόματα: {', '.join(duplicates)}")
    
    # Check for invalid gender values
    valid_genders = ['Α', 'Κ']
    invalid_genders = data[~data['ΦΥΛΟ'].isin(valid_genders)]
    if len(invalid_genders) > 0:
        issues.append(f"Μη έγκυρες τιμές φύλου: {len(invalid_genders)} εγγραφές")
    
    # Check for invalid yes/no values
    yes_no_columns = ['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ', 'ΖΩΗΡΟΣ', 'ΙΔΙΑΙΤΕΡΟΤΗΤΑ', 'ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ']
    valid_yn = ['Ν', 'Ο']
    
    for col in yes_no_columns:
        if col in data.columns:
            invalid_values = data[~data[col].isin(valid_yn)]
            if len(invalid_values) > 0:
                issues.append(f"Μη έγκυρες τιμές στη στήλη {col}: {len(invalid_values)} εγγραφές")
    
    # Check for missing names
    missing_names = data[data['ΟΝΟΜΑ'].isna() | (data['ΟΝΟΜΑ'] == '')]
    if len(missing_names) > 0:
        issues.append(f"Κενά ονόματα: {len(missing_names)} εγγραφές")
    
    return issues

def suggest_improvements(statistics, detailed_stats):
    """Προτείνει βελτιώσεις στην κατανομή"""
    suggestions = []
    
    if detailed_stats is None:
        return suggestions
    
    # Population balance suggestions
    pop_stats = detailed_stats.get('population_balance', {})
    if pop_stats.get('balance_score', 10) < 7:
        suggestions.append({
            'category': 'Πληθυσμός',
            'priority': 'Υψηλή',
            'suggestion': 'Εξετάστε ανακατανομή μαθητών για καλύτερη ισορροπία πληθυσμού'
        })
    
    # Gender balance suggestions
    gender_stats = detailed_stats.get('gender_balance', {})
    if gender_stats.get('balance_score', 10) < 7:
        suggestions.append({
            'category': 'Φύλο',
            'priority': 'Μεσαία',
            'suggestion': 'Προσπαθήστε να ισορροπήσετε καλύτερα αγόρια και κορίτσια'
        })
    
    # Friendship suggestions
    friend_stats = detailed_stats.get('friendships', {})
    if friend_stats.get('total_broken', 0) > 3:
        suggestions.append({
            'category': 'Φιλίες',
            'priority': 'Μεσαία',
            'suggestion': 'Πολλές σπασμένες φιλίες - εξετάστε εναλλακτικές κατανομές'
        })
    
    # Special categories suggestions
    special_cats = detailed_stats.get('special_categories', {})
    for category, stats in special_cats.items():
        if stats.get('balance_score', 10) < 6:
            cat_name = category.replace('_', ' ').lower()
            suggestions.append({
                'category': 'Ειδικές Κατηγορίες',
                'priority': 'Χαμηλή',
                'suggestion': f'Βελτίωση κατανομής για {cat_name}'
            })
    
    return suggestions

# Run the application
if __name__ == "__main__":
    main()
        