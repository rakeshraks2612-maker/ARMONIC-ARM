"""Generates Bottleneck Score (B_s) visualization charts."""
import matplotlib.pyplot as plt

def generate_chart():
    labels = ['Baseline', 'Optimized (Arm64 Patch)']
    cycles = [1.2, 0.8] # Millions
    
    plt.bar(labels, cycles, color=['#ff9999','#66b3ff'])
    plt.ylabel('Execution Cycles (Millions)')
    plt.title('ARMONIC: Arm Performix APX Benchmark Results')
    plt.savefig('results_chart.png')
    print("[+] Chart saved to results_chart.png")

if __name__ == "__main__":
    generate_chart()
