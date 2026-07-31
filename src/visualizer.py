"""
ARMONIC-ARM: Performance Visualization Dashboard.
Generates before/after comparison charts.
"""
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import json
import os


def generate_comparison_chart(baseline_file, optimized_file, output_path="results/comparison.png"):
    with open(baseline_file) as f:
        base = json.load(f)
    with open(optimized_file) as f:
        opt = json.load(f)

    labels = ["Total Samples\n(Lower = Faster)", "Top Function %"]
    baseline_vals = [base.get("total_samples", 0), base.get("top_function_pct", 0)]
    optimized_vals = [opt.get("total_samples", 0), opt.get("top_function_pct", 0)]

    x = range(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(10, 6))
    bars1 = ax.bar([i - width/2 for i in x], baseline_vals, width, label='Baseline', color='#e74c3c')
    bars2 = ax.bar([i + width/2 for i in x], optimized_vals, width, label='Optimized', color='#27ae60')

    ax.set_ylabel('Value')
    ax.set_title('ARMONIC: Baseline vs Optimized Performance')
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend()

    for bar in bars1 + bars2:
        height = bar.get_height()
        ax.annotate(f'{int(height):,}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10)

    if baseline_vals[0] > 0:
        improvement = ((baseline_vals[0] - optimized_vals[0]) / baseline_vals[0]) * 100
    else:
        improvement = 0.0

    ax.text(0.5, 0.95, f"Overall Improvement: {improvement:.1f}%",
            transform=ax.transAxes, fontsize=14, fontweight='bold',
            ha='center', va='top',
            bbox=dict(boxstyle='round', facecolor='#fff8e1', edgecolor='#f39c12'))

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    print(f"[+] Chart saved to {output_path}")
    plt.close()


if __name__ == "__main__":
    generate_comparison_chart("results/apx_baseline.json", "results/apx_optimized.json")
