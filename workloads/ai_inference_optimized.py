import hashlib
import numpy as np
from numba import njit


@njit(fastmath=True, cache=True)
def process_batch(batch):
    out = np.empty_like(batch)
    for i in range(batch.shape[0]):
        x = batch[i]
        out[i] = np.sin(x) * np.cos(x) + np.sin(x * 0.5)
    return out


def run_workload():
    np.random.seed(42)
    batches = [np.random.uniform(0.0, 100.0, size=50000) for _ in range(20)]
    results = []
    for batch in batches:
        results.append(process_batch(batch))
    return np.concatenate(results)


def run_test():
    # Warm-up call before run_workload to trigger JIT compilation
    dummy_data = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    _ = process_batch(dummy_data)

    result = run_workload()
    result_rounded = np.round(result, decimals=10)
    return hashlib.sha256(result_rounded.tobytes()).hexdigest()


if __name__ == "__main__":
    print(run_test())