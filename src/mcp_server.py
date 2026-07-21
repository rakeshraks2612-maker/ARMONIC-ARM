import sys
import json
from performix_wrapper import PerformixWrapper

class ArmonicMcpServer:
    def __init__(self):
        # Tools schema configuration map
        self.tools = {
            "profile_workload": {
                "description": "Runs Arm Performix microarchitecture profiling against a binary target.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "binary_path": {"type": "string", "description": "The file system path to the target binary executable."}
                    },
                    "required": ["binary_path"]
                }
            }
        }

    def listen(self):
        """Monitors standard input for incoming JSON-RPC 2.0 requests from the LLM host."""
        for line in sys.stdin:
            try:
                request = json.loads(line)
                response = self._handle_request(request)
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except Exception as e:
                error_response = {"jsonrpc": "2.0", "error": {"code": -32603, "message": str(e)}, "id": None}
                sys.stdout.write(json.dumps(error_response) + "\n")
                sys.stdout.flush()

    def _handle_request(self, request):
        method = request.get("method")
        params = request.get("params", {})
        req_id = request.get("id")

        if method == "list_tools":
            return {"jsonrpc": "2.0", "result": self.tools, "id": req_id}
        
        elif method == "call_tool":
            name = params.get("name")
            arguments = params.get("arguments", {})
            
            if name == "profile_workload":
                path = arguments.get("binary_path")
                try:
                    # Instantiates the Performix wrapper built in phase 2
                    profiler = PerformixWrapper(path)
                    metrics = profiler.run_profile()
                    return {"jsonrpc": "2.0", "result": {"status": "success", "metrics": metrics}, "id": req_id}
                except Exception as e:
                    return {"jsonrpc": "2.0", "result": {"status": "error", "message": str(e)}, "id": req_id}
            
            return {"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Tool {name} not found."}, "id": req_id}

        return {"jsonrpc": "2.0", "error": {"code": -32601, "message": f"Method {method} not found."}, "id": req_id}

if __name__ == "__main__":
    server = ArmonicMcpServer()
    server.listen()
