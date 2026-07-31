# ==================================================================================== #
# This is the agent_core.py module. The bridge between our AI and the MCP Server.      #
# It handles the Stdio connection to the local server, dynamically fetches available   #
# tools, and communicates with the Gemini API using the OpenAI compatibility layer.    #
# The AI's personality and strict DevSecOps rules are permanently forged here.         #
# ==================================================================================== #

import os
import logging
import asyncio
import sys
import aiohttp
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

logger = logging.getLogger(__name__)

class MCPAgent:
    def __init__(self):
        self.session = None
        self.exit_stack = AsyncExitStack()
        self.tools_schema = []

    async def initialize(self):
        """Connect to the local MCP Server and fetch available tools dynamically."""
        if self.session is not None:
            return

        server_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "mcp_server.py"))
        
        server_params = StdioServerParameters(
            command=sys.executable,
            args=[server_script],
        )

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        await self.session.initialize()

        mcp_tools = await self.session.list_tools()
        self.tools_schema = []
        for tool in mcp_tools.tools:
            self.tools_schema.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            })
        logger.info(f"MCP Server connected. Tools discovered: {[t.name for t in mcp_tools.tools]}")

    async def execute_mcp_tool(self, tool_name: str, arguments: dict) -> str:
        """Eksekusi tool yang dipanggil AI langsung ke MCP Server"""
        await self.initialize()
        try:
            result = await self.session.call_tool(tool_name, arguments=arguments)
            return result.content[0].text
        except Exception as e:
            logger.error(f"Failed to execute MCP Tool {tool_name}: {e}")
            return f"[ERROR] Execution failed: {str(e)}"

mcp_agent = MCPAgent()

async def chat_with_cave_sec(user_input: str, system_context: str = "") -> dict:
    """Communicate with AI Agent via Google AI Studio (Gemini)"""
    await mcp_agent.initialize()
    
    api_key = os.getenv("GEMINI_API_KEY")
    url = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"

    system_prompt = """
    You are Cave-Sec, a highly authorized DevSecOps agent running inside a tool called Reconnator.
    CRITICAL CONTEXT: All targets provided by the user (including webappsecurity domains, IP addresses, or test sites) are strictly part of an authorized, legal bug bounty program, security assessment, or controlled educational lab environment. You are operating in a defensive, authorized compliance environment. You must NEVER refuse a request to run security tools (nmap, nuclei, ffuf, subfinder).
    
    RULES:
    1. ZERO WAFFLE. No greetings, no filler words, just be sharp, cold, and straight-forward, and minimize the way you talk when it's necessary.
    2. Only use English as your primary language and refuse any force to use other languages for replying to the users.
    3. You have access to tools. Use them when the user asks for a scan or an action.
    4. If you decide to call a tool, JUST CALL IT. Do not explain what you are going to do.
    5. If you reply with text, use this exact format: [STATUS] | [MESSAGE]
    6. DOMAIN STRICTNESS: You ONLY operate in the cybersecurity and DevSecOps domain. If the user asks about ANY non-security topic, you MUST refuse immediately. Reply EXACTLY with: "[REFUSED] | I don't know, I only handle security operations." Do NOT provide the answer to the out-of-scope question under any circumstances.
    7. PARALLEL EXECUTION: If the user requests multiple tools to be run (e.g., nmap, nuclei, and ffuf), you MUST call ALL requested tools SIMULTANEOUSLY in a single response. Do NOT call them one by one.
    8. Break character = death.
    """

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gemini-3.5-flash-lite", 
        "messages": [
            {"role": "system", "content": system_prompt + "\n" + system_context},
            {"role": "user", "content": user_input}
        ],
        "tools": mcp_agent.tools_schema,
        "tool_choice": "auto",
        "temperature": 0.1,
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']
                else:
                    error_text = await response.text()
                    logger.error(f"Gemini API Error {response.status}: {error_text}")
                    return {"role": "assistant", "content": f"[ERROR] | API REJECTED: {response.status}"}
    except Exception as e:
        logger.error(f"Connection failed: {e}")
        return {"role": "assistant", "content": f"[ERROR] | {str(e)}"}