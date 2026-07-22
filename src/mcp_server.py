import asyncio
import json
import sys
from mcp.server.models import InitializationOptions
from mcp.server import Notification, Server
import mcp.types as types
from mcp.server.stdio import stdio_server
from performix_wrapper import PerformixWrapper

# Initialize the MCP Server context
server = Server("armonic-performance-server")

@server.list_tools()
async def handle_list_tools() -> list[types.Tool]:
    """
    Exposes our Arm Performix wrapper tool to any connected AI Agent.
    """
    return [
        types.Tool(
            name="profile_arm_binary",
            description="Executes a compiled binary through the Arm Performix engine to extract hardware counters and microarchitectural bottlenecks.",
            input_schema={
                "type": "object",
                "properties": {
                    "binary_path": {
                        "type": "string",
                        "description": "The absolute or relative path to the compiled target executable binary."
                    }
                },
                "required": ["binary_path"],
            },
        )
    ]

@server.call_tool()
async def handle_call_tool(
    name: str, arguments: dict | None
) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handles execution requests from the AI agent loop.
    """
    if name != "profile_arm_binary":
        raise ValueError(f"Unknown tool requested: {name}")

    if not arguments or "binary_path" not in arguments:
        return [types.TextContent(type="text", text="Error: Missing 'binary_path' argument.")]

    binary_path = arguments["binary_path"]

    try:
        # Initialize our telemetry wrapper
        profiler = PerformixWrapper(binary_path)
        metrics = profiler.run_profile()
        
        # Build the structural optimization analysis block for GenAI consumption
        analysis = []
        if metrics["l1_icache_misses"] > 500:
            analysis.append("- HIGH L1 I-CACHE MISS DETECTION: Recommend instruction alignment or loop unrolling optimization techniques.")
        if metrics["frontend_bound_cycles"] > 20.0:
            analysis.append("- FRONTEND CYCLE BOTTLE-NECK: Evaluate branch predictor behavior or simplify conditional execution flow.")
            
        payload = {
            "status": "success",
            "telemetry": metrics,
            "agent_guidance": analysis if analysis else ["- Telemetry within stable operational thresholds."]
        }

        return [
            types.TextContent(
                type="text",
                text=json.dumps(payload, indent=2)
            )
        ]

    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=json.dumps({"status": "error", "message": str(e)}, indent=2)
            )
        ]

async def main():
    # Standard input/output communication channel setup for the server loop
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="armonic-performance-server",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=Notification(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())
