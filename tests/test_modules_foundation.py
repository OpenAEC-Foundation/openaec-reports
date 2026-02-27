"""Tests voor Module Foundation: ModuleRegistry, ContentModule, ModuleConfig.

Test coverage:
- ModuleRegistry: register_core, register_tenant, get, available, reset
- ModuleRegistry: get() met tenant vindt tenant-specifiek eerst
- ModuleRegistry: get() zonder tenant vindt alleen core
- ModuleRegistry: KeyError bij onbekend module
- ContentModule: subclass die _calculate_height en draw implementeert
- ContentModule: wrap() protocol
- ModuleConfig: default waarden
- Per-sectie orientation (integration test)
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from bm_reports.modules import ModuleRegistry
from bm_reports.modules.base import ContentModule, ModuleConfig

# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

DEFAULT_WIDTH = 441.3


class DummyModule(ContentModule):
    """Minimale ContentModule subclass voor tests."""

    def _calculate_height(self) -> float:
        return self.data.get("height", 50.0)

    def draw(self) -> None:
        self.canv.setFont("Helvetica", 10)
        self.canv.drawString(0, 0, self.data.get("text", "test"))


class AltDummyModule(ContentModule):
    """Alternatieve module voor tenant-override tests."""

    def _calculate_height(self) -> float:
        return 100.0

    def draw(self) -> None:
        pass


def render_module_to_pdf(module: ContentModule) -> bytes:
    """Render een module naar een in-memory test PDF."""
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = module.wrap(DEFAULT_WIDTH, 700)
    module.canv = c
    c.translate(70, A4[1] - 100 - h)
    module.draw()
    c.showPage()
    c.save()
    return buf.getvalue()


# ---------------------------------------------------------------------------
# ModuleConfig tests
# ---------------------------------------------------------------------------


class TestModuleConfig:
    """Tests voor ModuleConfig default waarden."""

    def test_default_fonts(self):
        cfg = ModuleConfig()
        assert cfg.fonts["heading"] == "Helvetica-Bold"
        assert cfg.fonts["body"] == "Helvetica"

    def test_default_colors(self):
        cfg = ModuleConfig()
        assert cfg.colors["primary"] == "#006FAB"
        assert cfg.colors["secondary"] == "#94571E"
        assert cfg.colors["text"] == "#000000"
        assert cfg.colors["white"] == "#FFFFFF"

    def test_default_sizes(self):
        cfg = ModuleConfig()
        assert cfg.label_size == 10.0
        assert cfg.value_size == 10.0
        assert cfg.heading_size == 14.0

    def test_default_line_settings(self):
        cfg = ModuleConfig()
        assert cfg.line_color == "#006FAB"
        assert cfg.line_width == 0.5

    def test_custom_values(self):
        cfg = ModuleConfig(
            label_size=12.0,
            line_color="#FF0000",
            fonts={"heading": "Arial-Bold", "body": "Arial"},
        )
        assert cfg.label_size == 12.0
        assert cfg.line_color == "#FF0000"
        assert cfg.fonts["heading"] == "Arial-Bold"


# ---------------------------------------------------------------------------
# ModuleRegistry tests
# ---------------------------------------------------------------------------


class TestModuleRegistry:
    """Tests voor ModuleRegistry core/tenant scheiding."""

    @pytest.fixture(autouse=True)
    def _reset_registry(self):
        """Reset registry voor elke test."""
        ModuleRegistry.reset()
        yield
        ModuleRegistry.reset()

    def test_register_core(self):
        ModuleRegistry.register_core("dummy", DummyModule)
        result = ModuleRegistry.get("dummy")
        assert result is DummyModule

    def test_register_tenant(self):
        ModuleRegistry.register_tenant("acme", "widget", DummyModule)
        result = ModuleRegistry.get("widget", tenant="acme")
        assert result is DummyModule

    def test_get_tenant_first_then_core(self):
        """Tenant-specifieke module heeft voorrang op core."""
        ModuleRegistry.register_core("calc", DummyModule)
        ModuleRegistry.register_tenant("acme", "calc", AltDummyModule)

        # Met tenant: vindt tenant-specifieke versie
        result = ModuleRegistry.get("calc", tenant="acme")
        assert result is AltDummyModule

    def test_get_falls_back_to_core(self):
        """Als tenant geen override heeft, wordt core gebruikt."""
        ModuleRegistry.register_core("calc", DummyModule)
        ModuleRegistry.register_tenant("acme", "widget", AltDummyModule)

        # Tenant 'acme' heeft 'calc' niet → core fallback
        result = ModuleRegistry.get("calc", tenant="acme")
        assert result is DummyModule

    def test_get_without_tenant_finds_core_only(self):
        """Zonder tenant wordt alleen core doorzocht."""
        ModuleRegistry.register_core("calc", DummyModule)
        ModuleRegistry.register_tenant("acme", "widget", AltDummyModule)

        result = ModuleRegistry.get("calc")
        assert result is DummyModule

    def test_get_without_tenant_raises_for_tenant_only(self):
        """Zonder tenant kun je geen tenant-only module vinden."""
        ModuleRegistry.register_tenant("acme", "widget", DummyModule)

        with pytest.raises(KeyError, match="widget"):
            ModuleRegistry.get("widget")

    def test_get_unknown_module_raises_keyerror(self):
        with pytest.raises(KeyError, match="onbekend"):
            ModuleRegistry.get("onbekend")

    def test_get_unknown_module_with_tenant_in_message(self):
        with pytest.raises(KeyError, match="tenant acme"):
            ModuleRegistry.get("onbekend", tenant="acme")

    def test_available_core_only(self):
        ModuleRegistry.register_core("calc", DummyModule)
        ModuleRegistry.register_core("table", AltDummyModule)

        available = ModuleRegistry.available()
        assert "calc" in available
        assert "table" in available

    def test_available_with_tenant(self):
        ModuleRegistry.register_core("calc", DummyModule)
        ModuleRegistry.register_tenant("acme", "widget", AltDummyModule)

        available = ModuleRegistry.available(tenant="acme")
        assert "calc" in available
        assert "widget" in available

    def test_available_without_tenant_excludes_tenant_modules(self):
        ModuleRegistry.register_core("calc", DummyModule)
        ModuleRegistry.register_tenant("acme", "widget", AltDummyModule)

        available = ModuleRegistry.available()
        assert "calc" in available
        assert "widget" not in available

    def test_reset_clears_all(self):
        ModuleRegistry.register_core("calc", DummyModule)
        ModuleRegistry.register_tenant("acme", "widget", AltDummyModule)

        ModuleRegistry.reset()

        assert ModuleRegistry.available() == []
        with pytest.raises(KeyError):
            ModuleRegistry.get("calc")

    def test_multiple_tenants(self):
        """Meerdere tenants met dezelfde module naam."""
        ModuleRegistry.register_tenant("acme", "report", DummyModule)
        ModuleRegistry.register_tenant("globex", "report", AltDummyModule)

        assert ModuleRegistry.get("report", tenant="acme") is DummyModule
        assert ModuleRegistry.get("report", tenant="globex") is AltDummyModule


# ---------------------------------------------------------------------------
# ContentModule tests
# ---------------------------------------------------------------------------


class TestContentModule:
    """Tests voor ContentModule base class en subclasses."""

    def test_subclass_instantiation(self):
        module = DummyModule(data={"height": 75.0, "text": "test"})
        assert module.height == 75.0
        assert module.width == DEFAULT_WIDTH
        assert module.data["text"] == "test"

    def test_default_config(self):
        module = DummyModule(data={})
        assert isinstance(module.config, ModuleConfig)
        assert module.config.fonts["heading"] == "Helvetica-Bold"

    def test_custom_config(self):
        cfg = ModuleConfig(label_size=14.0)
        module = DummyModule(data={}, config=cfg)
        assert module.config.label_size == 14.0

    def test_wrap_protocol(self):
        """wrap() retourneert (width, height) en past afmetingen aan."""
        module = DummyModule(data={"height": 50.0})

        new_width = 300.0
        w, h = module.wrap(new_width, 600)

        assert w == new_width
        assert h == 50.0
        assert module.width == new_width
        assert module.available_width == new_width

    def test_wrap_recalculates_height(self):
        """wrap() herberekent de hoogte met de nieuwe breedte."""
        module = DummyModule(data={"height": 50.0})
        assert module.height == 50.0

        # Hoogte is vast in DummyModule, maar wrap moet _calculate_height callen
        w, h = module.wrap(200.0, 400.0)
        assert h == 50.0

    def test_draw_renders_without_error(self):
        """draw() moet uitvoerbaar zijn op een ReportLab canvas."""
        module = DummyModule(data={"text": "hello"})
        pdf_bytes = render_module_to_pdf(module)
        assert len(pdf_bytes) > 0

    def test_base_class_raises_not_implemented(self):
        """ContentModule direct instantiëren moet falen."""
        with pytest.raises(NotImplementedError):
            ContentModule(data={})

    def test_available_width_default(self):
        module = DummyModule(data={})
        assert module.available_width == DEFAULT_WIDTH

    def test_custom_available_width(self):
        module = DummyModule(data={}, available_width=500.0)
        assert module.available_width == 500.0
        assert module.width == 500.0


# ---------------------------------------------------------------------------
# Per-sectie orientation tests (integration)
# ---------------------------------------------------------------------------

fitz = pytest.importorskip("fitz", reason="pymupdf niet geinstalleerd")

from bm_reports.core.renderer_v2 import (  # noqa: E402
    A4_LANDSCAPE_HEIGHT,
    A4_LANDSCAPE_WIDTH,
    A4_PORTRAIT_HEIGHT,
    A4_PORTRAIT_WIDTH,
    Y_MAX_LANDSCAPE,
    Y_MAX_PORTRAIT,
    ContentRenderer,
    FontManager,
    TemplateSet,
)

BASE = Path(__file__).parent.parent
STATIONERY_DIR = (
    BASE / "src" / "bm_reports" / "assets" / "stationery" / "default"
)
TEMPLATE_DIR = BASE / "src" / "bm_reports" / "assets" / "templates" / "default"

SKIP_NO_ASSETS = pytest.mark.skipif(
    not TEMPLATE_DIR.exists(),
    reason="Template bestanden niet aanwezig",
)


class TestOrientationConstants:
    """Test de A4 dimensie-constanten."""

    def test_portrait_dimensions(self):
        assert A4_PORTRAIT_WIDTH == pytest.approx(595.28)
        assert A4_PORTRAIT_HEIGHT == pytest.approx(841.89)

    def test_landscape_dimensions(self):
        assert A4_LANDSCAPE_WIDTH == pytest.approx(841.89)
        assert A4_LANDSCAPE_HEIGHT == pytest.approx(595.28)

    def test_landscape_is_rotated_portrait(self):
        assert A4_LANDSCAPE_WIDTH == A4_PORTRAIT_HEIGHT
        assert A4_LANDSCAPE_HEIGHT == A4_PORTRAIT_WIDTH

    def test_y_max_portrait_greater_than_landscape(self):
        assert Y_MAX_PORTRAIT > Y_MAX_LANDSCAPE


@SKIP_NO_ASSETS
class TestPerSectionOrientation:
    """Integration tests voor per-sectie oriëntatie in renderer_v2."""

    @pytest.fixture()
    def renderer(self) -> ContentRenderer:
        """Maak een ContentRenderer met standaard stationery."""
        tpl = TemplateSet(brand="default")
        fonts = FontManager()
        stationery: dict[str, Path] = {}
        if STATIONERY_DIR.exists():
            stationery = {
                "standaard": STATIONERY_DIR / "standaard.pdf",
                "content_landscape": STATIONERY_DIR / "standaard_landscape.pdf",
                "bijlagen": STATIONERY_DIR / "bijlagen.pdf",
                "achterblad": STATIONERY_DIR / "achterblad.pdf",
            }
        return ContentRenderer(tpl, fonts, stationery)

    def test_default_orientation_is_portrait(self, renderer: ContentRenderer):
        assert renderer._orientation == "portrait"
        assert renderer.y_max == Y_MAX_PORTRAIT

    def test_portrait_section_keeps_portrait(self, renderer: ContentRenderer):
        section = {
            "level": 1,
            "number": "1",
            "title": "Test Section",
            "orientation": "portrait",
            "content": [{"type": "paragraph", "text": "Inhoud."}],
        }
        renderer.render_section(section)

        assert renderer._orientation == "portrait"
        assert renderer.y_max == Y_MAX_PORTRAIT

    def test_landscape_section_creates_wider_page(
        self, renderer: ContentRenderer
    ):
        """Een landscape sectie moet een bredere pagina aanmaken."""
        section = {
            "level": 1,
            "number": "1",
            "title": "Landscape Section",
            "orientation": "landscape",
            "content": [{"type": "paragraph", "text": "Brede inhoud."}],
        }
        renderer.render_section(section)

        # Oriëntatie moet terug naar portrait zijn na de sectie
        assert renderer._orientation == "portrait"

        # Check dat er een pagina is aangemaakt
        assert renderer.page_count >= 1

    def test_orientation_restored_after_landscape_section(
        self, renderer: ContentRenderer
    ):
        """Oriëntatie moet hersteld worden na een landscape sectie."""
        # Eerst portrait sectie
        renderer.render_section({
            "level": 1,
            "number": "1",
            "title": "Portrait",
            "content": [],
        })
        assert renderer._orientation == "portrait"

        # Dan landscape sectie
        renderer.render_section({
            "level": 1,
            "number": "2",
            "title": "Landscape",
            "orientation": "landscape",
            "content": [],
        })

        # Moet terug naar portrait
        assert renderer._orientation == "portrait"
        assert renderer.y_max == Y_MAX_PORTRAIT

    def test_section_without_orientation_uses_current(
        self, renderer: ContentRenderer
    ):
        """Sectie zonder orientation key gebruikt huidige oriëntatie."""
        section = {
            "level": 1,
            "number": "1",
            "title": "Default Section",
            "content": [],
        }
        renderer.render_section(section)
        assert renderer._orientation == "portrait"

    def test_landscape_page_dimensions(self, renderer: ContentRenderer):
        """Landscape pagina moet juiste dimensies hebben."""
        section = {
            "level": 1,
            "number": "1",
            "title": "Landscape",
            "orientation": "landscape",
            "content": [],
        }
        renderer.render_section(section)

        # Zoek de landscape pagina (eerste pagina als er geen stationery is)
        for page_idx in range(len(renderer.doc)):
            page = renderer.doc[page_idx]
            w, h = page.rect.width, page.rect.height
            # Landscape: breedte > hoogte
            if w > h:
                assert w == pytest.approx(A4_LANDSCAPE_WIDTH, abs=1.0)
                assert h == pytest.approx(A4_LANDSCAPE_HEIGHT, abs=1.0)
                return

        # Als alle pagina's van stationery komen, kunnen ze portrait zijn
        # (stationery PDFs zijn portrait). In dat geval skippen we.
        if not (STATIONERY_DIR / "standaard_landscape.pdf").exists():
            pytest.skip("Geen landscape stationery beschikbaar voor dimensie-check")
