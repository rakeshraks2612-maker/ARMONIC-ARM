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
        and outputs structured JSON data.
        """
        if not os.path.exists(self.binary_path):
            raise FileNotFoundError(f"Target binary not found at {self.binary_path}")

        # The 'apx run' command executing microarchitecture recipes targeting JSON/CDF logs
        cmd = ["apx", "run", "--recipe", "microarchitecture", "--format", "json", "--", self.binary_path]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            raw_json = json.loads(result.stdout)
            self._parse_metrics(raw_json)
            return self.metrics
        except subprocess.CalledProcessError as e:
            print(f"Execution Error during profiling via apx: {e.stderr}")
            return None
        except json.JSONDecodeError:
            print("Failed to parse Arm Performix structured telemetry output.")
            return None

    def _parse_metrics(self, raw_data):
        """
        Extracts specific hardware counters returned by Arm Performix 
        """
        # Traverses the Arm Performix Common Data Format (CDF) log tree
        summary = raw_data.get("performance_summary", {})
        
        self.metrics["frontend_bound_cycles"] = float(summary.get("frontend_bound_cycles", 0.0))
        self.metrics["l1_icache_misses"] = int(summary.get("l1_instruction_cache_misses", 0))
        self.metrics["execution_time"] = float(summary.get("wall_clock_time", 0.0))
        self.metrics["total_cycles"] = float(summary.get("total_cpu_cycles", 1.0))
        self.metrics["instructions_retired"] = float(summary.get("instructions_retired", 1.0))

# Quick local test loop block
if __name__ == "__main__":
    # Placeholder profile target path
    profiler = PerformixWrapper("./tests/dummy_agent_target")
    print("Initial configuration initialized. Awaiting pipeline integration.")
