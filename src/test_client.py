"""
ARMONIC-ARM: Integration Driver Verification Test Loop.
"""

import os
from interleaving_engine import InstructionInterleaver
from hardware_engine import ARMPipelineSimulator
from performix_wrapper import profile_assembly_workload
from visualizer import render_pipeline_matrix

def run_pipeline_optimization():
    # Setup our real test asset path inside src/ directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    target_assembly = os.path.join(current_dir, "verify_dsp_loop.s")

    # Generate a realistic DSP trace containing hard RAW Hazards and structural neon vectors
    with open(target_assembly, "w") as f:
        f.write("""; Safe Arm64 Target DSP Test Array Loop
.global _start
_start:
    MUL X0, X1, X2
    ADD X3, X0, X4
    DUP V0.8B, W9
    LDR X5, [X6]
""")

    print("=" * 80)
    print("ARMONIC ARCHITECTURE PROFILE VISUALIZER: CLOSED-LOOP PERFORMANCE ENGINE")
    print("=" * 80)
    
    # Step 1: Performix Profile Validation Checks
    prof = profile_assembly_workload(target_assembly)
    print(f"\n[+] Performix Verification: Profile Status -> {prof['status']}")
    print(f"[+] Loaded Context Space Payload Buffer: {prof['raw_payload_bytes']} bytes")
    
    # Step 2: Extract Token Streams via Interleaver
    interleaver = InstructionInterleaver(target_assembly)
    raw_stream = interleaver.optimize_stream()
    
    # Step 3: Run true hazard detection metrics simulation
    simulator = ARMPipelineSimulator()
    results = simulator.simulate_trace(raw_stream)
    
    # Step 4: Render genuine diagnostic telemetry visual matrices
    render_pipeline_matrix(results["parsed"], results["stalls"])
    
    print("\n[+] Verification Trace Complete.")
    print(f"[+] Actual Data/Structural Hazards Mitigated: {results['total_stalls']}")
    print(f"[+] Final Cycle Runtime Block Duration: {len(results['parsed']) + sum(s[1] for s in results['stalls'])} cycles")
    print("=" * 80)

if __name__ == "__main__":
    run_pipeline_optimization()
