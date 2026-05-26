"""import subcommand — import a portable diagnostic package and optionally open the viewer."""

from __future__ import annotations

import json
import shutil
import sys
import tarfile
import tempfile
from pathlib import Path

import click


_IMPORTS_DIR = Path.home() / "Downloads" / "deep-ai-analysis-imports"
_RAW_IMPORTS_DIR = Path.home() / "Downloads" / "deep-ai-analysis-imports" / "raw-req-resp"
_MANIFEST_FILENAME = "manifest.json"
_PACKAGE_ROOT = "deep-ai-analysis-export"


def _find_package_root(base: Path) -> Path:
    """Return the deep-ai-analysis-export/ dir, whether base IS it or contains it."""
    if (base / _MANIFEST_FILENAME).exists():
        return base
    candidate = base / _PACKAGE_ROOT
    if candidate.is_dir() and (candidate / _MANIFEST_FILENAME).exists():
        return candidate
    raise click.ClickException(
        f"No manifest.json found in {base}. "
        "This doesn't look like a valid deep-ai-analysis diagnostic package."
    )


def _read_manifest(package_dir: Path) -> dict:
    manifest_path = package_dir / _MANIFEST_FILENAME
    try:
        manifest = json.loads(manifest_path.read_text())
    except (json.JSONDecodeError, OSError) as exc:
        raise click.ClickException(f"Failed to read manifest.json: {exc}") from exc
    if "sessionId" not in manifest or "projectDir" not in manifest:
        raise click.ClickException("manifest.json is missing required fields (sessionId, projectDir).")
    return manifest


def _import_package(package_dir: Path, manifest: dict) -> tuple[Path, Path]:
    """Copy package contents into the local imports dirs. Returns (projects_dir, raw_dir)."""
    session_id: str = manifest["sessionId"]
    project_dir_name: str = manifest["projectDir"]

    dest_project = _IMPORTS_DIR / project_dir_name
    dest_project.mkdir(parents=True, exist_ok=True)

    # Main log
    main_log_src = package_dir / "claude-logs" / "main-session.jsonl"
    if not main_log_src.exists():
        raise click.ClickException(f"main-session.jsonl not found in package: {main_log_src}")
    shutil.copy2(main_log_src, dest_project / f"{session_id}.jsonl")

    # Subagents
    subagents_src = package_dir / "claude-logs" / "subagents"
    if subagents_src.is_dir():
        dest_subagents = dest_project / session_id / "subagents"
        dest_subagents.mkdir(parents=True, exist_ok=True)
        for f in subagents_src.iterdir():
            if f.is_file():
                shutil.copy2(f, dest_subagents / f.name)

    # Raw req-resp
    req_resp_src = package_dir / "req-resp"
    if req_resp_src.is_dir():
        dest_raw = _RAW_IMPORTS_DIR / session_id
        dest_raw.mkdir(parents=True, exist_ok=True)
        for f in req_resp_src.iterdir():
            if f.is_file():
                shutil.copy2(f, dest_raw / f.name)

    return _IMPORTS_DIR, _RAW_IMPORTS_DIR


def _find_free_port(start: int, attempts: int = 10) -> int:
    import socket
    for port in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    raise click.ClickException(f"No free port found in range {start}–{start + attempts - 1}.")


def _open_viewer(port: int = 7789) -> None:
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from viewer.server import run_server as _run_server

    free_port = _find_free_port(port)
    if free_port != port:
        click.echo(f"Port {port} already in use, using {free_port} instead.")

    click.echo(f"Starting viewer at http://127.0.0.1:{free_port}/claude-log.html")
    click.echo("Press Ctrl+C to stop.")
    _run_server(free_port, _IMPORTS_DIR, _RAW_IMPORTS_DIR)


@click.command("import")
@click.argument("path", type=click.Path(exists=True, path_type=Path))
@click.option("--open", "open_viewer", is_flag=True, help="Open the viewer in the browser after import.")
@click.option("--force", is_flag=True, help="Overwrite existing imported session without prompting.")
def import_(path: Path, open_viewer: bool, force: bool) -> None:
    """Import a portable diagnostic package (tar.gz or extracted directory)."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        if path.is_file() and tarfile.is_tarfile(path):
            with tarfile.open(path, "r:gz") as tar:
                tar.extractall(tmp_path)
            package_dir = _find_package_root(tmp_path)
        elif path.is_dir():
            package_dir = _find_package_root(path)
        else:
            raise click.ClickException(f"{path} is not a tar.gz file or a directory.")

        manifest = _read_manifest(package_dir)
        session_id: str = manifest["sessionId"]
        project_dir_name: str = manifest["projectDir"]

        dest_session_log = _IMPORTS_DIR / project_dir_name / f"{session_id}.jsonl"
        if dest_session_log.exists() and not force:
            click.echo(f"Session {session_id} already imported at {dest_session_log.parent}.")
            if not click.confirm("Overwrite?", default=False):
                click.echo("Import cancelled.")
                return

        _import_package(package_dir, manifest)

    click.echo(f"Imported session: {session_id}")
    click.echo(f"Location: {_IMPORTS_DIR / project_dir_name}")

    if open_viewer:
        _open_viewer()
