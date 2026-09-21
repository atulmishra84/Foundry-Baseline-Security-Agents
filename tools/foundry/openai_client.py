"""Azure OpenAI helper: Entra ID preferred, API key optional fallback."""

from __future__ import annotations

import json
import os
from typing import Any

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def is_configured() -> bool:
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    if not endpoint:
        return False
    if os.getenv("AZURE_OPENAI_API_KEY"):
        return True
    return os.getenv("FOUNDRY_USE_AZURE_AD", "true").lower() == "true"


def _client():
    from openai import AzureOpenAI

    endpoint = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-10-21")
    key = os.getenv("AZURE_OPENAI_API_KEY")
    if key and os.getenv("FOUNDRY_USE_AZURE_AD", "true").lower() != "true":
        return AzureOpenAI(api_key=key, api_version=api_version, azure_endpoint=endpoint)

    from azure.identity import DefaultAzureCredential, get_bearer_token_provider

    token_provider = get_bearer_token_provider(
        DefaultAzureCredential(),
        "https://cognitiveservices.azure.com/.default",
    )
    return AzureOpenAI(
        azure_ad_token_provider=token_provider,
        api_version=api_version,
        azure_endpoint=endpoint,
    )


def chat_json(system_prompt: str, user_prompt: str) -> dict[str, Any] | None:
    if not is_configured():
        print("[Foundry] Azure OpenAI not configured; using local deterministic path.")
        return None
    try:
        client = _client()
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o"),
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or "{}"
        parsed = json.loads(content)
        if isinstance(parsed, dict):
            return parsed
    except Exception as exc:
        print(f"[Foundry] Azure OpenAI call failed ({exc}); using local deterministic path.")
    return None
