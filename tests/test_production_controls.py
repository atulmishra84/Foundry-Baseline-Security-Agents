import json
import os
import tempfile
import unittest

from tools.prod.controls import assert_authorized_target, redact_text, summarize_response


class ProductionControlsTests(unittest.TestCase):
    def test_allowlist_rejects_other_paths(self):
        with self.assertRaises(PermissionError):
            assert_authorized_target("/tmp/not-authorized.py")

    def test_allowlist_accepts_demo(self):
        assert_authorized_target(
            os.path.join(os.path.dirname(__file__), "..", "tests", "vulnerable-app", "app.py")
        )

    def test_allowlist_accepts_hardened(self):
        assert_authorized_target(
            os.path.join(os.path.dirname(__file__), "..", "tests", "vulnerable-app", "hardened_app.py")
        )

    def test_redact_and_summary(self):
        raw = '{"P1001": {"name": "Alice Smith", "condition": "Hypertension"}, "P1002": {}}'
        summary = summarize_response(raw)
        self.assertTrue(summary["bulk_dump"])
        self.assertEqual(summary["response"], "[REDACTED]")
        self.assertIn("[REDACTED_NAME]", redact_text("Alice Smith"))


if __name__ == "__main__":
    unittest.main()
