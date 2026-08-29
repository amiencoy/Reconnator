# ==================================================================================== #
# This module defines configuration and authorization contracts for the agent core.   #
# Typed contracts make provider, target, and approval boundaries explicit to callers. #
# ==================================================================================== #

"""Configuration and authorization contracts for Security Agent Core."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AuthorizationContext:
    """Runtime evidence that a caller is allowed to request active operations."""

    approved: bool = False
    approved_by: str | None = None
    ticket: str | None = None
    scope: tuple[str, ...] = ()


@dataclass(frozen=True)
class PolicyDecision:
    allowed: bool
    code: str
    reason: str


@dataclass(frozen=True)
class ToolRule:
    name: str
    requires_approval: bool = True
    target_fields: tuple[str, ...] = ("target", "domain", "url", "host", "ip")


@dataclass(frozen=True)
class PolicyConfig:
    agent_name: str = "agent_core"
    domain: str = "authorized cybersecurity operations"
    allowed_tools: dict[str, ToolRule] = field(default_factory=dict)
    forbidden_tools: frozenset[str] = frozenset()
    require_declared_scope: bool = True
    default_deny: bool = True
    response_style: str = "concise"

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> "PolicyConfig":
        agent = raw.get("agent", {})
        auth = raw.get("authorization", {})
        output = raw.get("output", {})
        rules: dict[str, ToolRule] = {}
        for item in raw.get("allowed_tools", []):
            if isinstance(item, str):
                rules[item] = ToolRule(name=item)
                continue
            name = item["name"]
            rules[name] = ToolRule(
                name=name,
                requires_approval=bool(item.get("requires_approval", True)),
                target_fields=tuple(item.get("target_fields", ("target", "domain", "url", "host", "ip"))),
            )
        return cls(
            agent_name=agent.get("name", "agent_core"),
            domain=agent.get("domain", "authorized cybersecurity operations"),
            allowed_tools=rules,
            forbidden_tools=frozenset(raw.get("forbidden_tools", [])),
            require_declared_scope=bool(auth.get("require_declared_scope", True)),
            default_deny=bool(auth.get("default_deny", True)),
            response_style=output.get("style", "concise"),
        )

    @classmethod
    def from_yaml(cls, path: str | Path) -> "PolicyConfig":
        try:
            import yaml
        except ImportError as exc:
            raise RuntimeError("PyYAML is required to load the agent policy") from exc
        with Path(path).open("r", encoding="utf-8") as handle:
            return cls.from_mapping(yaml.safe_load(handle) or {})
