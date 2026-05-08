"""mitmproxy addon that records HTTP/HTTPS traffic to JSONL files."""

from __future__ import annotations

import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from mitmproxy import http

from deep_ai_analysis.config import RECORD_DOMAINS


class RecorderAddon:
    """Records matching HTTP flows to a daily JSONL file.

    Each request is written as a single JSON line to ``<output_dir>/YYYY-MM-DD.jsonl``.
    SSE (text/event-stream) responses are buffered in memory and written as one
    record when the flow completes.
    """

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir
        self._domains: list[str] = RECORD_DOMAINS
        # Per-flow SSE state: flow_id -> {"events": [...], "buffer": ""}
        self._sse_buffers: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _should_record(self, flow: http.HTTPFlow) -> bool:
        return flow.request.pretty_host in self._domains

    def _jsonl_path(self) -> Path:
        today = date.today().isoformat()  # YYYY-MM-DD
        path = self._output_dir / f"{today}.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    def _append_record(self, record: dict[str, Any]) -> None:
        path = self._jsonl_path()
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _headers_to_dict(self, headers: Any) -> dict[str, str]:
        return dict(headers)

    # ------------------------------------------------------------------
    # mitmproxy hooks
    # ------------------------------------------------------------------

    def responseheaders(self, flow: http.HTTPFlow) -> None:
        """Detect SSE responses and enable streaming mode."""
        if not self._should_record(flow):
            return
        if flow.response is None:
            return
        content_type = flow.response.headers.get("content-type", "")
        if "text/event-stream" in content_type:
            # Enable streaming: response body will arrive in chunks
            flow.response.stream = self._make_sse_stream_handler(flow)
            self._sse_buffers[flow.id] = {"events": [], "buffer": ""}

    def _make_sse_stream_handler(self, flow: http.HTTPFlow):
        """Return a streaming callback that buffers SSE chunks for this flow."""

        def handler(chunk: bytes) -> bytes:
            state = self._sse_buffers.get(flow.id)
            if state is None:
                return chunk
            text = state["buffer"] + chunk.decode("utf-8", errors="replace")
            # Split on double-newline (SSE event boundary)
            parts = text.split("\n\n")
            # All parts except the last are complete events
            for event in parts[:-1]:
                event = event.strip()
                if event:
                    state["events"].append(event)
            # The last part may be incomplete — keep it in the buffer
            state["buffer"] = parts[-1]
            return chunk  # pass through unchanged

        return handler

    def response(self, flow: http.HTTPFlow) -> None:
        """Write the completed flow to JSONL."""
        if not self._should_record(flow):
            return
        if flow.response is None:
            return

        timestamp = datetime.now(tz=timezone.utc).isoformat()

        # Request fields
        try:
            req_body = flow.request.get_text(strict=False) or ""
        except Exception:
            req_body = flow.request.content.decode("utf-8", errors="replace")

        request_data = {
            "headers": self._headers_to_dict(flow.request.headers),
            "body": req_body,
        }

        # SSE vs normal response
        sse_state = self._sse_buffers.pop(flow.id, None)
        is_sse = sse_state is not None

        if is_sse:
            # Flush any remaining buffered text as a final (possibly incomplete) event
            remaining = sse_state["buffer"].strip()
            if remaining:
                sse_state["events"].append(remaining)
            sse_events: list[str] = sse_state["events"]
            resp_body = "\n\n".join(sse_events)
        else:
            try:
                resp_body = flow.response.get_text(strict=False) or ""
            except Exception:
                resp_body = flow.response.content.decode("utf-8", errors="replace")
            sse_events = []

        response_data = {
            "status": flow.response.status_code,
            "headers": self._headers_to_dict(flow.response.headers),
            "body": resp_body,
        }

        record: dict[str, Any] = {
            "timestamp": timestamp,
            "domain": flow.request.pretty_host,
            "method": flow.request.method,
            "url": flow.request.pretty_url,
            "request": request_data,
            "response": response_data,
            "is_sse": is_sse,
        }
        if is_sse:
            record["sse_events"] = sse_events

        try:
            self._append_record(record)
        except OSError as exc:
            print(f"[deep-ai-analysis] Failed to write log: {exc}", file=sys.stderr)
