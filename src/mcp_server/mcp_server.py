"""
ARMONIC-ARM: MCP Server Client Bridge.
Interfaces with `armlimited/arm-mcp:latest` Docker container.
Falls back to local heuristic analysis when the container is unavailable.
"""
import requests
import json


class ArmMCPClient:
    def __init__(self, host="http://localhost:8080"):
        self.endpoint = f"{host}/v1/analyze"

    def query_architecture_bottlenecks(self, workload_metrics):
        """
        Attempts to query the official Arm MCP Server.
        Falls back to local heuristic if server unavailable.
        """
        print("[+] Querying Arm MCP Server...")
        payload = {
            "metrics": workload_metrics,
            "target_arch": "arm64-v8a"
        }

        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                timeout=5
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.ConnectionError:
            print("[!] Arm MCP Server unreachable. Using local heuristic fallback.")
            return self._local_heuristic(workload_metrics)

        except requests.exceptions.Timeout:
            print("[!] Arm MCP Server timeout. Using local heuristic fallback.")
            return self._local_heuristic(workload_metrics)

    def _local_heuristic(self, metrics):
        """Local analysis when MCP server is unavailable."""
        total = metrics.get("total_samples", 0)
        top_pct = metrics.get("top_function_pct", 0)

        if top_pct > 40:
            insight = "Severe hotspot concentration detected. Recommend JIT compilation (numba/torch.compile)."
        elif total > 1000000:
            insight = "High total sample count. Consider parallelization or vectorization."
        else:
            insight = "Moderate overhead. Focus on cache-friendly data layouts."

        return {
            "status": "fallback",
            "insight": insight,
            "source": "local_heuristic"
        }
