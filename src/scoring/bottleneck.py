"""
ARMONIC-ARM: Bottleneck Scoring Engine.
"""

def compute_bottleneck_score(metrics, scoring_config=None):
    if scoring_config is None:
        scoring_config = {}

    weights = scoring_config.get('weights', {
        'w1': 0.3, 'w2': 0.25, 'w3': 0.2, 'w4': 0.15, 'w5': 0.1,
    })

    total_samples = metrics.get("total_samples", 0)
    top_pct = metrics.get("top_function_pct", 0)
    func_count = metrics.get("function_count", 0)

    C_s = total_samples
    M_s = top_pct * 1000
    L_s = func_count * 100
    I_s = total_samples
    P_s = 0

    B_s = (
        weights.get('w1', 0.3) * C_s +
        weights.get('w2', 0.25) * M_s +
        weights.get('w3', 0.2) * L_s +
        weights.get('w4', 0.15) * I_s +
        weights.get('w5', 0.1) * P_s
    )
    return round(B_s, 2)
