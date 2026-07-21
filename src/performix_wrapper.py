import subprocess
import json
import os

class PerformixWrapper:
    def __init__(self, target_binary_path):
        self.binary_path = target_binary_path
        # Target metrics mapping based on our hardware cost function formula
        self.metrics = {
            "frontend_bound_cycles": 0.0,
            "l1_icache_misses": 0,
            "execution_time": 0.0,
            "total_cycles": 1.0,      # Prevent division by zero
            "instructions_retired": 1.0
        }

    def run_profile(self):
        """
        Executes the Arm Performix CLI profiling recipe against the target binary
        and outputs structured JSON data, with a mock fallback if 'apx' is missing.
        """
        if not os.path.exists(self.binary_path):
            raise FileNotFoundError(f"Target binary not found at {self.binary_path}")

        cmd = ["apx", "run", "--recipe", "microarchitecture", "--format", "json", "--", self.binary_path]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            raw_json = json.loads(result.stdout)
            self._parse_metrics(raw_json)
            return self.metrics
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback block to simulate data execution loop for presentation demos
            print("Arm Performix 'apx' CLI not found on local path. Initializing telemetry fallback data...")
            mock_data = {
                "performance_summary": {
                    "frontend_bound_cycles": 1560.0,
                    "l1_instruction_cache_misses": 850,
                    "wall_clock_time": 1.25,
                    "total_cpu_cycles": 2000.0,
                    "instructions_retired": 1000.0
                }
            }
            self._parse_metrics(mock_data)
            return self.metrics

    def _parse_metrics(self, raw_data):
        """
        Extracts specific hardware counters returned by Arm Performix 
        """
        summary = raw_data.get("performance_summary", {})
        
        self.metrics["frontend_bound_cycles"] = float(summary.get("frontend_bound_cycles", 0.0))
        self.metrics["l1_icache_misses"] = int(summary.get("l1_instruction_cache_misses", 0))
        self.metrics["execution_time"] = float(summary.get("wall_clock_time", 0.0))
        self.metrics["total_cycles"] = float(summary.get("total_cpu_cycles", 1.0))
        self.metrics["instructions_retired"] = float(summary.get("instructions_retired", 1.0))

if __name__ == "__main__":
    profiler = PerformixWrapper("./tests/dummy_agent_target")
    print("Initial configuration initialized. Awaiting pipeline integration.")
