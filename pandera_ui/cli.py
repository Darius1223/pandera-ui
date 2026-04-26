"""CLI entry point for pandera-ui."""

import json
from pathlib import Path
from typing import Optional

import typer
import uvicorn

from ._console import print_server_ready, print_summary, scan_spinner
from .scanner import scan_project


def cli_app(
    project_path: Path = typer.Argument(Path("."), help="Project root to scan"),
    port: int = typer.Option(8765, "--port", "-p", help="Port for the UI server"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind"),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Print JSON to stdout, do not start server",
    ),
    export: Optional[str] = typer.Option(
        None,
        "--export",
        help="Export format: 'markdown' or 'html'. Prints to stdout, no server.",
    ),
    coverage: bool = typer.Option(
        False,
        "--coverage",
        help="Print documentation coverage stats and exit",
    ),
    watch: bool = typer.Option(
        False,
        "--watch",
        "-w",
        help="Auto-reload schemas when .py files change (requires watchdog)",
    ),
) -> None:
    """Scan PROJECT_PATH for Pandera schemas and serve a documentation UI."""
    with scan_spinner(str(project_path.resolve())):
        schemas = scan_project(project_path)

    print_summary(schemas)

    if output_json:
        print(json.dumps([s.model_dump() for s in schemas], indent=2, default=str))
        return

    if export is not None:
        from ._export import to_html, to_markdown

        if export == "markdown":
            print(to_markdown(schemas))
        elif export == "html":
            print(to_html(schemas))
        else:
            typer.echo(f"Unknown export format: {export!r}. Use 'markdown' or 'html'.", err=True)
            raise typer.Exit(1)
        return

    if coverage:
        from ._coverage import compute_coverage, format_coverage

        report = compute_coverage(schemas)
        typer.echo(format_coverage(report))
        return

    from . import server  # import here so server state is isolated from tests

    server.load_schemas(str(project_path))
    print_server_ready(host, port)

    if watch:
        _run_watch(str(project_path.resolve()), server, host, port)
    else:
        uvicorn.run(server.app, host=host, port=port, log_level="warning")


def _run_watch(project_path: str, server, host: str, port: int) -> None:  # type: ignore[type-arg]
    import threading

    try:
        from watchdog.events import FileSystemEvent, FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        typer.echo(
            "watchdog is required for --watch. Install with: pip install watchdog",
            err=True,
        )
        raise typer.Exit(1)

    t = threading.Thread(
        target=uvicorn.run,
        args=(server.app,),
        kwargs={"host": host, "port": port, "log_level": "warning"},
        daemon=True,
    )
    t.start()

    class _ReloadHandler(FileSystemEventHandler):
        def dispatch(self, event: FileSystemEvent) -> None:
            if not event.is_directory and str(event.src_path).endswith(".py"):
                typer.echo("  [watch] change detected — reloading schemas…", err=True)
                server.load_schemas(project_path)

    observer = Observer()
    observer.schedule(_ReloadHandler(), project_path, recursive=True)
    observer.start()
    try:
        t.join()
    except KeyboardInterrupt:
        pass
    finally:
        observer.stop()
        observer.join()


def main() -> None:
    typer.run(cli_app)
