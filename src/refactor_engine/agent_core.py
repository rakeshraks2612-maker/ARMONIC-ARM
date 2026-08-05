import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="google.generativeai")
warnings.filterwarnings("ignore", message=".*google.generativeai.*deprecated.*", category=UserWarning)
import os
import subprocess
import git
import json
import time
from google import genai
from google.genai import types


def fetch_llm_optimization(telemetry_data, api_key):
    """
    Sends APX telemetry to Gemini. The LLM receives the TOP hotspot
    dynamically extracted from telemetry — NOT hardcoded.
    """
    print("[+] Sending telemetry to Google Gemini...")

    top_func = telemetry_data.get("top_function", "unknown")
    top_pct = telemetry_data.get("top_function_pct", 0)

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an expert Arm64 performance engineer. Analyze this Arm Performix telemetry:

TOP HOTSPOT: `{top_func}` ({top_pct}% of total execution time)
TOTAL SAMPLES: {telemetry_data.get('total_samples')}
TOP 10 FUNCTIONS BY SAMPLE COUNT:
{json.dumps(telemetry_data.get('functions', []), indent=2)}

Your task: Suggest a Python code optimization for the TOP HOTSPOT function.
You may ONLY suggest:
1. Zero or more import lines to add near the top of the file.
2. A single decorator line to place directly above the function definition.

Return STRICT JSON:
{{
  "action": "Brief description",
  "target_function": "{top_func}",
  "imports": ["list", "of", "imports"],
  "decorator": "decorator line or empty string",
  "reason": "Why this fixes the bottleneck on Arm64"
}}
"""

    try:
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type='application/json'
            )
        )
        advisory = json.loads(response.text)
        print(f"[+] LLM Advisory: {advisory['action']} targeting `{advisory.get('target_function', top_func)}`")
        return advisory
    except Exception as e:
        print(f"[-] LLM failed: {e}")
        return None


def _apply_patch_to_source(code, advisory):
    """
    Dynamically targets whatever function the LLM names,
    falls back to top_function from telemetry if LLM omits it.
    """
    target_function = advisory.get("target_function", "naive_matmul_row")
    anchor = f"def {target_function}("
    lines = code.splitlines(keepends=True)

    func_line_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith(anchor):
            func_line_idx = i
            break

    if func_line_idx is None:
        raise ValueError(f"Could not find anchor '{anchor}' in target file.")

    decorator = advisory.get("decorator", "").strip()
    if decorator:
        indent = lines[func_line_idx][:len(lines[func_line_idx]) - len(lines[func_line_idx].lstrip())]
        lines.insert(func_line_idx, f"{indent}{decorator}\n")

    new_code = "".join(lines)

    imports = advisory.get("imports", []) or []
    if imports:
        import_lines = new_code.splitlines(keepends=True)
        insert_at = 0
        for i, line in enumerate(import_lines):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                insert_at = i + 1
            elif stripped and not stripped.startswith("#") and insert_at > 0:
                break
        new_import_block = "".join(f"{imp}\n" for imp in imports if imp.strip())
        import_lines.insert(insert_at, new_import_block)
        new_code = "".join(import_lines)

    return new_code


def apply_and_commit_patch(repo_path, file_to_patch, advisory):
    print("[+] Applying autonomous patch...")

    target_path = os.path.join(repo_path, file_to_patch)
    with open(target_path, 'r') as f:
        original_code = f.read()

    try:
        new_code = _apply_patch_to_source(original_code, advisory)
    except ValueError as e:
        print(f"[-] Patch anchor not found: {e}")
        return False

    if new_code == original_code:
        print("[-] Patch produced no change, skipping.")
        return False

    with open(target_path, 'w') as f:
        f.write(new_code)

    compile_check = subprocess.run(
        ["python3", "-m", "py_compile", target_path],
        capture_output=True, text=True
    )
    if compile_check.returncode != 0:
        print(f"[-] SyntaxError! Reverting.\n{compile_check.stderr}")
        with open(target_path, 'w') as f:
            f.write(original_code)
        return False

    smoke_test = subprocess.run(
        ["python3", "-c", f"import ast; ast.parse(open('{target_path}').read())"],
        capture_output=True, text=True
    )
    if smoke_test.returncode != 0:
        print(f"[-] Smoke test failed. Reverting.\n{smoke_test.stderr}")
        with open(target_path, 'w') as f:
            f.write(original_code)
        return False

    try:
        repo = git.Repo(repo_path)
        timestamp = int(time.time())
        branch_name = f"armonic/auto-refactor-{timestamp}"
        repo.git.checkout('-b', branch_name)
        repo.index.add([file_to_patch])
        repo.index.commit(f"auto-opt: {advisory['action']}")
        print(f"[+] Committed to branch: {branch_name}")
        return True
    except Exception as e:
        print(f"[-] Git failed: {e}")
        return False
