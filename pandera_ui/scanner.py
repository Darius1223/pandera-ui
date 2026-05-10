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

import ast
import sys
from pathlib import Path

import typer

from ._extract_ast import ast_extract
from ._extract_runtime import load_module, runtime_extract
from .models import SchemaMetadata

_SKIP_DIRS = {
    ".venv", "venv", ".env", "__pycache__", ".git",
    "node_modules", ".tox", "dist", "build", "site-packages",
}

# Top-level packages whose import triggers DB/network connections or heavy init.
_SIDE_EFFECT_PACKAGES = {"airflow", "django", "flask", "celery"}


def _package_sys_path_entries(root: Path) -> list[str]:
    """Return sys.path candidates for *root* and all its parent packages.

    When the scan root is itself a Python package (has __init__.py), its
    parent directories up to the first non-package ancestor are also valid
    sys.path entries.  This lets imports like ``from ibp.calculations.x``
    succeed when the user points pandera-ui at the inner ``calculations/``
    directory rather than the project root.
    """
    entries = [str(root)]
    candidate = root
    while (candidate / "__init__.py").exists():
        parent = candidate.parent
        if parent == candidate:
            break
        entries.append(str(parent))
        candidate = parent
    return entries


def _has_side_effect_imports(path: Path) -> bool:
    """Return True if this file imports packages known to cause side effects on import."""
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source)
    except Exception:
        return False
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in _SIDE_EFFECT_PACKAGES:
                    return True
        elif isinstance(node, ast.ImportFrom) and node.module:
            if node.module.split(".")[0] in _SIDE_EFFECT_PACKAGES:
                return True
    return False


def scan_project(
    project_path: str | Path,
    *,
    workers: int = 4,
    verbose: bool = False,
    no_import: bool = False,
) -> list[SchemaMetadata]:
    """Walk *project_path* and return metadata for every Pandera schema found.

    Each ``.py`` file is first imported at runtime for full accuracy.
    If the import fails (missing dependency, side-effects, etc.) the file is
    re-processed with a static AST parser as a safe fallback.  AST-derived
    schemas are marked ``metadata_source="ast"``.

    Pass ``no_import=True`` to skip dynamic import entirely (faster, less accurate).
    Pass ``workers=N`` to scan files in parallel using N threads.

    Directories named ``.venv``, ``venv``, ``__pycache__``, ``.git``,
    ``node_modules``, ``dist``, and ``build`` are skipped automatically.
    """
    root = Path(project_path).resolve()
    for entry in reversed(_package_sys_path_entries(root)):
        if entry not in sys.path:
            sys.path.insert(0, entry)

    py_files = [
        f for f in sorted(root.rglob("*.py"))
        if not any(part in _SKIP_DIRS for part in f.parts)
    ]

    def scan(f: Path) -> list[SchemaMetadata]:
        return _scan_file(f, root, f.relative_to(root), verbose, no_import)

    if workers > 1:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=workers) as executor:
            all_batches = list(executor.map(scan, py_files))
    else:
        all_batches = [scan(f) for f in py_files]

    results: list[SchemaMetadata] = []
    seen_ids: set[int] = set()
    for batch in all_batches:
        for schema in batch:
            oid = id(schema)
            if oid not in seen_ids:
                seen_ids.add(oid)
                results.append(schema)

    return results


def _scan_file(
    path: Path,
    root: Path,
    relative: Path,
    verbose: bool,
    no_import: bool,
) -> list[SchemaMetadata]:
    if no_import or _has_side_effect_imports(path):
        schemas = ast_extract(path, relative)
        for s in schemas:
            s.metadata_source = "ast"
        if verbose:
            _verbose_line(relative, "ast", len(schemas))
        return schemas

    module = load_module(path, root)
    if module is not None:
        schemas = runtime_extract(module, relative)
        for s in schemas:
            s.metadata_source = "runtime"
        if verbose:
            _verbose_line(relative, "runtime", len(schemas))
        return schemas

    schemas = ast_extract(path, relative)
    for s in schemas:
        s.metadata_source = "ast"
    if verbose:
        _verbose_line(relative, "ast[fallback]", len(schemas))
    return schemas


def _verbose_line(relative: Path, source: str, count: int) -> None:
    typer.echo(f"  {source:18s} {relative}  ({count} schema(s))", err=True)
