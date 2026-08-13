# MIGRATION.md — Onboarding Guide

> **Goal:** Drop any Python AI inference workload into ARMONIC and get an optimized, validated patch in under 5 minutes.

---

## Step 1: Prepare Your Workload

Place your Python file inside the `workloads/` directory:

```bash
cp /path/to/your/inference_pipeline.py workloads/my_pipeline.py
```

**Requirements:**
- Pure Python (NumPy, PyTorch, TensorFlow, stdlib all supported)
- A runnable `main()` or top-level execution block
- No external network dependencies during execution

**Example structure:**
```python
# workloads/my_pipeline.py
import json
import numpy as np

def predict(batch):
    # your inference logic
    return results

if __name__ == "__main__":
    predict(load_batch())
```

---

## Step 2: Configure & Run

```bash
# 1. Copy config template
cp config.example.yaml config.yaml

# 2. Add your Gemini API key to config.yaml
#    (key is never committed; see .gitignore)

# 3. Run ARMONIC against your workload
python -m armonic.run --workload workloads/my_pipeline.py
```

**What happens:**
1. APX profiles your workload on Neoverse V1 hardware counters
2. Bottleneck score `B_s` is computed with Neoverse-tuned weights
3. LLM generates an Arm64-aware patch
4. Patch is validated (syntax → AST → functional re-profile)
5. On success: committed to `armonic/auto-refactor-<timestamp>`
6. On failure: rejected, original code untouched on `main`

---

## Step 3: Review & Merge

```bash
# See what changed
git diff main armonic/auto-refactor-20260813-143022

# Review the validation report
cat demo/patches/my_pipeline_validation.json

# If satisfied, merge back to main
git checkout main
git merge armonic/auto-refactor-20260813-143022
```

**Before merging, verify:**
- [ ] `B_s` decreased (improvement confirmed)
- [ ] Output semantics preserved (spot-check results)
- [ ] No new dependencies introduced without your approval

---

## Migration Checklist

| Check | Status |
|-------|--------|
| Workload runs standalone on Arm64 | ☐ |
| `config.yaml` has valid Gemini API key | ☐ |
| Docker / container has APX toolkit installed | ☐ |
| Git repo initialized (for branch isolation) | ☐ |
| Reviewed auto-generated patch before merge | ☐ |

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `APX not found` | Install Arm Performix toolkit or use `--fallback-cprofile` |
| `Gemini API error` | Verify key in `config.yaml`; check quota |
| `Patch rejected: score regression` | LLM suggestion hurt performance; retry or inspect logs |
| `SyntaxError on patch` | Automatically rejected; retry with `--verbose` to see raw LLM output |
| `No git repo detected` | Run `git init` in project root |

---

## Next Steps

- Add your workload to `workloads/` and benchmark it alongside the 4 included examples
- Tune `src/scoring/bottleneck.py` weights if your workload has different bottleneck patterns
- Extend `prompts/optimize.txt` with domain-specific optimization hints

**Need help?** Open an issue or see [CONTRIBUTING.md](CONTRIBUTING.md).
