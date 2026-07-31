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