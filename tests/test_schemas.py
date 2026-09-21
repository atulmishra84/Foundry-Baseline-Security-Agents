import json
import os
import unittest

from jsonschema import Draft7Validator

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def load(rel):
    with open(os.path.join(ROOT, rel), encoding="utf-8") as handle:
        return json.load(handle)


class SchemaTests(unittest.TestCase):
    def test_sot_and_schemas_are_valid_json(self):
        for folder in ("schemas", "sot/threats", "sot/attacks", "sot/controls", "sot/frameworks"):
            path = os.path.join(ROOT, folder)
            for name in os.listdir(path):
                if name.endswith(".json"):
                    load(os.path.join(folder, name))

    def test_owasp_has_ten_entries(self):
        catalog = load("sot/frameworks/OWASP-LLM-Top-10-2025.json")
        self.assertEqual(len(catalog["entries"]), 10)

    def test_atlas_and_nist_exist(self):
        atlas = load("sot/frameworks/MITRE-ATLAS.json")
        nist = load("sot/frameworks/NIST-AI-RMF.json")
        self.assertGreaterEqual(len(atlas["entries"]), 4)
        self.assertEqual({fn["id"] for fn in nist["functions"]}, {"GOVERN", "MAP", "MEASURE", "MANAGE"})

    def test_asset_schema(self):
        schema = load("schemas/asset.json")
        Draft7Validator.check_schema(schema)
        Draft7Validator(schema).validate(
            {
                "asset_id": "a1",
                "asset_type": "Agent",
                "name": "demo",
                "discovered_tools": ["patient_search"],
                "identities": ["system-admin-identity"],
            }
        )


if __name__ == "__main__":
    unittest.main()
