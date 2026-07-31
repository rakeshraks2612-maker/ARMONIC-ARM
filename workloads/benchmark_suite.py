"""
ARMONIC-ARM: Benchmark Suite for Arm64 Optimization Challenge.
Run: python workloads/benchmark_suite.py --workload <name>
"""
import argparse
import time
import numpy as np


def naive_matmul(a, b):
    """Classic O(n³) matrix multiply — prime target for numba/torch."""
    n = len(a)
    c = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            for k in range(n):
                c[i][j] += a[i][k] * b[k][j]
    return c


def json_serialization_stress():
    """Simulates agentic AI runtime JSON overhead."""
    import json
    data = {"messages": [{"role": "user", "content": "x" * 1000}] * 500}
    for _ in range(1000):
        _ = json.dumps(data)
        _ = json.loads(_)


def fibonacci_recursive(n=30):
    """CPU-bound recursive workload."""
    if n <= 1:
        return n
    return fibonacci_recursive(n - 1) + fibonacci_recursive(n - 2)


WORKLOADS = {
    "matmul": lambda: naive_matmul(
        np.random.rand(50, 50).tolist(),
        np.random.rand(50, 50).tolist()
    ),
    "json_stress": json_serialization_stress,
    "fibonacci": lambda: fibonacci_recursive(30),
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workload", choices=list(WORKLOADS.keys()), required=True)
    args = parser.parse_args()

    workload = WORKLOADS[args.workload]
    start = time.perf_counter()
    workload()
    elapsed = time.perf_counter() - start
    print(f"Workload '{args.workload}' completed in {elapsed:.4f}s")
