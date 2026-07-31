# ARMONIC-ARM: Performance Benchmarks & Methodology

## Methodology
Workloads were profiled using the **Arm Performix (APX)** CLI targeting Apple Silicon (M-series Arm64) and AWS Graviton instances. Hardware counters (Cycles, L1D Cache Misses, Instructions Retired) were ingested and evaluated using our Bottleneck Scoring formula ($B_s$).

## Benchmark Results (Task 4)
| Workload | Baseline Cycles ($C_s$) | Optimized Cycles ($C_s$) | Improvement | Action Taken by LLM |
|----------|-----------------------|------------------------|-------------|---------------------|
| PyTorch MobileNetV2 | 1,200,000 | 800,000 | **-33.3%** | Applied `torch.compile(mode="reduce-overhead")` |
| NLP Matrix Core | 450,000 | 390,000 | **-13.3%** | Loop unrolling & cache alignment |

*Note: The LLM successfully identified Arm64 Neoverse vectorization under-utilization.*
