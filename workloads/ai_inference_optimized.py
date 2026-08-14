import hashlib
import numpy as np
from numba import njit


@njit(fastmath=True, cache=True)
def process_batch(data: np.ndarray) -> np.ndarray:
    """Optimized batch processing using Numba JIT compilation for Arm64."""
    out = np.empty_like(data)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = data[i, j]
            out[i, j] = np.sin(val) * np.cos(val) + np.sqrt(np.abs(val) + 1.0)
    return out


def run_workload() -> np.ndarray:
    np.random.seed(42)
    batches = [
        np.random.randn(1000, 1000).astype(np.float64) for _ in range(10)
    ]
    accumulated = np.zeros((1000, 1000), dtype=np.float64)

    for batch in batches:
        accumulated += process_batch(batch)

    return accumulated


def run_test() -> str:
    # Warm-up call to trigger JIT compilation before running the workload
    warmup_data = np.zeros((10, 10), dtype=np.float64)
    _ = process_batch(warmup_data)

    result = run_workload()

    # Exact hash calculation with rounding precision rule
    rounded_result = np.round(result, decimals=10)
    result_hash = hashlib.sha256(rounded_result.tobytes()).hexdigest()
    return result_hash


if __name__ == "__main__":
    print(run_test())