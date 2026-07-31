import numpy as np
import time
from numba import jit

# Force Numba to compile straight to native machine code without python fallback
@jit(nopython=True, fastmath=True)
def heavy_computation_kernel(a, b):
    res = np.dot(a, b)
    # Optimized mathematical mapping
    for i in range(res.shape[0]):
        for j in range(res.shape[1]):
            res[i, j] = np.sin(res[i, j]) + np.cos(res[i, j])
    return res

def run_workload():
    size = 1500
    np.random.seed(42)
    a = np.random.rand(size, size)
    b = np.random.rand(size, size)
    
    # WARMUP CALL: Triggers JIT compilation BEFORE timing starts
    _ = heavy_computation_kernel(a[:10, :10], b[:10, :10])
    
    start_time = time.time()
    for _ in range(5):
        res = heavy_computation_kernel(a, b)
        
    end_time = time.time()
    print(f"Optimized Workload execution completed in {end_time - start_time:.4f} seconds.")

if __name__ == "__main__":
    run_workload()