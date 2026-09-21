"""Re-validate T-001 after local controls are applied to the hardened demo copy."""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from tools.foundry.blob_store import write_json
from tools.security.apply_controls import apply_local_controls
from tools.security.attacker import execute_attack


def retest(finding_file: str) -> dict:
    hardened = apply_local_controls()
    attacks, evidence = execute_attack(finding_file, hardened)
    write_json("attack-retest.json", attacks)
    write_json("evidence-retest.json", evidence)
    statuses = [item.get("exploitability") for item in attacks]
    return {
        "target": hardened,
        "exploitability": statuses,
        "blocked": all(status == "BLOCKED" for status in statuses) if statuses else False,
    }


if __name__ == "__main__":
    result = retest(os.path.join(ROOT, "output", "finding.json"))
    print(json.dumps(result, indent=2))
