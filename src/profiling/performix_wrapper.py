"""
ARMONIC-ARM: Performance Monitoring Wrapper.
Tries Arm Performix (APX) first. Falls back to cProfile on macOS/Windows
or when apx is not installed.
"""
import csv
import json
import os
import shutil
import subprocess
import tempfile
import zipfile

from src.profiling.fallback_profiler import run_fallback_profiler


class ApxProfilingError(Exception):
    pass


def _apx_available():
    """Check if apx binary exists on PATH."""
    return shutil.which("apx") is not None


def _run_apx_command(command, timeout):
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout,
        )
    except FileNotFoundError:
        raise ApxProfilingError("'apx' binary not found on PATH.")
    except subprocess.TimeoutExpired:
        raise ApxProfilingError(f"Command timed out after {timeout}s: {' '.join(command)}")
    return result


def _parse_ndjson_stream(raw_stdout):
    events = []
    for i, line in enumerate(raw_stdout.splitlines()):
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError as e:
            raise ApxProfilingError(
                f"Line {i} of apx stream wasn't valid JSON: {e}\nLine was: {line[:300]}"
            )
    return events


def _launch_recipe(workload_command, recipe, timeout):
    launch_cmd = [
        "apx", "recipe", "run", recipe,
        "--workload", workload_command,
        "--deploy-tools",
        "--timeout", "30",
        "--json",
    ]
    result = _run_apx_command(launch_cmd, timeout)

    if result.returncode != 0:
        raise ApxProfilingError(
            f"apx recipe run exited {result.returncode}.\n"
            f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
        )

    events = _parse_ndjson_stream(result.stdout)
    if not events:
        raise ApxProfilingError("apx recipe run produced no parseable events.")

    for ev in events:
        err = ev.get("error") or {}
        if err.get("message"):
            raise ApxProfilingError(f"apx reported an error mid-run: {err}")

    run_id, completed = None, False
    for ev in events:
        rid = (ev.get("data") or {}).get("run_id", {}).get("value")
        if rid:
            run_id = rid
        if (ev.get("data") or {}).get("stage", "").startswith("Recipe completed"):
            completed = True

    if not run_id:
        raise ApxProfilingError(f"Could not find run_id in apx event stream: {events}")
    if not completed:
        last_stage = (events[-1].get("data") or {}).get("stage", "")
        raise ApxProfilingError(f"Stream ended without 'Recipe completed'. Last stage: {last_stage}")

    info_cmd = ["apx", "run", "info", run_id, "--json"]
    info_result = _run_apx_command(info_cmd, timeout)
    if info_result.returncode == 0:
        try:
            info = json.loads(info_result.stdout.strip())
            run_error = (info.get("data") or {}).get("run_error", "")
            run_result = (info.get("data") or {}).get("run_result", "")
            if run_error or run_result not in ("success", ""):
                raise ApxProfilingError(
                    f"Run {run_id} did not succeed. run_result={run_result!r} "
                    f"run_error={run_error!r}"
                )
        except json.JSONDecodeError:
            pass

    return run_id


def _export_and_parse(run_id, timeout):
    tmp_export = tempfile.mkdtemp(prefix="apx_export_")
    tmp_extract = tempfile.mkdtemp(prefix="apx_extract_")
    try:
        export_cmd = ["apx", "run", "export", run_id, tmp_export]
        result = _run_apx_command(export_cmd, timeout)
        if result.returncode != 0:
            raise ApxProfilingError(
                f"apx run export exited {result.returncode}.\n"
                f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
            )

        zips = [f for f in os.listdir(tmp_export) if f.endswith(".zip")]
        if not zips:
            raise ApxProfilingError(f"apx run export produced no .zip in {tmp_export}")

        zip_path = os.path.join(tmp_export, zips[0])
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(tmp_extract)

        target_name = "functions-capture-periodic_sampling.csv"
        csv_path = None
        for root, _, files in os.walk(tmp_extract):
            if target_name in files:
                csv_path = os.path.join(root, target_name)
                break

        if not csv_path:
            raise ApxProfilingError(
                f"Could not find {target_name} anywhere under the exported run. "
                f"The neoprof tool may not have collected samples for this run."
            )

        total_samples = 0
        functions = []
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    samples = int(row["Periodic Samples"])
                except (KeyError, ValueError):
                    continue
                total_samples += samples
                functions.append({
                    "symbol": row.get("symbol", ""),
                    "image": row.get("image", ""),
                    "samples": samples,
                })

        functions.sort(key=lambda x: x["samples"], reverse=True)
        top = functions[0] if functions else None

        return {
            "total_samples": total_samples,
            "top_function": top["symbol"] if top else None,
            "top_function_image": top["image"] if top else None,
            "top_function_samples": top["samples"] if top else 0,
            "top_function_pct": round(100 * top["samples"] / total_samples, 2)
            if top and total_samples else 0.0,
            "function_count": len(functions),
            "functions": functions[:10],
            "_profiler": "apx",
        }
    finally:
        shutil.rmtree(tmp_export, ignore_errors=True)
        shutil.rmtree(tmp_extract, ignore_errors=True)


def run_apx_profiler(workload_path, recipe="code_hotspots", timeout=300):
    """
    Unified profiler entry point.
    Uses APX on Linux/Arm64 systems where it's installed.
    Falls back to cProfile on macOS, Windows, or when apx is missing.
    """
    if not _apx_available():
        print("[!] APX not detected on this system.")
        return run_fallback_profiler(workload_path, timeout)

    print("[+] APX detected. Using Arm Performix for profiling.")
    workload_command = f"python3 {workload_path}"
    run_id = _launch_recipe(workload_command, recipe, timeout)
    metrics = _export_and_parse(run_id, timeout)
    return metrics, run_id


def save_to_disk(filename, content, is_json=False):
    with open(filename, "w") as f:
        if is_json:
            json.dump(content, f, indent=2)
        else:
            f.write(content)
