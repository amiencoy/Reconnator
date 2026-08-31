# ==================================================================================== #
# These tests verify provider presets, environment parsing, and configuration errors. #
# They keep local, hosted, Gemini, and custom endpoint selection deterministic.        #
# ==================================================================================== #

import unittest

from agent_core.providers import (
    FallbackProvider,
    ProviderConfigurationError,
    create_provider,
    create_provider_from_env,
)


class ProviderFactoryTests(unittest.TestCase):
    def test_ollama_defaults_to_local_qwen(self):
        provider = create_provider("ollama")
        self.assertEqual(provider.base_url, "http://localhost:11434/v1/chat/completions")
        self.assertEqual(provider.model, "qwen3:8b")
        self.assertIsNone(provider.api_key)

    def test_custom_provider_requires_endpoint_and_model(self):
        with self.assertRaises(ProviderConfigurationError):
            create_provider("openai-compatible")

    def test_gemini_supports_legacy_key(self):
        provider = create_provider_from_env(
            {"AI_PROVIDER": "gemini", "GEMINI_API_KEY": "test-key"}
        )
        self.assertEqual(provider.api_key, "test-key")

    def test_environment_can_select_vllm_model(self):
        provider = create_provider_from_env(
            {"AI_PROVIDER": "vllm", "AI_MODEL": "Qwen/Qwen3-14B"}
        )
        self.assertEqual(provider.model, "Qwen/Qwen3-14B")

    def test_environment_configures_local_model_timeout(self):
        provider = create_provider_from_env({"AI_PROVIDER": "ollama", "AI_TIMEOUT_SECONDS": "600"})
        self.assertEqual(provider.timeout_seconds, 600)

    def test_gemini_key_wraps_primary_provider_as_fallback(self):
        provider = create_provider_from_env(
            {"AI_PROVIDER": "ollama", "GEMINI_API_KEY": "fallback-key"}
        )
        self.assertIsInstance(provider, FallbackProvider)
        self.assertEqual(provider.primary.model, "qwen3:8b")
        self.assertEqual(provider.fallback.model, "gemini-3.5-flash-lite")
        self.assertEqual(provider.fallback.api_key, "fallback-key")

    def test_incomplete_custom_provider_uses_configured_gemini(self):
        provider = create_provider_from_env(
            {"AI_PROVIDER": "openai-compatible", "GEMINI_API_KEY": "fallback-key"}
        )
        self.assertEqual(provider.model, "gemini-3.5-flash-lite")
        self.assertEqual(provider.api_key, "fallback-key")

    def test_explicit_gemini_provider_is_not_wrapped(self):
        provider = create_provider_from_env(
            {"AI_PROVIDER": "gemini", "GEMINI_API_KEY": "primary-key"}
        )
        self.assertNotIsInstance(provider, FallbackProvider)


if __name__ == "__main__":
    unittest.main()
