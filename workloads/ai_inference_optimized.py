import numpy as np
import time
from numba import njit

@njit(fastmath=True, cache=True)
def process_batch(data):
    results = np.empty(len(data), dtype=np.float64)
    for i in range(len(data)):
        x = data[i]
        result = 0.0
        for j in range(2000):
            result += np.sin(x + j) * np.cos(x - j)
        results[i] = result
    return results

def run_workload():
    np.random.seed(42)
    size = 25000
    data = np.random.rand(size)
    result = process_batch(data)
    return result

def run_test():
    import hashlib
    np.random.seed(42)
    data = np.random.rand(10)
    result = process_batch(data)
    result = np.round(result, decimals=10)
    return hashlib.sha256(result.tobytes()).hexdigest()

if __name__ == "__main__":
    _ = process_batch(np.zeros(1, dtype=np.float64))
    run_workload()