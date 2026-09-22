import json
import os
import tempfile
import unittest

from jsonschema import Draft7Validator

from tools.security.discovery import discover_assets

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestDiscovery(unittest.TestCase):
    def setUp(self):
        with open(os.path.join(ROOT, "schemas", "asset.json"), encoding="utf-8") as f:
            self.schema = json.load(f)
        self.validator = Draft7Validator(self.schema)

    def test_discover_vulnerable_app(self):
        target = os.path.join(ROOT, "tests", "vulnerable-app", "app.py")
        asset = discover_assets(target)

        # Validate against JSON schema
        self.validator.validate(asset)

        self.assertEqual(asset["asset_type"], "Agent")
        self.assertEqual(asset["name"], "HealthcareAIAssistant")
        self.assertIn("patient_search", asset["discovered_tools"])
        self.assertIn("appointment_booking", asset["discovered_tools"])
        self.assertIn("system-admin-identity", asset["identities"])
        self.assertIn("json", asset["dependencies"])
        self.assertIn("logging", asset["dependencies"])

    def test_discover_custom_agent_via_ast(self):
        code = """
import os
import requests

def tool_calculate(x, y):
    return x + y

class CustomerSupportAgent:
    def __init__(self):
        self.execution_role = "support-reader-role"

    def execute_tool(self, tool_name, args):
        if tool_name == "tool_calculate":
            return tool_calculate(**args)
"""
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
            f.write(code)
            tmp_path = f.name

        try:
            asset = discover_assets(tmp_path)
            self.validator.validate(asset)
            self.assertEqual(asset["name"], "CustomerSupportAgent")
            self.assertIn("requests", asset["dependencies"])
            self.assertIn("os", asset["dependencies"])
            self.assertIn("tool_calculate", asset["discovered_tools"])
            self.assertIn("support-reader-role", asset["identities"])
        finally:
            os.unlink(tmp_path)

    def test_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            discover_assets("/path/does/not/exist/agent.py")


if __name__ == "__main__":
    unittest.main()
