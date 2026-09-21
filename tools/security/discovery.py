import os
import json
import uuid

def discover_assets(target_file):
    """
    Mock discovery tool for the Security Engineer Agent.
    Parses a target file and maps the AI asset boundaries.
    """
    if not os.path.exists(target_file):
        raise FileNotFoundError(f"Target {target_file} not found.")

    with open(target_file, "r") as f:
        content = f.read()

    # Simplistic static analysis for MVP
    asset = {
        "asset_id": str(uuid.uuid4()),
        "asset_type": "Agent",
        "name": "HealthcareAIAssistant",
        "description": "Auto-discovered AI Agent from source code.",
        "dependencies": [],
        "discovered_tools": [],
        "identities": []
    }

    if "patient_search" in content:
        asset["discovered_tools"].append("patient_search")
    if "appointment_booking" in content:
        asset["discovered_tools"].append("appointment_booking")
    
    if "system-admin-identity" in content:
        asset["identities"].append("system-admin-identity")

    return asset

if __name__ == "__main__":
    target = "tests/vulnerable-app/app.py"
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    asset = discover_assets(target)
    output_file = os.path.join(output_dir, "asset.json")
    
    with open(output_file, "w") as f:
        json.dump(asset, f, indent=2)
    print(f"[Security Engineer] Discovery complete. Asset saved to {output_file}")
