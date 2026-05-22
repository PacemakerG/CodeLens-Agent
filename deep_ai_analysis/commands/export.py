"""export subcommand — bundle Claude Code logs and raw request/response logs."""

from __future__ import annotations

import re
import sys
import tarfile
from datetime import datetime
from pathlib import Path

import click

from deep_ai_analysis.config import DEFAULT_RAW_LOG_DIR

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from viewer.server import get_projects, get_req_resp_sessions, get_session

SESSION_ID_RE = re.compile(r"[0-9a-f-]{36}")


def _default_output_path() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Path.cwd() / f"export-{timestamp}.tar.gz"


def _print_sessions(projects_dir: Path) -> None:
    projects = get_projects(projects_dir)
    if not projects:
        click.echo(f"No Claude Code sessions found in {projects_dir}")
        return

    total = 0
    for project in projects:
        click.echo(project["projectDir"])
        for session in project["sessions"]:
            first = session.get("firstTimestamp") or "-"
            last = session.get("lastTimestamp") or "-"
            click.echo(f"  {session['id']}  {first} ~ {last}")
            total += 1

    click.echo(f"\nTotal sessions: {total}")


def _req_resp_dates_by_session(req_resp_dir: Path) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for session in get_req_resp_sessions(req_resp_dir)["sessions"]:
        result[session["id"]] = session["dates"]
    return result


def _add_file(tar: tarfile.TarFile, src: Path, arcname: str) -> None:
    tar.add(src, arcname=arcname, recursive=False)


def _validate_session_ids(session_ids: tuple[str, ...]) -> list[str]:
    unique_ids = list(dict.fromkeys(session_ids))
    invalid_ids = [session_id for session_id in unique_ids if not SESSION_ID_RE.fullmatch(session_id)]
    if invalid_ids:
        raise click.ClickException(f"Invalid session ID(s): {', '.join(invalid_ids)}")
    return unique_ids


def _export_session(
    tar: tarfile.TarFile,
    session_id: str,
    projects_dir: Path,
    req_resp_dir: Path,
    req_resp_dates: dict[str, list[str]],
) -> dict[str, str | int]:
    session = get_session(session_id, projects_dir)
    if session is None:
        raise click.ClickException(f"Session not found: {session_id}")

    project_dir = projects_dir / session["projectDir"]
    main_log = project_dir / f"{session_id}.jsonl"
    if not main_log.exists():
        raise click.ClickException(f"Main Claude log not found: {main_log}")

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


@click.command("export")
@click.argument("session_ids", nargs=-1)
@click.option(
    "--projects-dir",
    default=str(Path.home() / ".claude" / "projects"),
    show_default=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Path to the Claude Code projects directory.",
)
@click.option(
    "--req-resp-dir",
    default=str(DEFAULT_RAW_LOG_DIR),
    show_default=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory containing raw HTTP request/response JSONL files.",
)
@click.option(
    "--output",
    "-o",
    default=None,
    type=click.Path(dir_okay=False, path_type=Path),
    help="Output archive path. Defaults to ./export-<timestamp>.tar.gz.",
)
@click.option(
    "--list",
    "list_only",
    is_flag=True,
    help="List available Claude Code sessions and exit.",
)
def export(
    session_ids: tuple[str, ...],
    projects_dir: Path,
    req_resp_dir: Path,
    output: Path | None,
    list_only: bool,
) -> None:
    """Export Claude Code logs and raw request/response logs into a tar.gz archive."""
    if list_only:
        _print_sessions(projects_dir)
        return

    if not session_ids:
        raise click.ClickException("No session IDs provided. Use --list to discover available sessions.")

    resolved_session_ids = _validate_session_ids(session_ids)
    output = output or _default_output_path()
    output.parent.mkdir(parents=True, exist_ok=True)

    req_resp_dates = _req_resp_dates_by_session(req_resp_dir)

    summaries = []
    with tarfile.open(output, "w:gz") as tar:
        for session_id in resolved_session_ids:
            summaries.append(
                _export_session(tar, session_id, projects_dir, req_resp_dir, req_resp_dates)
            )

    click.echo(f"Exported {len(summaries)} session(s) to {output}")
    for summary in summaries:
        raw_note = " (no raw req/resp found)" if summary["raw_count"] == 0 else ""
        click.echo(
            f"- {summary['session_id']} [{summary['project_dir']}]: "
            f"{summary['subagent_count']} subagent files, {summary['raw_count']} raw log files{raw_note}"
        )
