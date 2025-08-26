# Αντικατάσταση στη συνάρτηση show_details_section() στο streamlit_app.py

def show_details_section():
    """Detailed steps analytics section"""
    st.markdown("## 📊 Αναλυτικά Βήματα Κατανομής")
    
    if st.session_state.detailed_steps is None:
        st.warning("⚠️ Δεν υπάρχουν αναλυτικά βήματα")
        if st.button("⚡ Πήγαινε στην Εκτέλεση", key="go_to_execute_from_details", use_container_width=True):
            st.session_state.current_section = 'execute'
            st.rerun()
        return
    
    st.info("Σε κάθε στήλη εμφανίζονται οι νέες τοποθετήσεις του βήματος και οι τοποθετήσεις του αμέσως προηγούμενου βήματος. Τα υπόλοιπα κελιά μένουν κενά.")
    
    # Display analytical steps per scenario
    for scenario_num, scenario_data in st.session_state.detailed_steps.items():
        st.markdown(f"### 📄 Σενάριο {scenario_num} — Αναλυτική Προβολή")
        view = build_analytics_view_upto6_with_score(st.session_state.data, scenario_data, scenario_num)
        st.dataframe(view, use_container_width=True, hide_index=True)
        
        # Display score
        if 'step7_score' in scenario_data:
            st.markdown(f"**🏆 ΒΗΜΑ7 Βαθμολογία:** {scenario_data['step7_score']}")
        
        st.markdown("---")
    
    # ========= ΤΡΟΠΟΠΟΙΗΣΗ ΕΔΩ =========
    # Export VIMA6 format directly instead of ZIP
    st.markdown("### 📥 Λήψη Αναλυτικών Βημάτων (VIMA6 Format)")
    st.info("Ενιαίο Excel αρχείο με τη μορφή VIMA6_from_ALL_SHEETS.xlsx - σωρευτικά βήματα σε ένα φύλλο")
    
    if st.button("📥 Λήψη VIMA6_from_ALL_SHEETS.xlsx", key="download_vima6_format", use_container_width=True):
        try:
            # Συλλογή scores από scenarios
            scores = {}
            for scen_num, scen_data in st.session_state.detailed_steps.items():
                if isinstance(scen_data, dict) and 'step7_score' in scen_data:
                    scores[scen_num] = scen_data['step7_score']
            
            # Δημιουργία VIMA6 format Excel
            excel_bytes = build_vima6_excel_bytes(
                base_df=st.session_state.data,
                detailed_steps=st.session_state.detailed_steps,
                step7_scores=scores if scores else None
            )
            
            st.download_button(
                label="⬇️ Λήψη Αρχείου",
                data=excel_bytes,
                file_name="VIMA6_from_ALL_SHEETS.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_vima6_file"
            )
            
            st.success("✅ Το αρχείο VIMA6 είναι έτοιμο για λήψη!")
            
        except Exception as e:
            st.error(f"❌ Σφάλμα δημιουργίας VIMA6: {str(e)}")
            st.code(traceback.format_exc())
    
    # Προαιρετικά: Κρατάμε και την παλιά επιλογή ZIP για backward compatibility
    st.markdown("---")
    st.markdown("### 📦 Εναλλακτικά: Λήψη ZIP με Όλες τις Λεπτομέρειες")
    st.info("ZIP αρχείο με όλα τα ενδιάμεσα βήματα (ΒΗΜΑ1 έως ΒΗΜΑ6) + βαθμολογία ΒΗΜΑ7")
    
    if st.button("📥 Λήψη Αναλυτικών ZIP", key="download_detailed_zip", use_container_width=True):
        try:
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                
                for scenario_num, scenario_data in st.session_state.detailed_steps.items():
                    # Create Excel for each scenario
                    excel_buffer = io.BytesIO()
                    
                    with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
                        # Analytical view (new + previous step)
                        df_detailed_view = build_analytics_view_upto6_with_score(
                            st.session_state.data, 
                            scenario_data, 
                            scenario_num
                        )
                        df_detailed_view.to_excel(writer, sheet_name=f'Σενάριο_{scenario_num}_Αναλυτικά', index=False)
                        
                        # Complete history (all columns filled)
                        df_full_history = st.session_state.data[['ΟΝΟΜΑ']].copy()
                        for step_key in sorted(scenario_data['data'].keys()):
                            df_full_history[step_key] = scenario_data['data'][step_key]
                        df_full_history['ΒΗΜΑ7_ΤΕΛΙΚΟ'] = scenario_data['final_after6']
                        df_full_history.to_excel(writer, sheet_name=f'Σενάριο_{scenario_num}_Πλήρες_Ιστορικό', index=False)
                        
                        # Score
                        if 'step7_score' in scenario_data:
                            scores_df = pd.DataFrame([{
                                'ΣΕΝΑΡΙΟ': f'ΣΕΝΑΡΙΟ_{scenario_num}',
                                'ΒΗΜΑ7_ΒΑΘΜΟΛΟΓΙΑ': scenario_data['step7_score'],
                                'Περιγραφή': 'Τελική βαθμολογία για το Βήμα 7 (Αποφυγή Συγκρούσεων & Τελική Κατανομή)'
                            }])
                            scores_df.to_excel(writer, sheet_name='ΒΑΘΜΟΛΟΓΙΑ_ΒΗΜΑ7', index=False)
                    
                    zip_file.writestr(
                        f"Σενάριο_{scenario_num}_Αναλυτικά.xlsx",
                        excel_buffer.getvalue()
                    )
                
                # Summary comparison file
                if st.session_state.detailed_steps:
                    summary_buffer = io.BytesIO()
                    with pd.ExcelWriter(summary_buffer, engine='xlsxwriter') as writer:
                        
                        # Statistics
                        if st.session_state.statistics is not None:
                            st.session_state.statistics.to_excel(writer, sheet_name='Στατιστικά', index=False)
                        
                        # Scenario comparison
                        scenario_comparison = []
                        for scenario_num, scenario_data in st.session_state.detailed_steps.items():
                            if 'step7_score' in scenario_data:
                                scenario_comparison.append({
                                    'Σενάριο': f'ΣΕΝΑΡΙΟ_{scenario_num}',
                                    'ΒΗΜΑ7_ΤΕΛΙΚΟ_SCORE': scenario_data['step7_score']
                                })
                        
                        if scenario_comparison:
                            comparison_df = pd.DataFrame(scenario_comparison)
                            comparison_df.to_excel(writer, sheet_name='Σύγκριση_ΒΗΜΑ7_Scores', index=False)
                    
                    zip_file.writestr("ΣΥΝΟΨΗ_Σύγκριση_Σεναρίων.xlsx", summary_buffer.getvalue())
            
            st.download_button(
                label="⬇️ Λήψη ZIP Αρχείου",
                data=zip_buffer.getvalue(),
                file_name=f"Αναλυτικά_Βήματα_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.zip",
                mime="application/zip",
                key="download_detailed_zip_file"
            )
            
            st.success("✅ Το ZIP αρχείο είναι έτοιμο για λήψη!")
            
        except Exception as e:
            st.error(f"❌ Σφάλμα δημιουργίας ZIP: {str(e)}")


