# ==================================================================================== #
# These tests verify that only explicitly allowed Telegram chats can invoke scanning. #
# They protect the single ChatOps entrypoint from unauthorized multi-user execution.  #
# ==================================================================================== #

import os
import asyncio
import unittest
from types import SimpleNamespace

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghi")
os.environ["TELEGRAM_ALLOWED_CHAT_IDS"] = "123,456"

import bot as bot_module


class TelegramAuthorizationTests(unittest.TestCase):
    def test_only_configured_operator_chats_are_accepted(self):
        self.assertTrue(bot_module._is_operator(123))
        self.assertTrue(bot_module._is_operator(456))
        self.assertFalse(bot_module._is_operator(999))

    def test_authorization_parser_deduplicates_scope_and_extracts_ticket(self):
        scope, ticket = bot_module._parse_authorization_args(
            "/authorize example.com,192.0.2.0/24 example.com ticket=ENG-42"
        )
        self.assertEqual(scope, ("example.com", "192.0.2.0/24"))
        self.assertEqual(ticket, "ENG-42")


class TelegramParallelWorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def test_scanners_overlap_and_report_runs_after_all_scanners(self):
        mcp = _ConcurrentMCP()
        runtime = SimpleNamespace(mcp=mcp)
        calls = [
            SimpleNamespace(name="execute_nmap", arguments={"target": "example.com"}),
            SimpleNamespace(name="execute_nuclei", arguments={"target": "example.com"}),
            SimpleNamespace(name="execute_ffuf", arguments={"target": "example.com"}),
            SimpleNamespace(name="create_pdf_report", arguments={}),
        ]

        completed = await bot_module._execute_approved_workflow(runtime, calls)

        self.assertEqual(mcp.max_active_scanners, 3)
        self.assertEqual(mcp.started[-1], "create_pdf_report")
        self.assertEqual([call.name for call, _ in completed], [call.name for call in calls])


class _ConcurrentMCP:
    def __init__(self):
        self.active_scanners = 0
        self.max_active_scanners = 0
        self.finished_scanners = set()
        self.started = []

    async def call_tool(self, name, arguments):
        self.started.append(name)
        if name == "create_pdf_report":
            if len(self.finished_scanners) != 3:
                raise AssertionError("report started before every scanner completed")
            return "[SUCCESS] PDF Report successfully generated at: report.pdf"

        self.active_scanners += 1
        self.max_active_scanners = max(self.max_active_scanners, self.active_scanners)
        await asyncio.sleep(0.02)
        self.active_scanners -= 1
        self.finished_scanners.add(name)
        return f"[SUCCESS] {name} complete"


if __name__ == "__main__":
    unittest.main()
