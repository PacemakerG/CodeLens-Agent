"""Shared export logic — used by both the CLI command and the viewer HTTP server."""

from __future__ import annotations

import io
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Any


def _add_file(tar: tarfile.TarFile, src: Path, arcname: str) -> None:
    tar.add(src, arcname=arcname, recursive=False)


def export_session(
    tar: tarfile.TarFile,
    session_id: str,
    projects_dir: Path,
    req_resp_dir: Path,
    req_resp_dates: dict[str, list[str]],
    get_session_fn: Any,
) -> dict[str, Any]:
    """Add one session's files into an open TarFile. Returns a summary dict.

    get_session_fn is viewer.server.get_session, passed in to avoid circular imports.
    """
    session = get_session_fn(session_id, projects_dir)
    if session is None:
        raise ValueError(f"Session not found: {session_id}")

    project_dir = projects_dir / session["projectDir"]
    main_log = project_dir / f"{session_id}.jsonl"
    if not main_log.exists():
        raise ValueError(f"Main Claude log not found: {main_log}")

    _add_file(tar, main_log, f"{session_id}/claude-log.jsonl")

    subagent_count = 0
    subagents_dir = project_dir / session_id / "subagents"
    if subagents_dir.is_dir():
        for path in sorted(subagents_dir.iterdir()):
            if not path.is_file():
                continue
            _add_file(tar, path, f"{session_id}/subagents/{path.name}")
            subagent_count += 1

    raw_count = 0
    for date in req_resp_dates.get(session_id, []):
        raw_path = req_resp_dir / session_id / f"{date}.jsonl"
        if not raw_path.exists():
            continue
        _add_file(tar, raw_path, f"{session_id}/raw-req-resp/{raw_path.name}")
        raw_count += 1

    return {
        "session_id": session_id,
        "project_dir": session["projectDir"],
        "subagent_count": subagent_count,
        "raw_count": raw_count,
    }


def build_tar_gz_bytes(
    session_ids: list[str],
    projects_dir: Path,
    req_resp_dir: Path,
    req_resp_dates: dict[str, list[str]],
    get_session_fn: Any,
) -> tuple[bytes, list[dict[str, Any]]]:
    """Generate a tar.gz archive in memory and return (bytes, summaries)."""
    buf = io.BytesIO()
    summaries: list[dict[str, Any]] = []
    with tarfile.open(mode="w:gz", fileobj=buf) as tar:
        for session_id in session_ids:
            summaries.append(
                export_session(tar, session_id, projects_dir, req_resp_dir, req_resp_dates, get_session_fn)
            )
    return buf.getvalue(), summaries


def default_filename() -> str:
    return f"export-{datetime.now().strftime('%Y%m%d-%H%M%S')}.tar.gz"
