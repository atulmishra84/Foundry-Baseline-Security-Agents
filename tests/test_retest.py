import os
import tempfile
import unittest

from tools.security.apply_controls import apply_local_controls
from tools.security.attacker import execute_attack


class RetestTests(unittest.TestCase):
    def test_hardened_blocks_authorized_prompt(self):
        findings = [
            {
                "finding_id": "FND-test",
                "asset": "demo",
                "threats": ["T-001"],
            }
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
            import json

            json.dump(findings, handle)
            path = handle.name
        try:
            attacks, _ = execute_attack(path, apply_local_controls())
        finally:
            os.unlink(path)
        self.assertTrue(attacks)
        self.assertEqual(attacks[0]["exploitability"], "BLOCKED")


if __name__ == "__main__":
    unittest.main()
