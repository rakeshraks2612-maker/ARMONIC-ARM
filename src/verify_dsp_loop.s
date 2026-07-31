// ARMONIC Microarchitectural Test Workload
// Packed with explicit Read-After-Write (RAW) register dependencies
// to verify cycle-accurate scoreboard tracking.

.global _start
.text

_start:
    MUL W0, W1, W2           // Multi-cycle scalar multiplication (Locks destination W0)
    ADD W3, W0, W4           // RAW Hazard: Instantly attempts to read W0 before lock release
    LSL W5, W3, #2           // RAW Hazard: Instantly attempts to read W3 via shift operation
    SMULL X6, W7, W8         // 64-bit Sign Extended Multiply (Locks destination X6)
    DUP V0.8B, W9            // Advanced SIMD vector broadcast operation flooding Neon ALU unit
    MUL W10, W11, W12        // Secondary multiplication routine triggering structural limits
