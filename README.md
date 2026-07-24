# ARMONIC-ARM

An advanced optimizer designed to eliminate hardware pipeline stalls and speed up low-level math loops for AI on Arm64 infrastructure.

---

## How to Run the Project

Follow these quick steps to clear the cache and run the system:

1. Move into the source folder:
   cd src

2. Clear the hidden Python cache:
   find . -name "__pycache__" -exec rm -rf {} +

3. Run the main optimization application:
   python3 test_client.py
    
---

## Project Structure

* test_client.py: The main driver that parses instructions and checks for hardware pipeline hazards.
* interleaving_engine.py: The backend logic that builds the dependency graph and safely rearranges the instructions.
* visualizer.py: The tool that prints the clean pipeline diagrams and timing results to your terminal.

---

## Core Features

* Pipeline Hazard Detection: Automatically identifies data dependencies (like RAW and WAR hazards) that cause processing delays.
* Structural Scoreboarding: Tracks shared physical ports (ALU, NEON/SIMD, Load, Store) to avoid hardware conflicts.
* Automated Re-ordering: Rearranges assembly code automatically to ensure the processor's execution ports stay perfectly utilized.
