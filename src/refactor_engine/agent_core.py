import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)
import os
import sys
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

    Returns validated advisory dict or None on failure.
    """
    print("[+] Sending telemetry to Google Gemini...")

    top_func = telemetry_data.get("top_function", "unknown")
    top_pct = telemetry_data.get("top_function_pct", 0)

    client = genai.Client(api_key=api_key)

    prompt = f"""
You are an expert Arm64 performance engineer specializing in Neoverse microarchitecture optimization. Analyze this Arm Performix telemetry:

TOP HOTSPOT: `{top_func}` ({top_pct}% of total execution time)
TOTAL SAMPLES: {telemetry_data.get('total_samples')}
TOP 10 FUNCTIONS BY SAMPLE COUNT:
{json.dumps(telemetry_data.get('functions', []), indent=2)}

Your task: Suggest a Python code optimization for the TOP HOTSPOT function that specifically targets Arm64 performance characteristics.

Arm64-Specific Optimization Rules:
1. When suggesting Numba, ALWAYS include `fastmath=True` to leverage Arm64 NEON SIMD vectorization.
2. Include `cache=True` to avoid recompilation overhead on Arm64 cloud instances (AWS Graviton, Ampere).
3. For numerical hotspots, prefer Numba over raw NumPy because Numba compiles to native Arm64 assembly with NEON.
4. For serialization bottlenecks, suggest `orjson` which uses Arm64-optimized JSON parsing.
5. For recursive functions, suggest `functools.lru_cache` to exploit Neoverse's large L2 cache hierarchy.
6. NEVER suggest x86-specific libraries (e.g., Intel MKL, AVX intrinsics).
7. NEVER change algorithmic logic, control flow, or data structures.

You may ONLY output:
1. Zero or more import lines to add near the top of the file.
2. A single decorator line to place directly above the function definition.

Return STRICT JSON:
{{
  "action": "Brief description",
  "target_function": "{top_func}",
  "imports": ["list", "of", "imports"],
  "decorator": "decorator line or empty string",
  "reason": "Why this fixes the bottleneck specifically on Arm64 Neoverse"
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

        # ─── FATAL FIX #2: Validate LLM response structure ───
        required_keys = ["action", "target_function", "imports", "decorator", "reason"]
        missing = [k for k in required_keys if k not in advisory]
        if missing:
            print(f"[-] LLM response missing keys: {missing}. Raw: {response.text[:200]}")
            return None

        # Ensure target_function is never empty/None
        if not advisory.get("target_function"):
            advisory["target_function"] = top_func

        print(f"[+] LLM Advisory: {advisory['action']} targeting `{advisory.get('target_function')}`")
        return advisory

    except json.JSONDecodeError as e:
        print(f"[-] LLM returned invalid JSON: {e}")
        return None
    except Exception as e:
        print(f"[-] LLM failed: {e}")
        return None


def _apply_patch_to_source(code, advisory, fallback_target="unknown"):
    """
    Dynamically targets whatever function the LLM names,
    falls back to telemetry top_function if LLM omits it.
    """
    # ─── FATAL FIX #1: No hardcoded fallback ───
    target_function = advisory.get("target_function") or fallback_target
    if target_function == "unknown":
        raise ValueError("No target_function in advisory and no fallback provided.")

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


def apply_and_commit_patch(repo_path, file_to_patch, advisory, telemetry_data=None):
    """
    Applies patch, validates syntax + AST + imports, then commits to git.
    If ANY step fails, the original file is restored.

    NOTE: Score validation (re-profile & compare baseline vs optimized) must be
    handled by the orchestrator (armonic/run.py) AFTER this function returns True.
    This function only guarantees the patch is syntactically valid and importable.
    """
    print("[+] Applying autonomous patch...")

    target_path = os.path.join(repo_path, file_to_patch)
    with open(target_path, 'r') as f:
        original_code = f.read()

    # ─── FATAL FIX #1 continued: pass fallback from telemetry ───
    fallback = telemetry_data.get("top_function", "unknown") if telemetry_data else "unknown"

    try:
        new_code = _apply_patch_to_source(original_code, advisory, fallback_target=fallback)
    except ValueError as e:
        print(f"[-] Patch anchor not found: {e}")
        return False

    if new_code == original_code:
        print("[-] Patch produced no change, skipping.")
        return False

    # Write candidate patch
    with open(target_path, 'w') as f:
        f.write(new_code)

    # ─── Validation Layer 1: Syntax ───
    compile_check = subprocess.run(
        [sys.executable, "-m", "py_compile", target_path],
        capture_output=True, text=True
    )
    if compile_check.returncode != 0:
        print(f"[-] SyntaxError! Reverting.\n{compile_check.stderr}")
        with open(target_path, 'w') as f:
            f.write(original_code)
        return False

    # ─── Validation Layer 2: AST ───
    smoke_test = subprocess.run(
        [sys.executable, "-c", f"import ast; ast.parse(open('{target_path}').read())"],
        capture_output=True, text=True
    )
    if smoke_test.returncode != 0:
        print(f"[-] AST smoke test failed. Reverting.\n{smoke_test.stderr}")
        with open(target_path, 'w') as f:
            f.write(original_code)
        return False

    # ─── FATAL FIX #4: Functional import smoke test ───
    # Verify any new imports are resolvable before committing
    imports = advisory.get("imports", []) or []
    for imp in imports:
        imp_stripped = imp.strip()
        if not imp_stripped:
            continue
        # Test import in isolated subprocess (fast, safe)
        import_check = subprocess.run(
            [sys.executable, "-c", imp_stripped],
            capture_output=True, text=True, timeout=10
        )
        if import_check.returncode != 0:
            print(f"[-] Import resolution failed: '{imp_stripped}'. Reverting.\n{import_check.stderr}")
            with open(target_path, 'w') as f:
                f.write(original_code)
            return False
    print("[+] All imports resolved successfully.")

    # ─── Validation Layer 3: Git commit with rollback on failure ───
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
        # ─── FATAL FIX #5: Revert on git failure ───
        print(f"[-] Git failed: {e}. Restoring original file.")
        with open(target_path, 'w') as f:
            f.write(original_code)
        return False
