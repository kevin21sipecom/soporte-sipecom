import unittest

from soporte_sipecom.models import parse_agy_models, parse_codex_models, parse_grok_models


class ParseModelsTest(unittest.TestCase):
    def test_grok(self):
        text = """You are logged in with grok.com.

Default model: grok-4.6

Available models:
  * grok-4.6 (default)
  - grok-4.5
"""
        models = parse_grok_models(text)
        self.assertEqual([m.id for m in models], ["grok-4.6", "grok-4.5"])
        self.assertTrue(models[0].default)

    def test_agy(self):
        text = "Fetching available models...\ngemini-3.8-flash-high\tGemini 3.8 Flash (High)\nclaude-sonnet-4-6\tClaude Sonnet 4.6\n"
        models = parse_agy_models(text)
        self.assertEqual(models[0].id, "gemini-3.8-flash-high")
        self.assertEqual(models[0].efforts, [])
        self.assertEqual(models[1].id, "claude-sonnet-4-6")
        self.assertEqual(models[1].efforts, ["low", "medium", "high"])

    def test_baked_effort(self):
        from soporte_sipecom.models import baked_effort

        self.assertEqual(baked_effort("gemini-3.8-flash-high"), "high")
        self.assertEqual(baked_effort("gpt-oss-120b-medium"), "medium")
        self.assertIsNone(baked_effort("claude-sonnet-4-6"))

    def test_codex_hides(self):
        text = '{"models":[{"slug":"gpt-6-astra","display_name":"Astra","visibility":"list","supported_reasoning_levels":[{"effort":"low"},{"effort":"high"}]},{"slug":"hidden","visibility":"hide"}]}'
        models = parse_codex_models(text)
        self.assertEqual([m.id for m in models], ["gpt-6-astra"])
        self.assertEqual(models[0].efforts, ["low", "high"])


if __name__ == "__main__":
    unittest.main()
