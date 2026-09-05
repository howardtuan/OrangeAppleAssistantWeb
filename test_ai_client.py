import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import ai_client


class FakeOpenAI:
    calls = []
    fail_ikuncode = False

    def __init__(self, **kwargs):
        self.base_url = kwargs.get("base_url", "")
        self.chat = SimpleNamespace(completions=self)

    def create(self, *, model, messages):
        self.calls.append((self.base_url, model, messages))
        if self.fail_ikuncode and "ikuncode" in self.base_url:
            raise RuntimeError("model unavailable")
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="潤飾結果"))]
        )


class ProviderModelTests(unittest.TestCase):
    def setUp(self):
        FakeOpenAI.calls = []
        FakeOpenAI.fail_ikuncode = False
        self.env = patch.dict(
            os.environ,
            {
                "AI_PROVIDER_ORDER": "ikuncode,openai",
                "IKUNCODE_API_KEY": "ik-key",
                "IKUNCODE_BASE_URL": "https://api.ikuncode.cc/v1",
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

        self.assertEqual(providers[0]["model"], "gemini-3.8-flash")
        self.assertEqual(providers[1]["model"], "gpt-5.4-mini")

    def test_openai_fallback_keeps_its_own_model(self):
        FakeOpenAI.fail_ikuncode = True

        result = ai_client.polish_contact_book("草稿")

        self.assertEqual(result["provider"], "openai")
        self.assertEqual(result["model"], "gpt-5.4-mini")
        self.assertEqual(
            [model for _, model, _ in FakeOpenAI.calls],
            ["gemini-3.8-flash", "gpt-5.4-mini"],
        )

    def test_provider_model_overrides_legacy_shared_model(self):
        with patch.dict(
            os.environ,
            {"AI_MODEL": "legacy-model", "IKUNCODE_MODEL": "gemini-3.8-flash"},
        ):
            providers = ai_client.configured_providers()

        self.assertEqual(providers[0]["model"], "gemini-3.8-flash")
        self.assertEqual(providers[1]["model"], "legacy-model")


if __name__ == "__main__":
    unittest.main()
