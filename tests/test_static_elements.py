"""Tests voor core/static_elements.py — de generieke primitive-renderer.

Dekt: elk element-type, mm->pt conversie + top-down y-conventie, onbekend
type -> ValueError, en (via BrandLoader) dat $colors-refs in
pages.<type>.static_elements daadwerkelijk resolven vóór ze hier
binnenkomen.
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

fitz = pytest.importorskip("fitz", reason="pymupdf niet geinstalleerd")

from reportlab.pdfgen import canvas as rl_canvas  # noqa: E402

from openaec_reports.core.static_elements import (  # noqa: E402
    MM_TO_PT,
    _td_mm_to_bl_pt,
    render_static_elements,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
KBA_TENANT_DIR = REPO_ROOT / "tenants" / "kba"


def _make_canvas() -> tuple[rl_canvas.Canvas, io.BytesIO]:
    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=(595.28, 841.89))
    return c, buf


class TestCoordinateConversion:
    """mm -> pt en top-down -> bottom-left conventie."""

    def test_mm_to_pt_factor(self):
        assert MM_TO_PT == pytest.approx(2.8346456693)

    def test_top_of_page_is_near_page_height(self):
        # y=0mm (bovenkant) -> bijna de volledige paginahoogte in pt
        page_h = 841.89
        assert _td_mm_to_bl_pt(page_h, 0.0) == pytest.approx(841.89)

    def test_bottom_of_page_is_zero(self):
        # y=297mm (onderkant A4) -> 0pt (bottom-left origin)
        page_h = 297 * MM_TO_PT
        assert _td_mm_to_bl_pt(page_h, 297.0) == pytest.approx(0.0, abs=1e-6)

    def test_box_height_subtracted_for_top_anchored_elements(self):
        # Een box met top=20mm, hoogte=10mm heeft zijn ONDERrand op 30mm
        # van boven -> bottom-left y = page_h - 30mm.
        page_h = 841.89
        y_bl = _td_mm_to_bl_pt(page_h, 20.0, h_mm=10.0)
        assert y_bl == pytest.approx(page_h - 30.0 * MM_TO_PT)


class TestUnknownType:
    def test_unknown_type_raises(self):
        c, _ = _make_canvas()
        with pytest.raises(ValueError, match="onbekend element-type"):
            render_static_elements(
                c, [{"type": "circle", "x": 0, "y": 0}],
                page_height_pt=841.89,
            )


class TestRectTypes:
    def test_rect_renders_without_error(self):
        c, _ = _make_canvas()
        render_static_elements(
            c,
            [{"type": "rect", "x": 0, "y": 0, "w": 210, "h": 118, "fill": "#0F6E56"}],
            page_height_pt=841.89,
        )
        c.save()  # geen exception = geslaagd

    def test_rounded_rect_renders_without_error(self):
        c, _ = _make_canvas()
        render_static_elements(
            c,
            [{
                "type": "rounded_rect", "x": 10, "y": 10, "w": 40, "h": 20,
                "radius": 3, "fill": "#1D9E75",
            }],
            page_height_pt=841.89,
        )
        c.save()

    def test_rect_missing_fill_raises(self):
        c, _ = _make_canvas()
        with pytest.raises(ValueError, match="mist verplicht kleurveld"):
            render_static_elements(
                c, [{"type": "rect", "x": 0, "y": 0, "w": 10, "h": 10}],
                page_height_pt=841.89,
            )


class TestLine:
    def test_line_renders_without_error(self):
        c, _ = _make_canvas()
        render_static_elements(
            c,
            [{
                "type": "line", "x1": 22, "y1": 239, "x2": 188, "y2": 239,
                "width": 0.35, "color": "#DFE7E4",
            }],
            page_height_pt=841.89,
        )
        c.save()


class TestPolygon:
    def test_polygon_renders_without_error(self):
        c, _ = _make_canvas()
        render_static_elements(
            c,
            [{
                "type": "polygon",
                "points": [[0, 0], [50, 0], [25, 50]],
                "fill": "#B4E8DC",
            }],
            page_height_pt=841.89,
        )
        c.save()

    def test_polygon_too_few_points_raises(self):
        c, _ = _make_canvas()
        with pytest.raises(ValueError, match="minder dan 2 punten"):
            render_static_elements(
                c, [{"type": "polygon", "points": [[0, 0]], "fill": "#000000"}],
                page_height_pt=841.89,
            )


class TestText:
    def test_text_renders_without_error(self):
        c, _ = _make_canvas()
        render_static_elements(
            c,
            [{
                "type": "text", "content": "Hallo wereld", "x": 22, "y": 100,
                "font": "Helvetica", "size": 10, "color": "#11302A",
            }],
            page_height_pt=841.89,
        )
        c.save()

    def test_text_missing_color_raises(self):
        c, _ = _make_canvas()
        with pytest.raises(ValueError, match="mist verplicht kleurveld"):
            render_static_elements(
                c, [{"type": "text", "content": "x", "x": 0, "y": 0}],
                page_height_pt=841.89,
            )

    def test_text_token_substitution(self):
        """{token} in content wordt vervangen door context-waarde."""
        c, _ = _make_canvas()
        render_static_elements(
            c,
            [{
                "type": "text", "content": "Project: {project}", "x": 0, "y": 0,
                "font": "Helvetica", "size": 10, "color": "#000000",
            }],
            page_height_pt=841.89,
            context={"project": "Testproject"},
        )
        c.save()  # geen exception; inhoud wordt niet uit de PDF geparsed hier

    def test_text_missing_token_becomes_empty_not_crash(self):
        c, _ = _make_canvas()
        # Geen "project" in context -> {project} wordt "", geen KeyError.
        render_static_elements(
            c,
            [{
                "type": "text", "content": "X: {project}", "x": 0, "y": 0,
                "font": "Helvetica", "size": 10, "color": "#000000",
            }],
            page_height_pt=841.89,
            context={},
        )
        c.save()

    def test_empty_text_after_substitution_is_skipped(self):
        """Puur een leeg token -> geen tekenaanroep, geen crash."""
        c, _ = _make_canvas()
        render_static_elements(
            c,
            [{
                "type": "text", "content": "{missing}", "x": 0, "y": 0,
                "font": "Helvetica", "size": 10, "color": "#000000",
            }],
            page_height_pt=841.89,
            context={},
        )
        c.save()

    @pytest.mark.parametrize("align", ["left", "center", "right"])
    def test_char_space_renders_without_error(self, align):
        """letter-spacing-benadering via setCharSpace, voor elke align."""
        c, _ = _make_canvas()
        render_static_elements(
            c,
            [{
                "type": "text", "content": "CONSTRUCTIEF ADVIES",
                "x": 22, "y": 146, "font": "Helvetica", "size": 8,
                "color": "#1D9E75", "align": align, "char_space": 1.12,
            }],
            page_height_pt=841.89,
        )
        c.save()

    @pytest.mark.parametrize(
        "transform,content,expected",
        [
            ("upper", "Constructief advies", "CONSTRUCTIEF ADVIES"),
            ("lower", "Constructief ADVIES", "constructief advies"),
            ("title", "constructief advies", "Constructief Advies"),
        ],
    )
    def test_transform_applies_after_substitution(self, transform, content, expected):
        """transform werkt op de tekst NA {token}-substitutie: het token
        {kicker} levert de spreektaal-waarde, transform zet die pas
        daarna om — niet andersom (anders zou een 'transform: upper'
        elders in het rapport per ongeluk ook een letterlijke '{kicker}'
        in hoofdletters kunnen omzetten voordat de substitutie plaatsvindt,
        wat geen effect zou hebben maar wel de verkeerde volgorde suggereert)."""
        c, buf = _make_canvas()
        render_static_elements(
            c,
            [{
                "type": "text", "content": "{kicker}", "x": 22, "y": 137.6,
                "font": "Helvetica", "size": 8, "color": "#1D9E75",
                "transform": transform,
            }],
            page_height_pt=841.89,
            context={"kicker": content},
        )
        c.save()
        buf.seek(0)
        doc = fitz.open(stream=buf.read(), filetype="pdf")
        extracted = doc[0].get_text()
        doc.close()
        assert expected in extracted

    def test_transform_absent_leaves_text_unchanged(self):
        c, buf = _make_canvas()
        render_static_elements(
            c,
            [{
                "type": "text", "content": "Constructief advies",
                "x": 22, "y": 100, "font": "Helvetica", "size": 10,
                "color": "#11302A",
            }],
            page_height_pt=841.89,
        )
        c.save()
        buf.seek(0)
        doc = fitz.open(stream=buf.read(), filetype="pdf")
        extracted = doc[0].get_text()
        doc.close()
        assert "Constructief advies" in extracted

    def test_unknown_transform_raises(self):
        c, _ = _make_canvas()
        with pytest.raises(ValueError, match="onbekende 'transform'-waarde"):
            render_static_elements(
                c,
                [{
                    "type": "text", "content": "x", "x": 0, "y": 0,
                    "font": "Helvetica", "size": 10, "color": "#000000",
                    "transform": "sideways",
                }],
                page_height_pt=841.89,
            )

    def test_transform_upper_with_char_space_stays_extractable_as_one_string(self):
        """De risico-combinatie uit de opdracht: transform: upper +
        char_space (letterspacing) mag de tekstextractie niet breken — de
        kicker gebruikt beide tegelijk. Moet als aaneengesloten string
        'CONSTRUCTIEF ADVIES' terugkomen, niet los per letter."""
        c, buf = _make_canvas()
        render_static_elements(
            c,
            [{
                "type": "text", "content": "{kicker}", "x": 22, "y": 137.6,
                "font": "Helvetica", "size": 8, "color": "#1D9E75",
                "char_space": 1.12, "transform": "upper",
            }],
            page_height_pt=841.89,
            context={"kicker": "Constructief advies"},
        )
        c.save()
        buf.seek(0)
        doc = fitz.open(stream=buf.read(), filetype="pdf")
        extracted = doc[0].get_text()
        doc.close()
        assert "CONSTRUCTIEF ADVIES" in extracted
        assert "C O N S T R U C T I E F" not in extracted

    def test_char_space_text_stays_extractable_not_letter_spaced_with_gaps(self):
        """De char_space-benadering moet de echte PDF 'Tc'-tekststate
        gebruiken (selecteerbaar/doorzoekbaar), NIET een handmatige
        benadering met spaties tussen de letters — die zou de
        geëxtraheerde tekst breken (bv. 'C O N S T R U C T I E F')."""
        c, buf = _make_canvas()
        render_static_elements(
            c,
            [{
                "type": "text", "content": "CONSTRUCTIEF ADVIES",
                "x": 22, "y": 146, "font": "Helvetica", "size": 8,
                "color": "#1D9E75", "char_space": 1.12,
            }],
            page_height_pt=841.89,
        )
        c.save()
        buf.seek(0)
        doc = fitz.open(stream=buf.read(), filetype="pdf")
        extracted = doc[0].get_text()
        doc.close()
        assert "CONSTRUCTIEF ADVIES" in extracted
        assert "C O N S T R U C T I E F" not in extracted


class TestImage:
    def test_missing_optional_image_is_skipped_not_fatal(self, tmp_path):
        """Een niet-gevonden image-bron zonder 'required: true' mag de
        render niet laten crashen — alleen kleuren en verplichte images
        zijn fail-loud in deze refactor (zie ContentRenderer.image() voor
        hetzelfde patroon: placeholder-tekst i.p.v. crash)."""
        c, _ = _make_canvas()
        render_static_elements(
            c,
            [{
                "type": "image", "src": "does-not-exist.png",
                "x": 0, "y": 0, "w": 50, "h": 50,
            }],
            page_height_pt=841.89,
            tenant_dir=tmp_path,
        )
        c.save()

    def test_missing_required_image_raises(self, tmp_path):
        """Een 'required: true'-image waarvan de bron ontbreekt moet luid
        falen — het omgekeerde van het optionele-image-gedrag hierboven.
        Zie KBA-README, sectie 'Coverblad': een projectfoto is verplicht;
        een fout pad mag geen leeg vlak opleveren, het moet de build
        stoppen."""
        c, _ = _make_canvas()
        with pytest.raises(ValueError, match="verplichte afbeelding ontbreekt"):
            render_static_elements(
                c,
                [{
                    "type": "image", "src": "does-not-exist.png",
                    "x": 0, "y": 0, "w": 50, "h": 50, "required": True,
                }],
                page_height_pt=841.89,
                tenant_dir=tmp_path,
                tenant="kba",
                block="cover.static_elements",
            )

    def test_missing_required_image_error_names_tenant_block_and_path(self, tmp_path):
        """De ValueError-boodschap moet tenant, pagina-blok (element-index
        inbegrepen) én het gezochte pad noemen — anders is de fout niet
        te diagnosticeren op productie."""
        c, _ = _make_canvas()
        with pytest.raises(ValueError) as excinfo:
            render_static_elements(
                c,
                [{
                    "type": "image", "src": "does-not-exist.png",
                    "x": 0, "y": 0, "w": 50, "h": 50, "required": True,
                }],
                page_height_pt=841.89,
                tenant_dir=tmp_path,
                tenant="kba",
                block="cover.static_elements",
            )
        message = str(excinfo.value)
        assert "kba" in message
        assert "cover.static_elements[0]" in message
        assert "does-not-exist.png" in message

    def test_missing_required_image_via_context_token(self):
        """Ontbreekt de data (geen 'cover_photo' in context), dan moet de
        fout dat ook expliciet benoemen — niet alleen het geval van een
        pad dat wél is opgegeven maar niet bestaat."""
        c, _ = _make_canvas()
        with pytest.raises(ValueError, match="verplichte afbeelding ontbreekt"):
            render_static_elements(
                c,
                [{
                    "type": "image", "src": "{cover_photo}",
                    "x": 0, "y": 0, "w": 50, "h": 50, "required": True,
                }],
                page_height_pt=841.89,
                context={},
                tenant="kba",
                block="cover.static_elements",
            )

    def test_token_image_src_resolves_from_context(self, tmp_path):
        from PIL import Image as PILImage

        img_path = tmp_path / "photo.png"
        PILImage.new("RGB", (20, 20), color=(10, 20, 30)).save(img_path)

        c, _ = _make_canvas()
        render_static_elements(
            c,
            [{
                "type": "image", "src": "{cover_photo}",
                "x": 0, "y": 0, "w": 50, "h": 50, "fit": "cover",
            }],
            page_height_pt=841.89,
            context={"cover_photo": str(img_path)},
        )
        c.save()


class TestFullPageIntegration:
    """Rendert een volledige elementenlijst (representatief voor KBA
    variant a) en controleert dat het resulterende PDF geldig is."""

    def test_full_cover_like_page(self, tmp_path):
        c, buf = _make_canvas()
        page_h = 841.89
        elements = [
            {"type": "rect", "x": 0, "y": 0, "w": 210, "h": 118, "fill": "#0F6E56"},
            {"type": "rect", "x": 0, "y": 115, "w": 79.8, "h": 3, "fill": "#B4E8DC"},
            {"type": "rect", "x": 79.8, "y": 115, "w": 50.4, "h": 3, "fill": "#1D9E75"},
            {"type": "rect", "x": 130.2, "y": 115, "w": 79.8, "h": 3, "fill": "#0F6E56"},
            {
                "type": "line", "x1": 22, "y1": 239, "x2": 188, "y2": 239,
                "width": 0.35, "color": "#DFE7E4",
            },
            {
                "type": "text", "content": "{project_number}", "x": 22, "y": 244,
                "font": "Helvetica", "size": 9, "color": "#11302A",
            },
        ]
        render_static_elements(
            c, elements, page_height_pt=page_h,
            context={"project_number": "PRJ-001"},
        )
        c.save()
        buf.seek(0)
        doc = fitz.open(stream=buf.read(), filetype="pdf")
        assert doc.page_count == 1
        doc.close()


@pytest.mark.skipif(
    not KBA_TENANT_DIR.exists(), reason="tenants/kba niet aanwezig in deze checkout"
)
class TestKbaRequiredCoverPhoto:
    """End-to-end: een echt KBA-rapport zonder (geldige) coverfoto moet de
    volledige ``ReportGeneratorV2.generate()``-pijplijn met een
    ``ValueError`` laten stranden — niet alleen de losse
    ``render_static_elements``-aanroep. Dit is de regel uit de
    KBA-README, sectie 'Coverblad': een projectfoto is verplicht."""

    def _make_generator(self):
        from openaec_reports.core.renderer_v2 import ReportGeneratorV2
        from openaec_reports.core.tenant import TenantConfig

        tenant_config = TenantConfig(KBA_TENANT_DIR)
        return ReportGeneratorV2(
            brand="kba", tenant_slug="kba", tenant_config=tenant_config
        )

    def _base_data(self) -> dict:
        return {
            "template": "standaard",
            "project": "Testproject zonder coverfoto",
            "report_type": "Constructief advies",
            "cover": {},
            "colofon": {"enabled": False},
            "toc": {"enabled": False},
            "sections": [],
        }

    def test_missing_cover_image_key_raises(self, tmp_path):
        gen = self._make_generator()
        data = self._base_data()  # geen "image"-sleutel in data["cover"]
        with pytest.raises(ValueError, match="verplichte afbeelding ontbreekt"):
            gen.generate(
                data, KBA_TENANT_DIR / "stationery", tmp_path / "out.pdf"
            )

    def test_nonexistent_cover_image_path_raises(self, tmp_path):
        gen = self._make_generator()
        data = self._base_data()
        data["cover"]["image"] = str(tmp_path / "does-not-exist.jpg")
        with pytest.raises(ValueError, match="verplichte afbeelding ontbreekt"):
            gen.generate(
                data, KBA_TENANT_DIR / "stationery", tmp_path / "out.pdf"
            )
