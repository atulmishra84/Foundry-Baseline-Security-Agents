import json
import os
import unittest

from fastapi.testclient import TestClient

from services.foundry_runtime.main import app

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestRuntimeAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        token = os.getenv("FOUNDRY_RUNTIME_TOKEN", "")
        self.headers = {"Authorization": f"Bearer {token}"} if token else {}

    def test_health_endpoint_no_auth_needed(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["ecosystem"], "azure-ai-foundry")

    def test_unauthorized_when_token_required_and_missing(self):
        token = os.getenv("FOUNDRY_RUNTIME_TOKEN", "")
        if token:
            response = self.client.get("/v1/stages")
            self.assertEqual(response.status_code, 401)

    def test_stages_endpoint_with_auth(self):
        response = self.client.get("/v1/stages", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("stages", data)
        self.assertEqual(len(data["stages"]), 5)

        stage_names = [s["name"] for s in data["stages"]]
        self.assertIn("Asset Discovery", stage_names)
        self.assertIn("Threat Assessment", stage_names)
        self.assertIn("Red Team Validation", stage_names)
        self.assertIn("Runtime SOC Monitoring", stage_names)
        self.assertIn("Remediation & Retest", stage_names)

    def test_containment_approval_endpoint(self):
        test_incident = "INC-test-123"
        payload = {
            "incident_id": test_incident,
            "approved_by": "test-admin",
            "action": "disable_service_principal",
        }
        response = self.client.post("/v1/containment/approve", json=payload, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "APPROVED")
        self.assertEqual(data["incident_id"], test_incident)

        approval_file = os.path.join(ROOT, "output", "approvals", f"{test_incident}.json")
        self.assertTrue(os.path.exists(approval_file))

        with open(approval_file, encoding="utf-8") as f:
            saved = json.load(f)
        self.assertEqual(saved["approved_by"], "test-admin")

        if os.path.exists(approval_file):
            os.remove(approval_file)

    def test_dashboard_endpoint(self):
        response = self.client.get("/dashboard", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers.get("content-type", ""))
        html = response.text
        self.assertIn("Multi-Agent Security Pipeline", html)
        self.assertIn("Asset Discovery", html)
        self.assertIn("Red Team Validation", html)


if __name__ == "__main__":
    unittest.main()
