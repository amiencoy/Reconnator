# ==================================================================================== #
# This module orchestrates AI responses, MCP tool calls, and runtime policy checks.    #
# It keeps provider selection separate from authorized security-tool execution.       #
# ==================================================================================== #

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from typing import Any

from .contracts import AuthorizationContext, PolicyConfig, PolicyDecision
from .mcp import MCPAdapter
from .policy import PolicyEvaluator
from .prompts import build_system_prompt
from .providers import Provider


@dataclass(frozen=True)
class PlannedToolCall:
    id: str
    name: str
    arguments: dict[str, Any]
    decision: PolicyDecision


@dataclass
class TurnResult:
    content: str | None = None
    planned_calls: list[PlannedToolCall] = field(default_factory=list)
    tool_results: list[dict[str, str]] = field(default_factory=list)


class AgentCore:
    def __init__(self, *, provider: Provider, mcp: MCPAdapter, policy: PolicyConfig):
        self.provider = provider
        self.mcp = mcp
        self.policy = policy
        self.evaluator = PolicyEvaluator(policy)

    async def plan(
        self,
        user_input: str,
        authorization: AuthorizationContext | None = None,
        system_context: str = "",
    ) -> TurnResult:
        authorization = authorization or AuthorizationContext()
        discovered_tools = await self.mcp.list_tools()
        tools = [
            tool
            for tool in discovered_tools
            if tool.get("function", {}).get("name") in self.policy.allowed_tools
        ]
        response = await self.provider.complete(
            [
                {"role": "system", "content": build_system_prompt(self.policy) + "\n" + system_context},
                {"role": "user", "content": user_input},
            ],
            tools,
        )
        planned: list[PlannedToolCall] = []
        for index, item in enumerate(response.get("tool_calls") or []):
            function = item.get("function", {})
            name = function.get("name", "")
            raw_arguments = function.get("arguments", {})
            try:
                arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else dict(raw_arguments)
            except (json.JSONDecodeError, TypeError, ValueError):
                arguments = {}
            decision = self.evaluator.evaluate(name, arguments, authorization)
            planned.append(
                PlannedToolCall(
                    id=item.get("id", f"call-{index}"),
                    name=name,
                    arguments=arguments,
                    decision=decision,
                )
            )
        return TurnResult(content=response.get("content"), planned_calls=planned)

    async def execute(self, turn: TurnResult, *, parallel: bool = True) -> TurnResult:
        allowed = [call for call in turn.planned_calls if call.decision.allowed]
        denied = [call for call in turn.planned_calls if not call.decision.allowed]
        turn.tool_results.extend(
            {"tool": call.name, "status": "denied", "result": f"{call.decision.code}: {call.decision.reason}"}
            for call in denied
        )

        async def invoke(call: PlannedToolCall) -> dict[str, str]:
            result = await self.mcp.call_tool(call.name, call.arguments)
            return {"tool": call.name, "status": "completed", "result": result}

        if parallel and len(allowed) > 1:
            turn.tool_results.extend(await asyncio.gather(*(invoke(call) for call in allowed)))
        else:
            for call in allowed:
                turn.tool_results.append(await invoke(call))
        return turn

    async def aclose(self) -> None:
        await self.mcp.aclose()
