import argparse
import yaml
import sys
import os
import json
import shutil
import subprocess
import time

from src.profiling.performix_wrapper import run_apx_profiler
from src.refactor_engine.agent_core import fetch_llm_optimization, apply_and_commit_patch
from src.mcp_server.mcp_server import ArmMCPClient
from src.scoring.bottleneck import compute_bottleneck_score

def load_config(config_path):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def save_to_disk(filename, data, is_json=True):
    os.makedirs("results", exist_ok=True)
    path = os.path.join("results", filename)
    with open(path, 'w') as f:
        if is_json:
            json.dump(data, f, indent=4)
        else:
            f.write(data)
    return path

def run_workload_wall_time(workload_path, warmup=False):
    """Run workload and measure real wall-clock time.
    If warmup=True, run once first to warm Numba cache, then measure."""
    module_name = os.path.splitext(os.path.basename(workload_path))[0]
    
    # CRITICAL FIX: Pre-warm Numba JIT cache before measuring
    if warmup and "njit" in open(workload_path).read():
        print("[+] Pre-compiling Numba JIT (warm-up run)...")
        warm_cmd = (
            f"import sys; sys.path.insert(0, 'workloads'); "
            f"from {module_name} import process_batch; "
            f"import numpy as np; "
            f"process_batch(np.array([0.1, 0.2, 0.3], dtype=np.float64))"
        )
        subprocess.run(["python3", "-c", warm_cmd], capture_output=True, timeout=60)
    
    start = time.perf_counter()
    result = subprocess.run(
        ["python3", workload_path],
        capture_output=True, text=True, timeout=600
    )
    elapsed = time.perf_counter() - start
    if result.returncode != 0:
        raise RuntimeError(f"Workload failed: {result.stderr}")
    return elapsed

def main():
    parser = argparse.ArgumentParser(description="ARMONIC: Autonomous ARM64 Workload Optimizer")
    parser.add_argument("--config", required=True, help="Path to config.yaml")
    args = parser.parse_args()

    config = load_config(args.config)
    workload = config['pipeline']['target_workload']
    api_key = os.environ.get("GEMINI_API_KEY") or config.get('llm', {}).get('api_key', '')

    if not os.path.exists(workload):
        print(f"[!] Workload not found: {workload}")
        sys.exit(1)

    baseline_workload = workload
    optimized_workload = workload.replace(".py", "_optimized.py")

    if os.path.exists(optimized_workload):
        os.remove(optimized_workload)
    shutil.copy(baseline_workload, optimized_workload)

    print("\n" + "=" * 80)
    print("--- PHASE 1: BASELINE PROFILING ---")
    print("=" * 80)
    base_metrics, base_run_id = run_apx_profiler(baseline_workload)
    save_to_disk("apx_baseline.json", base_metrics, is_json=True)
    
    base_wall = run_workload_wall_time(baseline_workload, warmup=False)
    base_score = compute_bottleneck_score(base_metrics, config.get('scoring', {}))
    
    print(f"[+] Baseline APX samples: {base_metrics.get('total_samples', 0)}")
    print(f"[+] Baseline REAL wall_time: {base_wall:.4f}s")
    print(f"[+] Baseline B_s: {base_score}")
    if base_metrics.get("top_function"):
        print(f"[+] Baseline top hotspot: {base_metrics['top_function']} "
              f"({base_metrics['top_function_pct']}% of samples)")

    print("\n" + "=" * 80)
    print("--- PHASE 2: AGENTIC ANALYSIS & PATCH ---")
    print("=" * 80)

    mcp_host = config.get('mcp_server', {}).get('host', 'localhost')
    mcp_port = config.get('mcp_server', {}).get('port', 8080)
    if not str(mcp_host).startswith(("http://", "https://")):
        mcp_host = f"http://{mcp_host}"
    mcp = ArmMCPClient(host=f"{mcp_host}:{mcp_port}")
    mcp.query_architecture_bottlenecks(base_metrics)

    advisory = fetch_llm_optimization(base_metrics, api_key, baseline_workload)
    if not advisory:
        print("[!] LLM returned no advisory. Exiting.")
        sys.exit(1)

    branch_name = apply_and_commit_patch(".", optimized_workload, advisory)
    print(f"[+] Committed optimization to branch: {branch_name}")

    print("\n" + "=" * 80)
    print("--- PHASE 3: OPTIMIZED PROFILING ---")
    print("=" * 80)
    opt_metrics, opt_run_id = run_apx_profiler(optimized_workload)
    save_to_disk("apx_optimized.json", opt_metrics, is_json=True)
    
    # CRITICAL FIX: Warm up Numba cache before measuring wall time
    opt_wall = run_workload_wall_time(optimized_workload, warmup=True)
    opt_score = compute_bottleneck_score(opt_metrics, config.get('scoring', {}))
    
    print(f"[+] Optimized APX samples: {opt_metrics.get('total_samples', 0)}")
    print(f"[+] Optimized REAL wall_time: {opt_wall:.4f}s")
    print(f"[+] Optimized B_s: {opt_score}")
    if opt_metrics.get("top_function"):
        print(f"[+] Optimized top hotspot: {opt_metrics['top_function']} "
              f"({opt_metrics['top_function_pct']}% of samples)")

    print("\n" + "=" * 80)
    print("=== BOTTLENECK SCORE (B_s) COMPARISON ===")
    print("=" * 80)
    print("(B_s = weighted bottleneck score -- LOWER IS BETTER)")

    if base_wall > 0:
        improvement = ((base_wall - opt_wall) / base_wall) * 100
    else:
        improvement = 0.0

    report = (
        f"# ARMONIC Performance Report\n\n"
        f"| Metric | Baseline | Optimized |\n"
        f"|--------|----------|-----------|\n"
        f"| B_s | {base_score:,} | {opt_score:,} |\n"
        f"| REAL wall_time | {base_wall:.4f}s | {opt_wall:.4f}s |\n"
        f"| APX samples | {base_metrics.get('total_samples', 0)} | {opt_metrics.get('total_samples', 0)} |\n"
        f"| Top Hotspot | {base_metrics.get('top_function', 'N/A')} | {opt_metrics.get('top_function', 'N/A')} |\n"
        f"| Improvement | — | **{improvement:.2f}%** |\n\n"
        f"Baseline run_id: {base_run_id}\n"
        f"Optimized run_id: {opt_run_id}\n"
        f"Git branch: {branch_name}\n"
    )
    print(report)
    save_to_disk("report.md", report, is_json=False)

    try:
        from src.visualizer import generate_comparison_chart
        generate_comparison_chart(
            "results/apx_baseline.json",
            "results/apx_optimized.json",
            "results/comparison.png"
        )
    except Exception as e:
        print(f"[!] Chart generation skipped: {e}")

    print("\n[+] ARMONIC pipeline complete. Review results/ directory.")

if __name__ == "__main__":
    main()
