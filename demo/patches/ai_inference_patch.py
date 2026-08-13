# ARMONIC Auto-Generated Patch
# Workload: ai_inference
# Branch: armonic/auto-refactor-20260806-143022
# Validation: syntax=PASS | ast=PASS | score=PASS
# Improvement: 98.69%

# BEFORE (baseline B_s = 17.63):
# def process_batch(data):
#     results = []
#     for row in data:
#         results.append(heavy_compute(row))
#     return results

# AFTER (optimized B_s = 0.23):
from numba import njit
import numpy as np

@njit(fastmath=True)
def process_batch(data):
    results = np.empty(len(data), dtype=np.float64)
    for i in range(len(data)):
        results[i] = heavy_compute(data[i])
    return results
