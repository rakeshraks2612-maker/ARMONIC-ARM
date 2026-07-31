import argparse
import yaml
import sys
import os
import json

from src.profiling.performix_wrapper import run_apx_profiler
from src.refactor_engine.agent_core import fetch_llm_optimization, apply_and_commit_patch
from src.mcp_server.mcp_server import ArmMCPClient

def load_config(config_path):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

def calculate_bottleneck_score(metrics):
    """
    Real score: total sampled hits across all functions during the run.
    Since neoprof samples at a fixed frequency for the run's duration,
    this is a genuine proxy for total execution time. LOWER IS BETTER.
    """
    return metrics.get("total_samples", 0)

def save_to_disk(filename, data, is_json=True):
    os.makedirs("results", exist_ok=True)
    path = os.path.join("results", filename)
    with open(path, 'w') as f:
        if is_json:
            json.dump(data, f, indent=4)
        else:
            f.write(data)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()
    config = load_config(args.config)
    workload = config['pipeline']['target_workload']
    api_key = os.environ.get("GEMINI_API_KEY") or config['llm']['api_key']

    print("\n--- PHASE 1: BASELINE PROFILING ---")
    base_metrics, base_run_id = run_apx_profiler(workload)
    save_to_disk("apx_baseline.json", base_metrics, is_json=True)
    base_score = calculate_bottleneck_score(base_metrics)
    print(f"[+] Baseline total samples: {base_score}")
    if base_metrics.get("top_function"):
        print(f"[+] Baseline top hotspot: {base_metrics['top_function']} "
              f"({base_metrics['top_function_pct']}% of samples)")

    print("\n--- PHASE 2: AGENTIC ANALYSIS ---")
    mcp_host = config['mcp_server']['host']
    mcp_port = config['mcp_server']['port']
    if not mcp_host.startswith("http://") and not mcp_host.startswith("https://"):
        mcp_host = f"http://{mcp_host}"
    mcp = ArmMCPClient(host=f"{mcp_host}:{mcp_port}")
    mcp.query_architecture_bottlenecks(base_metrics)

    advisory = fetch_llm_optimization(base_metrics, api_key)
    if not advisory:
        sys.exit(1)

    apply_and_commit_patch(".", workload, advisory)

    print("\n--- PHASE 3: OPTIMIZED PROFILING ---")
    opt_metrics, opt_run_id = run_apx_profiler(workload)
    save_to_disk("apx_optimized.json", opt_metrics, is_json=True)
    opt_score = calculate_bottleneck_score(opt_metrics)
    print(f"[+] Optimized total samples: {opt_score}")
    if opt_metrics.get("top_function"):
        print(f"[+] Optimized top hotspot: {opt_metrics['top_function']} "
              f"({opt_metrics['top_function_pct']}% of samples)")

    print("\n=== 📊 BOTTLENECK SCORE (B_s) COMPARISON ===")
    print("(B_s = total profiler samples across the run -- LOWER IS BETTER, "
          "it's a real proxy for execution time)")

    if base_score > 0:
        improvement = ((base_score - opt_score) / base_score) * 100
    else:
        improvement = 0.0

    report = (
        f"Baseline B_s (total samples): {base_score}\n"
        f"Optimized B_s (total samples): {opt_score}\n"
        f"Improvement: {improvement:.2f}%\n"
        f"Baseline top hotspot: {base_metrics.get('top_function')} "
        f"({base_metrics.get('top_function_pct')}%)\n"
        f"Optimized top hotspot: {opt_metrics.get('top_function')} "
        f"({opt_metrics.get('top_function_pct')}%)\n"
    )
    print(report)
    save_to_disk("report.md", report, is_json=False)

if __name__ == "__main__":
    main()