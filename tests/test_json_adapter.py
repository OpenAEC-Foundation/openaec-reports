"""Tests voor data/json_adapter.py — JSON naar rapport data conversie."""

from __future__ import annotations

import json

import pytest

from openaec_reports.data.json_adapter import JsonAdapter


class TestJsonAdapterInit:
    def test_from_file(self, tmp_path):
        """Adapter laadt data uit JSON bestand."""
        data = {"project": "Test", "template": "structural", "sections": []}
        f = tmp_path / "test.json"
        f.write_text(json.dumps(data))
        adapter = JsonAdapter(str(f))
        assert adapter.data["project"] == "Test"

    def test_from_none(self):
        """Adapter zonder pad heeft lege data."""
        adapter = JsonAdapter()
        assert adapter.data == {}

    def test_nonexistent_file_raises(self):
        """Niet-bestaand bestand geeft fout."""
        with pytest.raises(FileNotFoundError):
            JsonAdapter("/nonexistent.json")


class TestJsonAdapterLoad:
    def test_load_valid_json(self, tmp_path):
        """load() retourneert data dict."""
        data = {"project": "LoadTest", "sections": []}
        f = tmp_path / "load.json"
        f.write_text(json.dumps(data))
        adapter = JsonAdapter()
        result = adapter.load(f)
        assert result["project"] == "LoadTest"
        assert adapter.data["project"] == "LoadTest"

    def test_load_string(self):
        """load_string() parst JSON string."""
        adapter = JsonAdapter()
        result = adapter.load_string('{"project": "StringTest"}')
        assert result["project"] == "StringTest"
        assert adapter.data["project"] == "StringTest"

    def test_load_string_invalid_raises(self):
        """load_string() met ongeldige JSON gooit error."""
        adapter = JsonAdapter()
        with pytest.raises(json.JSONDecodeError):
            adapter.load_string("{corrupt")


class TestJsonAdapterProjectInfo:
    def test_get_project_info(self, tmp_path):
        """get_project_info() retourneert projectvelden."""
        data = {
            "project": "Mijn Project",
            "project_number": "2026-042",
            "client": "Klant BV",
            "author": "Ing. Test",
            "report_type": "structural",
            "subtitle": "Berekening",
        }
        f = tmp_path / "info.json"
        f.write_text(json.dumps(data))
        adapter = JsonAdapter(str(f))
        info = adapter.get_project_info()

        assert info["project"] == "Mijn Project"
        assert info["project_number"] == "2026-042"
        assert info["client"] == "Klant BV"
        assert info["author"] == "Ing. Test"

    def test_get_project_info_defaults(self):
        """get_project_info() met ontbrekende velden geeft defaults."""
        adapter = JsonAdapter()
        adapter.data = {"project": "Minimal"}
        info = adapter.get_project_info()
        assert info["project"] == "Minimal"
        assert info["author"] == "3BM Bouwkunde"  # default

    def test_get_sections_empty(self):
        """get_sections() met lege data retourneert lege lijst."""
        adapter = JsonAdapter()
        assert adapter.get_sections() == []

    def test_get_sections_with_data(self, tmp_path):
        """get_sections() retourneert secties uit data."""
        data = {
            "sections": [
                {"title": "Sectie 1", "content": []},
                {"title": "Sectie 2", "content": []},
            ]
        }
        f = tmp_path / "sections.json"
        f.write_text(json.dumps(data))
        adapter = JsonAdapter(str(f))
        sections = adapter.get_sections()
        assert len(sections) == 2
        assert sections[0]["title"] == "Sectie 1"


class TestJsonAdapterValidation:
    def test_validate_returns_list(self, tmp_path):
        """validate() retourneert altijd een lijst."""
        data = {"project": "Test", "template": "t", "sections": []}
        f = tmp_path / "valid.json"
        f.write_text(json.dumps(data))
        adapter = JsonAdapter(str(f))
        errors = adapter.validate()
        assert isinstance(errors, list)

    def test_validate_empty_data(self):
        """validate() met lege data geeft validatie errors."""
        adapter = JsonAdapter()
        errors = adapter.validate()
        assert isinstance(errors, list)
        # Lege data zou minstens 1 fout moeten geven
        assert len(errors) > 0

    def test_validate_basic_fallback(self):
        """_validate_basic() checkt verplichte velden."""
        adapter = JsonAdapter()
        adapter.data = {}
        errors = adapter._validate_basic()
        assert any("project" in e.lower() for e in errors)

    def test_validate_basic_passes_with_required(self):
        """_validate_basic() slaagt met verplichte velden."""
        adapter = JsonAdapter()
        adapter.data = {"project": "Test", "template": "structural"}
        errors = adapter._validate_basic()
        assert len(errors) == 0
