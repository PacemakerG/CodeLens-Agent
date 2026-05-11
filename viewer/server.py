"""Viewer HTTP server — serves Claude Code session log data via REST API."""

from __future__ import annotations

import argparse
import json
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Data loading helpers
# ---------------------------------------------------------------------------

def _read_jsonl(path: Path) -> list[dict]:
    entries = []
    with path.open(encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                entry["_fileLine"] = lineno
                entries.append(entry)
            except json.JSONDecodeError:
                pass
    return entries


def _load_subagents(session_dir: Path) -> list[dict[str, Any]]:
    subagents_dir = session_dir / "subagents"
    if not subagents_dir.is_dir():
        return []
    subagents = []
    for jsonl_path in sorted(subagents_dir.glob("agent-*.jsonl")):
        agent_id = jsonl_path.stem[len("agent-"):]
        meta_path = subagents_dir / f"agent-{agent_id}.meta.json"
        meta: dict = {}
        if meta_path.exists():
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                pass
        entries = _read_jsonl(jsonl_path)
        subagents.append({
            "agentId": agent_id,
            "meta": meta,
            "entries": entries,
        })
    return subagents


def get_projects(projects_dir: Path) -> list[dict[str, Any]]:
    """Return list of {projectDir, sessions} for all projects."""
    result = []
    if not projects_dir.is_dir():
        return result
    for project_path in sorted(projects_dir.iterdir()):
        if not project_path.is_dir():
            continue
        sessions = sorted(
            p.stem for p in project_path.glob("*.jsonl")
            if re.fullmatch(r"[0-9a-f-]{36}", p.stem)
        )
        if sessions:
            result.append({
                "projectDir": project_path.name,
                "sessions": sessions,
            })
    return result


def get_session(session_id: str, projects_dir: Path) -> dict[str, Any] | None:
    """Find session by ID across all project dirs. Returns None if not found."""
    if not projects_dir.is_dir():
        return None
    for project_path in projects_dir.iterdir():
        if not project_path.is_dir():
            continue
        jsonl_path = project_path / f"{session_id}.jsonl"
        if jsonl_path.exists():
            main_entries = _read_jsonl(jsonl_path)
            session_dir = project_path / session_id
            subagents = _load_subagents(session_dir)
            return {
                "sessionId": session_id,
                "projectDir": project_path.name,
                "main": main_entries,
                "subagents": subagents,
            }
    return None


def get_message_http(
    session_id: str,
    message_id: str,
    projects_dir: Path,
    logs_dir: Path,
) -> list[dict[str, Any]] | None:
    """Find HTTP records matching an assistant message ID (msg_bdrk_xxx).

    message_id is the assistant entry's message.id field.
    Matches by response_json.message.id in parsed JSONL files.

    Returns a list of matching parsed records, or None if session not found.
    Returns [] if no matching records found.
    """
    # Verify the session exists
    session_data = get_session(session_id, projects_dir)
    if session_data is None:
        return None

    # Scan all *_parsed.jsonl files in logs_dir, match by response_json.message.id
    if not logs_dir.is_dir():
        return []

    matches = []
    for parsed_path in sorted(logs_dir.glob("*_parsed.jsonl")):
        for record in _read_jsonl(parsed_path):
            if record.get("claude_session_id") != session_id:
                continue
            rec_msg_id = record.get("response_json", {}).get("message", {}).get("id")
            if rec_msg_id == message_id:
                matches.append(record)

    matches.sort(key=lambda r: r.get("timestamp", ""))
    return matches


def get_logs(
    logs_dir: Path,
    session_filter: str | None = None,
) -> dict[str, Any]:
    """Return all parsed log records from *_parsed.jsonl files.

    Records are sorted by timestamp descending.
    Returns {"records": [...], "sessions": [...unique session ids]}.
    """
    if not logs_dir.is_dir():
        return {"records": [], "sessions": []}

    all_records: list[dict] = []
    for parsed_path in sorted(logs_dir.glob("*_parsed.jsonl")):
        all_records.extend(_read_jsonl(parsed_path))

    sessions = sorted({r.get("claude_session_id", "") for r in all_records if r.get("claude_session_id")})

    if session_filter:
        all_records = [r for r in all_records if r.get("claude_session_id") == session_filter]

    all_records.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return {"records": all_records, "sessions": sessions}


def get_req_resp_sessions(logs_dir: Path) -> dict[str, Any]:
    """Return all session IDs and their available date files under logs_dir.

    Returns {"sessions": [{"id": "<sessionId>", "dates": ["YYYY-MM-DD", ...]}, ...]}.
    """
    if not logs_dir.is_dir():
        return {"sessions": []}

    sessions = []
    for session_dir in sorted(logs_dir.iterdir()):
        if not session_dir.is_dir():
            continue
        dates = sorted(
            p.stem for p in session_dir.glob("*.jsonl")
            if not p.name.endswith("_parsed.jsonl")
        )
        if dates:
            sessions.append({"id": session_dir.name, "dates": dates})
    return {"sessions": sessions}


def get_req_resp_records(logs_dir: Path, session_id: str, date: str) -> list[dict]:
    """Return raw records from logs_dir/<session_id>/<date>.jsonl."""
    jsonl_path = logs_dir / session_id / f"{date}.jsonl"
    if not jsonl_path.exists():
        return []
    return _read_jsonl(jsonl_path)


# ---------------------------------------------------------------------------
# HTTP request handler
# ---------------------------------------------------------------------------

def _make_handler(projects_dir: Path, logs_dir: Path):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            pass

        def _send_json(self, data: Any, status: int = 200) -> None:
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()
            self.wfile.write(body)

        def do_OPTIONS(self) -> None:
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            self.end_headers()

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path.rstrip("/")
            query = parsed.query

            if path == "/api/projects":
                self._send_json(get_projects(projects_dir))

            elif path.startswith("/api/session/"):
                session_id = path[len("/api/session/"):]
                if not re.fullmatch(r"[0-9a-f-]{36}", session_id):
                    self._send_json({"error": "invalid session id"}, 400)
                    return
                data = get_session(session_id, projects_dir)
                if data is None:
                    self._send_json({"error": "session not found"}, 404)
                else:
                    self._send_json(data)

            elif path == "/api/logs":
                from urllib.parse import parse_qs
                params = parse_qs(query)
                session_filter = params.get("session", [None])[0]
                self._send_json(get_logs(logs_dir, session_filter))

            elif path.startswith("/api/message-http/"):
                # /api/message-http/<sessionId>/<messageId>
                rest = path[len("/api/message-http/"):]
                parts = rest.split("/", 1)
                if len(parts) != 2:
                    self._send_json({"error": "invalid path"}, 400)
                    return
                session_id, message_id = parts
                if not re.fullmatch(r"[0-9a-f-]{36}", session_id):
                    self._send_json({"error": "invalid session id"}, 400)
                    return
                records = get_message_http(session_id, message_id, projects_dir, logs_dir)
                if records is None:
                    self._send_json({"error": "message not found"}, 404)
                else:
                    self._send_json({"records": records})

            elif path == "/api/req-resp/sessions":
                self._send_json(get_req_resp_sessions(logs_dir))

            elif path == "/api/req-resp/records":
                from urllib.parse import parse_qs
                params = parse_qs(query)
                session_id = params.get("session", [""])[0]
                date = params.get("date", [""])[0]
                if not session_id or not date:
                    self._send_json({"error": "session and date are required"}, 400)
                    return
                records = get_req_resp_records(logs_dir, session_id, date)
                self._send_json({"records": records})

            else:
                self._send_json({"error": "not found"}, 404)

    return Handler


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_server(port: int, projects_dir: Path, logs_dir: Path) -> None:
    handler = _make_handler(projects_dir, logs_dir)
    server = HTTPServer(("127.0.0.1", port), handler)
    print(f"Viewer API listening on http://127.0.0.1:{port}")
    print(f"Projects dir : {projects_dir.resolve()}")
    print(f"Logs dir     : {logs_dir.resolve()}")
    print(f"Open viewer  : viewer/index.html")
    print("Press Ctrl+C to stop.\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()


# ---------------------------------------------------------------------------
# Direct CLI (python3 viewer/server.py)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Claude Code session viewer API server")
    parser.add_argument("--port", type=int, default=7789)
    parser.add_argument(
        "--projects-dir",
        type=Path,
        default=Path.home() / ".claude" / "projects",
    )
    parser.add_argument(
        "--logs-dir",
        type=Path,
        default=Path("./logs"),
    )
    args = parser.parse_args()
    run_server(args.port, args.projects_dir, args.logs_dir)
