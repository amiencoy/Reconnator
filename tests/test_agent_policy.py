# ==================================================================================== #
# These tests verify target authorization, approval requirements, and policy limits.  #
# They ensure model output cannot bypass Reconnator's runtime security boundary.      #
# ==================================================================================== #

import unittest

from agent_core.contracts import AuthorizationContext, PolicyConfig
from agent_core.policy import PolicyEvaluator


def policy() -> PolicyEvaluator:
    return PolicyEvaluator(
        PolicyConfig.from_mapping(
            {
                "authorization": {"default_deny": True, "require_declared_scope": True},
                "allowed_tools": [
                    {"name": "execute_nmap", "target_fields": ["target"]},
                    {"name": "create_pdf_report", "requires_approval": False, "target_fields": []},
                ],
                "forbidden_tools": ["exploit_target"],
            }
        )
    )


class PolicyTests(unittest.TestCase):
    def test_active_scan_requires_approval(self):
        result = policy().evaluate("execute_nmap", {"target": "app.example.com"}, AuthorizationContext(scope=("example.com",)))
        self.assertEqual(result.code, "APPROVAL_REQUIRED")

    def test_subdomain_is_inside_domain_scope(self):
        auth = AuthorizationContext(approved=True, scope=("example.com",))
        self.assertTrue(policy().evaluate("execute_nmap", {"target": "api.example.com"}, auth).allowed)

    def test_external_domain_is_denied(self):
        auth = AuthorizationContext(approved=True, scope=("example.com",))
        self.assertEqual(policy().evaluate("execute_nmap", {"target": "example.net"}, auth).code, "OUT_OF_SCOPE")

    def test_active_tool_without_target_is_denied(self):
        auth = AuthorizationContext(approved=True, scope=("example.com",))
        self.assertEqual(policy().evaluate("execute_nmap", {}, auth).code, "TARGET_REQUIRED")

    def test_ip_inside_cidr_is_allowed(self):
        auth = AuthorizationContext(approved=True, scope=("192.0.2.0/24",))
        self.assertTrue(policy().evaluate("execute_nmap", {"target": "192.0.2.15"}, auth).allowed)

    def test_unknown_and_forbidden_tools_are_denied(self):
        auth = AuthorizationContext(approved=True, scope=("example.com",))
        self.assertEqual(policy().evaluate("unknown", {}, auth).code, "TOOL_NOT_ALLOWED")
        self.assertEqual(policy().evaluate("exploit_target", {}, auth).code, "TOOL_FORBIDDEN")

    def test_report_can_run_without_scope_or_approval(self):
        self.assertTrue(policy().evaluate("create_pdf_report", {}, AuthorizationContext()).allowed)


if __name__ == "__main__":
    unittest.main()
