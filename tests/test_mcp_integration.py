import asyncio
import unittest
from pathlib import Path

from agent_core.mcp import StdioMCPAdapter


class MCPIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def test_stdio_server_exposes_only_expected_reconnator_tools(self):
        server = Path(__file__).resolve().parents[1] / "src" / "mcp_server.py"
        adapter = StdioMCPAdapter(server)
        try:
            tools = await asyncio.wait_for(adapter.list_tools(), timeout=30)
        finally:
            await adapter.aclose()

        names = {item["function"]["name"] for item in tools}
        self.assertEqual(
            names,
            {
                "create_pdf_report",
                "execute_ffuf",
                "execute_nmap",
                "execute_nuclei",
                "execute_subdomain_recon",
            },
        )


if __name__ == "__main__":
    unittest.main()

