"""Parse a raw proxy JSONL record into a cleaned, structured record."""

from __future__ import annotations

import json
from typing import Any


def parse_sse_record(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert a raw SSE proxy record into a cleaned structured record.

    Args:
        raw: A single record from the proxy JSONL log (must have is_sse=True).

    Returns:
        Cleaned record with keys: timestamp, domain, method, url,
        claude_session_id, request_json, response_json.

    Raises:
        ValueError: If request.body is not valid JSON.
    """
    # --- request_json ---
    request_json = json.loads(raw["request"]["body"])

    # --- claude_session_id ---
    headers = raw["request"].get("headers", {})
    claude_session_id = headers.get("X-Claude-Code-Session-Id", None)

    # --- response_json: reconstruct from sse_events ---
    message: dict[str, Any] = {}
    text_parts: list[str] = []

    for event_text in raw.get("sse_events", []):
        # Each event_text: "event: <type>\ndata: <json>"
        data_json = _extract_data(event_text)
        if data_json is None:
            continue

        event_type = data_json.get("type")

        if event_type == "message_start":
            msg = data_json.get("message", {})
            message["id"] = msg.get("id")
            message["type"] = msg.get("type")
            message["role"] = msg.get("role")
            message["model"] = msg.get("model")

        elif event_type == "content_block_delta":
            delta = data_json.get("delta", {})
            if delta.get("type") == "text_delta":
                text_parts.append(delta.get("text", ""))

        elif event_type == "message_delta":
            delta = data_json.get("delta", {})
            message["stop_reason"] = delta.get("stop_reason")
            message["usage"] = data_json.get("usage")

    message["content"] = {"text": "".join(text_parts)}
    response_json = {"message": message}

    return {
        "timestamp": raw["timestamp"],
        "domain": raw["domain"],
        "method": raw["method"],
        "url": raw["url"],
        "claude_session_id": claude_session_id,
        "request_json": request_json,
        "response_json": response_json,
    }


def _extract_data(event_text: str) -> dict[str, Any] | None:
    """Extract and parse the data: line from an SSE event string."""
    for line in event_text.splitlines():
        if line.startswith("data:"):
            data_str = line[len("data:"):].strip()
            if data_str == "[DONE]":
                return None
            try:
                return json.loads(data_str)
            except json.JSONDecodeError:
                return None
    return None
