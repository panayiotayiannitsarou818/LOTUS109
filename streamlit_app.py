import streamlit as st
import pandas as pd
from typing import Dict, Any

st.set_page_config(
    page_title="Ψηφιακή Κατανομή Μαθητών", 
    page_icon="🌸", 
    layout="wide"
)

def get_app_status() -> Dict[str, Any]:
    """Επιστρέφει την κατάσταση του app"""
    return {
        'auth_ok': st.session_state.get('auth_ok', False),
        'terms_ok': st.session_state.get('terms_ok', False),
        'app_enabled': st.session_state.get('app_enabled', False),
        'data_loaded': st.session_state.get('input_df') is not None,
        'pipeline_completed': st.session_state.get('pipeline_output') is not None,
        'student_count': len(st.session_state['input_df']) if st.session_state.get('input_df') is not None else 0,
        'class_count': st.session_state['pipeline_output']['final_df']['ΤΜΗΜΑ'].nunique() if (
            st.session_state.get('pipeline_output') and 
            st.session_state['pipeline_output'].get('final_df') is not None and
            'ΤΜΗΜΑ' in st.session_state['pipeline_output']['final_df'].columns
        ) else 0
    }

def main():
    st.title("🌸 Ψηφιακή Κατανομή Μαθητών")
    st.write("Σύστημα ανάθεσης μαθητών σε τμήματα με αλγόριθμο 7 βημάτων")
    
    # Login Section
    if not st.session_state.get('auth_ok', False):
        st.header("🔐 Είσοδος στο Σύστημα")
        
        # Quick info box
        with st.container():
            st.info("""
            **Demo Credentials:**
            • Κωδικός: `katanomi2025`
            • Απαιτείται αποδοχή όρων χρήσης
            """)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            password = st.text_input(
                "Κωδικός Πρόσβασης:", 
                type="password",
                help="Έλεγχος κωδικού και αποδοχής όρων για πρόσβαση στις σελίδες."
            )
            
            terms_accepted = st.checkbox("Αποδέχομαι τους όρους χρήσης")
            
            if st.button("Είσοδος", type="primary"):
                if password == "katanomi2025" and terms_accepted:
                    st.session_state['auth_ok'] = True
                    st.session_state['terms_ok'] = True
                    st.session_state['app_enabled'] = True  # Auto-enable μετά το login
                    st.success("✅ Επιτυχής είσοδος!")
                    st.rerun()
                else:
                    st.error("❌ Λάθος κωδικός ή δεν έχετε αποδεχθεί τους όρους")
        
        with col2:
            st.markdown("### 🎯 Χαρακτηριστικά")
            st.markdown("""
            • 7-βήμα κατανομή
            • Excel εισαγωγή/εξαγωγή
            • Αναλυτικά στατιστικά
            • Interactive visualizations
            • Demo mode με stubs
            """)
        
        return
    
    # Sidebar Controls
    with st.sidebar:
        st.header("⚙️ Έλεγχος Εφαρμογής")
        
        st.session_state['app_enabled'] = st.toggle(
            "Ενεργοποίηση εφαρμογής",
            value=st.session_state.get('app_enabled', False),
            help="Γενικός διακόπτης on/off. Αν είναι off, όλες οι σελίδες μπλοκάρονται."
        )
        
        # App Status στο sidebar
        status = get_app_status()
        st.markdown("---")
        st.subheader("📊 Κατάσταση")
        
        if status['app_enabled']:
            st.success("🟢 Εφαρμογή Ενεργή")
        else:
            st.error("🔴 Εφαρμογή Απενεργοποιημένη")
        
        if status['data_loaded']:
            st.success(f"📥 Δεδομένα: {status['student_count']} μαθητές")
        else:
            st.info("📥 Δεδομένα: Μη φορτωμένα")
        
        if status['pipeline_completed']:
            st.success(f"🧠 Pipeline: {status['class_count']} τμήματα")
        else:
            st.info("🧠 Pipeline: Εκκρεμές")
        
        # Reset Options
        st.markdown("---")
        st.subheader("🔄 Επανεκκίνηση")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Soft Reset", help="Καθαρισμός δεδομένων & pipeline"):
                # Καθαρισμός μόνο δεδομένων
                if 'input_df' in st.session_state:
                    del st.session_state['input_df']
                if 'pipeline_output' in st.session_state:
                    del st.session_state['pipeline_output']
                st.success("Soft reset ολοκληρώθηκε")
                st.rerun()
        
        with col2:
            if st.button("Hard Reset", help="Επαναφορά σε login screen"):
                # Καθαρισμός όλου του state
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.success("Hard reset ολοκληρώθηκε")
                st.rerun()
    
    # Main Content
    status = get_app_status()
    
    # Current Status Dashboard
    st.header("📈 Κατάσταση Εφαρμογής")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if status['app_enabled']:
            st.metric("Κατάσταση", "🟢 Ενεργή", delta="Ready")
        else:
            st.metric("Κατάσταση", "🔴 Απενεργή", delta="Disabled")
    
    with col2:
        st.metric("Δεδομένα", f"{status['student_count']} μαθητές" if status['data_loaded'] else "Μη φορτωμένα")
    
    with col3:
        st.metric("Τμήματα", f"{status['class_count']}" if status['pipeline_completed'] else "Εκκρεμές")
    
    with col4:
        if status['pipeline_completed']:
            completion = "100%"
            delta = "Ολοκληρώθηκε"
        elif status['data_loaded']:
            completion = "25%"  
            delta = "Δεδομένα έτοιμα"
        else:
            completion = "0%"
            delta = "Αναμονή δεδομένων"
        
        st.metric("Πρόοδος", completion, delta=delta)
    

    # Quick Actions
    st.subheader("⚡ Γρήγορες Ενέργειες")
    qa1, qa2 = st.columns(2)
    with qa1:
        if st.button("🔄 Επανεκκίνηση", help="Καθαρίζει τα φορτωμένα δεδομένα και τα αποτελέσματα (Soft Reset)"):
            st.session_state.pop('input_df', None)
            st.session_state.pop('pipeline_output', None)
            st.success("Έγινε επανεκκίνηση (Soft).")
            st.rerun()
    with qa2:
        if st.button("🚪 Αποσύνδεση", help="Έξοδος από την εφαρμογή και επιστροφή στην οθόνη εισόδου"):
            st.session_state['auth_ok'] = False
            st.session_state['terms_ok'] = False
            st.session_state['app_enabled'] = False
            st.session_state.pop('input_df', None)
            st.session_state.pop('pipeline_output', None)
            st.success("Αποσυνδεθήκατε.")
            st.rerun()
    # Quick Navigation - με conditional enabling
    st.header("🚀 Γρήγορη Πλοήγηση")
    
    nav_col1, nav_col2, nav_col3, nav_col4 = st.columns(4)
    
    with nav_col1:
        if st.button(
            "📥 Εισαγωγή Δεδομένων", 
            use_container_width=True,
            disabled=not status['app_enabled'],
            type="primary" if not status['data_loaded'] else "secondary"
        ):
            st.switch_page("pages/1_📥_Εισαγωγή.py")
    
    with nav_col2:
        if st.button(
            "🧠 Εκτέλεση Βημάτων",
            use_container_width=True,
            disabled=not (status['app_enabled'] and status['data_loaded']),
            type="primary" if (status['data_loaded'] and not status['pipeline_completed']) else "secondary"
        ):
            st.switch_page("pages/2_🧠_Βήματα.py")
    
    with nav_col3:
        if st.button(
            "📊 Στατιστικά",
            use_container_width=True,
            disabled=not (status['app_enabled'] and status['pipeline_completed']),
            type="secondary"
        ):
            st.switch_page("pages/3_📊_Στατιστικά.py")
    
    with nav_col4:
        if st.button(
            "📤 Εξαγωγή",
            use_container_width=True,
            disabled=not (status['app_enabled'] and status['pipeline_completed']),
            type="primary" if status['pipeline_completed'] else "secondary"
        ):
            st.switch_page("pages/4_📤_Εξαγωγή.py")
    
    # Workflow Guide
    st.header("📋 Οδηγίες Χρήσης")
    
    steps_data = [
        {
            "step": "1. Εισαγωγή Δεδομένων", 
            "description": "Ανεβάστε το Excel με τα στοιχεία μαθητών",
            "status": "✅ Ολοκληρώθηκε" if status['data_loaded'] else "⏳ Εκκρεμές",
            "enabled": status['app_enabled']
        },
        {
            "step": "2. Εκτέλεση Αλγορίθμου", 
            "description": "Τρέξτε τα 7 βήματα κατανομής",
            "status": "✅ Ολοκληρώθηκε" if status['pipeline_completed'] else ("🔄 Διαθέσιμο" if status['data_loaded'] else "🔒 Κλειδωμένο"),
            "enabled": status['app_enabled'] and status['data_loaded']
        },
        {
            "step": "3. Προβολή Στατιστικών", 
            "description": "Δείτε αναλυτικά στοιχεία ανά τμήμα",
            "status": "🔄 Διαθέσιμο" if status['pipeline_completed'] else "🔒 Κλειδωμένο",
            "enabled": status['app_enabled'] and status['pipeline_completed']
        },
        {
            "step": "4. Εξαγωγή Αποτελεσμάτων", 
            "description": "Κατεβάστε τα τελικά αρχεία",
            "status": "🔄 Διαθέσιμο" if status['pipeline_completed'] else "🔒 Κλειδωμένο",
            "enabled": status['app_enabled'] and status['pipeline_completed']
        }
    ]
    
    for step_info in steps_data:
        with st.container():
            col_step, col_status = st.columns([3, 1])
            
            with col_step:
                if step_info['enabled']:
                    st.write(f"**{step_info['step']}**: {step_info['description']}")
                else:
                    st.write(f"~~**{step_info['step']}**: {step_info['description']}~~")
            
            with col_status:
                st.write(step_info['status'])
    
    # Detailed Status (expandable)
    with st.expander("🔍 Λεπτομερής Κατάσταση"):
        if status['data_loaded']:
            input_df = st.session_state['input_df']
            
            st.write("**Φορτωμένα Δεδομένα:**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.write(f"• Συνολικοί μαθητές: {len(input_df)}")
                if 'ΦΥΛΟ' in input_df.columns:
                    boys = (input_df['ΦΥΛΟ'] == 'Α').sum()
                    girls = (input_df['ΦΥΛΟ'] == 'Κ').sum()
                    st.write(f"• Αγόρια: {boys}, Κορίτσια: {girls}")
            
            with col2:
                if 'ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ' in input_df.columns:
                    teachers = (input_df['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ'] == 'Ν').sum()
                    st.write(f"• Παιδιά εκπαιδευτικών: {teachers}")
                
                if 'ΖΩΗΡΟΣ' in input_df.columns:
                    lively = (input_df['ΖΩΗΡΟΣ'] == 'Ν').sum()
                    st.write(f"• Ζωηροί μαθητές: {lively}")
            
            with col3:
                if 'ΙΔΙΑΙΤΕΡΟΤΗΤΑ' in input_df.columns:
                    special = (input_df['ΙΔΙΑΙΤΕΡΟΤΗΤΑ'] == 'Ν').sum()
                    st.write(f"• Ιδιαιτερότητες: {special}")
                
                if 'ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ' in input_df.columns:
                    greek = (input_df['ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ'] == 'Ν').sum()
                    st.write(f"• Καλή γνώση ελληνικών: {greek}")
        
        if status['pipeline_completed']:
            pipeline = st.session_state['pipeline_output']
            final_df = pipeline['final_df']
            
            st.write("**Αποτελέσματα Pipeline:**")
            
            if 'ΤΜΗΜΑ' in final_df.columns:
                class_counts = final_df['ΤΜΗΜΑ'].value_counts().sort_index()
                for class_name, count in class_counts.items():
                    st.write(f"• {class_name}: {count} μαθητές")
            
            # Score από βήμα 7 αν υπάρχει
            if 'step7' in pipeline['artifacts']:
                step7_meta = pipeline['artifacts']['step7'].get('meta', {})
                scores = step7_meta.get('scores', {})
                if scores:
                    st.write(f"• Συνολική βαθμολογία: {scores.get('ΣΕΝΑΡΙΟ_1', 0):.1f}/100")
    
    # Footer info
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
    🌸 Ψηφιακή Κατανομή Μαθητών | Streamlit Multi-Page App | Demo Mode με Fallback Stubs
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()