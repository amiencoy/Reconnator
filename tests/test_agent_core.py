# ==================================================================================== #
# These tests verify agent orchestration, normalized tool calls, and response handling. #
# They protect the provider-agnostic execution loop from behavioral regressions.      #
# ==================================================================================== #

import unittest

from agent_core.agent import AgentCore
from agent_core.contracts import AuthorizationContext, PolicyConfig


class FakeProvider:
    def __init__(self):
        self.tools = []

    async def complete(self, messages, tools):
        self.tools = tools
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {"id": "1", "function": {"name": "execute_nmap", "arguments": '{"target":"api.example.com"}'}},
                {"id": "2", "function": {"name": "execute_nmap", "arguments": '{"target":"outside.test"}'}},
            ],
        }


class PartialWorkflowProvider:
    async def complete(self, messages, tools):
        return {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "1",
                    "function": {
                        "name": "execute_nmap",
                        "arguments": '{"target":"api.example.com"}',
                    },
                }
            ],
        }


class FakeMCP:
    def __init__(self):
        self.calls = []

    async def list_tools(self):
        return [
            {"type": "function", "function": {"name": "execute_nmap", "parameters": {}}},
            {"type": "function", "function": {"name": "unapproved_tool", "parameters": {}}},
        ]

    async def call_tool(self, name, arguments):
        self.calls.append((name, arguments))
        return "[SUCCESS] scan complete"

    async def aclose(self):
        return None


class AgentTests(unittest.IsolatedAsyncioTestCase):
    async def test_agent_executes_only_policy_allowed_calls(self):
        policy = PolicyConfig.from_mapping(
            {"authorization": {"default_deny": True}, "allowed_tools": [{"name": "execute_nmap"}]}
        )
        mcp = FakeMCP()
        provider = FakeProvider()
        agent = AgentCore(provider=provider, mcp=mcp, policy=policy)
        turn = await agent.plan(
            "scan",
            AuthorizationContext(approved=True, approved_by="tester", scope=("example.com",)),
        )
        result = await agent.execute(turn)
        self.assertEqual(len(mcp.calls), 1)
        self.assertEqual(result.tool_results[0]["status"], "denied")
        self.assertEqual(result.tool_results[1]["status"], "completed")
        self.assertEqual([item["function"]["name"] for item in provider.tools], ["execute_nmap"])

    async def test_explicit_multi_tool_request_completes_partial_model_plan(self):
        policy = PolicyConfig.from_mapping(
            {
                "authorization": {"default_deny": True},
                "allowed_tools": [
                    {"name": "execute_nmap"},
                    {"name": "execute_nuclei"},
                    {"name": "execute_ffuf"},
                    {
                        "name": "create_pdf_report",
                        "requires_approval": False,
                        "target_fields": [],
                    },
                ],
            }
        )
        mcp = FakeMCP()
        mcp.list_tools = lambda: _workflow_tools()
        provider = PartialWorkflowProvider()
        agent = AgentCore(provider=provider, mcp=mcp, policy=policy)

        turn = await agent.plan(
            "scan api.example.com with nmap, nuclei and ffuf, then generate a PDF report",
            AuthorizationContext(approved=True, approved_by="tester", scope=("example.com",)),
        )

        self.assertEqual(
            [call.name for call in turn.planned_calls],
            ["execute_nmap", "execute_nuclei", "execute_ffuf", "create_pdf_report"],
        )
        for call in turn.planned_calls:
            self.assertTrue(call.decision.allowed)
        self.assertEqual(turn.planned_calls[1].arguments, {"target": "api.example.com"})
        self.assertEqual(turn.planned_calls[2].arguments, {"target": "api.example.com"})

    async def test_explicit_completion_respects_excluded_tools(self):
        policy = PolicyConfig.from_mapping(
            {
                "allowed_tools": [
                    {"name": "execute_nmap"},
                    {"name": "execute_nuclei"},
                    {"name": "execute_ffuf"},
                ]
            }
        )
        mcp = FakeMCP()
        mcp.list_tools = lambda: _workflow_tools()
        agent = AgentCore(provider=PartialWorkflowProvider(), mcp=mcp, policy=policy)

        turn = await agent.plan(
            "scan api.example.com with nmap but without nuclei and ffuf",
            AuthorizationContext(approved=True, approved_by="tester", scope=("example.com",)),
        )

        self.assertEqual([call.name for call in turn.planned_calls], ["execute_nmap"])


async def _workflow_tools():
    return [
        {"type": "function", "function": {"name": name, "parameters": {}}}
        for name in (
            "execute_nmap",
            "execute_nuclei",
            "execute_ffuf",
            "create_pdf_report",
        )
    ]


if __name__ == "__main__":
    unittest.main()
