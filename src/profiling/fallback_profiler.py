"""
ARMONIC-ARM: Cross-Platform Fallback Profiler.
Uses Python's built-in cProfile when Arm Performix (APX) is unavailable
or returns unresolved symbols.
"""
import cProfile
import pstats
import io
import time
import json
import os

def run_fallback_profiler(workload_path, timeout=300):
    """
    Profiles a Python workload using cProfile.
    Explicitly calls run_workload() from the executed module.
    """
    print("[!] Using cross-platform fallback profiler (cProfile).")

    profiler = cProfile.Profile()
    start_time = time.perf_counter()

    try:
        profiler.enable()
        exec_globals = {}
        with open(workload_path, 'r') as f:
            code = compile(f.read(), workload_path, 'exec')
        exec(code, exec_globals)

        # CRITICAL: Explicitly call run_workload() if it exists
        if 'run_workload' in exec_globals:
            exec_globals['run_workload']()

        profiler.disable()
    except Exception as e:
        raise RuntimeError(f"Workload failed during profiling: {e}")

    elapsed = time.perf_counter() - start_time

    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()
    stats.sort_stats('ncalls')

    raw_stats = stats.stats
    functions = []

    for (file, line, func), (cc, nc, tt, ct, callers) in raw_stats.items():
        if file == '~' or func == '':
            continue
        functions.append({
            "symbol": f"{func}",
            "image": os.path.basename(file) if file else "__main__",
            "samples": nc,
            "cumtime": ct,
        })

    functions.sort(key=lambda x: x["samples"], reverse=True)
    top = functions[0] if functions else None
    total_samples = sum(f["samples"] for f in functions)

    metrics = {
        "total_samples": total_samples,
        "top_function": top["symbol"] if top else None,
        "top_function_image": top["image"] if top else None,
        "top_function_samples": top["samples"] if top else 0,
        "top_function_pct": round(100 * top["samples"] / total_samples, 2)
        if top and total_samples else 0.0,
        "function_count": len(functions),
        "functions": functions[:10],
        "_profiler": "fallback_cprofile",
        "_elapsed_sec": round(elapsed, 4),
    }

    print(f"[+] Fallback profiling complete: {total_samples} total calls, "
          f"top function: {metrics['top_function']} "
          f"({metrics['top_function_pct']}%)")
    return metrics, f"fallback-{int(time.time())}"
