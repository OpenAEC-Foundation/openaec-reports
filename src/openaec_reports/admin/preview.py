"""Page-type preview renderer — genereert PNG preview van een page_type YAML."""

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any

import yaml
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdf_canvas

from openaec_reports.core.stationery import StationeryRenderer
from openaec_reports.core.template_config import PageType, parse_page_type
from openaec_reports.core.template_engine import (
    _draw_line_zones,
    _draw_text_zones,
)

logger = logging.getLogger(__name__)

# DPI limieten voor preview rendering
MIN_PREVIEW_DPI = 72
MAX_PREVIEW_DPI = 300
DEFAULT_PREVIEW_DPI = 150

# A4 afmetingen in points
A4_W, A4_H = A4


def _generate_sample_data(page_type: PageType) -> dict[str, Any]:
    """Genereer plausibele sample data op basis van text zone bindings.

    Inspecteer bind paths en genereer passende placeholders.
    """
    data: dict[str, Any] = {}

    for zone in page_type.text_zones:
        bind = zone.bind
        if not bind or bind.startswith("_"):
            continue

        parts = bind.split(".")
        # Genereer placeholder waarde op basis van laatste segment
        leaf = parts[-1]
        value = _placeholder_for_field(leaf)

        # Bouw nested dict structuur
        current = data
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    # Genereer sample tabeldata
    if page_type.table:
        table_parts = page_type.table.data_bind.split(".")
        sample_rows = []
        for i in range(3):
            row = {}
            for col in page_type.table.columns:
                row[col.field] = _placeholder_for_field(col.field, row_index=i)
            sample_rows.append(row)

        current = data
        for part in table_parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[table_parts[-1]] = sample_rows

    return data


def _placeholder_for_field(field_name: str, row_index: int = 0) -> str:
    """Genereer een plausibele placeholder op basis van veldnaam."""
    name_lower = field_name.lower()

    # Specifieke velden — langste key eerst om greedy matches te voorkomen
    placeholders: list[tuple[str, str | list[str]]] = [
        ("company_name", "Voorbeeldbedrijf B.V."),
        ("company", "Voorbeeldbedrijf B.V."),
        ("invoice_date", "12-03-2026"),
        ("invoice_number", "2026-0042"),
        ("project_name", "Verbouwing kantoor"),
        ("btw_nummer", "NL001234567B01"),
        ("postal_code", "1015 AA"),
        ("grand_total", "€ 6.171,00"),
        ("page_count", "1"),
        ("due_date", "12-04-2026"),
        ("subtotal", "€ 5.100,00"),
        ("address", "Keizersgracht 100"),
        ("reference", "REF-2026-042"),
        ("description", "Omschrijving werkzaamheden"),
        ("quantity", ["3", "5", "2"]),
        ("amount", ["€ 1.500,00", "€ 2.750,00", "€ 850,00"]),
        ("project", "Voorbeeldproject"),
        ("number", "2026-0042"),
        ("total", "€ 5.100,00"),
        ("phone", "020-1234567"),
        ("email", "info@voorbeeld.nl"),
        ("title", "Voorbeeldtitel"),
        ("city", "Amsterdam"),
        ("date", "12-03-2026"),
        ("name", "Jan de Vries"),
        ("iban", "NL91 ABNA 0417 1643 00"),
        ("kvk", "12345678"),
        ("vat", "€ 1.071,00"),
        ("btw", "€ 1.071,00"),
    ]

    for key, val in placeholders:
        if key in name_lower:
            if isinstance(val, list):
                return val[row_index % len(val)]
            return val

    # Generiek: gebruik veldnaam als placeholder
    return f"[{field_name}]"


