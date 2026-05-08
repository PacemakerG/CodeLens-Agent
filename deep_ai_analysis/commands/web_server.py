"""web-server subcommand — start the Claude Code session viewer HTTP server."""

from __future__ import annotations

from pathlib import Path

import click


@click.command("web-server")
@click.option(
    "--port",
    default=7789,
    show_default=True,
    type=int,
    help="Port for the viewer API server.",
)
@click.option(
    "--projects-dir",
    default=str(Path.home() / ".claude" / "projects"),
    show_default=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Path to the Claude Code projects directory.",
)
def web_server(port: int, projects_dir: Path) -> None:
    """Start the Claude Code session viewer API server."""
    # Import here to keep startup fast and avoid issues if viewer/ isn't in path
    import sys
    from pathlib import Path as _Path

    # Add project root to path so viewer/server.py can be imported
    project_root = _Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    from viewer.server import run_server
    run_server(port, projects_dir)
