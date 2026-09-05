import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import ai_client


class InternalServerError(RuntimeError):
    pass


class FakeOpenAI:
    calls = []
    failures = {}

    def __init__(self, **kwargs):
        self.api_key = kwargs["api_key"]
        self.base_url = kwargs.get("base_url", "")
        self.chat = SimpleNamespace(completions=self)

    def create(self, *, model, messages):
        self.calls.append((self.api_key, self.base_url, model, messages))
        failure = self.failures.get((self.base_url, model))
        if failure:
            raise failure
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="潤飾結果"))]
        )


class ProviderModelTests(unittest.TestCase):
    def setUp(self):
        FakeOpenAI.calls = []
        FakeOpenAI.failures = {}
        self.env = patch.dict(
            os.environ,
            {
                "AI_PROVIDER_ORDER": "ikuncode,openai",
                "IKUNCODE_API_KEY": "ik-key",
                "IKUNCODE_BASE_URL": "https://api.ikuncode.cc/v1",
                "IKUNCODE_FALLBACK_API_KEY": "ik-fallback-key",
                "IKUNCODE_FALLBACK_BASE_URL": "https://backup.ikuncode.cc/v1",
                "IKUNCODE_FALLBACK_MODEL": "gemini-3.8-flash",
                "OPENAI_API_KEY": "oa-key",
                "OPENAI_BASE_URL": "https://api.openai.com/v1",
            },
            clear=True,
        )
        self.client = patch.object(ai_client, "OpenAI", FakeOpenAI)
        self.env.start()
        self.client.start()

    def tearDown(self):
        self.client.stop()
        self.env.stop()

    def test_uses_provider_specific_default_models(self):
        providers = ai_client.configured_providers()

        self.assertEqual(providers[0]["model"], "gpt-5.4-mini")
        self.assertEqual(providers[1]["model"], "gemini-3.8-flash")
        self.assertEqual(providers[2]["model"], "gpt-5.4-mini")

    def test_ikuncode_falls_back_to_gemini(self):
        FakeOpenAI.failures = {
            ("https://api.ikuncode.cc/v1", "gpt-5.4-mini"): InternalServerError(
                "Error code: 503 - model_not_found: No available channel"
            )
        }

        result = ai_client.polish_contact_book("草稿")

        self.assertEqual(result["provider"], "ikuncode_fallback")
        self.assertEqual(result["model"], "gemini-3.8-flash")
        self.assertEqual(
            [model for _, _, model, _ in FakeOpenAI.calls],
            ["gpt-5.4-mini", "gemini-3.8-flash"],
        )
        self.assertEqual(
            [api_key for api_key, _, _, _ in FakeOpenAI.calls],
            ["ik-key", "ik-fallback-key"],
        )

    def test_openai_runs_after_both_ikuncode_models_fail(self):
        FakeOpenAI.failures = {
            ("https://api.ikuncode.cc/v1", "gpt-5.4-mini"): RuntimeError(
                "model unavailable"
            ),
            ("https://backup.ikuncode.cc/v1", "gemini-3.8-flash"): RuntimeError(
                "model unavailable"
            ),
        }

        result = ai_client.polish_contact_book("草稿")

        self.assertEqual(result["provider"], "openai")
        self.assertEqual(result["model"], "gpt-5.4-mini")
        self.assertEqual(
            [model for _, _, model, _ in FakeOpenAI.calls],
            ["gpt-5.4-mini", "gemini-3.8-flash", "gpt-5.4-mini"],
        )

    def test_raises_only_after_every_model_and_provider_fail(self):
        FakeOpenAI.failures = {
            ("https://api.ikuncode.cc/v1", "gpt-5.4-mini"): RuntimeError(
                "model unavailable"
            ),
            ("https://backup.ikuncode.cc/v1", "gemini-3.8-flash"): RuntimeError(
                "model unavailable"
            ),
            ("https://api.openai.com/v1", "gpt-5.4-mini"): RuntimeError(
                "connection error"
            ),
        }

        with self.assertRaisesRegex(RuntimeError, "已嘗試所有可用供應商"):
            ai_client.polish_contact_book("草稿")

        self.assertEqual(
            [model for _, _, model, _ in FakeOpenAI.calls],
            ["gpt-5.4-mini", "gemini-3.8-flash", "gpt-5.4-mini"],
        )

    def test_provider_model_overrides_legacy_shared_model(self):
        with patch.dict(
            os.environ,
            {
                "AI_MODEL": "legacy-model",
                "IKUNCODE_MODEL": "gemini-3.8-flash",
                "IKUNCODE_FALLBACK_MODEL": "",
            },
        ):
            providers = ai_client.configured_providers()

        self.assertEqual(providers[0]["model"], "gemini-3.8-flash")
        self.assertEqual(providers[1]["model"], "gemini-3.8-flash")
        self.assertEqual(providers[2]["model"], "legacy-model")


if __name__ == "__main__":
    unittest.main()
