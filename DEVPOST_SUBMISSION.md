# DEVPOST SUBMISSION

## Project Name
ARMONIC-ARM: Autonomous Agentic Performance Optimization for Arm64 Cloud AI

## Elevator Pitch
ARMONIC is the first fully autonomous, closed-loop optimization agent for Python AI workloads on Arm64 cloud. It profiles with Arm Performix (APX), feeds live telemetry to an LLM, generates a patch, validates syntax and correctness, and commits the optimization to an isolated git branch. On AWS Graviton, it reduced an AI inference workload from 17.6s to 0.23s (98.7% improvement).

## Track
Cloud AI

## What Does Your Project Do?
ARMONIC executes a 3-phase autonomous pipeline:
1. Baseline Profiling: Uses Arm Performix (APX) on Arm64 Linux.
2. Agentic Analysis: Queries an LLM with structured telemetry.
3. Auto-Refactor: Applies patch, validates, re-profiles, commits to git branch.

## How We Built It
Python 3.12, Arm Performix (APX), Google Gemini API, GitPython, matplotlib, pytest. Cross-platform fallback: cProfile when APX is unavailable.

## Challenges
- Parsing APX export format (ZIP + CSV)
- Ensuring LLM output was deterministic enough to parse
- Building cross-platform profiler fallback with identical schema

## Accomplishments
- 98.7% wall-time reduction on AWS Graviton Arm64
- Fully autonomous end-to-end pipeline
- Zero manual code changes required
- Free-tier LLM compatibility

## What We Learned
Agentic optimization is viable. The bottleneck is not the LLM's suggestions — it is the validation and safety layer.

## What's Next
- OpenAI/Anthropic LLM provider support
- Arm MCP Server integration
- Multi-file refactoring

## Try It Out
git clone https://github.com/rakeshraks2612-maker/ARMONIC-ARM.git
cd ARMONIC-ARM
make install
cp config.example.yaml config.yaml
make run

## Video Demo
[YouTube link — update before submission]

## License
MIT
