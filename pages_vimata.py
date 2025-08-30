import streamlit as st
import pandas as pd
from typing import Dict, Any
import numpy as np

# Fallback stub functions για demo mode
def stub_run_step1(df: pd.DataFrame) -> Dict[str, Any]:
    """Stub για Βήμα 1: Παιδιά εκπαιδευτικών"""
    result_df = df.copy()
    # Απλή κατανομή παιδιών εκπαιδευτικών
    teachers_kids = result_df[result_df['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ'] == 'Ν'].index
    num_classes = max(2, len(teachers_kids) // 2 + 1)
    
    for i, idx in enumerate(teachers_kids):
        result_df.loc[idx, 'ΤΜΗΜΑ'] = f"Α{(i % num_classes) + 1}"
    
    return {
        "df": result_df,
        "scenarios": {"teachers_distributed": len(teachers_kids)},
        "meta": {"step": 1, "description": "Παιδιά εκπαιδευτικών"}
    }

def stub_run_step2(df: pd.DataFrame) -> Dict[str, Any]:
    """Stub για Βήμα 2: Ζωηροί & Ιδιαιτερότητες"""
    result_df = df.copy()
    
    # Κατανομή ζωηρών
    lively_kids = result_df[(result_df['ΖΩΗΡΟΣ'] == 'Ν') & (result_df['ΤΜΗΜΑ'] == '')].index
    for i, idx in enumerate(lively_kids[:4]):  # Max 4
        result_df.loc[idx, 'ΤΜΗΜΑ'] = f"Α{(i % 2) + 1}"
    
    return {
        "df": result_df,
        "scenarios": {"lively_distributed": min(4, len(lively_kids))},
        "meta": {"step": 2, "description": "Ζωηροί & Ιδιαιτερότητες"}
    }

def stub_run_step3(df: pd.DataFrame) -> Dict[str, Any]:
    """Stub για Βήμα 3: Αμοιβαίες φιλίες"""
    result_df = df.copy()
    return {
        "df": result_df,
        "scenarios": {"friends_processed": 0},
        "meta": {"step": 3, "description": "Αμοιβαίες φιλίες"}
    }

def stub_run_step4(df: pd.DataFrame) -> Dict[str, Any]:
    """Stub για Βήμα 4: Ομάδες"""
    result_df = df.copy()
    return {
        "df": result_df,
        "scenarios": {"groups_formed": 0},
        "meta": {"step": 4, "description": "Ομάδες"}
    }

def stub_run_step5(df: pd.DataFrame) -> Dict[str, Any]:
    """Stub για Βήμα 5: Υπόλοιποι μαθητές"""
    result_df = df.copy()
    
    # Κατανομή υπόλοιπων μαθητών
    remaining = result_df[result_df['ΤΜΗΜΑ'] == ''].index
    num_classes = 2
    
    for i, idx in enumerate(remaining):
        result_df.loc[idx, 'ΤΜΗΜΑ'] = f"Α{(i % num_classes) + 1}"
    
    return {
        "df": result_df,
        "scenarios": {"remaining_distributed": len(remaining)},
        "meta": {"step": 5, "description": "Υπόλοιποι μαθητές"}
    }

def stub_run_step6(df: pd.DataFrame) -> Dict[str, Any]:
    """Stub για Βήμα 6: Τελικός έλεγχος"""
    result_df = df.copy()
    
    # Βασικός balancing
    class_counts = result_df['ΤΜΗΜΑ'].value_counts()
    
    return {
        "df": result_df,
        "scenarios": {"balanced": True},
        "meta": {"step": 6, "description": "Τελικός έλεγχος", "class_counts": class_counts.to_dict()}
    }

def stub_run_step7(df: pd.DataFrame) -> Dict[str, Any]:
    """Stub για Βήμα 7: Βαθμολογία"""
    result_df = df.copy()
    
    # Υπολογισμός βασικού score
    class_counts = result_df['ΤΜΗΜΑ'].value_counts()
    balance_score = 100 - abs(class_counts.max() - class_counts.min()) * 5
    
    return {
        "df": result_df,
        "meta": {
            "step": 7,
            "description": "Βαθμολογία",
            "scores": {"ΣΕΝΑΡΙΟ_1": max(0, balance_score)}
        }
    }

# Import από core modules ή fallback σε stubs
try:
    from core.steps.step1 import run_step1
    from core.steps.step2 import run_step2  
    from core.steps.step3 import run_step3
    from core.steps.step4 import run_step4
    from core.steps.step5 import run_step5
    from core.steps.step6 import run_step6
    from core.steps.step7 import run_step7
    CORE_AVAILABLE = True
except ImportError:
    # Χρήση stubs
    run_step1 = stub_run_step1
    run_step2 = stub_run_step2
    run_step3 = stub_run_step3
    run_step4 = stub_run_step4
    run_step5 = stub_run_step5
    run_step6 = stub_run_step6
    run_step7 = stub_run_step7
    CORE_AVAILABLE = False

# Auth Guard
if not st.session_state.get('auth_ok') or not st.session_state.get('terms_ok') or not st.session_state.get('app_enabled'):
    st.error("❌ Δεν έχετε πρόσβαση. Επιστρέψτε στην αρχική σελίδα.")
    st.stop()

st.title("🧠 Εκτέλεση Βημάτων Κατανομής")

# Demo mode indicator
if not CORE_AVAILABLE:
    st.warning("⚠️ DEMO MODE: Χρήση προσωρινών stub functions (core modules δεν βρέθηκαν)")

# Έλεγχος input
if 'input_df' not in st.session_state:
    st.info("📥 Παρακαλώ φορτώστε πρώτα τα δεδομένα από τη σελίδα 'Εισαγωγή Δεδομένων'")
    st.stop()

input_df = st.session_state['input_df']

st.write(f"📊 Έτοιμο για επεξεργασία: {len(input_df)} εγγραφές")

if st.button(
    "▶️ Εκτέλεση Κατανομής",
    type="primary",
    help="Εκτελεί σειριακά τα 7 Βήματα (1–7) του αλγορίθμου κατανομής και αποθηκεύει το τελικό αποτέλεσμα & τα ενδιάμεσα στο pipeline."
):
    
    with st.spinner("Εκτέλεση αλγορίθμου κατανομής..."):
        try:
            # Αρχικοποίηση pipeline output
            pipeline_output = {
                "final_df": None,
                "artifacts": {}
            }
            
            progress_bar = st.progress(0)
            status_placeholder = st.empty()
            
            # ΒΗΜΑ 1
            status_placeholder.text("⏳ Βήμα 1/7: Παιδιά εκπαιδευτικών...")
            progress_bar.progress(1/7)
            
            step1_result = run_step1(input_df)
            pipeline_output["artifacts"]["step1"] = step1_result
            
            # ΒΗΜΑ 2  
            status_placeholder.text("⏳ Βήμα 2/7: Ζωηροί & Ιδιαιτερότητες...")
            progress_bar.progress(2/7)
            
            step2_result = run_step2(step1_result["df"])
            pipeline_output["artifacts"]["step2"] = step2_result
            
            # ΒΗΜΑ 3
            status_placeholder.text("⏳ Βήμα 3/7: Αμοιβαίες φιλίες...")
            progress_bar.progress(3/7)
            
            step3_result = run_step3(step2_result["df"])
            pipeline_output["artifacts"]["step3"] = step3_result
            
            # ΒΗΜΑ 4
            status_placeholder.text("⏳ Βήμα 4/7: Ομάδες...")
            progress_bar.progress(4/7)
            
            step4_result = run_step4(step3_result["df"])
            pipeline_output["artifacts"]["step4"] = step4_result
            
            # ΒΗΜΑ 5
            status_placeholder.text("⏳ Βήμα 5/7: Υπόλοιποι μαθητές...")
            progress_bar.progress(5/7)
            
            step5_result = run_step5(step4_result["df"])
            pipeline_output["artifacts"]["step5"] = step5_result
            
            # ΒΗΜΑ 6
            status_placeholder.text("⏳ Βήμα 6/7: Τελικός έλεγχος...")
            progress_bar.progress(6/7)
            
            step6_result = run_step6(step5_result["df"])
            pipeline_output["artifacts"]["step6"] = step6_result
            
            # ΒΗΜΑ 7
            status_placeholder.text("⏳ Βήμα 7/7: Βαθμολογία...")
            progress_bar.progress(1.0)
            
            step7_result = run_step7(step6_result["df"])
            pipeline_output["artifacts"]["step7"] = step7_result
            
            # Τελικό DataFrame
            pipeline_output["final_df"] = step7_result["df"]
            
            # Αποθήκευση στο session state
            st.session_state['pipeline_output'] = pipeline_output
            
            status_placeholder.text("✅ Ολοκληρώθηκε!")
            st.success("🎉 Ο αλγόριθμος ολοκληρώθηκε επιτυχώς!")
            
            # Άμεση προεπισκόπηση αποτελέσματος
            st.subheader("🎯 Προεπισκόπηση Αποτελέσματος")
            
            final_df = pipeline_output["final_df"]
            
            # Metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Συνολικοί Μαθητές", len(final_df))
            with col2:
                if 'ΤΜΗΜΑ' in final_df.columns:
                    num_classes = final_df['ΤΜΗΜΑ'].nunique()
                    st.metric("Αριθμός Τμημάτων", num_classes)
            with col3:
                if 'ΤΜΗΜΑ' in final_df.columns:
                    scores = step7_result.get("meta", {}).get("scores", {})
                    main_score = scores.get("ΣΕΝΑΡΙΟ_1", 0)
                    st.metric("Βαθμολογία", f"{main_score:.1f}")
            
            # Κατανομή ανά τμήμα
            if 'ΤΜΗΜΑ' in final_df.columns:
                class_counts = final_df['ΤΜΗΜΑ'].value_counts().sort_index()
                st.write("**Κατανομή ανά Τμήμα:**")
                for class_name, count in class_counts.items():
                    st.write(f"• {class_name}: {count} μαθητές")
            
            # Δείγμα δεδομένων
            st.write("**Δείγμα αποτελέσματος:**")
            st.dataframe(final_df[['ΟΝΟΜΑ', 'ΦΥΛΟ', 'ΤΜΗΜΑ']].head(), use_container_width=True)
            
        except Exception as e:
            st.error(f"❌ Σφάλμα κατά την εκτέλεση: {e}")
            st.exception(e)  # για debugging

# Προβολή κατάστασης pipeline
if 'pipeline_output' in st.session_state:
    st.subheader("📈 Κατάσταση Pipeline")
    
    pipeline = st.session_state['pipeline_output']
    
    cols = st.columns(7)
    for step_num in range(1, 8):
        with cols[step_num - 1]:
            step_key = f"step{step_num}"
            if step_key in pipeline["artifacts"]:
                st.success(f"✅ {step_num}")
            else:
                st.info(f"⏳ {step_num}")

# Quick navigation
st.markdown("---")
st.markdown("**Επόμενο βήμα**: Μετάβαση στα 📊 Στατιστικά ή 📤 Εξαγωγή")