import streamlit as st
import pandas as pd
from io import BytesIO
from typing import Dict, Any
import plotly.express as px

# Fallback stub functions
def stub_build_unified_stats_table(df: pd.DataFrame) -> pd.DataFrame:
    """Stub για δημιουργία πίνακα στατιστικών"""
    if df.empty or 'ΤΜΗΜΑ' not in df.columns:
        return pd.DataFrame({"ΤΜΗΜΑ": ["Α1", "Α2"], "Σύνολο": [25, 25]})
    
    # Βασικά στατιστικά ανά τμήμα
    stats_data = []
    
    for class_name in sorted(df['ΤΜΗΜΑ'].unique()):
        if class_name == '' or pd.isna(class_name):
            continue
            
        class_df = df[df['ΤΜΗΜΑ'] == class_name]
        
        row = {"ΤΜΗΜΑ": class_name, "Σύνολο": len(class_df)}
        
        # Στατιστικά φύλου
        if 'ΦΥΛΟ' in df.columns:
            row["Αγόρια"] = (class_df['ΦΥΛΟ'] == 'Α').sum()
            row["Κορίτσια"] = (class_df['ΦΥΛΟ'] == 'Κ').sum()
        
        # Στατιστικά παιδιών εκπαιδευτικών
        if 'ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ' in df.columns:
            row["Παιδιά_Εκπαιδευτικών"] = (class_df['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ'] == 'Ν').sum()
        
        # Στατιστικά ζωηρών
        if 'ΖΩΗΡΟΣ' in df.columns:
            row["Ζωηροί"] = (class_df['ΖΩΗΡΟΣ'] == 'Ν').sum()
        
        # Στατιστικά ιδιαιτεροτήτων
        if 'ΙΔΙΑΙΤΕΡΟΤΗΤΑ' in df.columns:
            row["Ιδιαιτερότητες"] = (class_df['ΙΔΙΑΙΤΕΡΟΤΗΤΑ'] == 'Ν').sum()
        
        # Στατιστικά γλωσσικών δεξιοτήτων
        if 'ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ' in df.columns:
            row["Καλή_Γνώση_Ελληνικών"] = (class_df['ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ'] == 'Ν').sum()
        
        stats_data.append(row)
    
    return pd.DataFrame(stats_data)

