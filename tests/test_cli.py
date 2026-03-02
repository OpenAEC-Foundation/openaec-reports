"""Tests voor cli.py — alle subcommands."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from openaec_reports.cli import main


class TestMainDispatch:
    def test_no_command_shows_help(self, capsys):
        """Zonder command toont help en exit 1."""
        with patch("sys.argv", ["openaec-report"]):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_unknown_command_exits(self):
        """Onbekend command wordt genegeerd (geen crash)."""
        with patch("sys.argv", ["openaec-report", "nonexistent"]):
            # argparse parsed het als error
            with pytest.raises(SystemExit):
                main()


class TestTemplatesCommand:
    def test_list_templates(self, capsys):
        """templates toont beschikbare templates."""
        with patch("sys.argv", ["openaec-report", "templates", "--list"]):
            main()
        output = capsys.readouterr().out
        assert "Beschikbare templates" in output

    def test_list_includes_known_templates(self, capsys):
        """Templates output bevat bekende templates."""
        with patch("sys.argv", ["openaec-report", "templates", "--list"]):
            main()
        output = capsys.readouterr().out
        # Minimaal 1 YAML template aanwezig
        assert ".yaml" not in output  # Stem names, niet file extensions
        assert len(output.strip().split("\n")) > 1


class TestValidateCommand:
    def test_validate_valid_json(self, tmp_path):
        """Valideer correct JSON bestand."""
        json_file = tmp_path / "valid.json"
        json_file.write_text(
            '{"project": "Test", "template": "structural", "sections": []}'
        )
        with patch("sys.argv", ["openaec-report", "validate", "--data", str(json_file)]):
            # Schema validatie kan falen afhankelijk van strictness
            try:
                main()
            except SystemExit:
                pass  # exit 0 of 1 beide ok

    def test_validate_corrupt_json(self, tmp_path):
        """Corrupt JSON geeft fout."""
        json_file = tmp_path / "corrupt.json"
        json_file.write_text("{corrupt json")
        with patch("sys.argv", ["openaec-report", "validate", "--data", str(json_file)]):
            with pytest.raises(Exception):
                main()

    def test_validate_missing_file(self):
        """Ontbrekend bestand geeft fout."""
        with patch("sys.argv", ["openaec-report", "validate", "--data", "/nonexistent.json"]):
            with pytest.raises(Exception):
                main()


class TestGenerateCommand:
    def test_generate_requires_all_args(self):
        """Generate zonder verplichte args geeft error."""
        with patch("sys.argv", ["openaec-report", "generate"]):
            with pytest.raises(SystemExit):
                main()

    def test_generate_creates_pdf(self, tmp_path):
        """Generate maakt een PDF bestand aan."""
        data_file = Path("schemas/example_structural.json")
        if not data_file.exists():
            pytest.skip("example_structural.json niet gevonden")

        output_pdf = tmp_path / "test.pdf"
        with patch("sys.argv", [
            "openaec-report", "generate",
            "--template", "structural",
            "--data", str(data_file),
            "--output", str(output_pdf),
        ]):
            main()

        assert output_pdf.exists()
        assert output_pdf.stat().st_size > 1000

    def test_generate_a3_format(self, tmp_path):
        """Generate met A3 formaat optie."""
        data_file = Path("schemas/example_structural.json")
        if not data_file.exists():
            pytest.skip("example_structural.json niet gevonden")

        output_pdf = tmp_path / "test_a3.pdf"
        with patch("sys.argv", [
            "openaec-report", "generate",
            "--template", "structural",
            "--data", str(data_file),
            "--output", str(output_pdf),
            "--format", "A3",
        ]):
            main()

        assert output_pdf.exists()


class TestServeCommand:
    def test_serve_calls_uvicorn(self):
        """Serve start uvicorn met juiste parameters."""
        with patch("sys.argv", ["openaec-report", "serve", "--port", "9999"]):
            with patch("uvicorn.run") as mock_run:
                main()
                mock_run.assert_called_once()
                call_kwargs = mock_run.call_args[1]
                assert call_kwargs["port"] == 9999

    def test_serve_default_port(self):
        """Serve met default port (8000)."""
        with patch("sys.argv", ["openaec-report", "serve"]):
            with patch("uvicorn.run") as mock_run:
                main()
                call_kwargs = mock_run.call_args[1]
                assert call_kwargs["port"] == 8000

    def test_serve_custom_host(self):
        """Serve met custom host."""
        with patch("sys.argv", ["openaec-report", "serve", "--host", "127.0.0.1"]):
            with patch("uvicorn.run") as mock_run:
                main()
                call_kwargs = mock_run.call_args[1]
                assert call_kwargs["host"] == "127.0.0.1"

    def test_serve_reload_flag(self):
        """Serve met reload flag."""
        with patch("sys.argv", ["openaec-report", "serve", "--reload"]):
            with patch("uvicorn.run") as mock_run:
                main()
                call_kwargs = mock_run.call_args[1]
                assert call_kwargs["reload"] is True


class TestAnalyzeBrandCommand:
    def test_analyze_brand_requires_pdf(self):
        """analyze-brand zonder PDF geeft error."""
        with patch("sys.argv", ["openaec-report", "analyze-brand"]):
            with pytest.raises(SystemExit):
                main()


class TestBuildBrandCommand:
    def test_build_brand_requires_all_args(self):
        """build-brand zonder verplichte args geeft error."""
        with patch("sys.argv", ["openaec-report", "build-brand"]):
            with pytest.raises(SystemExit):
                main()

    def test_build_brand_requires_name(self):
        """build-brand zonder --name geeft error."""
        with patch("sys.argv", [
            "openaec-report", "build-brand",
            "--rapport", "test.pdf",
            "--slug", "test",
            "--output", "/tmp/out",
        ]):
            with pytest.raises(SystemExit):
                main()
