"""
ARMONIC-ARM: Interactive Pipeline Trace Interface.
"""

def render_pipeline_matrix(parsed_instructions, stalls):
    """Renders real pipeline clock intervals reflecting data and structural stalls."""
    print("\n=== [ 🔄 CYCLE-ACCURATE PIPELINE DIAGRAM ] ===")
    print(f"{'Instruction / Cycle Trace':<30} | Latency | Clock Sequence Schedule Timeline")
    print("-" * 90)
    
    # Map stall lookup indexes
    stall_map = {item[0]: item[1] for item in stalls}

    for idx, inst in enumerate(parsed_instructions):
        timeline = "  " * inst['start_cycle']
        
        if idx in stall_map:
            # Render clear structural delay gaps in the chart
            timeline += "🛑 STALL " * stall_map[idx]
            
        timeline += "▶️ [IF]—[ID]—[EX]—[WB] 🟩"
        print(f"{inst['mnemonic']:<30} | {inst['latency']} cxl   | {timeline}")
    print("-" * 90)
