"""
ARMONIC-ARM: Main Orchestration Core.
Ingests assembly files, executes the pipeline simulation, and drives telemetry.
"""

import os
import sys
from interleaving_engine import InterleavingEngine
from hardware_model import calculate_synthesis_metrics
from visualizer import draw_header, render_pipeline_diagram, render_synthesis_matrix

def run_pipeline_optimization(assembly_file):
    # Guardrail against missing files
    if not os.path.exists(assembly_file):
        print(f"[-] Error: Assembly file target '{assembly_file}' not found.")
        sys.exit(1)
        
    draw_header("EXECUTION PIPELINE MATRIX")
    
    # 1. Initialize the true optimization engine with the file path
    engine = InterleavingEngine(assembly_file)
    
    # 2. Run the dynamic scheduling matrix to compute actual stalls
    metrics = engine.optimize_stream()
    
    # 3. Render the cycle-accurate pipeline trace using real computed data
    render_pipeline_diagram(metrics["parsed"], metrics["stalls"])
    
    # 4. Generate the synthesis space data dynamically from the total stall count
    total_stalls = metrics["total_stalls"]
    synthesis_data = calculate_synthesis_metrics(bit_width=32, total_stalls=total_stalls)
    
    # 5. Output the verified hardware metrics rather than hardcoded strings
    render_synthesis_matrix(bit_width=32, stalls=total_stalls)
    
    print("\n[+] Verification Trace Complete.")
    print(f"[+] Total Pipeline Stalls Mitigated: {total_stalls}")
    print(f"[+] Final Modeled Critical Latency: {synthesis_data['latency_ns']} ns")

if __name__ == "__main__":
    # Default path targeting your repository structure
    target_assembly = "src/verify_dsp_loop.s"
    
    # Create a dummy sample assembly file if none exists to prevent instant crashes
    if not os.path.exists(target_assembly):
        os.makedirs("src", exist_ok=True)
        with open(target_assembly, "w") as f:
            f.write("MUL R1, R2, R3\nLDR R4, [R1]\nSTR R4, [R5]\nADD R6, R6, #1\n")
            
    run_pipeline_optimization(target_assembly)
