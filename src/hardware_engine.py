"""
ARMONIC-ARM: Hardware Engine Layer.
Exposes microarchitectural latency profiling interfaces synchronized with the global hardware model.
"""

from hardware_model import get_instruction_metadata, calculate_synthesis_metrics

class ARMPipelineSimulator:
    def __init__(self):
        self.name = "Armonic Pipeline Engine Core"

    def analyze_hazards_and_stalls(self, parsed_instructions):
        """
        Calculates pipeline execution stalls for an incoming instruction trace.
        Guarantees exact parity with the core scheduler logic.
        """
        stalls = []
        current_cycle = 0
        last_port_usage = {}
        
        for idx, inst in enumerate(parsed_instructions):
            # Fallback for raw string tokens or dictionary objects
            mnemonic = inst if isinstance(inst, str) else inst.get('mnemonic', 'UNKNOWN')
            
            # Query the single source of truth configuration
            port, latency = get_instruction_metadata(mnemonic)
            
            if port in last_port_usage and current_cycle < last_port_usage[port]:
                stall_cycles = last_port_usage[port] - current_cycle
                stalls.append((idx, stall_cycles))
                current_cycle += stall_cycles
                
            last_port_usage[port] = current_cycle + latency
            current_cycle += 1
            
        return {
            "stalls": stalls,
            "total_stalls": len(stalls)
        }

def profile_advanced_multiplier(bit_width=32, total_stalls=0):
    """
    Exposes unified critical-path data endpoints to external clients.
    """
    return calculate_synthesis_metrics(bit_width, total_stalls)
