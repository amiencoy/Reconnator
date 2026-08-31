# ==================================================================================== #
# This module orchestrates AI responses, MCP tool calls, and runtime policy checks.    #
# It keeps provider selection separate from authorized security-tool execution.       #
# ==================================================================================== #

from __future__ import annotations

import asyncio
import json
import re
from dataclasses import dataclass, field
from typing import Any

from .contracts import AuthorizationContext, PolicyConfig, PolicyDecision
from .mcp import MCPAdapter
from .policy import PolicyEvaluator
from .prompts import build_system_prompt
from .providers import Provider


EXPLICIT_TOOL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("execute_subdomain_recon", re.compile(r"\b(?:subfinder|subdomain(?:s|\s+recon)?)\b", re.I)),
    ("execute_nmap", re.compile(r"\bnmap\b", re.I)),
    ("execute_nuclei", re.compile(r"\bnuclei\b", re.I)),
    ("execute_ffuf", re.compile(r"\bffuf\b", re.I)),
    ("create_pdf_report", re.compile(r"\b(?:pdf|report)\b", re.I)),
)
NEGATION_CUE = re.compile(r"\b(?:without|except|exclude|excluding|skip|do\s+not|don't|no)\b", re.I)
POSITIVE_CUE = re.compile(r"\b(?:with|using|include|including|run|scan)\b", re.I)


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
        self._add_missing_explicit_calls(user_input, planned, authorization, tools)
        return TurnResult(content=response.get("content"), planned_calls=planned)

    def _add_missing_explicit_calls(
        self,
        user_input: str,
        planned: list[PlannedToolCall],
        authorization: AuthorizationContext,
        discovered_tools: list[dict[str, Any]],
    ) -> None:
        """Complete explicit multi-tool requests that a model only partially planned."""
        if not planned:
            return

        available = {item.get("function", {}).get("name", "") for item in discovered_tools}
        existing = {call.name for call in planned}
        shared_target = self._shared_target(planned, authorization)

        for name, pattern in EXPLICIT_TOOL_PATTERNS:
            match = pattern.search(user_input)
            if not match or name in existing or name not in available:
                continue
            if self._is_negated(user_input, match.start()):
                continue

            if name == "create_pdf_report":
                arguments: dict[str, Any] = {}
            elif name == "execute_subdomain_recon":
                arguments = {"domain": shared_target} if shared_target else {}
            else:
                arguments = {"target": shared_target} if shared_target else {}
            planned.append(
                PlannedToolCall(
                    id=f"explicit-{name}",
                    name=name,
                    arguments=arguments,
                    decision=self.evaluator.evaluate(name, arguments, authorization),
                )
            )
            existing.add(name)

    @staticmethod
    def _is_negated(user_input: str, tool_position: int) -> bool:
        prefix = user_input[max(0, tool_position - 96) : tool_position]
        last_negation = max((match.start() for match in NEGATION_CUE.finditer(prefix)), default=-1)
        last_positive = max((match.start() for match in POSITIVE_CUE.finditer(prefix)), default=-1)
        return last_negation > last_positive

    @staticmethod
    def _shared_target(
        planned: list[PlannedToolCall], authorization: AuthorizationContext
    ) -> str | None:
        for call in planned:
            for field in ("target", "domain", "url", "host", "ip"):
                value = call.arguments.get(field)
                if isinstance(value, str) and value.strip():
                    return value.strip()
        return authorization.scope[0] if authorization.scope else None

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
