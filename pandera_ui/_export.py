"""Markdown and HTML exporters for Pandera schema metadata."""

from .models import SchemaMetadata


def to_markdown(schemas: list[SchemaMetadata]) -> str:
    lines = ["# Pandera Schema Documentation", ""]
    for s in schemas:
        lines.append(f"## {s.name}")
        if s.title:
            lines.append(f"**{s.title}**  ")
        lines.append("")
        schema_type = "DataFrameModel" if s.source_class else "DataFrameSchema"
        lines.append(f"- **File:** `{s.file_path}`")
        lines.append(f"- **Type:** {schema_type}")
        if s.description:
            lines.append(f"- **Description:** {s.description}")
        lines.append(f"- **Coerce:** {s.coerce}")
        lines.append("")

        if s.columns:
            lines.append("### Columns")
            lines.append("")
            lines.append("| Name | Type | Nullable | Required | Description |")
            lines.append("|------|------|:--------:|:--------:|-------------|")
            for col in s.columns:
                desc = col.description or col.title or ""
                nullable = "yes" if col.nullable else "no"
                required = "yes" if col.required else "no"
                lines.append(
                    f"| `{col.name}` | `{col.dtype or '-'}` | {nullable} | {required} | {desc} |"
                )
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def to_html(schemas: list[SchemaMetadata]) -> str:
    sections = []
    for s in schemas:
        schema_type = "DataFrameModel" if s.source_class else "DataFrameSchema"
        desc_html = f"<p class='desc'>{s.description}</p>" if s.description else ""

        cols_html = ""
        if s.columns:
            rows = "".join(
                "<tr>"
                f"<td><code>{col.name}</code></td>"
                f"<td><code>{col.dtype or '-'}</code></td>"
                f"<td>{'yes' if col.nullable else 'no'}</td>"
                f"<td>{'yes' if col.required else 'no'}</td>"
                f"<td>{col.description or col.title or ''}</td>"
                "</tr>"
                for col in s.columns
            )
            cols_html = (
                "<h3>Columns</h3>"
                "<table><thead><tr>"
                "<th>Name</th><th>Type</th><th>Nullable</th><th>Required</th><th>Description</th>"
                "</tr></thead>"
                f"<tbody>{rows}</tbody></table>"
            )

        sections.append(
            f"<section>"
            f"<h2>{s.name}</h2>"
            f"<p class='meta'><code>{s.file_path}</code> &middot; {schema_type}</p>"
            f"{desc_html}{cols_html}"
            f"</section>"
        )

    body = "\n".join(sections)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Pandera Schema Documentation</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            max-width: 960px; margin: 0 auto; padding: 2rem; color: #24292f; }}
    h1 {{ margin-bottom: 2rem; }}
    section {{ border: 1px solid #d0d7de; border-radius: 6px;
               padding: 1.5rem; margin-bottom: 1.5rem; }}
    h2 {{ margin-top: 0; }}
    h3 {{ margin: 1rem 0 0.5rem; }}
    .meta {{ color: #636c76; font-size: 0.85rem; margin: 0 0 0.75rem; }}
    .desc {{ margin: 0.5rem 0; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 0.5rem; font-size: 0.875rem; }}
    th, td {{ padding: 0.45rem 0.6rem; border: 1px solid #d0d7de; text-align: left; }}
    th {{ background: #f6f8fa; font-weight: 600; }}
    code {{ background: #f6f8fa; padding: 0.15em 0.4em; border-radius: 3px; font-size: 0.875em; }}
  </style>
</head>
<body>
  <h1>Pandera Schema Documentation</h1>
  {body}
</body>
</html>"""
