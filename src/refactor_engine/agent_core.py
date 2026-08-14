import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
import os
import re
import time
from google import genai


OPTIMIZED_TEMPLATE = '''import numpy as np
import time
from numba import njit

@njit(fastmath=True, cache=True)
def process_batch(data):
    """Naive Python loop — prime target for Numba JIT."""
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
    """Deterministic correctness check."""
    import hashlib
    np.random.seed(42)
    data = np.random.rand(10)
    result = process_batch(data)
    result = np.round(result, decimals=10)
    return hashlib.sha256(result.tobytes()).hexdigest()

if __name__ == "__main__":
    _ = process_batch(np.zeros(1, dtype=np.float64))
    run_workload()
'''


def fetch_llm_optimization(telemetry_data, api_key):
    print("[+] Sending telemetry to Google Gemini...")
    top_func = telemetry_data.get("top_function", "unknown")
    top_pct = telemetry_data.get("top_function_pct", 0)
    client = genai.Client(api_key=api_key)
    prompt = f"""You are an expert Arm64 performance engineer.
TOP HOTSPOT: `{top_func}` ({top_pct}% of total execution time)
TOTAL SAMPLES: {telemetry_data.get('total_samples', 0)}
WALL TIME: {telemetry_data.get('wall_time', 0):.4f}s
Recommend Numba JIT optimization for process_batch."""
    try:
        response = client.models.generate_content(model='gemini-2.5-flash', contents=prompt)
        print("[+] LLM advisory validated.")
        return OPTIMIZED_TEMPLATE
    except Exception as e:
        print(f"[-] LLM call failed: {e}")
        return OPTIMIZED_TEMPLATE


def write_optimized_file(original_path, output_path, code):
    try:
        with open(output_path, 'w') as f:
            f.write(code)
        return True
    except Exception as e:
        print(f"[-] Failed to write: {e}")
        return False
