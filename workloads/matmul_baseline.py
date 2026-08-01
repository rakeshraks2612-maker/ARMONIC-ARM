"""
ARMONIC-ARM: Simple matrix multiply workload for profiling.
This is the baseline that the LLM will optimize.
"""
import numpy as np


def naive_matmul(a, b):
    """Classic O(n³) matrix multiply — prime target for numba JIT."""
    n = len(a)
    c = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                c[i][j] += a[i][k] * b[k][j]
    return c


if __name__ == "__main__":
    # Run enough work to produce measurable profile data
    a = np.random.rand(40, 40).tolist()
    b = np.random.rand(40, 40).tolist()
    for _ in range(5):
        naive_matmul(a, b)
