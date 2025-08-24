# Auto `num_classes = ceil(N/25)`

Αυτή η ενημέρωση προσθέτει ενιαίο αυτόματο υπολογισμό του αριθμού τμημάτων σε **όλα τα σημεία** που ελέγχουμε εδώ.

## Τι αλλάζει
- **utils_num_classes.py** *(νέο)*: 
  - `compute_num_classes(N, max_per_class=25, min_classes=2)`
  - `make_class_labels(num_classes, prefix='Α')`
- **apply_step4_beltiosi_FIXED.py**: 
  - Χρήση του utility. Αν δεν υπάρχουν ήδη labels τύπου `Α1`, `Α2` κ.λπ., υπολογίζει `k = ceil(N/25)` και δημιουργεί labels.
- **debug_app.py** & **simple_app.py**:
  - Εμφανίζουν metric με `k` και αποθηκεύουν `num_classes.json` για downstream modules.

## Πώς να το καλέσεις στα υπόλοιπα βήματα
```python
from utils_num_classes import compute_num_classes, make_class_labels

N = len(df)
k = compute_num_classes(N)              # ceil(N/25), ελάχιστο 2
class_labels = make_class_labels(k)     # ['Α1', 'Α2', ..., 'Αk']

# Παράδειγμα:
result = stepX_run(df, num_classes=k, class_labels=class_labels)
```
Αν κάποιο βήμα δεν δέχεται `num_classes`, πρόσθεσε την παράμετρο ή δώσε του τα `class_labels`.

## Σημειώσεις
- Το όριο παραμένει 25 μαθητές ανά τμήμα.
- Αν σε ένα input υπάρχουν ήδη labels `Α1..Αk` από προηγούμενη φάση, ο driver **τα χρησιμοποιεί** και δεν αλλάζει τον αριθμό τμημάτων.
