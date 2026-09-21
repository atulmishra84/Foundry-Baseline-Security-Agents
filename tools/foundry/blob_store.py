"""Write JSON artifacts to the Foundry hub storage account."""

from __future__ import annotations

import json
import os
from typing import Any

from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient


def _client() -> BlobServiceClient | None:
    account = os.getenv("AZURE_STORAGE_ACCOUNT")
    if not account:
        return None
    url = f"https://{account}.blob.core.windows.net"
    return BlobServiceClient(url, credential=DefaultAzureCredential())


def write_bytes(name: str, data: bytes, container: str = "runtime-output") -> str:
    local_dir = os.path.join(os.getcwd(), "output")
    os.makedirs(local_dir, exist_ok=True)
    local_path = os.path.join(local_dir, name)
    with open(local_path, "wb") as handle:
        handle.write(data)

    client = _client()
    if client is None:
        return local_path
    try:
        cc = client.get_container_client(container)
        try:
            cc.create_container()
        except Exception:
            pass
        cc.upload_blob(name, data, overwrite=True)
        return f"{container}/{name}"
    except Exception as exc:
        print(f"[Foundry storage] blob write skipped ({exc})")
        return local_path


def write_json(name: str, payload: Any, container: str = "runtime-output") -> str:
    text = json.dumps(payload, indent=2) + "\n"
    return write_bytes(name, text.encode("utf-8"), container=container)
