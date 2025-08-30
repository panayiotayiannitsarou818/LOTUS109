import streamlit as st
import pandas as pd
from typing import Dict, Any

# Auth Guard
if not st.session_state.get('auth_ok') or not st.session_state.get('terms_ok') or not st.session_state.get('app_enabled'):
    st.error("❌ Δεν έχετε πρόσβαση. Επιστρέψτε στην αρχική σελίδα.")
    st.stop()

st.title("📥 Εισαγωγή Δεδομένων")

uploaded_file = st.file_uploader(
    "Επιλέξτε αρχείο Excel:",
    type=['xlsx'],
    help="Ανέβασε το αρχείο εισόδου (.xlsx). Απαιτούμενες στήλες: ΟΝΟΜΑ, ΦΥΛΟ, ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ, ΖΩΗΡΟΣ, ΙΔΙΑΙΤΕΡΟΤΗΤΑ, ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ, ΦΙΛΟΙ, ΣΥΓΚΡΟΥΣΗ. Κωδικοποίηση Ν/Ο για δυαδικά πεδία. Η στήλη ΤΜΗΜΑ θα δημιουργηθεί αυτόματα αν λείπει."
)

def validate_binary_columns(df: pd.DataFrame) -> Dict[str, Any]:
    """Έλεγχος δυαδικών στηλών (Ν/Ο) και επιστροφή warnings"""
    binary_cols = ['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ', 'ΖΩΗΡΟΣ', 'ΙΔΙΑΙΤΕΡΟΤΗΤΑ', 'ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ']
    warnings = []
    stats = {}
    
    for col in binary_cols:
        if col in df.columns:
            valid_values = df[col].isin(['Ν', 'Ο']).sum()
            invalid_values = len(df) - valid_values
            
            if invalid_values > 0:
                warnings.append(f"⚠️ {col}: {invalid_values} μη έγκυρες τιμές (εκτός Ν/Ο)")
            
            stats[col] = {
                'Ν': (df[col] == 'Ν').sum(),
                'Ο': (df[col] == 'Ο').sum(),
                'Invalid': invalid_values
            }
    
    return {'warnings': warnings, 'stats': stats}

if uploaded_file is not None:
    try:
        df = pd.read_excel(uploaded_file)
        
        # Validation απαιτούμενων στηλών (ΤΜΗΜΑ τώρα προαιρετικό)
        required_cols = [
            'ΟΝΟΜΑ', 'ΦΥΛΟ', 'ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ', 'ΖΩΗΡΟΣ', 
            'ΙΔΙΑΙΤΕΡΟΤΗΤΑ', 'ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ', 'ΦΙΛΟΙ', 
            'ΣΥΓΚΡΟΥΣΗ'
        ]
        
        optional_cols = ['ΤΜΗΜΑ']
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        # Δημιουργία προαιρετικών στηλών αν λείπουν
        for col in optional_cols:
            if col not in df.columns:
                df[col] = ""
                st.info(f"ℹ️ Δημιουργήθηκε κενή στήλη: {col}")
        
        if missing_cols:
            st.error(f"❌ Λείπουν απαιτούμενες στήλες: {', '.join(missing_cols)}")
        else:
            # Βασικοί έλεγχοι δεδομένων
            validation_result = validate_binary_columns(df)
            
            # Προβολή warnings
            for warning in validation_result['warnings']:
                st.warning(warning)
            
            # Αποθήκευση στο session state
            st.session_state['input_df'] = df
            
            st.success(f"✅ Επιτυχής φόρτωση: {len(df)} εγγραφές")
            
            # Προβολή πρώτων γραμμών
            st.subheader("Προεπισκόπηση Δεδομένων")
            st.dataframe(df.head(), use_container_width=True)
            
            # Βασικές πληροφορίες με 4 στήλες
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Συνολικοί Μαθητές", len(df))
            
            with col2:
                if 'ΦΥΛΟ' in df.columns:
                    boys = (df['ΦΥΛΟ'] == 'Α').sum()
                    girls = (df['ΦΥΛΟ'] == 'Κ').sum()
                    st.metric("Αγόρια / Κορίτσια", f"{boys} / {girls}")
            
            with col3:
                if 'ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ' in df.columns:
                    teachers = (df['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ'] == 'Ν').sum()
                    st.metric("Παιδιά Εκπαιδευτικών", teachers)
            
            with col4:
                if 'ΖΩΗΡΟΣ' in df.columns:
                    lively = (df['ΖΩΗΡΟΣ'] == 'Ν').sum()
                    st.metric("Ζωηροί Μαθητές", lively)
            
            # Αναλυτικά στατιστικά δυαδικών πεδίων
            if validation_result['stats']:
                with st.expander("📊 Αναλυτικά Στατιστικά"):
                    for col, stats in validation_result['stats'].items():
                        st.write(f"**{col}**: Ν={stats['Ν']}, Ο={stats['Ο']}", 
                                f"{'⚠️ ' + str(stats['Invalid']) + ' invalid' if stats['Invalid'] > 0 else ''}")
                    
    except Exception as e:
        st.error(f"❌ Σφάλμα κατά τη φόρτωση: {e}")

else:
    st.info("📁 Παρακαλώ επιλέξτε ένα αρχείο Excel για να ξεκινήσετε")

# Quick navigation
st.markdown("---")
st.markdown("**Επόμενο βήμα**: Μετάβαση στα 🧠 Βήματα Κατανομής")