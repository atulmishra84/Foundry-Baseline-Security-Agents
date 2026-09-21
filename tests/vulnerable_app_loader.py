"""Import HealthcareAIAssistant from tests/vulnerable-app/app.py without package install."""

from __future__ import annotations

import importlib.util
import os


def load_assistant(app_path: str):
    path = os.path.abspath(app_path)
    spec = importlib.util.spec_from_file_location("vulnerable_app", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.HealthcareAIAssistant()
