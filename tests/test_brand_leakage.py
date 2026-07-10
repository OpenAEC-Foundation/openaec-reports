"""Anti-lekkage-test — de kern van Fase 3 (2026-07-10).

Vóór deze refactor viel ``renderer_v2.ContentRenderer.calculation()``/
``check()`` stil terug op Python-hardcoded 3BM-kleuren
(``#40124A``/``#38BDA0``/``#56B49B``/``#45243D``) zodra een tenant-
template geen ``calculation``/``check``-blok definieerde. Dat gebeurde
o.a. bij KBA (zie orchestrator-sessie 2026-07-10, "699 paarse pixels" —
géén enkele test ving dat). Deze test bouwt een minimale, volledig
op-zichzelf-staande tenant zonder ``calculation``/``check``-stijl, rendert
een rapport met precies die blok-typen, en asserteert dat er NERGENS een
3BM-hex in de output-PDF voorkomt.

Verificatie dat deze test daadwerkelijk de regressie vangt: draai hem tegen
commit 894cef2 (vóór Fase 3) — hij faalt daar (de hardcoded defaults
render de 3BM-hexes). Zie orchestrator-rapportage voor het bewijs
(``git stash`` + her-run).
"""

from __future__ import annotations

import collections

import pytest

fitz = pytest.importorskip("fitz", reason="pymupdf niet geinstalleerd")
np = pytest.importorskip("numpy", reason="numpy niet geinstalleerd")

import yaml  # noqa: E402

from openaec_reports.core.renderer_v2 import ReportGeneratorV2  # noqa: E402
from openaec_reports.core.tenant import TenantConfig  # noqa: E402

# De 4 hexes die deze refactor uitroeit als Python-hardcoded default —
# zie de opdracht-context: "grep -n '"#40124A"\\|"#38BDA0"\\|"#56B49B"\\|
# "#45243D"' src/openaec_reports/core/renderer_v2.py".
FORBIDDEN_3BM_HEXES = {"#40124A", "#38BDA0", "#56B49B", "#45243D"}

# Kleuren van de minimale test-tenant — bewust NIETS wat op 3BM lijkt,
# zodat een 3BM-hex in de output ondubbelzinnig een lekkage is en niet
# toevallig samenvalt met de tenant's eigen palet.
MINIMAL_BRAND_YAML = """
brand:
  name: "Minimal Leakage Test Tenant"
  slug: "minimal-leakage-test"
colors:
  primary: "#123456"
  secondary: "#234567"
  text: "#111111"
  text_accent: "#345678"
  text_light: "#666666"
  surface: "#EEEEEE"
  paper: "#FFFFFF"
  separator: "#DDDDDD"
  warning: "#AA2222"
fonts:
  heading: LiberationSans-Bold
  body: LiberationSans
logos: {}
contact: {}
header:
  height: 0
  elements: []
footer:
  height: 0
  elements: []
"""

# Bevat BEWUST GEEN "calculation" of "check" blok — dat is precies het
# scenario dat de bug triggerde.
MINIMAL_CONTENT_STYLES_YAML = """
blocks:
  heading_1:
    number: {x: 90, font: LiberationSans-Bold, size: 18, color: "$colors.primary"}
    title: {x: 108, font: LiberationSans-Bold, size: 18, color: "$colors.primary"}
    spacing_after: 20.0
  paragraph:
    x: 90
    font: LiberationSans
    size: 10
    color: "$colors.text"
    line_height: 12.0
    max_width: 400.0
    spacing_before: 8.0
    spacing_after: 8.0
page_number:
  x: 500
  y_td: 800
  font: LiberationSans
  size: 9
  color: "$colors.primary"
"""

MINIMAL_STANDAARD_YAML = """
margins:
  top: 74.9
"""


@pytest.fixture()
def minimal_tenant_dir(tmp_path):
    """Bouwt een volledig op-zichzelf-staande tenant zonder calculation/
    check-stijl, geen stationery, geen custom fonts — alleen wat nodig is
    om ``ReportGeneratorV2.generate()`` zonder crash te doorlopen."""
    tenant_dir = tmp_path / "minimal-leakage-test"
    (tenant_dir / "templates").mkdir(parents=True)
    (tenant_dir / "stationery").mkdir(parents=True)

    (tenant_dir / "brand.yaml").write_text(MINIMAL_BRAND_YAML, encoding="utf-8")
    (tenant_dir / "templates" / "content_styles.yaml").write_text(
        MINIMAL_CONTENT_STYLES_YAML, encoding="utf-8"
    )
    (tenant_dir / "templates" / "standaard.yaml").write_text(
        MINIMAL_STANDAARD_YAML, encoding="utf-8"
    )
    return tenant_dir


