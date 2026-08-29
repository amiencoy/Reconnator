"""Security Agent Core public API."""

__version__ = "2.1.0"

from .agent import AgentCore, TurnResult
from .contracts import AuthorizationContext, PolicyConfig, PolicyDecision
from .mcp import MCPAdapter, StdioMCPAdapter
from .providers import (
    OpenAICompatibleProvider,
    Provider,
    ProviderConfigurationError,
    create_provider,
    create_provider_from_env,
)

__all__ = [
    "__version__",
    "AuthorizationContext",
    "AgentCore",
    "MCPAdapter",
    "OpenAICompatibleProvider",
    "PolicyConfig",
    "PolicyDecision",
    "Provider",
    "ProviderConfigurationError",
    "StdioMCPAdapter",
    "TurnResult",
    "create_provider",
    "create_provider_from_env",
]
