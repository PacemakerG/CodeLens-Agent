"""Main CLI entry point for deep-ai-analysis."""

import click

from deep_ai_analysis import __version__
from deep_ai_analysis.commands.proxy import proxy
from deep_ai_analysis.commands.start_mc import start_mc


@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="deep-ai-analysis")
@click.pass_context
def cli(ctx: click.Context) -> None:
    """deep-ai-analysis — CLI toolkit for intercepting and analyzing AI service traffic."""
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


cli.add_command(proxy)
cli.add_command(start_mc)