def stub_export_statistics_unified_excel(stats_df: pd.DataFrame) -> BytesIO:
    """Stub για export στατιστικών σε Excel"""
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Κύριος πίνακας στατιστικών
        stats_df.to_excel(writer, sheet_name="Στατιστικά_Τμημάτων", index=False)
        
        # Προσθήκη συνολικών στατιστικών
        if len(stats_df) > 0:
            summary_data = {
                "Μετρικό": ["Συνολικά Τμήματα", "Συνολικοί Μαθητές", "Μέσος Όρος/Τμήμα", "Τυπική Απόκλιση"],
                "Τιμή": [
                    len(stats_df),
                    stats_df['Σύνολο'].sum() if 'Σύνολο' in stats_df.columns else 0,
                    stats_df['Σύνολο'].mean() if 'Σύνολο' in stats_df.columns else 0,
                    stats_df['Σύνολο'].std() if 'Σύνολο' in stats_df.columns else 0
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name="Συνολικά", index=False)
    
    buffer.seek(0)
    return buffer

# Import από core modules ή fallback σε stubs
try:
    from core.stats import build_unified_stats_table, export_statistics_unified_excel
except ImportError:
    build_unified_stats_table = stub_build_unified_stats_table
    export_statistics_unified_excel = stub_export_statistics_unified_excel

# Auth Guard  
if not st.session_state.get('auth_ok') or not st.session_state.get('terms_ok') or not st.session_state.get('app_enabled'):
    st.error("❌ Δεν έχετε πρόσβαση. Επιστρέψτε στην αρχική σελίδα.")
    st.stop()

st.title("📊 Στατιστικά Κατανομής")

# Έλεγχος pipeline
if ('pipeline_output' not in st.session_state or 
    st.session_state['pipeline_output'].get('final_df') is None):
    st.info("🧠 Παρακαλώ εκτελέστε πρώτα τα βήματα κατανομής")
    st.stop()

final_df = st.session_state['pipeline_output']['final_df']
pipeline_output = st.session_state['pipeline_output']

st.write(f"📈 Αναλυτικά στοιχεία για {len(final_df)} μαθητές")

try:
    # Δημιουργία πίνακα στατιστικών
    stats_df = build_unified_stats_table(final_df)
    
    # Βασικές μετρικές στην κορυφή
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Συνολικά Τμήματα", len(stats_df))
    
    with col2:
        if 'Σύνολο' in stats_df.columns:
            total_students = stats_df['Σύνολο'].sum()
            st.metric("Συνολικοί Μαθητές", total_students)
    
    with col3:
        if 'Σύνολο' in stats_df.columns:
            avg_per_class = stats_df['Σύνολο'].mean()
            st.metric("Μέσος Όρος/Τμήμα", f"{avg_per_class:.1f}")
    
    with col4:
        if 'Σύνολο' in stats_df.columns:
            std_dev = stats_df['Σύνολο'].std()
            balance_score = max(0, 100 - std_dev * 10)  # Απλή μετρική balance
            st.metric("Balance Score", f"{balance_score:.1f}/100")
    
    st.subheader("🎯 Πίνακας Στατιστικών ανά Τμήμα")
    st.dataframe(stats_df, use_container_width=True)
    
    # Άμεσο download button για στατιστικά
    @st.cache_data
    def generate_stats_excel(stats_data: pd.DataFrame) -> bytes:
        """Cache-enabled function για generation του stats Excel"""
        try:
            buffer = export_statistics_unified_excel(stats_data)
            return buffer.getvalue()
        except Exception as e:
            st.error(f"Σφάλμα: {e}")
            return b""
    
    stats_excel_data = generate_stats_excel(stats_df)
    
    if stats_excel_data:
        st.download_button(
            label="⬇️ Λήψη Πίνακα Στατιστικών",
            data=stats_excel_data,
            file_name="Πίνακας_Στατιστικών.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Κατεβάζει αναλυτικό πίνακα στατιστικών ανά τμήμα με όλες τις μετρικές."
        )

    # Βελτιωμένα γραφήματα
    if len(stats_df) > 0:
        st.subheader("📊 Οπτικοποίηση Στατιστικών")
        
        # Tab-based organization για καλύτερη UX
        tab1, tab2, tab3 = st.tabs(["📈 Βασικά", "👥 Δημογραφικά", "🎯 Ειδικά Χαρακτηριστικά"])
        
        with tab1:
            if 'Σύνολο' in stats_df.columns:
                # Interactive bar chart με Plotly
                fig = px.bar(
                    stats_df, 
                    x='ΤΜΗΜΑ', 
                    y='Σύνολο',
                    title="Αριθμός Μαθητών ανά Τμήμα",
                    text='Σύνολο'
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(showlegend=False)
                st.plotly_chart(fig, use_container_width=True)
                
                # Balance visualization
                if len(stats_df) > 1:
                    diff = stats_df['Σύνολο'].max() - stats_df['Σύνολο'].min()
                    if diff <= 1:
                        st.success(f"✅ Άριστη ισορροπία! Διαφορά: {diff} μαθητής/ές")
                    elif diff <= 3:
                        st.info(f"ℹ️ Καλή ισορροπία. Διαφορά: {diff} μαθητές")
                    else:
                        st.warning(f"⚠️ Ανισορροπία. Διαφορά: {diff} μαθητές")
        
        with tab2:
            # Gender distribution
            if 'Αγόρια' in stats_df.columns and 'Κορίτσια' in stats_df.columns:
                gender_data = stats_df[['ΤΜΗΜΑ', 'Αγόρια', 'Κορίτσια']].melt(
                    id_vars=['ΤΜΗΜΑ'], 
                    var_name='Φύλο', 
                    value_name='Πλήθος'
                )
                
                fig = px.bar(
                    gender_data,
                    x='ΤΜΗΜΑ',
                    y='Πλήθος',
                    color='Φύλο',
                    title="Κατανομή Φύλου ανά Τμήμα",
                    barmode='stack'
                )
                st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            # Special characteristics
            special_cols = [col for col in stats_df.columns 
                          if col not in ['ΤΜΗΜΑ', 'Σύνολο', 'Αγόρια', 'Κορίτσια']]
            
            if special_cols:
                selected_metric = st.selectbox(
                    "Επιλέξτε μετρικό:",
                    special_cols,
                    help="Διαφορετικά χαρακτηριστικά μαθητών ανά τμήμα"
                )
                
                if selected_metric:
                    fig = px.bar(
                        stats_df,
                        x='ΤΜΗΜΑ',
                        y=selected_metric,
                        title=f"{selected_metric} ανά Τμήμα",
                        text=selected_metric
                    )
                    fig.update_traces(textposition='outside')
                    st.plotly_chart(fig, use_container_width=True)
    
    # Pipeline insights
    with st.expander("🔍 Pipeline Insights"):
        if pipeline_output and 'artifacts' in pipeline_output:
            st.write("**Πληροφορίες από τα βήματα:**")
            
            for step_num in range(1, 8):
                step_key = f"step{step_num}"
                if step_key in pipeline_output['artifacts']:
                    step_data = pipeline_output['artifacts'][step_key]
                    meta = step_data.get('meta', {})
                    scenarios = step_data.get('scenarios', {})
                    
                    if meta or scenarios:
                        st.write(f"**Βήμα {step_num}**: {meta.get('description', 'N/A')}")
                        
                        if scenarios:
                            for scenario, data in scenarios.items():
                                if isinstance(data, dict):
                                    for key, value in data.items():
                                        st.write(f"  • {key}: {value}")
                                else:
                                    st.write(f"  • {scenario}: {data}")

except Exception as e:
    st.error(f"❌ Σφάλμα στη δημιουργία στατιστικών: {e}")
    st.exception(e)  # για debugging

# Quick navigation
st.markdown("---")
st.markdown("**Επόμενο βήμα**: Μετάβαση στην 📤 Εξαγωγή για λήψη των αρχείων")