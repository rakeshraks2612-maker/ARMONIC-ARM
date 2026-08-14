"""
ARMONIC-ARM: Cross-Platform Fallback Profiler.
Uses cProfile in a subprocess for safety. Produces same schema as APX.
"""
import os
import sys
import time
import tempfile
import subprocess
import pstats


def run_fallback_profiler(workload_path, timeout=300, warmup=False):
    """
    Profiles a Python workload using cProfile in an isolated subprocess.
    Returns (metrics_dict, run_id_string).
    """
    print("[!] APX not found. Using cross-platform fallback profiler (cProfile).")

    prof_file = tempfile.mktemp(suffix=".prof")

    wrapper = f'''
import cProfile
import sys
import os
import importlib.util

workload_dir = os.path.dirname(os.path.abspath("{workload_path}"))
if workload_dir not in sys.path:
    sys.path.insert(0, workload_dir)

spec = importlib.util.spec_from_file_location("workload", "{workload_path}")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

if hasattr(mod, "run_workload"):
    mod.run_workload()
else:
    print("ERROR: no run_workload() found in workload", file=sys.stderr)
    sys.exit(1)
'''

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(wrapper)
        wrapper_path = f.name

    try:
        result = subprocess.run(
            [sys.executable, "-m", "cProfile", "-o", prof_file, wrapper_path],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            raise RuntimeError(f"cProfile failed: {result.stderr}")

        stats = pstats.Stats(prof_file)
        stats.strip_dirs()
        stats.sort_stats("ncalls")

        raw_stats = stats.stats
        functions = []
        for (file, line, func), (cc, nc, tt, ct, callers) in raw_stats.items():
            if file == "~" or func == "":
                continue
            functions.append({
                "symbol": func,
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
            "_elapsed_sec": 0.0,
        }

        print(f"[+] Fallback profiling complete: {total_samples} total calls, "
              f"top function: {metrics['top_function']} "
              f"({metrics['top_function_pct']}%)")
        return metrics, f"fallback-{int(time.time())}"

    finally:
        if os.path.exists(prof_file):
            os.unlink(prof_file)
        if os.path.exists(wrapper_path):
            os.unlink(wrapper_path)
