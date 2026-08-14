"""ARMONIC-ARM: Cross-platform fallback profiler (cProfile-based)."""

import cProfile
import importlib.util
import io
import numpy as np
import os
import pstats
import sys
import time


def run_fallback_profiler(workload_path, timeout=300):
    """Profile workload using cProfile. Returns metrics dict."""
    workload_dir = os.path.dirname(os.path.abspath(workload_path))
    workload_name = os.path.splitext(os.path.basename(workload_path))[0]
    
    if workload_dir not in sys.path:
        sys.path.insert(0, workload_dir)
    
    # Remove from cache if already imported
    if workload_name in sys.modules:
        del sys.modules[workload_name]
    
    spec = importlib.util.spec_from_file_location(workload_name, workload_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[workload_name] = module
    spec.loader.exec_module(module)
    
    # WARM UP Numba cache before profiling
    if hasattr(module, 'process_batch'):
        print("[+] Pre-compiling Numba JIT (warm-up run)...")
        _ = module.process_batch(np.zeros(1, dtype=np.float64))
    
    # Now profile
    start = time.time()
    pr = cProfile.Profile()
    pr.enable()
    
    module.run_workload()
    
    pr.disable()
    elapsed = time.time() - start

    # Parse stats
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(10)
    stats_text = s.getvalue()

    # Extract top function
    lines = stats_text.split('\n')
    top_func = "unknown"
    top_pct = 0.0
    total_calls = 0
    
    for line in lines:
        if 'function calls' in line:
            parts = line.split()
            for i, p in enumerate(parts):
                if 'calls' in p:
                    try:
                        total_calls = int(parts[i-1].replace(',', ''))
                    except:
                        pass
        if '/' in line and line.strip().startswith((' ')):
            parts = line.split()
            if len(parts) >= 6:
                try:
                    top_pct = float(parts[3])
                    top_func = parts[5]
                    break
                except:
                    continue

    return {
        "wall_time": elapsed,
        "top_function": top_func,
        "top_function_pct": top_pct,
        "total_samples": total_calls,
        "total_calls": total_calls,
        "functions": [],
        "profiler": "cProfile"
    }, None
