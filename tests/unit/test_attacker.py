import json
import os
import tempfile
import unittest

from jsonschema import Draft7Validator

from tools.security.apply_controls import apply_local_controls
from tools.security.attacker import execute_attack

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestAttacker(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "schemas", "attack.json"), encoding="utf-8") as f:
            self.attack_schema = json.load(f)
        with open(os.path.join(ROOT, "schemas", "evidence.json"), encoding="utf-8") as f:
            self.evidence_schema = json.load(f)

        self.attack_validator = Draft7Validator(self.attack_schema)
        self.evidence_validator = Draft7Validator(self.evidence_schema)

    def test_unauthorized_target_rejected(self):
        findings = [{"finding_id": "FND-1", "asset": "a1", "threats": ["T-001"]}]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(findings, f)
            findings_path = f.name

        try:
            with self.assertRaises(PermissionError):
                execute_attack(findings_path, "/tmp/rogue_agent.py")
        finally:
            os.unlink(findings_path)

    def test_multi_threat_validation_on_vulnerable_app(self):
        findings = [
            {"finding_id": "FND-T001", "asset": "demo", "threats": ["T-001"]},
            {"finding_id": "FND-T002", "asset": "demo", "threats": ["T-002"]},
            {"finding_id": "FND-T006", "asset": "demo", "threats": ["T-006"]},
            {"finding_id": "FND-T005", "asset": "demo", "threats": ["T-005"]},
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(findings, f)
            findings_path = f.name

        try:
            target = os.path.join(ROOT, "tests", "vulnerable-app", "app.py")
            attacks, evidence = execute_attack(findings_path, target)

            self.assertEqual(len(attacks), 4)
            self.assertEqual(len(evidence), 4)

            for atk in attacks:
                self.attack_validator.validate(atk)
                self.assertEqual(atk["exploitability"], "CONFIRMED")

            for ev in evidence:
                self.evidence_validator.validate(ev)
                self.assertEqual(ev["asset_id"], "demo")
        finally:
            os.unlink(findings_path)

    def test_multi_threat_validation_on_hardened_app(self):
        findings = [
            {"finding_id": "FND-T001", "asset": "demo", "threats": ["T-001"]},
            {"finding_id": "FND-T002", "asset": "demo", "threats": ["T-002"]},
            {"finding_id": "FND-T006", "asset": "demo", "threats": ["T-006"]},
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(findings, f)
            findings_path = f.name

        try:
            target = apply_local_controls()
            attacks, evidence = execute_attack(findings_path, target)

            self.assertEqual(len(attacks), 3)
            for atk in attacks:
                self.attack_validator.validate(atk)
                self.assertEqual(atk["exploitability"], "BLOCKED")
        finally:
            os.unlink(findings_path)


if __name__ == "__main__":
    unittest.main()
