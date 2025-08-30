import pandas as pd
from io import BytesIO
from typing import Dict, Any, Optional
import zipfile


def export_final_results_excel(final_df: pd.DataFrame) -> BytesIO:
    """
    Εξάγει το τελικό αποτέλεσμα σε Excel format.
    
    Args:
        final_df: DataFrame με τελικά αποτελέσματα κατανομής
        
    Returns:
        BytesIO buffer με Excel file
    """
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Τελικό αποτέλεσμα
        final_df.to_excel(writer, sheet_name="Τελικό_Αποτέλεσμα", index=False)
        
        # Formatting για καλύτερη παρουσίαση
        workbook = writer.book
        worksheet = writer.sheets["Τελικό_Αποτέλεσμα"]
        
        # Header format
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#2196F3',
            'font_color': 'white',
            'border': 1
        })
        
        # Auto-adjust column width
        for idx, col in enumerate(final_df.columns):
            max_len = max(
                final_df[col].astype(str).map(len).max(),
                len(col)
            )
            worksheet.set_column(idx, idx, max_len + 2)
        
        # Apply header formatting
        for col_num, value in enumerate(final_df.columns):
            worksheet.write(0, col_num, value, header_format)
        
        # Highlight ΤΜΗΜΑ column
        if 'ΤΜΗΜΑ' in final_df.columns:
            tmima_col = final_df.columns.get_loc('ΤΜΗΜΑ')
            tmima_format = workbook.add_format({
                'bg_color': '#E3F2FD',
                'border': 1
            })
            
            for row_num in range(1, len(final_df) + 1):
                worksheet.write(row_num, tmima_col, 
                              final_df.iloc[row_num-1]['ΤΜΗΜΑ'], 
                              tmima_format)
    
    buffer.seek(0)
    return buffer


