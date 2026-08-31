# ==================================================================================== #
# This module provides ordered AI-provider failover without changing agent behavior.  #
# Gemini can recover a turn when the preferred local or compatible provider is down.  #
# ==================================================================================== #

from __future__ import annotations

import logging
from typing import Any

from .base import Provider
from .openai_compatible import ProviderError

logger = logging.getLogger(__name__)


class FallbackProvider:
    """Try the primary provider first and fail over only on provider errors."""

    def __init__(self, primary: Provider, fallback: Provider):
        self.primary = primary
        self.fallback = fallback
        self.model = primary.model
        self.fallback_model = fallback.model

    async def complete(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        primary_failure: ProviderError | None = None
        try:
            return await self.primary.complete(messages, tools)
        except ProviderError as primary_error:
            primary_failure = primary_error
            logger.warning(
                "Primary AI provider failed for model=%s; trying Gemini fallback model=%s: %s",
                self.model,
                self.fallback_model,
                primary_error,
            )

        try:
            return await self.fallback.complete(messages, tools)
        except ProviderError as fallback_error:
            raise ProviderError(
                "primary and Gemini fallback providers failed; "
                f"primary: {primary_failure}; fallback: {fallback_error}"
            ) from fallback_error