def render_page_type_preview(
    yaml_content: str,
    tenant: str,
    tenants_dir: Path,
    sample_data: dict[str, Any] | None = None,
    dpi: int = DEFAULT_PREVIEW_DPI,
) -> tuple[bytes, int, int]:
    """Render een page_type YAML naar een PNG preview.

    Args:
        yaml_content: Raw YAML string van het page_type.
        tenant: Tenant identifier.
        tenants_dir: Pad naar de tenants root directory.
        sample_data: Optionele sample data. Auto-gegenereerd als None.
        dpi: Render resolutie (72-300).

    Returns:
        Tuple van (png_bytes, width_px, height_px).

    Raises:
        ValueError: Bij ongeldige YAML of parse-fouten.
    """
    # Clamp DPI
    dpi = max(MIN_PREVIEW_DPI, min(MAX_PREVIEW_DPI, dpi))

    # Parse YAML
    try:
        parsed = yaml.safe_load(yaml_content)
    except yaml.YAMLError as e:
        raise ValueError(f"Ongeldige YAML: {e}") from e

    if not isinstance(parsed, dict):
        raise ValueError("YAML moet een dict opleveren")

    # Parse naar PageType dataclass
    try:
        page_type = parse_page_type(parsed)
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(f"Ongeldig page_type formaat: {e}") from e

    # Genereer sample data als niet meegegeven
    if sample_data is None:
        sample_data = _generate_sample_data(page_type)

    # Laad brand config
    brand = _load_brand(tenant, tenants_dir)

    # Render PDF in-memory
    pdf_buffer = io.BytesIO()
    c = pdf_canvas.Canvas(pdf_buffer, pagesize=(A4_W, A4_H))

    # 1. Stationery achtergrond
    if page_type.stationery:
        stationery_dir = tenants_dir / tenant / "stationery"
        renderer = StationeryRenderer(brand_dir=stationery_dir)
        renderer.draw(c, page_type.stationery, A4_W, A4_H)

    # 2. Lijnen
    if page_type.line_zones:
        _draw_line_zones(c, page_type.line_zones, brand, A4_H)

    # 3. Text zones
    if page_type.text_zones:
        _draw_text_zones(c, page_type.text_zones, sample_data, brand, A4_H)

    # 4. Tabel met sample data
    if page_type.table:
        from openaec_reports.core.template_engine import _draw_table

        table_rows = _resolve_table_data(sample_data, page_type.table.data_bind)
        if table_rows:
            _draw_table(c, page_type.table, table_rows, brand, A4_H)

    c.save()
    pdf_bytes = pdf_buffer.getvalue()

    # PDF → PNG via PyMuPDF
    png_bytes, width, height = _pdf_to_png(pdf_bytes, dpi)

    return png_bytes, width, height


def _load_brand(tenant: str, tenants_dir: Path):
    """Laad brand config voor een tenant."""
    from openaec_reports.core.brand import BrandLoader

    brand_path = tenants_dir / tenant / "brand.yaml"
    if brand_path.exists():
        loader = BrandLoader(tenants_root=tenants_dir)
        return loader.load(tenant)

    # Fallback: default brand
    return BrandLoader(tenants_root=tenants_dir).load_default()


def _resolve_table_data(data: dict[str, Any], bind_path: str) -> list[dict[str, Any]]:
    """Resolve tabeldata uit de sample data dict."""
    parts = bind_path.split(".")
    current: Any = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return []
    if isinstance(current, list):
        return current
    return []


def _pdf_to_png(pdf_bytes: bytes, dpi: int) -> tuple[bytes, int, int]:
    """Converteer PDF bytes naar PNG via PyMuPDF.

    Args:
        pdf_bytes: In-memory PDF.
        dpi: Render resolutie.

    Returns:
        Tuple van (png_bytes, width_px, height_px).
    """
    try:
        import fitz  # PyMuPDF
    except ImportError as e:
        raise RuntimeError(
            "PyMuPDF (fitz) is vereist voor preview rendering. "
            "Installeer met: pip install PyMuPDF"
        ) from e

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        page = doc[0]
        zoom = dpi / 72.0
        mat = fitz.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        png_bytes = pix.tobytes("png")
        return png_bytes, pix.width, pix.height
    finally:
        doc.close()
