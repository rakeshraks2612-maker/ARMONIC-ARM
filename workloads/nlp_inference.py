#!/usr/bin/env python3
"""
Real-world AI inference workload for Arm64 benchmarking.

Runs a repeated quantized-style matmul + activation pipeline -- the same
core operation a transformer/CNN inner loop performs -- enough times to
generate a statistically meaningful number of profiler samples, and with
an intentionally naive hot path that a scheduling/instruction-level
optimization can legitimately improve.
"""
import time

MATRIX_SIZE = 64
ITERATIONS = 1500


def naive_matmul_row(a_row, b, size):
    """Deliberately unoptimized: no caching of repeated lookups, no
    vectorization -- a legitimate target for real optimization."""
    result = [0.0] * size
    for i in range(size):
        acc = 0.0
        for k in range(size):
            acc += a_row[k] * b[k][i]
        result[i] = acc
    return result


def relu(row):
    return [x if x > 0 else 0.0 for x in row]


def run_inference_step(a, b):
    output_rows = []
    for row in a:
        multiplied = naive_matmul_row(row, b, len(b))
        activated = relu(multiplied)
        output_rows.append(activated)
    return output_rows


def build_matrix(size, seed_offset=0):
    return [
        [((i * size + j + seed_offset) % 17) / 17.0 for j in range(size)]
        for i in range(size)
    ]


def run_inference():
    print("[+] Building input matrices...")
    a = build_matrix(MATRIX_SIZE, seed_offset=1)
    b = build_matrix(MATRIX_SIZE, seed_offset=2)

    print(f"[+] Running {ITERATIONS} inference steps on Arm64 CPU cores...")
    start_time = time.perf_counter()

    total_checksum = 0.0
    for step in range(ITERATIONS):
        out = run_inference_step(a, b)
        total_checksum += sum(sum(row) for row in out)

    end_time = time.perf_counter()

    print(f"[+] Inference complete. Checksum: {total_checksum:.4f}")
    print(f"[+] Execution Latency: {(end_time - start_time) * 1000:.2f} ms")


if __name__ == "__main__":
    run_inference()