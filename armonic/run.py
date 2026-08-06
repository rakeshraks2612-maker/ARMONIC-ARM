#!/usr/bin/env python3
"""
ARMONIC Orchestrator — Main entry point for autonomous optimization loop.

Flow:
  1. Profile baseline workload (APX or cProfile fallback)
  2. Send telemetry to LLM for optimization advisory
  3. Apply patch, validate syntax/AST/imports, commit to git branch
  4. Re-profile patched workload
  5. Compare bottleneck scores: reject if opt_score >= base_score
  6. Report results

Usage:
    python -m armonic.run --config config.yaml
"""
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

import os
import sys
import yaml
import time
import subprocess
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.profiling.apx_wrapper import profile_workload
from src.refactor_engine.agent_core import fetch_llm_optimization, apply_and_commit_patch


def run_armonic_pipeline(config_path="config.yaml"):
    print("=" * 60)
    print("  ARMONIC — Autonomous Agentic Optimizer for Arm64")
    print("=" * 60)

    # ─── Load config ───
    if not os.path.exists(config_path):
        print(f"[-] Config not found: {config_path}")
        sys.exit(1)

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    repo_path = config.get("repo_path", os.getcwd())
    workload_path = config.get("workload", "workloads/ai_inference.py")
    api_key = config.get("llm", {}).get("api_key") or os.environ.get("GEMINI_API_KEY")
    max_retries = config.get("max_retries", 1)

    if not api_key:
        print("[-] No Gemini API key found in config.yaml or GEMINI_API_KEY env var.")
        sys.exit(1)

    workload_file = os.path.basename(workload_path)

    # ─── Step 1: Baseline Profile ───
    print(f"\n[1/5] Profiling baseline: {workload_path}")
    baseline_telemetry = profile_workload(workload_path)
    baseline_score = baseline_telemetry.get("bottleneck_score", float("inf"))
    top_func = baseline_telemetry.get("top_function", "unknown")

    print(f"    Baseline B_s: {baseline_score}")
    print(f"    Top hotspot: {top_func} ({baseline_telemetry.get('top_function_pct', 0)}%)")

    # ─── Step 2: LLM Advisory ───
    print("\n[2/5] Querying LLM for Arm64-aware optimization...")
    advisory = None
    for attempt in range(max_retries):
        advisory = fetch_llm_optimization(baseline_telemetry, api_key)
        if advisory:
            break
        print(f"    Retry {attempt + 1}/{max_retries}...")
        time.sleep(2)

    if not advisory:
        print("[-] LLM failed to produce a valid advisory. Aborting.")
        sys.exit(1)

    # ─── Step 3: Apply Patch ───
    print("\n[3/5] Applying autonomous patch...")
    patch_applied = apply_and_commit_patch(
        repo_path=repo_path,
        file_to_patch=workload_path,
        advisory=advisory,
        telemetry_data=baseline_telemetry
    )

    if not patch_applied:
        print("[-] Patch application failed or produced no change. Aborting.")
        sys.exit(1)

    # ─── Step 4: Re-profile Optimized Workload ───
    print("\n[4/5] Re-profiling optimized workload...")
    optimized_telemetry = profile_workload(workload_path)
    optimized_score = optimized_telemetry.get("bottleneck_score", float("inf"))

    print(f"    Optimized B_s: {optimized_score}")

    # ─── Step 5: Score Validation (README CLAIM) ───
    print("\n[5/5] Validating improvement...")
    if optimized_score >= baseline_score:
        print(f"[-] SCORE REGRESSION: {baseline_score} -> {optimized_score}")
        print("[-] Rejecting patch. Reverting to original code...")

        # Revert file to original
        # We need to stash the original. apply_and_commit_patch already wrote it,
        # but we re-read from git to be safe.
        try:
            import git as git_module
            repo = git_module.Repo(repo_path)
            repo.git.checkout("HEAD", "--", workload_path)
            print("[+] File reverted to original.")
        except Exception as e:
            print(f"[!] Manual revert may be needed: {e}")

        print("\n[-] ARMONIC pipeline completed: PATCH REJECTED (no improvement)")
        sys.exit(1)
    else:
        improvement_pct = ((baseline_score - optimized_score) / baseline_score) * 100
        print(f"[+] IMPROVEMENT: {baseline_score} -> {optimized_score} ({improvement_pct:.2f}% faster)")
        print("[+] Patch accepted and committed to isolated git branch.")
        print("\n[*] ARMONIC pipeline completed: PATCH ACCEPTED")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="ARMONIC Autonomous Optimizer")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    args = parser.parse_args()
    run_armonic_pipeline(args.config)
