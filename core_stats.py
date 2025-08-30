import pandas as pd
from io import BytesIO
from typing import Dict, Any, Optional


def build_unified_stats_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Δημιουργεί ενοποιημένο πίνακα στατιστικών ανά τμήμα.
    
    Args:
        df: DataFrame με τελικά δεδομένα μαθητών
        
    Returns:
        DataFrame με στατιστικά ανά τμήμα
    """
    if df.empty or 'ΤΜΗΜΑ' not in df.columns:
        return pd.DataFrame({"ΤΜΗΜΑ": ["Α1", "Α2"], "Σύνολο": [0, 0]})
    
    stats_data = []
    
    # Ανάλυση ανά τμήμα
    for class_name in sorted(df['ΤΜΗΜΑ'].unique()):
        if class_name == '' or pd.isna(class_name):
            continue
            
        class_df = df[df['ΤΜΗΜΑ'] == class_name]
        
        row = {
            "ΤΜΗΜΑ": class_name,
            "Σύνολο": len(class_df)
        }
        
        # Στατιστικά φύλου
        if 'ΦΥΛΟ' in df.columns:
            row["Αγόρια"] = (class_df['ΦΥΛΟ'] == 'Α').sum()
            row["Κορίτσια"] = (class_df['ΦΥΛΟ'] == 'Κ').sum()
        
        # Στατιστικά παιδιών εκπαιδευτικών
        if 'ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ' in df.columns:
            row["Παιδιά_Εκπαιδευτικών"] = (class_df['ΠΑΙΔΙ_ΕΚΠΑΙΔΕΥΤΙΚΟΥ'] == 'Ν').sum()
        
        # Στατιστικά ζωηρών μαθητών
        if 'ΖΩΗΡΟΣ' in df.columns:
            row["Ζωηροί"] = (class_df['ΖΩΗΡΟΣ'] == 'Ν').sum()
        
        # Στατιστικά ιδιαιτεροτήτων
        if 'ΙΔΙΑΙΤΕΡΟΤΗΤΑ' in df.columns:
            row["Ιδιαιτερότητες"] = (class_df['ΙΔΙΑΙΤΕΡΟΤΗΤΑ'] == 'Ν').sum()
        
        # Στατιστικά γλωσσικών δεξιοτήτων
        if 'ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ' in df.columns:
            row["Καλή_Γνώση_Ελληνικών"] = (class_df['ΚΑΛΗ_ΓΝΩΣΗ_ΕΛΛΗΝΙΚΩΝ'] == 'Ν').sum()
        
        # Φιλίες και συγκρούσεις (αν υπάρχουν δεδομένα)
        if 'ΦΙΛΟΙ' in df.columns:
            friends_count = class_df['ΦΙΛΟΙ'].str.split(',').str.len().fillna(0).sum()
            row["Συνολικές_Φιλίες"] = int(friends_count)
        
        if 'ΣΥΓΚΡΟΥΣΗ' in df.columns:
            conflicts_count = class_df['ΣΥΓΚΡΟΥΣΗ'].str.split(',').str.len().fillna(0).sum()
            row["Συνολικές_Συγκρούσεις"] = int(conflicts_count)
        
        stats_data.append(row)
    
    return pd.DataFrame(stats_data)


def calculate_balance_metrics(stats_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Υπολογίζει μετρικές ισορροπίας για την κατανομή.
    
    Args:
        stats_df: DataFrame με στατιστικά ανά τμήμα
        
    Returns:
        Dict με μετρικές ισορροπίας
    """
    if 'Σύνολο' not in stats_df.columns or len(stats_df) == 0:
        return {"balance_score": 0, "std_deviation": 0, "max_diff": 0}
    
    student_counts = stats_df['Σύνολο']
    std_dev = student_counts.std()
    max_diff = student_counts.max() - student_counts.min()
    
    # Balance score: 100 - (std_dev * 10) - (max_diff * 5)
    balance_score = max(0, 100 - std_dev * 10 - max_diff * 5)
    
    return {
        "balance_score": float(balance_score),
        "std_deviation": float(std_dev),
        "max_diff": int(max_diff),
        "total_students": int(student_counts.sum()),
        "num_classes": len(stats_df),
        "avg_per_class": float(student_counts.mean())
    }


