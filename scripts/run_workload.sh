#!/bin/bash
# ARMONIC: Quick workload sanity check
# Runs the target workload once without profiling to verify it executes

set -e

WORKLOAD="${1:-workloads/ai_inference.py}"

echo "[*] Running workload sanity check: $WORKLOAD"
python3 "$WORKLOAD"

echo "[+] Workload completed successfully."
