# ==================================================================================== #
# These tests ensure Gemini failover runs only after a primary provider transport error. #
# They also preserve the original provider failures when both provider attempts fail. #
# ==================================================================================== #

import unittest

from agent_core.providers import FallbackProvider, ProviderError


class StubProvider:
    def __init__(self, model, response=None, error=None):
        self.model = model
        self.response = response
        self.error = error
        self.calls = 0

    async def complete(self, messages, tools):
        self.calls += 1
        if self.error:
            raise self.error
        return self.response


class FallbackProviderTests(unittest.IsolatedAsyncioTestCase):
    async def test_primary_success_does_not_call_fallback(self):
        primary = StubProvider("qwen3:8b", {"content": "local"})
        fallback = StubProvider("gemini-test", {"content": "cloud"})

        result = await FallbackProvider(primary, fallback).complete([], [])

        self.assertEqual(result["content"], "local")
        self.assertEqual(primary.calls, 1)
        self.assertEqual(fallback.calls, 0)

    async def test_provider_error_calls_fallback(self):
        primary = StubProvider("qwen3:8b", error=ProviderError("connection refused"))
        fallback = StubProvider("gemini-test", {"content": "cloud"})

        result = await FallbackProvider(primary, fallback).complete([], [])

        self.assertEqual(result["content"], "cloud")
        self.assertEqual(fallback.calls, 1)

    async def test_both_failures_are_reported(self):
        primary = StubProvider("qwen3:8b", error=ProviderError("connection refused"))
        fallback = StubProvider("gemini-test", error=ProviderError("HTTP 429"))

        with self.assertRaisesRegex(
            ProviderError, "primary: connection refused; fallback: HTTP 429"
        ):
            await FallbackProvider(primary, fallback).complete([], [])


if __name__ == "__main__":
    unittest.main()
