"""pandera-ui quickstart — Python API demo.

Run from the repo root:

    python examples/quickstart.py

Or point it at your own project:

    python examples/quickstart.py /path/to/myproject
"""

import sys
from pathlib import Path

# Allow running without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from pandera_ui import scan_project  # noqa: E402


def main(project_path: str = ".") -> None:
    print(f"Scanning {Path(project_path).resolve()} ...\n")
    schemas = scan_project(project_path)

    if not schemas:
        print("No Pandera schemas found.")
        return

    print(f"Found {len(schemas)} schema(s):\n")
    for schema in schemas:
        schema_type = "DataFrameModel" if schema.source_class else "DataFrameSchema"
        print(f"  {schema.name}  [{schema_type}]  {schema.file_path}")
        for col in schema.columns:
            checks = ", ".join(c.name for c in col.checks) or "—"
            nullable = "nullable" if col.nullable else "required"
            print(f"    • {col.name}: {col.dtype or '?'}  ({nullable})  checks: {checks}")
        print()


if __name__ == "__main__":
    _default = str(Path(__file__).parent.parent / "tests" / "fixtures")
    main(sys.argv[1] if len(sys.argv) > 1 else _default)
