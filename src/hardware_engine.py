"""
Unified Hardware Definition Model for ARMONIC-ARM.
Acts as the single source of truth for cycle latencies and instruction mapping.
"""

def get_instruction_metadata(opcode):
    """
    Maps an assembly opcode to its target execution port and cycle latency.
    Ensures all parts of the engine simulate the exact same processor behavior.
    """
    op = opcode.upper().strip()
    
    # Port 1: Vector / NEON Multipliers (High Latency)
    if op in ["MUL", "SMULL", "DUP", "SMLAL"]:
        return "PORT_1_NEON", 3
        
    # Port 2: Memory Operations (Loads)
    elif op in ["LDR", "LDUR", "LDP"]:
        return "PORT_2_LOAD", 4
        
    # Port 3: Memory Operations (Stores)
    elif op in ["STR", "STUR", "STP"]:
        return "PORT_3_STORE", 1
        
    # Port 0: Default Scalar ALU Operations (Fast Execution)
    else:
        return "PORT_0_ALU", 1


def calculate_synthesis_metrics(bit_width=32, total_stalls=0):
    """
    Calculates performance and area metrics based on the simulation results.
    Unified formula to ensure identical dashboard telemetry output.
    """
    # Mathematical latency formula derived from the structural stall matrix
    critical_latency_ns = 3.6 + (3 * 1.5) + (total_stalls * 0.5)
    
    # Hardware gate area evaluation based on multiplier bit width
    silicon_area_gates = (bit_width / 3) * 95 + (bit_width * 24)
    
    return {
        "topology": "High-Radix Radix-8 + Dadda",
        "latency_ns": round(critical_latency_ns, 2),
        "area_gates": int(silicon_area_gates)
    }
