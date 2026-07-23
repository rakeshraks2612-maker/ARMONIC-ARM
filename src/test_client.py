import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run_test():
    # Define how the AI agent boots up your server
    server_params = StdioServerParameters(
        command="python3",
        args=["src/mcp_server.py"]
    )

    print("⚡ Booting up MCP Client and connecting to Armonic server...")
    
    # Establish the standard input/output connection
    async with stdio_client(server_params) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the handshake
            await session.initialize()
            print("✅ Connected! Fetching available AI tools...")
            
            # Discover tools
            tools = await session.list_tools()
            print(f"🛠️  Found tools: {[t.name for t in tools.tools]}")
            
            print("\n🚀 Firing execution request to 'profile_arm_binary'...")
            
            # Call the tool with a dummy program path
            result = await session.call_tool(
                "profile_arm_binary", 
                arguments={"binary_path": "./dummy_compiled_math_program"}
            )
            
            print("\n--- 📊 SERVER PAYLOAD RESPONSE ---")
            print(result.content[0].text)

if __name__ == "__main__":
    asyncio.run(run_test())
