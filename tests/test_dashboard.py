import json
import os
import tempfile
import unittest

from tools.dashboard.export_powerbi import export_dataset


class DashboardTests(unittest.TestCase):
    def test_html_includes_retest_and_frameworks(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "finding.json"), "w", encoding="utf-8") as handle:
                json.dump(
                    [
                        {
                            "finding_id": "FND-1",
                            "risk_level": "HIGH",
                            "risk_score": 8.5,
                            "owasp_llm": ["LLM01"],
                            "mitre_atlas": ["AML.T0051"],
                            "nist_ai_rmf": ["MAP"],
                            "threats": ["T-001"],
                        }
                    ],
                    handle,
                )
            with open(os.path.join(tmp, "retest.json"), "w", encoding="utf-8") as handle:
                json.dump({"blocked": True, "exploitability": ["BLOCKED"]}, handle)
            with open(os.path.join(tmp, "framework-coverage.json"), "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "atlas": [{"id": "AML.T0051", "name": "LLM Prompt Injection", "status": "COVERED"}],
                        "nist": [{"id": "MAP", "covered_threats": ["T-001"], "status": "COVERED"}],
                    },
                    handle,
                )
            with open(os.path.join(tmp, "asset.json"), "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "asset_id": "a1",
                        "asset_type": "Agent",
                        "name": "HealthcareAIAssistant",
                        "discovered_tools": ["patient_search"],
                        "identities": ["system-admin-identity"],
                    },
                    handle,
                )
            for name, payload in (
                ("incident.json", []),
                ("attack.json", [{"exploitability": "CONFIRMED"}]),
                ("remediation.json", [{}]),
                ("owasp-coverage.json", [{"owasp_id": "LLM01", "name": "Prompt Injection", "status": "COVERED"}]),
            ):
                with open(os.path.join(tmp, name), "w", encoding="utf-8") as handle:
                    json.dump(payload, handle)

            export_dataset(tmp, meta={"correlation_id": "corr-test"})
            with open(os.path.join(tmp, "executive-dashboard.html"), encoding="utf-8") as handle:
                html = handle.read()
            self.assertIn("BLOCKED", html)
            self.assertIn("AML.T0051", html)
            self.assertIn("NIST AI RMF", html)
            self.assertIn("corr-test", html)
            self.assertIn("Risk mix", html)
            self.assertIn("Authorized validation", html)
            self.assertIn("Answers for leadership", html)
            self.assertIn("Is this a customer or production incident?", html)
            self.assertIn("Ship / no-ship decision?", html)
            self.assertIn("Which agents produced this dashboard", html)
            self.assertIn("Discovered assets", html)
            self.assertIn("HealthcareAIAssistant", html)
            self.assertIn("patient_search", html)
            self.assertIn("Multi-Agent Security Pipeline", html)
            self.assertIn("STAGE 01", html)
            self.assertIn("Asset Discovery", html)
            self.assertIn("Threat Assessment", html)
            self.assertIn("Red Team Validation", html)
            self.assertIn("Runtime SOC Monitor", html)
            self.assertIn("Retest & Controls", html)
            self.assertIn("A2A Message Stream", html)


if __name__ == "__main__":
    unittest.main()
