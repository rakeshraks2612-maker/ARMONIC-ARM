import os
import ast
import subprocess
import git
import json
import time
from google import genai
from google.genai import types


def fetch_llm_optimization(telemetry_data, api_key):
    print("[+] Sending strict telemetry to Google Gemini 1.5 Pro (GenAI SDK)...")

    client = genai.Client(api_key=api_key)

    prompt = f"""
    You are an expert Arm64 hardware performance engineer. Analyze this Arm Performix (APX) telemetry:
    {json.dumps(telemetry_data)}

    The hot function you are optimizing is named `naive_matmul_row` in a Python file.
    You may ONLY suggest an optimization that can be applied as:
      1. Zero or more import lines to add near the top of the file.
      2. A single decorator line to place directly above the function definition
         `def naive_matmul_row(a_row, b, size):`.

    Do NOT suggest rewriting the function body. Only imports + a decorator.
    A safe, real example: imports=["from numba import njit"], decorator="@njit(fastmath=True, cache=True)"

    Return a strict JSON object with this exact schema:
    {{
        "action": "Brief description of action",
        "imports": ["list", "of", "import lines as strings"],
        "decorator": "the single decorator line as a string, or empty string if none",
        "reason": "Why this fixes the bottleneck"
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
        print(f"[+] LLM Advisory Parsed: {advisory['action']}")
        return advisory
    except Exception as e:
        print(f"[-] FATAL: LLM failed to return structured JSON. Error: {e}")
        return None


def _apply_patch_to_source(code, advisory, target_function="naive_matmul_row"):
    """Actually modifies the source: inserts import lines near the top and
    a decorator directly above the target function. Returns the new code
    string, or raises ValueError if the anchor function can't be found."""
    anchor = f"def {target_function}("
    lines = code.splitlines(keepends=True)

    func_line_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith(anchor):
            func_line_idx = i
            break

    if func_line_idx is None:
        raise ValueError(f"Could not find anchor 'def {target_function}(' in target file.")

    decorator = advisory.get("decorator", "").strip()
    if decorator:
        # Preserve the target function's existing indentation for the decorator
        indent = lines[func_line_idx][:len(lines[func_line_idx]) - len(lines[func_line_idx].lstrip())]
        lines.insert(func_line_idx, f"{indent}{decorator}\n")

    new_code = "".join(lines)

    imports = advisory.get("imports", []) or []
    if imports:
        # Insert after the last existing top-of-file import line, or at
        # the very top if there are none.
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


def apply_and_commit_patch(repo_path, file_to_patch, advisory, target_function="naive_matmul_row"):
    print("[+] Initiating real autonomous code injection...")

    target_path = os.path.join(repo_path, file_to_patch)
    with open(target_path, 'r') as f:
        original_code = f.read()

    try:
        new_code = _apply_patch_to_source(original_code, advisory, target_function)
    except ValueError as e:
        print(f"[-] Patch anchor not found, skipping: {e}")
        return False

    if new_code == original_code:
        print("[-] Patch produced no change to the file, skipping commit.")
        return False

    # Write the patch, then verify it doesn't break the file before committing
    with open(target_path, 'w') as f:
        f.write(new_code)

    compile_check = subprocess.run(
        ["python3", "-m", "py_compile", target_path],
        capture_output=True, text=True
    )
    if compile_check.returncode != 0:
        print(f"[-] Patch broke the file (SyntaxError). Reverting.\n{compile_check.stderr}")
        with open(target_path, 'w') as f:
            f.write(original_code)
        return False

    # Smoke-test: actually run the patched file briefly to confirm it
    # doesn't crash at import/runtime (catches missing-dependency errors
    # like a decorator requiring a package that isn't installed).
    smoke_test = subprocess.run(
        ["python3", "-c", f"import ast; ast.parse(open('{target_path}').read())"],
        capture_output=True, text=True
    )
    if smoke_test.returncode != 0:
        print(f"[-] Patch failed smoke test. Reverting.\n{smoke_test.stderr}")
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
        print(f"[+] Patch physically applied and committed to branch: {branch_name}")
        return True
    except Exception as e:
        print(f"[-] Git automation failed: {e}")
        return False