# Επιπλέον: Αντικατάσταση στην working_app.py για συνέπεια

def create_detailed_steps_workbook():
    """ΤΡΟΠΟΠΟΙΗΣΗ: Δημιουργεί ΜΟΝΟ ένα Excel με 1 φύλλο 'ΑΝΑΛΥΤΙΚΑ_ΒΗΜΑΤΑ' (VIMA6) + προαιρετικό 'VIMA7_SCORE_ΣΥΝΟΨΗ'."""
    try:
        import streamlit as st
        if getattr(st.session_state, "data", None) is None or not getattr(st.session_state, "detailed_steps", {}):
            return None
            
        # Συλλογή scores
        scores = {}
        for scen_num, scen_data in st.session_state.detailed_steps.items():
            if isinstance(scen_data, dict) and 'step7_score' in scen_data:
                scores[scen_num] = scen_data['step7_score']
                
        # Δημιουργία VIMA6 format
        excel_bytes = build_vima6_excel_bytes(
            base_df=st.session_state.data, 
            detailed_steps=st.session_state.detailed_steps, 
            step7_scores=scores if scores else None
        )
        return excel_bytes
        
    except Exception as e:
        import streamlit as st, traceback
        st.error(f"Σφάλμα στη δημιουργία VIMA6 αρχείου: {e}")
        st.code(traceback.format_exc())
        return None