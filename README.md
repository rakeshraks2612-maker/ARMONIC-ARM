# Armonic: Autonomous AI Workload Optimization for Arm64

Armonic is a closed-loop performance engineering framework that profiles AI
workloads running on Arm64 (Neoverse/Cortex) infrastructure, exposes
hardware-level telemetry to an LLM agent via the **Model Context Protocol
(MCP)**, and autonomously generates, validates, and commits refactoring
patches that reduce microarchitectural bottlenecks.

Rather than optimizing neural network layers, Armonic targets the
system-level overhead of agentic AI runtimes — JSON serialization, thread
spawning, and repeated tool execution — that causes instruction cache misses
and memory stalls on cloud-native Arm64 servers.

---

## How it works

```
1. Source Workload   (Python/C++, checked into the Raw AI Workload Repository)
2. Run on Arm64      (Arm64 Target Container — Cloud / Data Center / Edge)
3. Profile           (Arm Performix Profiling Engine — CPU cycles, instructions
                       retired, L1/L2/L3 cache, branch misses, memory accesses)
4. Expose via MCP    (Armonic MCP Server — JSON-RPC 2.0, bidirectional)
5. Analyze & Score   (LLM Performance Co-Pilot + Bottleneck Scoring B_s)
6. Auto-Refactor     (generates a patch, isolates the hotspot, opens a git branch)
7. Rebuild & Repeat  (reprofile the new branch and validate the improvement)
```

The bottleneck score used to prioritize hotspots is:

```
B_s = w1*C_s + w2*M_s + w3*L_s + w4*I_s + w5*P_s

C_s : CPU Cycles
M_s : Memory Stalls
L_s : Cache Misses
I_s : Instructions Retired
P_s : Branch Misses
```

Weights (`w1..w5`) are configurable per workload — see [Configuration](#configuration).

---

## Architecture

| Component | Role |
|---|---|
| **Arm64 Target Environment** | Runs the raw workload inside an Arm64 container (Neoverse/Cortex), on cloud, data center, or edge. |
| **Telemetry Pipeline** | Arm Performix collects hardware counters via `apx trace`; the Armonic MCP Server exposes them as structured, schema-validated telemetry over JSON-RPC 2.0. |
| **Autonomous Refactoring Engine** | An LLM Performance Co-Pilot consumes telemetry, scores bottlenecks, isolates the responsible code, and pushes an automated git branch with the refactor, tests, and validated metrics. |

---

## Prerequisites

- An Arm64 host or container runtime (Neoverse/Cortex-class hardware, or QEMU
  Arm64 emulation for local development)
- `apx` (Arm Performix CLI) installed and able to read hardware performance
  counters on the target
- Python 3.10+ and/or your workload's native toolchain (C++ build tools if
  profiling native code)
- Git, with push access to the repo Armonic will branch from
- An Anthropic API key (or your configured LLM provider) for the Refactoring
  Engine

---

## Quick Start

1. **Clone and enter the project:**
   ```bash
   git clone <https://github.com/rakeshraks2612-maker/ARMONIC-ARM> armonic-arm
   cd armonic-arm
   ```

2. **Set up a Python environment and install dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **(Optional) Clear cached bytecode before a clean profiling run:**
   ```bash
   find . -name "__pycache__" -type d -print -exec rm -rf {} +
   ```
   > This only removes Python's compiled bytecode cache and is safe to skip —
   > it does not touch source files. Review the printed list before running
   > if you're pointing this at a directory you don't fully trust.

4. **Configure your target and credentials:**
   ```bash
   cp config.example.yaml config.yaml
   # edit config.yaml: target host, apx path, bottleneck weights, LLM API key
   ```

5. **Run the workload once on the Arm64 target to sanity-check it builds/runs:**
   ```bash
   ./scripts/run_workload.sh
   ```

6. **Start a profiling + optimization loop:**
   ```bash
   python -m armonic.run --config config.yaml
   ```
   This will profile the workload with Performix, surface telemetry through
   the MCP server, let the LLM agent score and isolate hotspots, and open a
   branch (default `armonic/auto-refactor-<timestamp>`) with the proposed
   fix and before/after metrics.

7. **Review the generated branch** before merging — Armonic validates that
   the bottleneck score improved and tests still pass, but a human review
   step is still recommended for production code.

---

## Configuration

Key options in `config.yaml`:

```yaml
target:
  host: <arm64-host-or-container>
  arch: aarch64

profiling:
  tool: apx
  counters: [cycles, instructions, cache_l1, cache_l2, cache_l3, branch_misses, memory_accesses]

scoring:
  weights:
    w1: 0.3   # CPU cycles
    w2: 0.25  # Memory stalls
    w3: 0.2   # Cache misses
    w4: 0.15  # Instructions retired
    w5: 0.1   # Branch misses

llm:
  provider: anthropic
  model: <your-model-id>
```

---

## Repository Layout

```
armonic-arm/
├── src/
│   ├── mcp_server/        # Armonic MCP server (JSON-RPC 2.0 endpoints)
│   ├── profiling/         # Performix (apx) integration + counter parsing
│   ├── scoring/           # Bottleneck scoring (B_s) implementation
│   └── refactor_engine/   # LLM agent: hotspot isolation, patch generation, git automation
├── workloads/             # Sample AI workloads used for benchmarking
├── config.example.yaml
├── requirements.txt
└── README.md
```

---

## Status

Actively in development for the ARM optimization competition. Current focus:
MCP telemetry schema, bottleneck scoring calibration, and closed-loop
validation (profile → refactor → reprofile) on sample agentic workloads.

## License

TBD.
