# ==================================================================================== #
# This module defines the common protocol and response types for every AI provider.   #
# Provider implementations return normalized assistant messages and tool calls.       #
# ==================================================================================== #

from __future__ import annotations

from typing import Any, Protocol


class Provider(Protocol):
    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]: ...
