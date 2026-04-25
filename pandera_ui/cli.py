"""CLI entry point for pandera-ui."""

import json
from pathlib import Path

import typer
import uvicorn

from .scanner import scan_project


def _cli(
    project_path: Path = typer.Argument(Path("."), help="Project root to scan"),
    port: int = typer.Option(8765, "--port", "-p", help="Port for the UI server"),
    host: str = typer.Option("127.0.0.1", "--host", help="Host to bind"),
    output_json: bool = typer.Option(
        False,
        "--json",
        help="Print JSON to stdout, do not start server",
    ),
) -> None:
    """Scan PROJECT_PATH for Pandera schemas and serve a documentation UI."""
    typer.echo(f"Scanning {project_path.resolve()} ...")
    schemas = scan_project(project_path)
    typer.echo(f"Found {len(schemas)} schema(s).")

    if output_json:
        print(json.dumps([s.model_dump() for s in schemas], indent=2, default=str))
        return

    from . import server  # import here so server state is isolated from tests
    server.load_schemas(str(project_path))
    typer.echo(f"UI ready at http://{host}:{port}")
    uvicorn.run(server.app, host=host, port=port, log_level="warning")


def main() -> None:
    typer.run(_cli)
