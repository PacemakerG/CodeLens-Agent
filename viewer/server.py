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
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def _load_subagents(session_dir: Path) -> list[dict[str, Any]]:
    subagents_dir = session_dir / "subagents"
    if not subagents_dir.is_dir():
        return []
    subagents = []
    # Find all agent JSONL files
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


# ---------------------------------------------------------------------------
# HTTP request handler
# ---------------------------------------------------------------------------

def _make_handler(projects_dir: Path):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args: Any) -> None:
            # Suppress default access log noise
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

            else:
                self._send_json({"error": "not found"}, 404)

    return Handler


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_server(port: int, projects_dir: Path) -> None:
    handler = _make_handler(projects_dir)
    server = HTTPServer(("127.0.0.1", port), handler)
    print(f"Viewer API listening on http://127.0.0.1:{port}")
    print(f"Projects dir : {projects_dir.resolve()}")
    print(f"Open viewer  : viewer/index.html  (or http://127.0.0.1:{port}/)")
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
    args = parser.parse_args()
    run_server(args.port, args.projects_dir)
