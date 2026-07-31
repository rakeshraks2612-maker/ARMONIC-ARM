"""
ARMONIC-ARM: Microarchitectural Ground Truth Engine.
Tracks actual Arm64 execution port configurations and instruction latencies.
"""

# Hardwired latency configuration for structural conflict analysis
INSTRUCTION_LATENCY_TABLE = {
    "MUL": ("PORT_0_ALU", 3),
    "ADD": ("PORT_0_ALU", 1),
    "SUB": ("PORT_0_ALU", 1),
    "LDR": ("PORT_2_LOAD", 2),
    "STR": ("PORT_3_STORE", 2),
    "FADD": ("PORT_1_NEON", 4),
    "FMUL": ("PORT_1_NEON", 5),
    "LSL": ("PORT_0_ALU", 1),
    "SMULL": ("PORT_0_ALU", 3),
    "DUP": ("PORT_1_NEON", 2)
}

def get_instruction_metadata(mnemonic):
    """Returns the associated execution port and latency cycles for a given mnemonic."""
    return INSTRUCTION_LATENCY_TABLE.get(mnemonic.upper(), ("PORT_0_ALU", 1))


class ARMPipelineSimulator:
    """True register dependency hazard scoreboard simulator engine."""
    def __init__(self):
        pass
        
    def simulate_trace(self, instructions):
        """
        Parses raw assembly tokens to simulate structural port conflicts 
        and true Read-After-Write (RAW) data dependencies.
        """
        parsed = []
        stalls = []
        current_cycle = 0
        
        # Track state for register write-backs and functional port hazards
        register_ready_cycle = {}
        port_available_cycle = {}

        for idx, inst in enumerate(instructions):
            mnemonic = inst["mnemonic"]
            dest_reg = inst["dest"]
            src_regs = inst["sources"]
            
            port, latency = get_instruction_metadata(mnemonic)
            inst_stall = 0

            # 1. Evaluate Data Hazard (RAW Dependency Check)
            for src in src_regs:
                if src in register_ready_cycle and current_cycle < register_ready_cycle[src]:
                    raw_stall = register_ready_cycle[src] - current_cycle
                    inst_stall = max(inst_stall, raw_stall)

            # 2. Evaluate Structural Hazard (Execution Port Conflict)
            if port in port_available_cycle and current_cycle < port_available_cycle[port]:
                structural_stall = port_available_cycle[port] - current_cycle
                inst_stall = max(inst_stall, structural_stall)

            # Accumulate cycles if a hazard condition was detected
            if inst_stall > 0:
                stalls.append([idx, inst_stall])
                current_cycle += inst_stall

            # Lock port and register resources dynamically based on parameters
            port_available_cycle[port] = current_cycle + 1
            if dest_reg:
                register_ready_cycle[dest_reg] = current_cycle + latency

            parsed.append({
                "mnemonic": mnemonic,
                "port": port,
                "start_cycle": current_cycle,
                "latency": latency
            })
            current_cycle += 1
            
        return {"parsed": parsed, "stalls": stalls, "total_stalls": len(stalls)}
