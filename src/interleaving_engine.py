"""
ARMONIC-ARM: Assembly Parser Stream Processor.
Strips out directives and labels, isolating register allocations.
"""

import os
import re

class InstructionInterleaver:
    def __init__(self, assembly_file_path):
        self.assembly_file_path = assembly_file_path

    def optimize_stream(self):
        """Parses target assembly from physical storage file path explicitly."""
        cleaned_instructions = []
        
        if not os.path.exists(self.assembly_file_path):
            raise FileNotFoundError(f"Target assembly profile missing at: {self.assembly_file_path}")

        with open(self.assembly_file_path, 'r') as f:
            lines = f.readlines()

        for line in lines:
            clean = line.strip()
            # Strict validation: strip comments, labels, and architectural directives
            if not clean or clean.startswith((';', '//', '@', '.')) or clean.endswith(':'):
                continue
                
            # Normalize structure splits to parse operands cleanly
            parts = re.split(r'\s+', clean, maxsplit=1)
            mnemonic = parts[0].replace(',', '').upper()
            
            dest = None
            sources = []
            
            if len(parts) > 1:
                operands = [op.strip().upper() for op in parts[1].split(',')]
                if operands:
                    dest = operands[0]  # Destination register token
                    sources = operands[1:]  # Dependent source operands list

            cleaned_instructions.append({
                "mnemonic": mnemonic,
                "dest": dest,
                "sources": sources
            })

        return cleaned_instructions
