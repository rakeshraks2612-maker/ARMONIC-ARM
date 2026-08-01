"""
ARMONIC-ARM: Cross-Platform Fallback Profiler.
Uses Python's built-in cProfile + time.perf_counter when Arm Performix (APX)
is not available (e.g., macOS, Windows, or systems without apx installed).
Produces the SAME output schema as performix_wrapper.py so the rest of
the pipeline doesn't know the difference.
"""
import cProfile
import pstats
import io
import time
import subprocess
import json
import os


def run_fallback_profiler(workload_path, timeout=300):
    """
    Profiles a Python workload using cProfile and returns metrics in the
    same schema as APX's performix_wrapper:
    {
        "total_samples": int,          # proxy: total function calls
        "top_function": str,           # hottest function name
        "top_function_image": str,     # always "__main__" for fallback
        "top_function_samples": int,   # call count of top function
        "top_function_pct": float,     # % of total calls
        "function_count": int,         # unique functions profiled
        "functions": [...]             # top 10 by call count
    }
    """
    print("[!] APX not found. Using cross-platform fallback profiler (cProfile).")

    profiler = cProfile.Profile()
    start_time = time.perf_counter()

    # Run the workload under cProfile
    try:
        profiler.enable()
        # Execute the workload file
        exec_globals = {}
        with open(workload_path, 'r') as f:
            code = compile(f.read(), workload_path, 'exec')
        exec(code, exec_globals)
        profiler.disable()
    except Exception as e:
        raise RuntimeError(f"Workload failed during profiling: {e}")

    elapsed = time.perf_counter() - start_time

    # Parse stats
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()
    stats.sort_stats('ncalls')

    # Extract per-function data
    raw_stats = stats.stats  # dict: (file, line, func) -> (cc, nc, tt, ct, callers)
    functions = []

    for (file, line, func), (cc, nc, tt, ct, callers) in raw_stats.items():
        # Skip builtins and very short names
        if file == '~' or func == '<module>':
            continue
        functions.append({
            "symbol": f"{func}",
            "image": os.path.basename(file) if file else "__main__",
            "samples": nc,  # primitive call count as proxy for "samples"
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


if __name__ == "__main__":
    # Quick smoke test
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
def slow():
    for i in range(100000):
        pass

slow()
""")
        path = f.name
    metrics, rid = run_fallback_profiler(path)
    print(json.dumps(metrics, indent=2))
    os.unlink(path)
