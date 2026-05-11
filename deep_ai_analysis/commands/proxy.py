"""proxy subcommand — start a mitmproxy-based HTTP/HTTPS intercepting proxy."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import click

from deep_ai_analysis.config import DEFAULT_RAW_LOG_DIR


@click.command()
@click.option(
    "--port",
    default=7788,
    show_default=True,
    type=int,
    help="Port for the proxy to listen on.",
)
@click.option(
    "--output",
    default=str(DEFAULT_RAW_LOG_DIR),
    show_default=True,
    type=click.Path(file_okay=False, path_type=Path),
    help="Directory where JSONL log files are written.",
)
def proxy(port: int, output: Path) -> None:
    """Start an HTTP/HTTPS intercepting proxy and record matching traffic to JSONL."""
    # Check mitmproxy is available
    try:
        import mitmproxy  # noqa: F401
    except ImportError:
        click.echo(
            "Error: mitmproxy is not installed.\n"
            "Install it with:  pip install mitmproxy",
            err=True,
        )
        sys.exit(1)

    try:
        asyncio.run(_start_proxy(port, output))
    except OSError as exc:
        click.echo(f"Error: could not start proxy — {exc}", err=True)
        sys.exit(1)


async def _start_proxy(port: int, output_dir: Path) -> None:
    from mitmproxy.options import Options
    from mitmproxy.tools.dump import DumpMaster

    from deep_ai_analysis.addons.recorder import RecorderAddon
    from deep_ai_analysis.config import RECORD_DOMAINS

    output_dir.mkdir(parents=True, exist_ok=True)

    opts = Options(listen_host="127.0.0.1", listen_port=port)
    master = DumpMaster(opts, with_termlog=False, with_dumper=False)
    master.addons.add(RecorderAddon(output_dir))

    ca_cert = Path.home() / ".mitmproxy" / "mitmproxy-ca-cert.pem"
    domains_str = ", ".join(RECORD_DOMAINS)
    click.echo(f"Proxy listening on http://127.0.0.1:{port}")
    click.echo(f"Recording domains : {domains_str}")
    click.echo(f"Log directory     : {output_dir.resolve()}")
    click.echo(f"CA certificate    : {ca_cert}")
    click.echo(
        "  → Install the CA cert so HTTPS traffic is decrypted.\n"
        "  → macOS: sudo security add-trusted-cert -d -r trustRoot "
        f"-k /Library/Keychains/System.keychain {ca_cert}\n"
        "  → Set your client's HTTP proxy to http://127.0.0.1:{port}"
        .format(port=port)
    )
    click.echo("Press Ctrl+C to stop.\n")

    try:
        await master.run()
    except KeyboardInterrupt:
        click.echo("\nShutting down proxy…")
        master.shutdown()
        # Give active SSE flows a moment to flush
        await asyncio.sleep(0)
        click.echo("Proxy stopped.")
