import time
import sys
import os
import subprocess

from src.profiling.performix_wrapper import run_apx_profiler
from src.profiling.fallback_profiler import run_fallback_profiler
from src.scoring.bottleneck import calculate_bottleneck_score


def _measure_real_time(workload_path, timeout=300):
    """
    Run workload in a clean subprocess and measure actual wall time.
    This avoids importlib caching, .pyc staleness, and sys.modules pollution.
    """
    print(f"[+] Measuring real wall time: python3 {workload_path}")
    start = time.time()
    result = subprocess.run(
        [sys.executable, workload_path],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    elapsed = time.time() - start

    if result.returncode != 0:
        print(f"[!] Workload stderr: {result.stderr[:500]}")
        raise RuntimeError(f"Workload failed with exit code {result.returncode}")

    print(f"[+] Real wall time: {elapsed:.4f}s")
    return elapsed


def profile_workload(workload_path, recipe="code_hotspots", timeout=300, warmup=False):
    """
    1. Detect hotspots via APX (or cProfile fallback).
    2. Measure REAL wall time via subprocess.
    3. Return unified telemetry dict.
    """
    apx_failed = False
    metrics = None
    run_id = None

    try:
        metrics, run_id = run_apx_profiler(workload_path, recipe=recipe, timeout=timeout)
        top_func = metrics.get("top_function")
        if not top_func or "unknown" in str(top_func).lower() or metrics.get("total_samples", 0) == 0:
            apx_failed = True
            print("[!] APX returned unresolved/unknown hotspot. Falling back to cProfile...")
    except Exception as e:
        print(f"[!] APX profiling failed: {e}")
        apx_failed = True

    if apx_failed:
        metrics, run_id = run_fallback_profiler(workload_path, timeout=timeout, warmup=warmup)
        metrics["top_function"] = metrics.get("top_function") or "unknown"
        metrics["top_function_pct"] = metrics.get("top_function_pct", 0)

    real_wall_time = _measure_real_time(workload_path, timeout=timeout)
    metrics["_elapsed_sec"] = real_wall_time
    metrics["wall_time"] = real_wall_time

    return {
        "wall_time": real_wall_time,
        "bottleneck_score": calculate_bottleneck_score(metrics),
        "profiler": "cProfile" if apx_failed else "APX",
        "top_function": metrics.get("top_function", "unknown"),
        "top_function_pct": metrics.get("top_function_pct", 0),
        "total_samples": metrics.get("total_samples", 0),
        "functions": metrics.get("functions", []),
    }
