"""
ARMONIC-ARM: Bottleneck Score Calculator.
Computes the unified Bottleneck Score (B_s) from profiler telemetry.
"""


def calculate_bottleneck_score(metrics, weights=None):
    """
    B_s = w1*C_s + w2*M_s + w3*L_s + w4*I_s + w5*P_s
    Lower B_s = Better performance.
    """
    if weights is None:
        weights = {
            "w1_cycles": 0.40,
            "w2_memory": 0.25,
            "w3_latency": 0.20,
            "w4_instructions": 0.10,
            "w5_power": 0.05,
        }

    total_samples = metrics.get("total_samples", 0)
    top_pct = metrics.get("top_function_pct", 0)
    func_count = metrics.get("function_count", 1)
    elapsed = metrics.get("_elapsed_sec", 1.0)

    C_s = total_samples
    M_s = top_pct * 1000
    L_s = top_pct * 1000
    I_s = 1000 / max(func_count, 1)
    P_s = elapsed * 100

    B_s = (
        weights["w1_cycles"] * C_s +
        weights["w2_memory"] * M_s +
        weights["w3_latency"] * L_s +
        weights["w4_instructions"] * I_s +
        weights["w5_power"] * P_s
    )

    return round(B_s, 2)


# Compatibility alias for any file that imports compute_bottleneck_score
compute_bottleneck_score = calculate_bottleneck_score