def _render(tenant_dir, tmp_path):
    tenant_config = TenantConfig(tenant_dir)
    gen = ReportGeneratorV2(tenant_config=tenant_config)
    data = {
        "template": "standaard",
        "project": "Lekkagetest",
        "report_type": "Testrapport",
        "cover": {"enabled": False},
        "colofon": {"enabled": False},
        "toc": {"enabled": False},
        "sections": [
            {
                "level": 1, "number": "1", "title": "Berekening",
                "content": [
                    {
                        "type": "calculation",
                        "title": "Voorbeeldberekening",
                        "formula": "F = m * a",
                        "substitution": "F = 10 * 9.81",
                        "result": "98.1",
                        "unit": "N",
                        "reference": "NEN-EN 1990",
                    },
                    {
                        "type": "check",
                        "description": "Toetsing",
                        "required_value": "100 N",
                        "calculated_value": "98.1 N",
                        "unity_check": 0.981,
                        "result": "VOLDOET",
                    },
                ],
            }
        ],
    }
    out_pdf = tmp_path / "leakage_test.pdf"
    gen.generate(data, tenant_dir / "stationery", out_pdf)
    return out_pdf


def _find_forbidden_hexes(pdf_path) -> dict[str, int]:
    """Rasterize elke pagina en tel voorkomens van de verboden 3BM-hexes
    onder de "donkere pixels"-mask (zelfde techniek als de opdracht-
    context voorschrijft)."""
    found: collections.Counter[str] = collections.Counter()
    doc = fitz.open(str(pdf_path))
    try:
        for page in doc:
            pix = page.get_pixmap(dpi=100)
            arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
                pix.height, pix.width, pix.n
            )
            if pix.n == 4:
                arr = arr[:, :, :3]
            mask = arr.sum(axis=2) < 500
            for rgb in arr[mask]:
                hex_val = "#{:02X}{:02X}{:02X}".format(*rgb)
                if hex_val in FORBIDDEN_3BM_HEXES:
                    found[hex_val] += 1
    finally:
        doc.close()
    return dict(found)


class TestNoBrandLeakage:
    """De test die vóór Fase 3 zou hebben gefaald op commit 894cef2."""

    def test_minimal_tenant_calculation_check_render_without_crash(
        self, minimal_tenant_dir, tmp_path
    ):
        # Vóór Fase 3: renderer_v2.calculation()/check() gebruikten alleen
        # ".get(key, '#hardcoded')" — dat "werkte" altijd (geen crash),
        # dus deze regel documenteert vooral de verwachting.
        out_pdf = _render(minimal_tenant_dir, tmp_path)
        assert out_pdf.exists()

    def test_no_3bm_hex_in_output(self, minimal_tenant_dir, tmp_path):
        out_pdf = _render(minimal_tenant_dir, tmp_path)
        found = _find_forbidden_hexes(out_pdf)
        assert found == {}, (
            f"3BM-merkkleur(en) gevonden in output van een tenant die "
            f"'calculation'/'check' niet definieert: {found}. Dit is "
            "precies de brand-lekkage die Fase 3 uitroeit."
        )

    def test_missing_semantic_color_fails_loud(self, tmp_path):
        """Als de tenant zelf ook geen 'surface' (of andere benodigde
        semantische kleur) heeft, moet de render met een duidelijke
        ValueError falen — GEEN stille terugval naar een hardcoded kleur."""
        tenant_dir = tmp_path / "incomplete-tenant"
        (tenant_dir / "templates").mkdir(parents=True)
        (tenant_dir / "stationery").mkdir(parents=True)

        incomplete_brand = yaml.safe_load(MINIMAL_BRAND_YAML)
        del incomplete_brand["colors"]["surface"]
        (tenant_dir / "brand.yaml").write_text(
            yaml.safe_dump(incomplete_brand), encoding="utf-8"
        )
        (tenant_dir / "templates" / "content_styles.yaml").write_text(
            MINIMAL_CONTENT_STYLES_YAML, encoding="utf-8"
        )
        (tenant_dir / "templates" / "standaard.yaml").write_text(
            MINIMAL_STANDAARD_YAML, encoding="utf-8"
        )

        with pytest.raises(ValueError, match="Ontbrekende kleur"):
            _render(tenant_dir, tmp_path)
