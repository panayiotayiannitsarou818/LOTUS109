# -*- coding: utf-8 -*-
"""
Utility for computing the number of classes automatically.
- num_classes = max(min_classes, ceil(N / max_per_class))
- default: max_per_class = 25, min_classes = 2
Also provides make_class_labels() -> ['Α1', 'Α2', ...]
"""
from math import ceil

def compute_num_classes(N, max_per_class=25, min_classes=2):
    try:
        N = int(N)
    except Exception:
        N = 0
    return max(int(min_classes), int(ceil((N or 0) / float(max_per_class))))

def make_class_labels(num_classes, prefix='Α'):
    try:
        k = int(num_classes)
    except Exception:
        k = 2
    return [f"{prefix}{i+1}" for i in range(k)]