def export_vima6_all_sheets(pipeline_output: Dict[str, Any]) -> BytesIO:
    """
    Εξάγει VIMA6 format με όλα τα sheets από το pipeline.
    
    Args:
        pipeline_output: Dict με artifacts από όλα τα βήματα
        
    Returns:
        BytesIO buffer με Excel file
    """
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        workbook = writer.book
        
        # Header format
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#FF9800',
            'font_color': 'white',
            'border': 1
        })
        
        # Εξαγωγή ενός sheet ανά βήμα
        for step_num in range(1, 8):
            step_key = f"step{step_num}"
            
            if step_key in pipeline_output.get("artifacts", {}):
                step_data = pipeline_output["artifacts"][step_key]
                df = step_data.get("df", pd.DataFrame())
                
                # Δημιουργία sheet name
                sheet_name = f"ΒΗΜΑ{step_num}"
                
                # Ειδική περίπτωση για βήμα 7 - προσθήκη score
                if step_num == 7:
                    scores = step_data.get("meta", {}).get("scores", {})
                    main_score = scores.get("ΣΕΝΑΡΙΟ_1", 0)
                    sheet_name = f"ΒΗΜΑ7_SCORE_{main_score:.0f}"
                
                # Εξαγωγή DataFrame
                if not df.empty:
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    # Formatting
                    worksheet = writer.sheets[sheet_name]
                    
                    # Auto-adjust columns
                    for idx, col in enumerate(df.columns):
                        max_len = max(
                            df[col].astype(str).map(len).max(),
                            len(col)
                        )
                        worksheet.set_column(idx, idx, max_len + 2)
                    
                    # Apply header formatting
                    for col_num, value in enumerate(df.columns):
                        worksheet.write(0, col_num, value, header_format)
                    
                    # Metadata σε comment (αν υπάρχει)
                    meta = step_data.get("meta", {})
                    scenarios = step_data.get("scenarios", {})
                    
                    if meta or scenarios:
                        comment_text = f"Βήμα {step_num}: {meta.get('description', '')}"
                        if scenarios:
                            comment_text += f"\nΣενάρια: {scenarios}"
                        
                        worksheet.write_comment('A1', comment_text)
        
        # Προσθήκη summary sheet
        if "final_df" in pipeline_output and pipeline_output["final_df"] is not None:
            final_df = pipeline_output["final_df"]
            
            # Summary στατιστικών ανά τμήμα
            summary_data = []
            if 'ΤΜΗΜΑ' in final_df.columns:
                class_counts = final_df['ΤΜΗΜΑ'].value_counts().sort_index()
                
                for class_name, count in class_counts.items():
                    class_df = final_df[final_df['ΤΜΗΜΑ'] == class_name]
                    
                    row = {"ΤΜΗΜΑ": class_name, "ΜΑΘΗΤΕΣ": count}
                    
                    # Πρόσθετα στατιστικά
                    if 'ΦΥΛΟ' in final_df.columns:
                        row["ΑΓΟΡΙΑ"] = (class_df['ΦΥΛΟ'] == 'Α').sum()
                        row["ΚΟΡΙΤΣΙΑ"] = (class_df['ΦΥΛΟ'] == 'Κ').sum()
                    
                    if 'ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ' in final_df.columns:
                        row["ΠΑΙΔΙΑ_ΕΚΠΑΙΔΕΥΤΙΚΩΝ"] = (class_df['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ'] == 'Ν').sum()
                    
                    summary_data.append(row)
            
            summary_df = pd.DataFrame(summary_data)
            
            if not summary_df.empty:
                summary_df.to_excel(writer, sheet_name="ΣΥΝΟΨΗ", index=False)
                
                # Formatting για summary
                worksheet = writer.sheets["ΣΥΝΟΨΗ"]
                
                for idx, col in enumerate(summary_df.columns):
                    max_len = max(
                        summary_df[col].astype(str).map(len).max(),
                        len(col)
                    )
                    worksheet.set_column(idx, idx, max_len + 2)
                
                for col_num, value in enumerate(summary_df.columns):
                    worksheet.write(0, col_num, value, header_format)
        
        # Metadata sheet
        metadata_sheet = workbook.add_worksheet("METADATA")
        
        metadata_info = [
            ["Αρχείο", "VIMA6_from_ALL_SHEETS.xlsx"],
            ["Περιγραφή", "Αναλυτικά βήματα αλγορίθμου κατανομής"],
            ["Ημερομηνία", pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")],
            ["Συνολικά Βήματα", str(len([k for k in pipeline_output.get("artifacts", {}).keys() if k.startswith("step")]))],
            ["Τελικοί Μαθητές", str(len(pipeline_output.get("final_df", pd.DataFrame())))]
        ]
        
        for row_num, (key, value) in enumerate(metadata_info):
            metadata_sheet.write(row_num, 0, key, header_format)
            metadata_sheet.write(row_num, 1, value)
        
        metadata_sheet.set_column(0, 0, 20)
        metadata_sheet.set_column(1, 1, 30)
    
    buffer.seek(0)
    return buffer


def create_comprehensive_export_zip(pipeline_output: Dict[str, Any], 
                                   stats_df: Optional[pd.DataFrame] = None) -> BytesIO:
    """
    Δημιουργεί συνολικό ZIP αρχείο με όλα τα exports.
    
    Args:
        pipeline_output: Dict με artifacts από pipeline
        stats_df: Optional DataFrame με στατιστικά
        
    Returns:
        BytesIO buffer με ZIP file
    """
    zip_buffer = BytesIO()
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # README file
        readme_content = """ΠΕΡΙΕΧΟΜΕΝΑ ΠΑΚΕΤΟΥ ΑΝΑΛΥΤΙΚΩΝ
=========================================

Αυτό το πακέτο περιέχει όλα τα αποτελέσματα από τον αλγόριθμο 
κατανομής μαθητών σε τμήματα.

ΠΕΡΙΕΧΟΜΕΝΑ:
1. Τελικό_Αποτέλεσμα.xlsx - Τελικό αρχείο με κατανομή
2. VIMA6_Αναλυτικά.xlsx - Ενδιάμεσα βήματα αλγορίθμου
3. Στατιστικά_Σύνοψη.xlsx - Αναλυτικά στατιστικά
4. Pipeline_Report.txt - Τεχνική αναφορά

ΟΔΗΓΙΕΣ ΧΡΗΣΗΣ:
- Το αρχείο "Τελικό_Αποτέλεσμα.xlsx" περιέχει την οριστική κατανομή
- Το "VIMA6_Αναλυτικά.xlsx" δείχνει τη διαδικασία βήμα-βήμα
- Τα στατιστικά δίνουν αναλυτική εικόνα της ισορροπίας

Δημιουργήθηκε από: Ψηφιακή Κατανομή Μαθητών
Ημερομηνία: {date}
""".format(date=pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        zip_file.writestr("README.txt", readme_content)
        
        # Τελικό αποτέλεσμα
        if "final_df" in pipeline_output and pipeline_output["final_df"] is not None:
            final_excel = export_final_results_excel(pipeline_output["final_df"])
            zip_file.writestr("Τελικό_Αποτέλεσμα.xlsx", final_excel.getvalue())
        
        # VIMA6 αναλυτικά
        vima6_excel = export_vima6_all_sheets(pipeline_output)
        zip_file.writestr("VIMA6_Αναλυτικά.xlsx", vima6_excel.getvalue())
        
        # Στατιστικά αν διαθέσιμα
        if stats_df is not None and not stats_df.empty:
            from .stats import export_statistics_unified_excel
            stats_excel = export_statistics_unified_excel(stats_df)
            zip_file.writestr("Στατιστικά_Σύνοψη.xlsx", stats_excel.getvalue())
        
        # Pipeline report
        pipeline_report = generate_pipeline_report(pipeline_output)
        zip_file.writestr("Pipeline_Report.txt", pipeline_report)
    
    zip_buffer.seek(0)
    return zip_buffer


def generate_pipeline_report(pipeline_output: Dict[str, Any]) -> str:
    """
    Δημιουργεί τεχνική αναφορά για το pipeline.
    
    Args:
        pipeline_output: Dict με artifacts από pipeline
        
    Returns:
        String με αναφορά
    """
    report_lines = [
        "ΤΕΧΝΙΚΗ ΑΝΑΦΟΡΑ PIPELINE ΚΑΤΑΝΟΜΗΣ",
        "=" * 50,
        f"Ημερομηνία: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]
    
    # Γενικές πληροφορίες
    final_df = pipeline_output.get("final_df")
    if final_df is not None:
        report_lines.extend([
            "ΓΕΝΙΚΑ ΣΤΟΙΧΕΙΑ:",
            f"- Συνολικοί μαθητές: {len(final_df)}",
            f"- Αριθμός τμημάτων: {final_df['ΤΜΗΜΑ'].nunique() if 'ΤΜΗΜΑ' in final_df.columns else 0}",
            ""
        ])
    
    # Ανάλυση βημάτων
    report_lines.append("ΑΝΑΛΥΣΗ ΒΗΜΑΤΩΝ:")
    
    artifacts = pipeline_output.get("artifacts", {})
    for step_num in range(1, 8):
        step_key = f"step{step_num}"
        
        if step_key in artifacts:
            step_data = artifacts[step_key]
            meta = step_data.get("meta", {})
            scenarios = step_data.get("scenarios", {})
            
            description = meta.get("description", f"Βήμα {step_num}")
            report_lines.append(f"✓ ΒΗΜΑ {step_num}: {description}")
            
            if scenarios:
                for key, value in scenarios.items():
                    report_lines.append(f"  - {key}: {value}")
        else:
            report_lines.append(f"✗ ΒΗΜΑ {step_num}: Δεν εκτελέστηκε")
    
    report_lines.append("")
    
    # Τελικά στατιστικά
    if final_df is not None and 'ΤΜΗΜΑ' in final_df.columns:
        class_counts = final_df['ΤΜΗΜΑ'].value_counts().sort_index()
        
        report_lines.extend([
            "ΤΕΛΙΚΗ ΚΑΤΑΝΟΜΗ:",
            *[f"- {class_name}: {count} μαθητές" for class_name, count in class_counts.items()],
            "",
            "ΜΕΤΡΙΚΕΣ ΙΣΟΡΡΟΠΙΑΣ:",
            f"- Μέσος όρος μαθητών/τμήμα: {class_counts.mean():.1f}",
            f"- Τυπική απόκλιση: {class_counts.std():.2f}",
            f"- Μέγιστη διαφορά: {class_counts.max() - class_counts.min()}"
        ])
    
    return "\n".join(report_lines)