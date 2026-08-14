"""
ARMONIC-ARM: LLM Refactor Engine Core.
Uses google.genai (new API) instead of deprecated google.generativeai.
"""
import os
import time
import subprocess
from google import genai
from google.genai import types

SYSTEM_PROMPT = """You are an elite ARM64 Neoverse performance engineer.
Your job is to optimize Python code for ARM64 cloud instances (AWS Graviton / Neoverse).
You must output ONLY a valid Python file. No markdown fences, no explanations.

ARM64 Optimization Rules:
1. For pure-Python nested loops (especially those calling numpy functions on SCALARS inside loops),
   ALWAYS suggest Numba @njit(fastmath=True, cache=True). This is the #1 optimization for ARM64.
   Example: a loop calling np.sin(x) where x is a scalar -> @njit(fastmath=True, cache=True).
2. For already-vectorized NumPy (np.dot, np.matmul on arrays), do NOT suggest Numba.
3. For JSON workloads, use `orjson` instead of `json`.
4. For recursive Python, use @lru_cache or iterative rewrite.
5. Do NOT change function names, signatures, or the `if __name__ == "__main__":` block.
6. The code must be 100% valid Python. Do NOT wrap the output in ```python blocks.
"""

def _strip_markdown_fences(text):
    text = text.strip()
    if text.startswith("```python"):
        text = text[len("```python"):]
    elif text.startswith("```"):
        text = text[len("```"):]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def _ensure_imports(code, suggestions):
    libs = {
        "orjson": "import orjson",
        "njit": "from numba import njit",
        "lru_cache": "from functools import lru_cache",
    }
    for lib, imp in libs.items():
        if lib in code and imp not in code:
            lines = code.splitlines()
            insert_idx = 0
            for i, line in enumerate(lines):
                if line.startswith(("import ", "from ")):
                    insert_idx = i + 1
            lines.insert(insert_idx, imp)
            code = "\n".join(lines)
    return code

def fetch_llm_optimization(metrics, api_key, workload_path):
    if not api_key:
        print("[!] No GEMINI_API_KEY provided. Skipping LLM optimization.")
        return None

    client = genai.Client(api_key=api_key)

    with open(workload_path, 'r') as f:
        source_code = f.read()

    user_prompt = (
        "Profile metrics from ARM64 execution:\n"
        "- Total samples (proxy for cycles): " + str(metrics.get('total_samples', 'N/A')) + "\n"
        "- Top hotspot function: " + str(metrics.get('top_function', 'N/A')) + " (" + str(metrics.get('top_function_pct', 0)) + "%)\n"
        "- Profiler used: " + str(metrics.get('_profiler', 'unknown')) + "\n"
        "- Unique functions: " + str(metrics.get('function_count', 'N/A')) + "\n\n"
        "Original Python source code:\n"
        "```python\n"
        + source_code + "\n"
        "```\n\n"
        "Generate the COMPLETE optimized Python file below.\n"
        "Apply the single best ARM64 optimization.\n"
        "Return ONLY raw Python code. No markdown, no explanations.\n"
    )

    print("[+] Sending telemetry to Google Gemini...")
    try:
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=[SYSTEM_PROMPT, user_prompt],
            config=types.GenerateContentConfig(
                temperature=0.2,
                max_output_tokens=8192,
                response_mime_type='text/plain'
            )
        )
        optimized_code = _strip_markdown_fences(response.text)
        optimized_code = _ensure_imports(optimized_code, "")

        try:
            compile(optimized_code, '<string>', 'exec')
        except SyntaxError as e:
            print(f"[!] LLM generated invalid Python: {e}")
            return None

        print("[+] LLM Advisory received and validated.")
        return optimized_code
    except Exception as e:
        print(f"[!] LLM call failed: {e}")
        return None

def apply_and_commit_patch(repo_root, target_file_path, new_source_code):
    with open(target_file_path, 'w') as f:
        f.write(new_source_code)
    print(f"[+] Wrote optimized workload to: {target_file_path}")

    timestamp = int(time.time())
    branch_name = f"armonic/auto-refactor-{timestamp}"

    try:
        subprocess.run(["git", "rev-parse", "--git-dir"], cwd=repo_root,
                       capture_output=True, check=True)
        subprocess.run(["git", "checkout", "-b", branch_name], cwd=repo_root,
                       capture_output=True, check=True)
        subprocess.run(["git", "add", target_file_path], cwd=repo_root,
                       capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", f"ARMONIC auto-refactor: optimize {os.path.basename(target_file_path)}"],
            cwd=repo_root, capture_output=True, check=True
        )
        print(f"[+] Committed to branch: {branch_name}")
    except subprocess.CalledProcessError as e:
        print(f"[!] Git operation failed (non-fatal): {e}")
        branch_name = "git-unavailable"
    except FileNotFoundError:
        print("[!] Git not found. Skipping branch commit.")
        branch_name = "git-unavailable"

    return branch_name
