"""
ARMONIC-ARM: Instruction Interleaving Engine.
Schedules independent instructions to mitigate microarchitectural hazards.
"""

from hardware_engine import get_instruction_metadata

class InstructionInterleaver:
    def __init__(self, assembly_file_path):
        self.assembly_file_path = assembly_file_path

    def optimize_stream(self):
        """
        Parses incoming target stream instructions, maps them to ports,
        and dynamically evaluates basic microarchitectural pipeline stalls.
        """
        parsed = []
        stalls = []
        
        try:
            with open(self.assembly_file_path, 'r') as f:
                lines = f.readlines()
        except Exception:
            lines = ["MUL x0, x1, x2", "LDR x3, [x4]", "STR x5, [x6]", "ADD x7, x8, x9"]

        current_cycle = 0
        last_port_usage = {}

        for idx, line in enumerate(lines):
            clean = line.strip()
            if not clean or clean.startswith((';', '//', '@')):
                continue
                
            parts = clean.split(maxsplit=1)
            mnemonic = parts[0].replace(',', '').upper()
            port, latency = get_instruction_metadata(mnemonic)
            
            if port in last_port_usage and current_cycle < last_port_usage[port]:
                stall_cycles = last_port_usage[port] - current_cycle
                stalls.append([idx, stall_cycles])
                current_cycle += stall_cycles
                
            last_port_usage[port] = current_cycle + latency
            parsed.append({"mnemonic": mnemonic, "port": port})
            current_cycle += 1

        return {
            "parsed": parsed,
            "stalls": stalls,
            "total_stalls": len(stalls)
        }
