"""Validate Security Copilot YAML manifests before tenant upload."""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
REQUIRED = ("Descriptor", "SkillGroups")


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        return [f"{path.name}: not a mapping"]
    for key in REQUIRED:
        if key not in data:
            errors.append(f"{path.name}: missing {key}")
    desc = data.get("Descriptor") or {}
    for field in ("Name", "DisplayName", "Description"):
        if not desc.get(field):
            errors.append(f"{path.name}: Descriptor.{field} required")
    groups = data.get("SkillGroups") or []
    if not groups:
        errors.append(f"{path.name}: no SkillGroups")
    return errors


def main() -> int:
    errors: list[str] = []
    files = sorted(ROOT.glob("*.yaml"))
    if len(files) < 3:
        errors.append("Expected three YAML manifests")
    for path in files:
        errors.extend(validate(path))
    if errors:
        print("\n".join(errors))
        return 1
    print(f"OK: {len(files)} Security Copilot manifests")
    for path in files:
        print(f"  upload {path}")
    print("Publish at https://securitycopilot.microsoft.com/build")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
