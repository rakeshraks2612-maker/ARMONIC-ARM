import numpy as np
import time

def run_workload():
    # Large scale matrix operations to make bottlenecks obvious and measurable
    size = 1500
    np.random.seed(42)
    
    # Create heavy random matrices
    a = np.random.rand(size, size)
    b = np.random.rand(size, size)
    
    # Compute-heavy workload loop
    start_time = time.time()
    for _ in range(5):
        # Heavy dot product and mathematical transformations
        res = np.dot(a, b)
        res = np.sin(res) + np.cos(res)
    
    end_time = time.time()
    print(f"Workload execution completed in {end_time - start_time:.4f} seconds.")

if __name__ == "__main__":
    run_workload()
def run_test():
    """Deterministic correctness check. Returns hash of computation result."""
    import hashlib
    # Small deterministic computation (fast, same seed)
    np.random.seed(42)
    size = 10
    a = np.random.rand(size, size)
    b = np.random.rand(size, size)
    res = np.dot(a, b)
    res = np.sin(res) + np.cos(res)
    return hashlib.md5(res.tobytes()).hexdigest()[:16]
