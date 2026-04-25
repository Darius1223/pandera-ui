import json
from pathlib import Path
from unittest.mock import patch

import typer
from typer.testing import CliRunner

from pandera_ui.cli import cli_app

runner = CliRunner()
_app = typer.Typer()
_app.command()(cli_app)

FIXTURES = Path(__file__).parent / "fixtures"


def _parse_json(result) -> list:
    """Extract JSON array from CLI output (output also contains echo lines)."""
    out = result.output
    start = out.index('[')
    return json.loads(out[start:])


def test_json_output():
    result = runner.invoke(_app, [str(FIXTURES), "--json"])
    assert result.exit_code == 0
    data = _parse_json(result)
    assert isinstance(data, list)
    assert len(data) > 0
    assert "name" in data[0]
    assert "columns" in data[0]
    assert "metadata_source" in data[0]


def test_json_no_server_started():
    result = runner.invoke(_app, [str(FIXTURES), "--json"])
    assert "UI ready" not in result.output


def test_scan_echo_messages():
    result = runner.invoke(_app, [str(FIXTURES), "--json"])
    # "Found" is always printed; "Scanning" may be transient when rich is installed
    assert "Found" in result.output


def test_empty_dir_json(tmp_path):
    result = runner.invoke(_app, [str(tmp_path), "--json"])
    assert result.exit_code == 0
    out = result.output
    start = out.index('[')
    assert json.loads(out[start:]) == []


def test_json_schema_names():
    result = runner.invoke(_app, [str(FIXTURES), "--json"])
    names = {s["name"] for s in _parse_json(result)}
    assert "orders" in names
    assert "users" in names


def test_json_metadata_source_values():
    result = runner.invoke(_app, [str(FIXTURES), "--json"])
    sources = {s["metadata_source"] for s in _parse_json(result)}
    assert sources <= {"runtime", "ast"}


def test_server_mode_calls_uvicorn():
    """Without --json, uvicorn.run should be called with the app."""
    with patch("pandera_ui.cli.uvicorn") as mock_uv:
        result = runner.invoke(_app, [str(FIXTURES)])
    assert result.exit_code == 0
    assert "UI ready" in result.output
    mock_uv.run.assert_called_once()
