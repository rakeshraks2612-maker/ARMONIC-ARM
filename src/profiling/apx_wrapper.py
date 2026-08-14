"""ARMONIC-ARM: APX Wrapper — bridges Performix to the orchestrator."""

import time
from src.profiling.performix_wrapper import run_apx_profiler
from src.profiling.fallback_profiler import run_fallback_profiler
from src.scoring.bottleneck import compute_bottleneck_score


def profile_workload(workload_path, recipe="code_hotspots", timeout=300):
    """Profile workload. Returns dict with wall_time and bottleneck_score."""
    start = time.time()
    apx_failed = False

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
        metrics, run_id = run_fallback_profiler(workload_path, timeout=timeout)
        metrics["top_function"] = metrics.get("top_function") or "unknown"
        metrics["top_function_pct"] = metrics.get("top_function_pct", 0)

    elapsed = time.time() - start
    return {
        "wall_time": elapsed,
        "bottleneck_score": compute_bottleneck_score(metrics),
        "profiler": "cProfile" if apx_failed else "APX",
        "top_function": metrics.get("top_function", "unknown"),
        "top_function_pct": metrics.get("top_function_pct", 0),
        "total_samples": metrics.get("total_samples", 0),
        "functions": metrics.get("functions", []),
    }
