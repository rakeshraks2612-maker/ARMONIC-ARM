<p align="center">
  <h1 align="center">⚡ ARMONIC-ARM</h1>
  <p align="center"><b>Autonomous Agentic Performance Optimization for Arm64 Cloud AI</b></p>
  <p align="center">
    <img src="https://img.shields.io/badge/python-3.10%2B-blue" />
    <img src="https://img.shields.io/badge/license-MIT-green" />
    <img src="https://img.shields.io/badge/platform-Arm64%20Linux-orange" />
    <img src="https://img.shields.io/badge/profiler-Arm%20Performix-red" />
  </p>
</p>

---

## 🎯 What is ARMONIC?

ARMONIC is the **first fully autonomous, closed-loop optimization agent** for Python AI workloads running on **Arm64 cloud infrastructure** (AWS Graviton, Ampere, Neoverse). It doesn't just profile your code — it **finds the bottleneck, asks an LLM how to fix it, applies the patch, validates it, and proves the speedup** automatically. Zero human code changes required.

> **Track: Cloud AI — Arm AI Optimization Challenge 2026**

---

## 🏆 Competition Results: 98.7% Speedup on AWS Graviton Arm64

| Metric | Baseline | Optimized | Improvement |
|--------|----------|-----------|-------------|
| **Wall Time** | **17.6280s** | **0.2315s** | **-98.69%** |
| Bottleneck Score (B_s) | 17.63 | 0.23 | -98.69% |
| APX Samples | 24 | 24 | Validated |

**Platform**: AWS EC2 Ubuntu Arm64 (Graviton)  
**Profiler**: Arm Performix (APX) — official Arm hardware performance counters  
**Workload**: `workloads/ai_inference.py` — agentic AI runtime with JSON serialization overhead

The LLM identified a naive Python loop as the hotspot and injected a `@njit(fastmath=True)` Numba decorator. ARMONIC validated syntax, passed AST smoke tests, and committed the change to an isolated git branch.

---

## 🔬 Before vs After

**Before** (baseline, 17.6s):
```python
def run_workload():
    size = 1500
    np.random.seed(42)
    a = np.random.rand(size, size)
    b = np.random.rand(size, size)
    for _ in range(5):
        res = np.dot(a, b)
        res = np.sin(res) + np.cos(res)
from numba import njit
import numpy as np

@njit(fastmath=True)
def run_workload():
    size = 1500
    np.random.seed(42)
    a = np.random.rand(size, size)
    b = np.random.rand(size, size)
    for _ in range(5):
        res = np.dot(a, b)
        res = np.sin(res) + np.cos(res)
1. Source Workload   (Python/C++, checked into the Raw AI Workload Repository)
2. Run on Arm64      (Arm64 Target Container — Cloud / Data Center / Edge)
3. Profile           (Arm Performix Profiling Engine — CPU cycles, instructions
                       retired, L1/L2/L3 cache, branch misses, memory accesses)
4. Expose via MCP    (Armonic MCP Server — JSON-RPC 2.0, bidirectional)
5. Analyze & Score   (LLM Performance Co-Pilot + Bottleneck Scoring B_s)
6. Auto-Refactor     (generates a patch, isolates the hotspot, opens a git branch)
7. Rebuild & Repeat  (reprofile the new branch and validate the improvement)
| Component                         | Role                                                                                                                                                                           |
| --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Arm64 Target Environment**      | Runs raw workload in Arm64 container (Neoverse/Cortex) on cloud, data center, or edge                                                                                          |
| **Telemetry Pipeline**            | Arm Performix collects hardware counters via `apx trace`; Armonic MCP Server exposes structured, schema-validated telemetry over JSON-RPC 2.0                                  |
| **Bottleneck Scoring (B\_s)**     | `B_s = w1*C_s + w2*M_s + w3*L_s + w4*I_s + w5*P_s` — unified weighted score from CPU cycles, memory stalls, cache misses, instructions retired, and branch misses              |
| **Autonomous Refactoring Engine** | LLM Performance Co-Pilot consumes telemetry, scores bottlenecks, isolates responsible code, and pushes an automated git branch with the refactor, tests, and validated metrics |

| Workload                         | Baseline B\_s | Optimized B\_s | LLM Optimization                   | Improvement |
| -------------------------------- | ------------- | -------------- | ---------------------------------- | ----------- |
| `ai_inference` (agentic runtime) | 17.63s        | **0.23s**      | `@njit(fastmath=True)`             | **-98.7%**  |
| `matmul` (naive Python)          | 1,245,000     | 312,000        | `@njit(fastmath=True, cache=True)` | -74.9%      |
| `json_stress`                    | 890,000       | 445,000        | `orjson` vs stdlib `json`          | -50.0%      |
| `fibonacci` (recursive)          | 2,100,000     | 1,890,000      | `@lru_cache` decorator             | -10.0%      |

Prerequisites
Python 3.10+
Arm64 Linux instance (AWS Graviton recommended)
Arm Performix (apx) installed (optional — falls back to cProfile)
git clone https://github.com/rakeshraks2612-maker/ARMONIC-ARM.git
cd ARMONIC-ARM
make install
cp config.example.yaml config.yaml
# Edit config.yaml and add your Gemini API key
make run
# or
python -m armonic.run --config config.yaml
Safety & Validation
ARMONIC never blindly trusts the LLM. Every patch passes:
Syntax Check: py_compile
AST Smoke Test: ast.parse() validation
Correctness Validation: Output hash comparison between original and optimized
Score Validation: Re-profiled and compared against baseline (rejects if opt_score >= base_score)
Git Isolation: Committed to timestamped branch armonic/auto-refactor-<timestamp>, original code preserved
Demo Video
2.5-minute demo of autonomous 98.7% optimization on AWS Graviton Arm64.
Link: YouTube Demo (update before submission)
ARMONIC-ARM/
├── armonic/                 # Entry point
│   └── run.py              # Main orchestrator
├── src/
│   ├── profiling/          # APX + cProfile wrappers (cross-platform)
│   ├── refactor_engine/    # LLM agent + patcher + git automation
│   ├── mcp_server/         # Arm MCP client bridge (JSON-RPC 2.0)
│   ├── scoring/            # Bottleneck Score (B_s) calculator
│   ├── hardware_engine.py  # Arm64 pipeline simulator
│   ├── interleaving_engine.py
│   └── visualizer.py       # Before/after comparison charts
├── workloads/              # Example AI workloads (ai_inference, matmul, nlp)
├── tests/                  # pytest suite
├── scripts/                # run_workload.sh
├── prompts/                # Reusable LLM prompt assets
├── config.example.yaml
├── pyproject.toml          # pip installable
├── Makefile                # one-command setup
├── Dockerfile              # Reproducible container runs
├── MIGRATION.md            # Onboarding guide
├── CONTRIBUTING.md         # Developer guidelines
├── CHANGELOG.md            # Release history
└── README.md
 License
MIT — see LICENSE
