# ==================================================================================== #
# This module adapts Model Context Protocol tools for the provider-agnostic agent.     #
# It discovers schemas and normalizes calls before handing them to the MCP session.   #
# ==================================================================================== #

from __future__ import annotations

import sys
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any, Protocol


class MCPAdapter(Protocol):
    async def list_tools(self) -> list[dict[str, Any]]: ...
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str: ...
    async def aclose(self) -> None: ...


class StdioMCPAdapter:
    """Optional stdio MCP transport; install Security Agent Core with the ``mcp`` extra."""

    def __init__(self, server_script: str | Path, *, command: str = sys.executable):
        self.server_script = str(Path(server_script).resolve())
        self.command = command
        self._stack = AsyncExitStack()
        self._session = None

    async def _initialize(self) -> None:
        if self._session is not None:
            return
        try:
            from mcp import ClientSession, StdioServerParameters
            from mcp.client.stdio import stdio_client
        except ImportError as exc:
            raise RuntimeError("the `mcp` package is required for Reconnator's agent runtime") from exc

        params = StdioServerParameters(command=self.command, args=[self.server_script])
        read, write = await self._stack.enter_async_context(stdio_client(params))
        self._session = await self._stack.enter_async_context(ClientSession(read, write))
        await self._session.initialize()

    async def list_tools(self) -> list[dict[str, Any]]:
        await self._initialize()
        response = await self._session.list_tools()
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in response.tools
        ]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        await self._initialize()
        result = await self._session.call_tool(name, arguments=arguments)
        return "\n".join(getattr(item, "text", str(item)) for item in result.content)

    async def aclose(self) -> None:
        await self._stack.aclose()
        self._session = None
