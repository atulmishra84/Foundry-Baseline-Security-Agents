"""In-process A2A (agent-to-agent) message bus with durable JSON log."""

from __future__ import annotations

import json
import os
import uuid
from typing import Any

BUS_PATH = os.path.join("output", "a2a-messages.json")

VALID_AGENTS = {
    "security-engineer",
    "red-team",
    "runtime-soc",
    "orchestrator",
}


def _load() -> list[dict[str, Any]]:
    if not os.path.exists(BUS_PATH):
        return []
    with open(BUS_PATH, encoding="utf-8") as handle:
        return json.load(handle)


def _save(messages: list[dict[str, Any]]) -> None:
    os.makedirs(os.path.dirname(BUS_PATH), exist_ok=True)
    with open(BUS_PATH, "w", encoding="utf-8") as handle:
        json.dump(messages, handle, indent=2)


def publish(
    *,
    from_agent: str,
    to_agent: str,
    intent: str,
    correlation_id: str,
    payload_ref: str = "",
    summary: str = "",
) -> dict[str, Any]:
    if from_agent not in VALID_AGENTS or to_agent not in VALID_AGENTS:
        raise ValueError("Unknown A2A agent")
    message = {
        "message_id": str(uuid.uuid4()),
        "correlation_id": correlation_id,
        "from_agent": from_agent,
        "to_agent": to_agent,
        "intent": intent,
        "payload_ref": payload_ref,
        "summary": summary,
    }
    messages = _load()
    messages.append(message)
    _save(messages)
    print(f"[A2A] {from_agent} → {to_agent} ({intent})")
    return message


def inbox(agent: str, correlation_id: str | None = None) -> list[dict[str, Any]]:
    messages = _load()
    return [
        msg
        for msg in messages
        if msg.get("to_agent") == agent
        and (correlation_id is None or msg.get("correlation_id") == correlation_id)
    ]
