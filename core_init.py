"""
Ψηφιακή Κατανομή Μαθητών - Core Package
======================================

Περιέχει τη βασική λογική του αλγορίθμου κατανομής 7-βημάτων
και utility functions για I/O και στατιστικές.
"""

__version__ = "1.0.0"
__author__ = "Ψηφιακή Κατανομή Μαθητών Team"

# Core modules availability flag
try:
    from .steps.step1 import run_step1
    from .steps.step2 import run_step2
    from .steps.step3 import run_step3
    from .steps.step4 import run_step4
    from .steps.step5 import run_step5
    from .steps.step6 import run_step6
    from .steps.step7 import run_step7
    from .stats import build_unified_stats_table, export_statistics_unified_excel
    from .io_utils import export_final_results_excel, export_vima6_all_sheets
    
    CORE_MODULES_AVAILABLE = True
except ImportError:
    CORE_MODULES_AVAILABLE = False

__all__ = [
    'CORE_MODULES_AVAILABLE'
]