import json
import os
import unittest

from tools.sot.loader import (
    attack_library,
    attacks,
    controls,
    detections,
    frameworks,
    remediations,
    threats,
)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


class TestSourceOfTruth(unittest.TestCase):
    def test_threats_loaded(self):
        loaded = threats()
        self.assertEqual(len(loaded), 10)
        threat_ids = {t["threat_id"] for t in loaded}
        self.assertIn("T-001", threat_ids)
        self.assertIn("T-010", threat_ids)

    def test_controls_loaded(self):
        loaded = controls()
        self.assertGreaterEqual(len(loaded), 7)
        control_ids = {c["control_id"] for c in loaded}
        self.assertIn("CTRL-001-Input-Validation", control_ids)
        self.assertIn("CTRL-005-Least-Privilege", control_ids)

    def test_frameworks_loaded(self):
        loaded = frameworks()
        self.assertGreaterEqual(len(loaded), 3)

    def test_detections_loaded(self):
        loaded = detections()
        self.assertGreaterEqual(len(loaded), 4)
        det_ids = {d["detection_id"] for d in loaded}
        self.assertIn("DET-001", det_ids)
        self.assertIn("DET-002", det_ids)

    def test_remediations_loaded(self):
        loaded = remediations()
        self.assertGreaterEqual(len(loaded), 4)
        rem_ids = {r["remediation_id"] for r in loaded}
        self.assertIn("REM-001", rem_ids)
        self.assertIn("REM-003", rem_ids)

    def test_attack_library_loaded(self):
        loaded = attack_library()
        self.assertGreaterEqual(len(loaded), 5)
        atk_ids = {a["attack_id"] for a in loaded}
        self.assertIn("ATK-001", atk_ids)
        self.assertIn("ATK-002", atk_ids)


if __name__ == "__main__":
    unittest.main()
