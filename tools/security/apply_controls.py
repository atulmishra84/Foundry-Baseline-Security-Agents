"""Ensure the hardened authorized demo exists (CTRL-001 / CTRL-003 / CTRL-005)."""

from __future__ import annotations

import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
HARDENED = os.path.join(ROOT, "tests", "vulnerable-app", "hardened_app.py")


def apply_local_controls() -> str:
    if not os.path.exists(HARDENED):
        raise FileNotFoundError(HARDENED)
    return HARDENED
