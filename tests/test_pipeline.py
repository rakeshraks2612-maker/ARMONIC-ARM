"""
ARMONIC-ARM: Core pipeline unit tests.
Run: python -m pytest tests/
"""
import sys
import os
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.hardware_engine import get_instruction_metadata, ARMPipelineSimulator
from src.interleaving_engine import InstructionInterleaver


def test_instruction_metadata():
    assert get_instruction_metadata("MUL") == ("PORT_0_ALU", 3)
    assert get_instruction_metadata("FADD") == ("PORT_1_NEON", 4)
    assert get_instruction_metadata("UNKNOWN") == ("PORT_0_ALU", 1)


def test_pipeline_simulator_raw_hazard():
    sim = ARMPipelineSimulator()
    instructions = [
        {"mnemonic": "ADD", "dest": "R0", "sources": ["R1", "R2"]},
        {"mnemonic": "MUL", "dest": "R3", "sources": ["R0", "R4"]},
    ]
    result = sim.simulate_trace(instructions)
    assert result["total_stalls"] >= 1


def test_interleaver_parsing():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.s', delete=False) as f:
        f.write("ADD R0, R1, R2\n")
        f.write("; this is a comment\n")
        f.write("MUL R3, R0, R4\n")
        f.write(".global main\n")
        path = f.name

    interleaver = InstructionInterleaver(path)
    instructions = interleaver.optimize_stream()

    assert len(instructions) == 2
    assert instructions[0]["mnemonic"] == "ADD"
    assert instructions[0]["dest"] == "R0"
    assert instructions[1]["mnemonic"] == "MUL"

    os.unlink(path)
