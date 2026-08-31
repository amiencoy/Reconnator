# ==================================================================================== #
# These tests exercise local OpenAI-compatible provider requests and tool responses.  #
# They validate self-hosted model support without requiring a live cloud dependency.  #
# ==================================================================================== #

import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from agent_core.providers import OpenAICompatibleProvider, ProviderError


class _Handler(BaseHTTPRequestHandler):
    request_json = None
    authorization = None
    response_body = None

    def do_POST(self):
        length = int(self.headers["Content-Length"])
        type(self).request_json = json.loads(self.rfile.read(length))
        type(self).authorization = self.headers.get("Authorization")
        body = type(self).response_body or json.dumps(
            {"choices": [{"message": {"role": "assistant", "content": "[READY] | local"}}]}
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        return


class LocalProviderTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        _Handler.response_body = None
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    async def asyncTearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)

    async def test_local_endpoint_needs_no_api_key_and_receives_tools(self):
        provider = OpenAICompatibleProvider(
            base_url=f"http://127.0.0.1:{self.server.server_port}/v1/chat/completions",
            model="local-qwen",
        )
        result = await provider.complete(
            [{"role": "user", "content": "hello"}],
            [{"type": "function", "function": {"name": "test_tool", "parameters": {}}}],
        )
        self.assertEqual(result["content"], "[READY] | local")
        self.assertIsNone(_Handler.authorization)
        self.assertEqual(_Handler.request_json["model"], "local-qwen")
        self.assertEqual(_Handler.request_json["tools"][0]["function"]["name"], "test_tool")

    async def test_invalid_json_is_reported_as_provider_error(self):
        _Handler.response_body = b"not-json"
        provider = OpenAICompatibleProvider(
            base_url=f"http://127.0.0.1:{self.server.server_port}/v1/chat/completions",
            model="local-qwen",
        )

        with self.assertRaisesRegex(ProviderError, "invalid JSON"):
            await provider.complete([], [])


if __name__ == "__main__":
    unittest.main()
