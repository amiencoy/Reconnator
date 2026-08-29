"""Runtime authorization enforcement. Prompt instructions are not a security boundary."""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse
from typing import Any, Iterable

from .contracts import AuthorizationContext, PolicyConfig, PolicyDecision


def _normalize_target(value: str) -> str:
    value = value.strip().lower().rstrip(".")
    parsed = urlparse(value if "://" in value else f"//{value}")
    host = parsed.hostname
    return (host or value).strip("[]")


def _iter_values(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            if isinstance(item, str):
                yield item


def _in_scope(target: str, scope_entry: str) -> bool:
    target_host = _normalize_target(target)
    try:
        target_ip = ipaddress.ip_address(target_host)
        try:
            return target_ip in ipaddress.ip_network(scope_entry.strip(), strict=False)
        except ValueError:
            return target_ip == ipaddress.ip_address(_normalize_target(scope_entry))
    except ValueError:
        entry = _normalize_target(scope_entry)
        return target_host == entry or target_host.endswith(f".{entry}")


class PolicyEvaluator:
    def __init__(self, config: PolicyConfig):
        self.config = config

    def evaluate(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        authorization: AuthorizationContext,
    ) -> PolicyDecision:
        if tool_name in self.config.forbidden_tools:
            return PolicyDecision(False, "TOOL_FORBIDDEN", f"{tool_name} is explicitly forbidden")

        rule = self.config.allowed_tools.get(tool_name)
        if rule is None and self.config.default_deny:
            return PolicyDecision(False, "TOOL_NOT_ALLOWED", f"{tool_name} is not allowlisted")
        if rule is None:
            return PolicyDecision(True, "ALLOWED", "default-allow policy")

        if rule.requires_approval and not authorization.approved:
            return PolicyDecision(False, "APPROVAL_REQUIRED", "human approval is required")

        targets = [
            value
            for field_name in rule.target_fields
            for value in _iter_values(arguments.get(field_name))
        ]
        if rule.target_fields and not targets:
            return PolicyDecision(False, "TARGET_REQUIRED", "a target argument is required")
        if targets and self.config.require_declared_scope and not authorization.scope:
            return PolicyDecision(False, "SCOPE_REQUIRED", "authorized target scope is missing")

        for target in targets:
            if not any(_in_scope(target, entry) for entry in authorization.scope):
                return PolicyDecision(False, "OUT_OF_SCOPE", f"target {target!r} is outside approved scope")

        return PolicyDecision(True, "ALLOWED", "tool and target passed runtime policy")
