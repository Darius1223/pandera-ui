"""Schema discovery for Pandera schemas.

Two-pass strategy per file:
1. Runtime import — accurate, handles dynamic schemas.
2. AST fallback   — safe static parse when import fails (missing deps, side-effects).

Usage::

    from pandera_ui import scan_project

    schemas = scan_project("./myproject")
    for s in schemas:
        print(s.name, [c.name for c in s.columns])
"""

from pathlib import Path

from ._extract_ast import ast_extract
from ._extract_runtime import load_module, runtime_extract
from .models import SchemaMetadata

_SKIP_DIRS = {
    ".venv", "venv", ".env", "__pycache__", ".git",
    "node_modules", ".tox", "dist", "build", "site-packages",
}


def scan_project(project_path: str | Path) -> list[SchemaMetadata]:
    """Walk *project_path* and return metadata for every Pandera schema found.

    Each ``.py`` file is first imported at runtime for full accuracy.
    If the import fails (missing dependency, side-effects, etc.) the file is
    re-processed with a static AST parser as a safe fallback.  AST-derived
    schemas are marked ``metadata_source="ast"``.

    Directories named ``.venv``, ``venv``, ``__pycache__``, ``.git``,
    ``node_modules``, ``dist``, and ``build`` are skipped automatically.
    """
    root = Path(project_path).resolve()
    results: list[SchemaMetadata] = []
    seen_ids: set[int] = set()

    for py_file in sorted(root.rglob("*.py")):
        if any(part in _SKIP_DIRS for part in py_file.parts):
            continue

        relative = py_file.relative_to(root)
        for schema in _scan_file(py_file, root, relative):
            obj_id = id(schema)
            if obj_id not in seen_ids:
                seen_ids.add(obj_id)
                results.append(schema)

    return results


def _scan_file(path: Path, root: Path, relative: Path) -> list[SchemaMetadata]:
    """Try runtime import first; fall back to AST on failure."""
    module = load_module(path, root)
    if module is not None:
        schemas = runtime_extract(module, relative)
        for s in schemas:
            s.metadata_source = "runtime"
        return schemas

    schemas = ast_extract(path, relative)
    for s in schemas:
        s.metadata_source = "ast"
    return schemas
