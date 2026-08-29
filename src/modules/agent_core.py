# ==================================================================================== #
# This adapter connects legacy Reconnator imports to the provider-agnostic agent core. #
# It preserves existing consumers while removing the former Gemini-only dependency.  #
# ==================================================================================== #

"""Reconnator consumer for the provider-agnostic security agent core.

Product concerns stay in Reconnator. Provider selection, MCP transport, prompt
contracts, and runtime policy live in ``src/agent_core``.
"""

from __future__ import annotations

import logging
from pathlib import Path

from agent_core import (
    AgentCore,
    AuthorizationContext,
    PolicyConfig,
    StdioMCPAdapter,
    TurnResult,
    create_provider_from_env,
)

logger = logging.getLogger(__name__)

_runtime: AgentCore | None = None


def get_agent_runtime() -> AgentCore:
    """Build the shared runtime lazily, after ``.env`` has been loaded."""
    global _runtime
    if _runtime is None:
        src_root = Path(__file__).resolve().parents[1]
        policy = PolicyConfig.from_yaml(src_root / "config" / "agent-policy.yaml")
        provider = create_provider_from_env()
        mcp = StdioMCPAdapter(src_root / "mcp_server.py")
        _runtime = AgentCore(provider=provider, mcp=mcp, policy=policy)
        logger.info(
            "Security agent initialized with provider=%s model=%s",
            provider.__class__.__name__,
            provider.model,
        )
    return _runtime


async def chat_with_agent(
    user_input: str,
    authorization: AuthorizationContext | None = None,
    system_context: str = "",
) -> TurnResult:
    return await get_agent_runtime().plan(
        user_input,
        authorization=authorization,
        system_context=system_context,
    )


async def close_agent_runtime() -> None:
    global _runtime
    if _runtime is not None:
        await _runtime.aclose()
        _runtime = None
