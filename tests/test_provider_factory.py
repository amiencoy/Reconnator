import unittest

from agent_core.providers import ProviderConfigurationError, create_provider, create_provider_from_env


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


if __name__ == "__main__":
    unittest.main()
