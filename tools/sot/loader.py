"""Load Source of Truth JSON from disk."""

from __future__ import annotations

import json
import os
from typing import Any

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _read_dir(rel_path: str) -> list[dict[str, Any]]:
    folder = os.path.join(ROOT, rel_path)
    if not os.path.isdir(folder):
        return []
    items = []
    for name in sorted(os.listdir(folder)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(folder, name), encoding="utf-8") as handle:
            items.append(json.load(handle))
    return items


def threats() -> list[dict[str, Any]]:
    return _read_dir(os.path.join("sot", "threats"))


def attacks() -> list[dict[str, Any]]:
    return _read_dir(os.path.join("sot", "attacks"))


def controls() -> list[dict[str, Any]]:
    return _read_dir(os.path.join("sot", "controls"))


def frameworks() -> list[dict[str, Any]]:
    return _read_dir(os.path.join("sot", "frameworks"))


def detections() -> list[dict[str, Any]]:
    return _read_dir(os.path.join("sot", "detections"))


def remediations() -> list[dict[str, Any]]:
    return _read_dir(os.path.join("sot", "remediations"))


def attack_library() -> list[dict[str, Any]]:
    return _read_dir(os.path.join("agents", "red-team", "attack-library"))
