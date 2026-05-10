"""FastAPI application that serves the schema metadata API and the HTML UI."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from ._coverage import compute_coverage
from .models import CoverageReport, SchemaMetadata
from .scanner import scan_project

app = FastAPI(title="Pandera UI", docs_url=None, redoc_url=None)

_schemas: list[SchemaMetadata] = []


def load_schemas(project_path: str) -> None:
    """Scan *project_path* and populate the in-memory schema store."""
    global _schemas
    _schemas = scan_project(project_path)


@app.get("/api/schemas", response_model=list[SchemaMetadata])
def get_schemas() -> list[SchemaMetadata]:
    """Return all discovered schemas as JSON."""
    return _schemas


@app.get("/api/coverage", response_model=CoverageReport)
def get_coverage() -> CoverageReport:
    """Return documentation coverage statistics."""
    return compute_coverage(_schemas)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    """Serve the single-page UI."""
    html = Path(__file__).parent / "frontend" / "index.html"
    return html.read_text(encoding="utf-8")
