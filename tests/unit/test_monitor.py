import json
import os
import tempfile
import unittest

from jsonschema import Draft7Validator

from tools.runtime.monitor import analyze_evidence

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestMonitor(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "schemas", "incident.json"), encoding="utf-8") as f:
            self.schema = json.load(f)
        self.validator = Draft7Validator(self.schema)

    def test_detect_bulk_dump_incident(self):
        evidence = [
            {
                "evidence_id": "ev-1",
                "asset_id": "demo",
                "source": "Red_Team_Agent",
                "timestamp": "2026-09-21T10:00:00Z",
                "tool": "HealthcareAIAssistant.patient_search",
                "request": "{}",
                "response": json.dumps({"bulk_dump": True, "record_ids": ["P1001", "P1002"]}),
            }
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(evidence, f)
            path = f.name

        try:
            incidents = analyze_evidence(path)
            self.assertEqual(len(incidents), 1)
            self.validator.validate(incidents[0])
            self.assertIn("Exfiltration", incidents[0]["title"])
            self.assertEqual(incidents[0]["severity"], "CRITICAL")
        finally:
            os.unlink(path)

    def test_detect_excessive_agency_incident(self):
        evidence = [
            {
                "evidence_id": "ev-2",
                "asset_id": "demo",
                "source": "Red_Team_Agent",
                "timestamp": "2026-09-21T10:00:00Z",
                "tool": "HealthcareAIAssistant.managed_identity",
                "request": "identity_inspection",
                "response": json.dumps({"managed_identity": "system-admin-identity", "elevated": True}),
            }
        ]
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(evidence, f)
            path = f.name

        try:
            incidents = analyze_evidence(path)
            self.assertEqual(len(incidents), 1)
            self.validator.validate(incidents[0])
            self.assertIn("Excessive Agency", incidents[0]["title"])
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
