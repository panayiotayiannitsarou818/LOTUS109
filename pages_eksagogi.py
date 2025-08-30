import streamlit as st
import pandas as pd
from io import BytesIO
import zipfile
from typing import Any

# Fallback stub functions
def stub_export_final_results_excel(final_df: pd.DataFrame) -> BytesIO:
    """Stub για export τελικού αποτελέσματος"""
    buffer = BytesIO()
    final_df.to_excel(buffer, index=False, sheet_name="Τελικό_Αποτέλεσμα")
    buffer.seek(0)
    return buffer

def stub_export_vima6_all_sheets(pipeline_output: Any) -> BytesIO:
    """Stub για export VIMA6 με όλα τα sheets"""
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Γράψε ένα sheet ανά βήμα
        for step_num in range(1, 8):
            step_key = f"step{step_num}"
            if step_key in pipeline_output["artifacts"]:
                step_data = pipeline_output["artifacts"][step_key]
                df = step_data.get("df", pd.DataFrame())
                
                sheet_name = f"ΒΗΜΑ{step_num}"
                if step_num == 7:
                    # Για βήμα 7, προσθήκη scores
                    scores = step_data.get("meta", {}).get("scores", {})
                    sheet_name = f"ΒΗΜΑ7_SCORE_{scores.get('ΣΕΝΑΡΙΟ_1', 0):.0f}"
                
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        # Προσθήκη summary sheet
        if "final_df" in pipeline_output and pipeline_output["final_df"] is not None:
            final_df = pipeline_output["final_df"]
            
            # Summary στατιστικών
            summary_data = []
            if 'ΤΜΗΜΑ' in final_df.columns:
                class_counts = final_df['ΤΜΗΜΑ'].value_counts().sort_index()
                for class_name, count in class_counts.items():
                    summary_data.append({"ΤΜΗΜΑ": class_name, "ΜΑΘΗΤΕΣ": count})
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name="ΣΥΝΟΨΗ", index=False)
    
    buffer.seek(0)
    return buffer

# Import από core modules ή fallback σε stubs
try:
    from core.io_utils import export_final_results_excel, export_vima6_all_sheets
except ImportError:
    export_final_results_excel = stub_export_final_results_excel
    export_vima6_all_sheets = stub_export_vima6_all_sheets

# Auth Guard
if not st.session_state.get('auth_ok') or not st.session_state.get('terms_ok') or not st.session_state.get('app_enabled'):
    st.error("❌ Δεν έχετε πρόσβαση. Επιστρέψτε στην αρχική σελίδα.")
    st.stop()

st.title("📤 Εξαγωγή Αποτελεσμάτων")

# Έλεγχος pipeline
pipeline_exists = ('pipeline_output' in st.session_state and 
                  st.session_state['pipeline_output'] is not None and
                  st.session_state['pipeline_output'].get('final_df') is not None)

if not pipeline_exists:
    st.info("🧠 Παρακαλώ εκτελέστε πρώτα τα βήματα κατανομής")
    st.stop()

pipeline_output = st.session_state['pipeline_output']
final_df = pipeline_output['final_df']

st.write(f"📋 Διαθέσιμα αποτελέσματα για {len(final_df)} εγγραφές")

# Γρήγορη προεπισκόπηση
with st.expander("👀 Γρήγορη Προεπισκόπηση"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Κατανομή ανά Τμήμα:**")
        if 'ΤΜΗΜΑ' in final_df.columns:
            class_counts = final_df['ΤΜΗΜΑ'].value_counts().sort_index()
            for class_name, count in class_counts.items():
                st.write(f"• {class_name}: {count} μαθητές")
    
    with col2:
        st.write("**Δείγμα δεδομένων:**")
        st.dataframe(final_df[['ΟΝΟΜΑ', 'ΦΥΛΟ', 'ΤΜΗΜΑ']].head(3))

# 1. Τελικό Αποτέλεσμα (άμεσο download)
st.subheader("🎯 Τελικό Αποτέλεσμα")

@st.cache_data
def generate_final_excel(df: pd.DataFrame) -> bytes:
    """Cache-enabled function για generation του τελικού Excel"""
    try:
        buffer = export_final_results_excel(df)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"Σφάλμα: {e}")
        return b""

final_excel_data = generate_final_excel(final_df)

if final_excel_data:
    st.download_button(
        label="⬇️ Λήψη Τελικού Αποτελέσματος",
        data=final_excel_data,
        file_name="Τελικό_Αποτέλεσμα.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="Κατεβάζει το τελικό αρχείο (.xlsx) με τις ίδιες στήλες του εισόδου και συμπληρωμένη τη στήλη ΤΜΗΜΑ."
    )

# 2. Αναλυτικά Βήματα VIMA6 (άμεσο download)
st.subheader("📋 Αναλυτικά Βήματα")

@st.cache_data
def generate_vima6_excel(pipeline_data: Any) -> bytes:
    """Cache-enabled function για generation του VIMA6 Excel"""
    try:
        buffer = export_vima6_all_sheets(pipeline_data)
        return buffer.getvalue()
    except Exception as e:
        st.error(f"Σφάλμα: {e}")
        return b""

