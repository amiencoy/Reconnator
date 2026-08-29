# ==================================================================================== #
# This module selects and configures local or hosted AI provider implementations.     #
# Presets cover Ollama, vLLM, LM Studio, llama.cpp, Gemini, and custom endpoints.      #
# ==================================================================================== #

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

from .openai_compatible import OpenAICompatibleProvider


class ProviderConfigurationError(ValueError):
    pass


@dataclass(frozen=True)
class ProviderPreset:
    endpoint: str
    default_model: str
    requires_api_key: bool = False


PROVIDER_PRESETS: dict[str, ProviderPreset] = {
    "ollama": ProviderPreset("http://localhost:11434/v1/chat/completions", "qwen3:8b"),
    "vllm": ProviderPreset("http://localhost:8000/v1/chat/completions", "Qwen/Qwen3-8B"),
    "lmstudio": ProviderPreset("http://localhost:1234/v1/chat/completions", "local-model"),
    "llamacpp": ProviderPreset("http://localhost:8080/v1/chat/completions", "local-model"),
    "gemini": ProviderPreset(
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
        "gemini-3.5-flash-lite",
        True,
    ),
}


def create_provider(
    provider_name: str,
    *,
    base_url: str | None = None,
    model: str | None = None,
    api_key: str | None = None,
    temperature: float = 0.0,
    timeout_seconds: float = 300.0,
) -> OpenAICompatibleProvider:
    name = provider_name.strip().lower()
    preset = PROVIDER_PRESETS.get(name)
    if preset is None and name != "openai-compatible":
        supported = ", ".join([*sorted(PROVIDER_PRESETS), "openai-compatible"])
        raise ProviderConfigurationError(f"unknown provider {provider_name!r}; supported: {supported}")

    endpoint = base_url or (preset.endpoint if preset else None)
    selected_model = model or (preset.default_model if preset else None)
    if not endpoint:
        raise ProviderConfigurationError("AI_BASE_URL is required for openai-compatible providers")
    if not selected_model:
        raise ProviderConfigurationError("AI_MODEL is required for openai-compatible providers")
    if preset and preset.requires_api_key and not api_key:
        raise ProviderConfigurationError(f"an API key is required for provider {name}")

    return OpenAICompatibleProvider(
        base_url=endpoint,
        model=selected_model,
        api_key=api_key,
        temperature=temperature,
        timeout_seconds=timeout_seconds,
    )


def create_provider_from_env(env: Mapping[str, str] | None = None) -> OpenAICompatibleProvider:
    values = os.environ if env is None else env
    name = values.get("AI_PROVIDER", "ollama")
    api_key = values.get("AI_API_KEY")
    if name.lower() == "gemini" and not api_key:
        api_key = values.get("GEMINI_API_KEY")
    try:
        temperature = float(values.get("AI_TEMPERATURE", "0"))
    except ValueError as exc:
        raise ProviderConfigurationError("AI_TEMPERATURE must be numeric") from exc
    try:
        timeout_seconds = float(values.get("AI_TIMEOUT_SECONDS", "300"))
    except ValueError as exc:
        raise ProviderConfigurationError("AI_TIMEOUT_SECONDS must be numeric") from exc
    if timeout_seconds <= 0:
        raise ProviderConfigurationError("AI_TIMEOUT_SECONDS must be greater than zero")
    return create_provider(
        name,
        base_url=values.get("AI_BASE_URL"),
        model=values.get("AI_MODEL"),
        api_key=api_key,
        temperature=temperature,
        timeout_seconds=timeout_seconds,
    )
