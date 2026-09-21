"""Coverage rows for OWASP, MITRE ATLAS, and NIST AI RMF."""

from __future__ import annotations

import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from tools.sot.loader import frameworks
from tools.sot.owasp_coverage import build_coverage, owasp_catalog


def _by_id(framework_id: str) -> dict:
    for item in frameworks():
        if item.get("framework_id") == framework_id:
            return item
    return {}


def build_framework_coverage(finding_file: str) -> dict:
    findings = []
    if os.path.exists(finding_file):
        with open(finding_file, encoding="utf-8") as handle:
            findings = json.load(handle)
    threats = set()
    for finding in findings:
        threats.update(finding.get("threats") or [])

    atlas = []
    for entry in _by_id("MITRE-ATLAS").get("entries") or []:
        atlas.append(
            {
                "id": entry["id"],
                "name": entry["name"],
                "threat_id": entry["threat_id"],
                "status": "COVERED" if entry["threat_id"] in threats else "MAPPED",
            }
        )

    nist = []
    for fn in _by_id("NIST-AI-RMF").get("functions") or []:
        mapped = [tid for tid in fn.get("maps_to") or [] if tid in threats]
        nist.append(
            {
                "id": fn["id"],
                "mapped_threats": fn.get("maps_to") or [],
                "covered_threats": mapped,
                "status": "COVERED" if mapped else "MAPPED",
            }
        )

    return {
        "owasp": build_coverage(finding_file),
        "atlas": atlas,
        "nist": nist,
        "owasp_catalog_id": owasp_catalog().get("framework_id"),
    }