def export_statistics_unified_excel(stats_df: pd.DataFrame) -> BytesIO:
    """
    Εξάγει στατιστικά σε Excel format με πολλαπλά sheets.
    
    Args:
        stats_df: DataFrame με στατιστικά ανά τμήμα
        
    Returns:
        BytesIO buffer με Excel file
    """
    buffer = BytesIO()
    
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        # Κύριος πίνακας στατιστικών
        stats_df.to_excel(writer, sheet_name="Στατιστικά_Τμημάτων", index=False)
        
        # Υπολογισμός και εξαγωγή συνολικών μετρικών
        if len(stats_df) > 0:
            balance_metrics = calculate_balance_metrics(stats_df)
            
            summary_data = {
                "Μετρικό": [
                    "Συνολικά Τμήματα",
                    "Συνολικοί Μαθητές", 
                    "Μέσος Όρος Μαθητών/Τμήμα",
                    "Τυπική Απόκλιση",
                    "Μέγιστη Διαφορά Μαθητών",
                    "Βαθμολογία Ισορροπίας"
                ],
                "Τιμή": [
                    balance_metrics['num_classes'],
                    balance_metrics['total_students'],
                    round(balance_metrics['avg_per_class'], 1),
                    round(balance_metrics['std_deviation'], 2),
                    balance_metrics['max_diff'],
                    round(balance_metrics['balance_score'], 1)
                ]
            }
            
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name="Συνολικά", index=False)
            
            # Detailed breakdown αν υπάρχουν αρκετά δεδομένα
            if 'Αγόρια' in stats_df.columns and 'Κορίτσια' in stats_df.columns:
                gender_stats = stats_df[['ΤΜΗΜΑ', 'Αγόρια', 'Κορίτσια']].copy()
                gender_stats['Ποσοστό_Αγοριών'] = (
                    gender_stats['Αγόρια'] / (gender_stats['Αγόρια'] + gender_stats['Κορίτσια']) * 100
                ).round(1)
                gender_stats.to_excel(writer, sheet_name="Ανάλυση_Φύλου", index=False)
        
        # Formatting για καλύτερη παρουσίαση
        workbook = writer.book
        
        # Header format
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#4CAF50',
            'font_color': 'white',
            'border': 1
        })
        
        # Εφαρμογή formatting σε όλα τα sheets
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            
            # Auto-adjust column width
            for idx, col in enumerate(stats_df.columns):
                max_len = max(
                    stats_df[col].astype(str).map(len).max(),
                    len(col)
                )
                worksheet.set_column(idx, idx, max_len + 2)
            
            # Header formatting
            for col_num, value in enumerate(stats_df.columns):
                worksheet.write(0, col_num, value, header_format)
    
    buffer.seek(0)
    return buffer


def generate_class_comparison_report(stats_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Δημιουργεί αναφορά σύγκρισης τμημάτων.
    
    Args:
        stats_df: DataFrame με στατιστικά ανά τμήμα
        
    Returns:
        Dict με αναφορά σύγκρισης
    """
    if len(stats_df) == 0:
        return {"error": "Κενά δεδομένα"}
    
    report = {
        "overview": calculate_balance_metrics(stats_df),
        "class_rankings": {},
        "recommendations": []
    }
    
    # Κατάταξη τμημάτων
    if 'Σύνολο' in stats_df.columns:
        sorted_by_size = stats_df.sort_values('Σύνολο', ascending=False)
        report["class_rankings"]["by_size"] = sorted_by_size[['ΤΜΗΜΑ', 'Σύνολο']].to_dict('records')
    
    # Συστάσεις βελτίωσης
    balance_metrics = report["overview"]
    
    if balance_metrics["max_diff"] > 3:
        report["recommendations"].append(
            f"Μεγάλη ανισορροπία μεγέθους: διαφορά {balance_metrics['max_diff']} μαθητών"
        )
    
    if balance_metrics["std_deviation"] > 2:
        report["recommendations"].append(
            "Υψηλή τυπική απόκλιση - εξετάστε ανακατανομή"
        )
    
    if balance_metrics["balance_score"] < 70:
        report["recommendations"].append(
            "Χαμηλή βαθμολογία ισορροπίας - απαιτείται βελτιστοποίηση"
        )
    
    return report