"""Documentation coverage calculator for Pandera schema metadata."""

from .models import CoverageReport, SchemaMetadata


def compute_coverage(schemas: list[SchemaMetadata]) -> CoverageReport:
    schema_count = len(schemas)
    schemas_with_title = sum(1 for s in schemas if s.title)
    schemas_with_description = sum(1 for s in schemas if s.description)

    all_columns = [col for s in schemas for col in s.columns]
    column_count = len(all_columns)
    columns_with_title = sum(1 for c in all_columns if c.title)
    columns_with_description = sum(1 for c in all_columns if c.description)

    def pct(num: int, denom: int) -> float:
        return round(num / denom * 100, 1) if denom else 0.0

    return CoverageReport(
        schema_count=schema_count,
        schemas_with_title=schemas_with_title,
        schemas_with_description=schemas_with_description,
        column_count=column_count,
        columns_with_title=columns_with_title,
        columns_with_description=columns_with_description,
        schema_title_pct=pct(schemas_with_title, schema_count),
        schema_description_pct=pct(schemas_with_description, schema_count),
        column_title_pct=pct(columns_with_title, column_count),
        column_description_pct=pct(columns_with_description, column_count),
    )


def format_coverage(report: CoverageReport) -> str:
    lines = [
        "Documentation Coverage",
        "======================",
        f"Schemas : {report.schema_count}",
        f"  title       : {report.schemas_with_title}/{report.schema_count}"
        f" ({report.schema_title_pct}%)",
        f"  description : {report.schemas_with_description}/{report.schema_count}"
        f" ({report.schema_description_pct}%)",
        f"Columns : {report.column_count}",
        f"  title       : {report.columns_with_title}/{report.column_count}"
        f" ({report.column_title_pct}%)",
        f"  description : {report.columns_with_description}/{report.column_count}"
        f" ({report.column_description_pct}%)",
    ]
    return "\n".join(lines)
