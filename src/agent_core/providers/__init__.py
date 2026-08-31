# ==================================================================================== #
# This package exports the provider interfaces used by Reconnator's AI agent core.    #
# The abstraction lets local and hosted models share the same execution pipeline.     #
# ==================================================================================== #

from .base import Provider
from .fallback import FallbackProvider
from .factory import PROVIDER_PRESETS, ProviderConfigurationError, create_provider, create_provider_from_env
from .openai_compatible import OpenAICompatibleProvider, ProviderError

__all__ = [
    "FallbackProvider",
    "OpenAICompatibleProvider",
    "PROVIDER_PRESETS",
    "Provider",
    "ProviderConfigurationError",
    "ProviderError",
    "create_provider",
    "create_provider_from_env",
]
