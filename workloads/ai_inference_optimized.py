import hashlib
import numpy as np
import numba


def _verbose_message(msg, verbose=False):
    if verbose:
        print(msg)


@numba.njit(fastmath=True, cache=True)
def process_batch(batch):
    n = len(batch)
    result = np.empty(n, dtype=np.float64)
    for i in range(n):
        x = batch[i]
        result[i] = np.sin(x) * np.cos(x)
    return result


def run_workload(data, batch_size=10000, verbose=False):
    num_batches = (len(data) + batch_size - 1) // batch_size
    results = []
    for i in range(num_batches):
        batch = data[i * batch_size : (i + 1) * batch_size]
        _verbose_message(f"Processing batch {i}/{num_batches}", verbose=verbose)
        res = process_batch(batch)
        results.append(res)
    return np.concatenate(results)


def run_test():
    np.random.seed(42)
    data = np.random.uniform(0.0, 100.0, size=100000)

    # Warm-up Numba JIT compilation before running workload
    warmup_data = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    _ = process_batch(warmup_data)

    result = run_workload(data)

    rounded_result = np.round(result, decimals=10)
    hasher = hashlib.sha256()
    hasher.update(rounded_result.tobytes())
    return hasher.hexdigest()