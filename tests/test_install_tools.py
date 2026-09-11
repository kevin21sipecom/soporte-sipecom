import unittest

from soporte_sipecom.detect import Probe
from soporte_sipecom.install_tools import parse_answer
from soporte_sipecom.onboard import _missing_auto


class ParseAnswerTests(unittest.TestCase):
    def test_yes(self):
        for raw in ("s", "S", "si", "sí", "y", "yes"):
            self.assertIs(parse_answer(raw), True)

    def test_no(self):
        for raw in ("n", "no", "N"):
            self.assertIs(parse_answer(raw), False)

    def test_other(self):
        self.assertIsNone(parse_answer(""))
        self.assertIsNone(parse_answer("maybe"))


class MissingAutoTests(unittest.TestCase):
    def test_skips_npm_tools_without_npm(self):
        rows = [
            Probe("npm", "runtime", False, False),
            Probe("codegraph", "codegraph", False, False),
            Probe("repomix", "repomix", False, False),
            Probe("archify", "archify", False, False),
        ]
        self.assertEqual(_missing_auto(rows), ["archify"])

    def test_with_npm(self):
        rows = [
            Probe("npm", "runtime", True, True),
            Probe("codegraph", "codegraph", False, False),
            Probe("archify", "archify", False, False),
        ]
        self.assertEqual(_missing_auto(rows), ["codegraph", "archify"])


if __name__ == "__main__":
    unittest.main()
