from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from pandera_ui._export import to_html, to_markdown
from pandera_ui.cli import cli_app
from pandera_ui.scanner import scan_project

runner = CliRunner()
_app = typer.Typer()
_app.command()(cli_app)

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(scope="module")
def schemas():
    return scan_project(FIXTURES)


class TestToMarkdown:
    def test_returns_string(self, schemas):
        out = to_markdown(schemas)
        assert isinstance(out, str)

    def test_contains_header(self, schemas):
        out = to_markdown(schemas)
        assert "# Pandera Schema Documentation" in out

    def test_contains_schema_names(self, schemas):
        out = to_markdown(schemas)
        assert "## orders" in out
        assert "## products" in out

    def test_contains_column_table(self, schemas):
        out = to_markdown(schemas)
        assert "| Name |" in out
        assert "order_id" in out

    def test_contains_file_path(self, schemas):
        out = to_markdown(schemas)
        assert "dataframe_schemas.py" in out

    def test_empty_schemas(self):
        out = to_markdown([])
        assert "# Pandera Schema Documentation" in out


class TestToHtml:
    def test_returns_html(self, schemas):
        out = to_html(schemas)
        assert out.startswith("<!DOCTYPE html>")

    def test_contains_schema_names(self, schemas):
        out = to_html(schemas)
        assert "orders" in out
        assert "products" in out

    def test_contains_table(self, schemas):
        out = to_html(schemas)
        assert "<table>" in out
        assert "order_id" in out

    def test_empty_schemas(self):
        out = to_html([])
        assert "<!DOCTYPE html>" in out


class TestExportCli:
    def test_export_markdown_exit_code(self):
        result = runner.invoke(_app, [str(FIXTURES), "--export", "markdown"])
        assert result.exit_code == 0

    def test_export_markdown_output(self):
        result = runner.invoke(_app, [str(FIXTURES), "--export", "markdown"])
        assert "# Pandera Schema Documentation" in result.output
        assert "orders" in result.output

    def test_export_html_exit_code(self):
        result = runner.invoke(_app, [str(FIXTURES), "--export", "html"])
        assert result.exit_code == 0

    def test_export_html_output(self):
        result = runner.invoke(_app, [str(FIXTURES), "--export", "html"])
        assert "<!DOCTYPE html>" in result.output
        assert "orders" in result.output

    def test_export_no_server(self):
        result = runner.invoke(_app, [str(FIXTURES), "--export", "markdown"])
        assert "UI ready" not in result.output

    def test_export_unknown_format(self):
        result = runner.invoke(_app, [str(FIXTURES), "--export", "pdf"])
        assert result.exit_code == 1
