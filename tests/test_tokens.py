import unittest

from pathlib import Path

from soporte_sipecom.engine import build_prompt, looks_like_error
from soporte_sipecom.tokens import estimate_tokens, format_int, thread_usage


class TokensTests(unittest.TestCase):
    def test_estimate(self):
        self.assertEqual(estimate_tokens(""), 0)
        self.assertGreaterEqual(estimate_tokens("abcd"), 1)

    def test_thread_usage(self):
        msgs = [
            {"role": "user", "content": "hola"},
            {"role": "assistant", "content": "ok", "tokens_in": 100, "tokens_out": 20},
        ]
        tin, tout, total = thread_usage(msgs)
        self.assertEqual(tout, 20)
        self.assertEqual(tin, 100 + estimate_tokens("hola"))
        self.assertEqual(total, tin + tout)

    def test_format_int(self):
        self.assertEqual(format_int(12400), "12.400")

    def test_incidente_in_prompt(self):
        text = build_prompt({"nombre": "X", "origen": "", "pack": ""}, "por qué falla", [], "NullReferenceException")
        self.assertIn("Error pegado", text)
        self.assertIn("NullReferenceException", text)

    def test_error_in_chat(self):
        self.assertTrue(looks_like_error("Unhandled Exception at line 12"))
        self.assertFalse(looks_like_error("Hola"))
        text = build_prompt({"nombre": "X", "origen": "", "pack": ""}, "Unhandled Exception: boom", [])
        self.assertIn("captura", text.lower())
        hola = build_prompt({"nombre": "X", "origen": "", "pack": ""}, "Hola", [])
        self.assertNotIn("captura de pantalla", hola)

    def test_image_is_error_evidence(self):
        text = build_prompt({"nombre": "X", "origen": "", "pack": ""}, "qué es esto", [Path("error.png")])
        self.assertIn("captura", text.lower())


if __name__ == "__main__":
    unittest.main()
