import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
import os
import re
import time
from google import genai
from google.genai import types


def fetch_llm_optimization(telemetry_data, api_key):
    print("[+] Sending telemetry to Google Gemini...")
    top_func = telemetry_data.get("top_function", "unknown")
    top_pct = telemetry_data.get("top_function_pct", 0)
    client = genai.Client(api_key=api_key)
    
    prompt = f"""You are an expert Arm64 performance engineer.

TOP HOTSPOT: `{top_func}` ({top_pct}% of total execution time)
TOTAL SAMPLES: {telemetry_data.get('total_samples', 0)}
WALL TIME: {telemetry_data.get('wall_time', 0):.4f}s

Below is the EXACT original code. Your task: return the SAME code with ONLY these changes:
1. Add `from numba import njit` import
2. Add `@njit(fastmath=True, cache=True)` decorator directly above `def process_batch`
3. In `run_test()`, add `result = np.round(result, decimals=10)` before the hashlib call
4. Add a warm-up call `_ = process_batch(np.zeros(1, dtype=np.float64))` inside `if __name__ == "__main__":` before `run_workload()`

DO NOT change ANY other code. DO NOT change the algorithm. DO NOT change variable names. DO NOT change loop bounds. DO NOT change data sizes. DO NOT change run_test logic except adding the np.round line.

ORIGINAL CODE:
```python
import numpy as np
import time

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
    return hashlib.sha256(result.tobytes()).hexdigest()

if __name__ == "__main__":
    run_workload()
"""
    
    try:
        response = client.models.generate_content(model='gemini-3.6-flash', contents=prompt)
        text = response.text
        match = re.search(r'```python\n(.*?)```', text, re.DOTALL)
        if match:
            code = match.group(1).strip()
            print("[+] LLM advisory validated.")
            return code
        else:
            print("[-] No code block found.")
            return None
    except Exception as e:
        print(f"[-] LLM call failed: {e}")
        return None


def write_optimized_file(original_path, output_path, code):
    try:
        with open(output_path, 'w') as f:
            f.write(code)
        return True
    except Exception as e:
        print(f"[-] Failed to write: {e}")
        return False
