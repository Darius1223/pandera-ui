from pathlib import Path

import typer
from fastapi.testclient import TestClient
from typer.testing import CliRunner

import pandera_ui.server as srv
from pandera_ui._coverage import compute_coverage, format_coverage
from pandera_ui.cli import cli_app
from pandera_ui.models import CoverageReport, SchemaMetadata
from pandera_ui.server import app

runner = CliRunner()
_app = typer.Typer()
_app.command()(cli_app)

client = TestClient(app)
FIXTURES = Path(__file__).parent / "fixtures"


def _make_schema(title=None, description=None, col_title=None, col_description=None):
    from pandera_ui.models import ColumnMetadata

    col = ColumnMetadata(
        name="x",
        title=col_title,
        description=col_description,
    )
    return SchemaMetadata(
        name="s",
        var_name="s",
        file_path="f.py",
        title=title,
        description=description,
        columns=[col],
    )


class TestComputeCoverage:
    def test_empty(self):
        report = compute_coverage([])
        assert report.schema_count == 0
        assert report.schema_title_pct == 0.0
        assert report.column_count == 0

    def test_all_undocumented(self):
        schema = _make_schema()
        report = compute_coverage([schema])
        assert report.schemas_with_title == 0
        assert report.schemas_with_description == 0
        assert report.columns_with_title == 0
        assert report.columns_with_description == 0
        assert report.schema_title_pct == 0.0

    def test_all_documented(self):
        schema = _make_schema(
            title="T", description="D", col_title="CT", col_description="CD"
        )
        report = compute_coverage([schema])
        assert report.schemas_with_title == 1
        assert report.schemas_with_description == 1
        assert report.columns_with_title == 1
        assert report.columns_with_description == 1
        assert report.schema_title_pct == 100.0
        assert report.column_description_pct == 100.0

    def test_partial(self):
        s1 = _make_schema(title="T")
        s2 = _make_schema()
        report = compute_coverage([s1, s2])
        assert report.schema_title_pct == 50.0
        assert report.schemas_with_title == 1

    def test_returns_coverage_report_type(self):
        report = compute_coverage([])
        assert isinstance(report, CoverageReport)


class TestFormatCoverage:
    def test_contains_headings(self):
        report = compute_coverage([_make_schema()])
        text = format_coverage(report)
        assert "Schemas" in text
        assert "Columns" in text

    def test_contains_percentages(self):
        report = compute_coverage([_make_schema(title="T")])
        text = format_coverage(report)
        assert "100.0%" in text or "0.0%" in text


class TestCoverageApi:
    def setup_method(self):
        srv._schemas = []

    def teardown_method(self):
        srv._schemas = []

    def test_coverage_empty(self):
        r = client.get("/api/coverage")
        assert r.status_code == 200
        data = r.json()
        assert data["schema_count"] == 0

    def test_coverage_after_load(self):
        srv.load_schemas(str(FIXTURES))
        r = client.get("/api/coverage")
        assert r.status_code == 200
        data = r.json()
        assert data["schema_count"] > 0
        assert "schema_title_pct" in data
        assert "column_description_pct" in data

    def test_coverage_structure(self):
        srv.load_schemas(str(FIXTURES))
        data = client.get("/api/coverage").json()
        for key in (
            "schema_count", "schemas_with_title", "schemas_with_description",
            "column_count", "columns_with_title", "columns_with_description",
            "schema_title_pct", "schema_description_pct",
            "column_title_pct", "column_description_pct",
        ):
            assert key in data, f"missing key: {key}"


class TestCoverageCli:
    def test_coverage_exit_code(self):
        result = runner.invoke(_app, [str(FIXTURES), "--coverage"])
        assert result.exit_code == 0

    def test_coverage_output(self):
        result = runner.invoke(_app, [str(FIXTURES), "--coverage"])
        assert "Schemas" in result.output
        assert "Columns" in result.output

    def test_coverage_no_server(self):
        result = runner.invoke(_app, [str(FIXTURES), "--coverage"])
        assert "UI ready" not in result.output
