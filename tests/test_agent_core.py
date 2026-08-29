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


if __name__ == "__main__":
    unittest.main()