vima6_excel_data = generate_vima6_excel(pipeline_output)

if vima6_excel_data:
    st.download_button(
        label="📋 Λήψη Αναλυτικών Βημάτων (VIMA6)",
        data=vima6_excel_data,
        file_name="VIMA6_from_ALL_SHEETS.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="Εξάγει το VIMA6_from_ALL_SHEETS.xlsx με ένα φύλλο ανά έγκυρο σενάριο (ΒΗΜΑ1..ΒΗΜΑ6 + ΒΗΜΑ7_SCORE)."
    )

# 3. ZIP Αναλυτικών (άμεσο download με README)
st.subheader("🗜️ Πακέτο Αναλυτικών")

@st.cache_data
def generate_analytics_zip(final_df: pd.DataFrame, pipeline_data: Any) -> bytes:
    """Cache-enabled function για generation του ZIP"""
    try:
        zip_buffer = BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # README.txt
            readme_content = """ΠΕΡΙΕΧΟΜΕΝΑ ΠΑΚΕΤΟΥ ΑΝΑΛΥΤΙΚΩΝ
=========================================

1. Τελικό_Αποτέλεσμα.xlsx
   - Τελικό αρχείο με την κατανομή μαθητών σε τμήματα
   - Περιέχει όλες τις αρχικές στήλες + στήλη ΤΜΗΜΑ

2. VIMA6_Αναλυτικά.xlsx  
   - Αναλυτικά δεδομένα από όλα τα βήματα του αλγορίθμου
   - Ένα φύλλο ανά βήμα (ΒΗΜΑ1-ΒΗΜΑ7)
   - Φύλλο ΣΥΝΟΨΗ με στατιστικά ανά τμήμα

3. Στατιστικά_Σύνοψη.xlsx (αν διαθέσιμο)
   - Συγκεντρωτικά στοιχεία κατανομής

Δημιουργήθηκε από: Ψηφιακή Κατανομή Μαθητών
"""
            
            zip_file.writestr("README.txt", readme_content)
            
            # Τελικό αποτέλεσμα
            if final_excel_data:
                zip_file.writestr("Τελικό_Αποτέλεσμα.xlsx", final_excel_data)
            
            # VIMA6
            if vima6_excel_data:
                zip_file.writestr("VIMA6_Αναλυτικά.xlsx", vima6_excel_data)
            
            # Πρόσθετα αρχεία (αν διαθέσιμα)
            # TODO: Προσθήκη περισσότερων αρχείων όπως στατιστικών
        
        zip_buffer.seek(0)
        return zip_buffer.getvalue()
        
    except Exception as e:
        st.error(f"Σφάλμα δημιουργίας ZIP: {e}")
        return b""

zip_data = generate_analytics_zip(final_df, pipeline_output)

if zip_data:
    st.download_button(
        label="🗜️ Λήψη ZIP Αναλυτικών",
        data=zip_data,
        file_name="Αναλυτικά_Βήματα.zip",
        mime="application/zip",
        help="Πακέτο .zip με αναλυτικά ενδιάμεσα/σενάρια και README αρχείο."
    )

# Πληροφορίες pipeline
st.subheader("ℹ️ Πληροφορίες Pipeline")

col1, col2 = st.columns(2)

with col1:
    st.write("**Ολοκληρωμένα Βήματα:**")
    completed_steps = 0
    for step_num in range(1, 8):
        step_key = f"step{step_num}"
        if step_key in pipeline_output["artifacts"]:
            st.write(f"✅ Βήμα {step_num}")
            completed_steps += 1
        else:
            st.write(f"❌ Βήμα {step_num}")
    
    st.metric("Ποσοστό Ολοκλήρωσης", f"{(completed_steps/7)*100:.1f}%")

with col2:
    st.write("**Τελικές Μετρικές:**")
    
    if 'ΤΜΗΜΑ' in final_df.columns:
        class_counts = final_df['ΤΜΗΜΑ'].value_counts().sort_index()
        total_classes = len(class_counts)
        avg_students = class_counts.mean()
        std_students = class_counts.std()
        
        st.metric("Αριθμός Τμημάτων", total_classes)
        st.metric("Μέσος Όρος Μαθητών/Τμήμα", f"{avg_students:.1f}")
        st.metric("Τυπική Απόκλιση", f"{std_students:.1f}")
        
        # Score από βήμα 7
        step7_meta = pipeline_output["artifacts"].get("step7", {}).get("meta", {})
        scores = step7_meta.get("scores", {})
        main_score = scores.get("ΣΕΝΑΡΙΟ_1", 0)
        st.metric("Συνολική Βαθμολογία", f"{main_score:.1f}/100")

# Quick navigation
st.markdown("---")
st.markdown("**Επιτυχής ολοκλήρωση!** Μπορείτε να επιστρέψετε στη 📥 Εισαγωγή για νέα δεδομένα ή στα 📊 Στατιστικά για περαιτέρω ανάλυση.")