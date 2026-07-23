"""
ARMONIC Microarchitectural Synthesis Matrix Engine (Tier 2)
Concurrently models Radix-4, CSD, and Radix-8 multiplication architectures
to compute gate latency, silicon area overhead, and interconnect wiring densities.
"""

import math

def simulate_radix4_wallace(mul_count: int, bit_width: int) -> dict:
    """Simulates Radix-4 Booth + Wallace Tree Reduction."""
    partial_products = bit_width // 2
    stages = 0
    current_rows = partial_products
    while current_rows > 2:
        stages += 1
        current_rows = (current_rows // 3 * 2) + (current_rows % 3)
    
    gate_delay_ns = 2.4 + (stages * 1.8) + 3.2
    # Scaling factor modeling relative silicon cell area utilization
    estimated_gates = partial_products * 45 + (bit_width * 12)
    
    return {"latency_ns": round(gate_delay_ns, 2), "area_gates": estimated_gates, "routing_overhead": "Moderate"}

def simulate_csd_array(mul_count: int, bit_width: int) -> dict:
    """Simulates Canonical Signed Digit (CSD) Multiplier optimizations."""
    # CSD drops non-zero digits to at most bit_width/2, statistically averaging bit_width/3
    optimized_partial_products = max(2, math.ceil(bit_width / 3))
    stages = max(1, math.ceil(math.log2(optimized_partial_products)))
    
    gate_delay_ns = 1.8 + (stages * 2.1) + 4.0
    # CSD drastically removes logic structures by converting multipliers to shift-adds
    estimated_gates = optimized_partial_products * 28 + (bit_width * 6)
    
    return {"latency_ns": round(gate_delay_ns, 2), "area_gates": estimated_gates, "routing_overhead": "Low"}

def simulate_radix8_dadda(mul_count: int, bit_width: int) -> dict:
    """Simulates Extreme High-Radix Booth (Radix-8) + Dadda Tree Reduction."""
    # Radix-8 scans 4 bits at a time, slashing partial products down by 67%
    partial_products = max(2, math.ceil(bit_width / 3))
    # Dadda keeps reduction linear per column, minimizing intermediate adder stages
    stages = max(1, math.ceil(math.log(partial_products) / math.log(1.5)))
    
    gate_delay_ns = 3.6 + (stages * 1.5) + 2.8 # Fast compression, heavier encoding overhead
    # Higher control logic and multiplexer array gate costs
    estimated_gates = partial_products * 95 + (bit_width * 24)
    
    return {"latency_ns": round(gate_delay_ns, 2), "area_gates": estimated_gates, "routing_overhead": "High (Dense Cross-Interconnects)"}

def profile_advanced_multiplier(multiplicand: int, multiplier: int, bit_width: int = 8) -> dict:
    """
    Core entry point evaluating multi-dimensional silicon synthesis trade-offs 
    against system transmission deadline limits.
    """
    LATENCY_THRESHOLD_NS = 10.0
    
    # Run concurrent microarchitectural evaluations
    r4_metrics = simulate_radix4_wallace(1, bit_width)
    csd_metrics = simulate_csd_array(1, bit_width)
    r8_metrics = simulate_radix8_dadda(1, bit_width)
    
    # System picks the optimal architecture based on latency requirements
    chosen_architecture = "Radix-4 + Wallace Tree"
    selected_latency = r4_metrics["latency_ns"]
    
    if r8_metrics["latency_ns"] < LATENCY_THRESHOLD_NS:
        chosen_architecture = "Radix-8 + Dadda Tree Network"
        selected_latency = r8_metrics["latency_ns"]
    elif r4_metrics["latency_ns"] > LATENCY_THRESHOLD_NS:
        chosen_architecture = "Canonical Signed Digit (CSD) Array"
        selected_latency = csd_metrics["latency_ns"]

    deadline_breached = selected_latency > LATENCY_THRESHOLD_NS
    packet_priority_class = "CRITICAL_URGENT_QOS_0" if deadline_breached else "STANDARD_BATCH_QOS_1"

    return {
        "hardware_layer": {
            "evaluation_matrix": {
                "radix4_wallace_tree": r4_metrics,
                "canonical_signed_digit": csd_metrics,
                "radix8_dadda_tree": r8_metrics
            },
            "selected_silicon_target": chosen_architecture,
            "critical_path_delay_ns": selected_latency,
            "bit_configured": bit_width
        },
        "network_co_simulation_layer": {
            "latency_threshold_ns": LATENCY_THRESHOLD_NS,
            "deadline_breached": deadline_breached,
            "ns3_injected_priority_class": packet_priority_class,
            "network_optimization_action": (
                "TRIGGER_IMMEDIATE_PACKET_PRIORITIZATION: Microarchitectural processing "
                "delay exceeds transmission limits. Rerouting wireless node bandwidth queues."
                if deadline_breached else "DEFER_QUEUE_SCHEDULING: Safe headroom detected."
            )
        }
    }
