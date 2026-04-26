"""Optional rich-enhanced CLI output.

When ``rich`` is installed (``pip install pandera-ui[rich]``), scanning shows
a progress spinner and a summary table.  Falls back to plain ``typer.echo``
when ``rich`` is not available.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING, Generator

import typer

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table

    _console = Console(stderr=True)
    _HAS_RICH = True
except ImportError:
    _HAS_RICH = False

if TYPE_CHECKING:
    from .models import SchemaMetadata


@contextmanager
def scan_spinner(path: str) -> Generator[None, None, None]:
    """Context manager that shows a spinner (rich) or a plain echo while scanning."""
    if _HAS_RICH:
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold cyan]Scanning[/bold cyan] {task.description}"),
            transient=True,
            console=_console,
        ) as progress:
            progress.add_task(path, total=None)
            yield
    else:
        typer.echo(f"Scanning {path} ...", err=True)
        yield


def print_summary(schemas: list[SchemaMetadata]) -> None:
    """Print count + per-schema table (rich) or a plain echo line."""
    if not _HAS_RICH:
        typer.echo(f"Found {len(schemas)} schema(s).", err=True)
        return

    _console.print(f"\n[bold green]Found {len(schemas)} schema(s).[/bold green]\n")

    if not schemas:
        return

    table = Table(show_header=True, header_style="bold magenta", box=None)
    table.add_column("Schema", style="bold")
    table.add_column("Type", style="cyan")
    table.add_column("File", style="dim")
    table.add_column("Columns", justify="right")

    for s in schemas:
        schema_type = "DataFrameModel" if s.source_class else "DataFrameSchema"
        table.add_row(s.name, schema_type, s.file_path, str(len(s.columns)))

    _console.print(table)


def print_server_ready(host: str, port: int) -> None:
    """Announce the server URL."""
    url = f"http://{host}:{port}"
    if _HAS_RICH:
        _console.print(f"\n[bold green]UI ready at[/bold green] [link={url}]{url}[/link]\n")
    else:
        typer.echo(f"UI ready at {url}", err=True)
