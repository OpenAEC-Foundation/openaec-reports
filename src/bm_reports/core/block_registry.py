"""Block registry — Factory functies voor het aanmaken van content blocks uit JSON data."""

from __future__ import annotations

import base64
import logging
import tempfile
from pathlib import Path
from typing import Any

from reportlab.platypus import Flowable, PageBreak, Paragraph, Spacer

from bm_reports.core.document import MM_TO_PT
from bm_reports.core.styles import BM_STYLES

logger = logging.getLogger(__name__)


# ============================================================
# Image source resolution
# ============================================================


def resolve_image_source(
    src: str | dict[str, Any],
    base_dir: Path | None = None,
) -> Path:
    """Resolves een image source (pad of base64 dict) naar een bestandspad.

    Args:
        src: Bestandspad (str) of dict met 'data' en 'media_type' (base64).
        base_dir: Basis directory voor relatieve paden.

    Returns:
        Path naar het afbeeldingsbestand.
    """
    if isinstance(src, dict):
        # Base64 encoded afbeelding
        data_b64 = src["data"]
        media_type = src["media_type"]
        ext_map = {
            "image/png": ".png",
            "image/jpeg": ".jpg",
            "image/svg+xml": ".svg",
        }
        ext = ext_map.get(media_type, ".png")
        filename = src.get("filename", f"image{ext}")

        raw = base64.b64decode(data_b64)
        tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=ext, prefix=f"bm_{filename}_")
        tmp = Path(tmp_file.name)
        tmp_file.write(raw)
        tmp_file.close()
        return tmp

    # String pad
    path = Path(src)
    if not path.is_absolute() and base_dir is not None:
        path = base_dir / path
    return path


# ============================================================
# Factory functies per block type
# ============================================================


def create_paragraph(data: dict[str, Any], *, styles=None) -> Flowable:
    """Maak een Paragraph flowable."""
    ss = styles or BM_STYLES
    style_name = data.get("style", "Normal")
    style = ss[style_name] if style_name in ss else ss["Normal"]
    return Paragraph(data["text"], style)


def create_calculation(data: dict[str, Any]) -> Flowable:
    """Maak een CalculationBlock flowable."""
    from bm_reports.components.calculation import CalculationBlock

    return CalculationBlock(
        title=data["title"],
        formula=data.get("formula", ""),
        substitution=data.get("substitution", ""),
        result=data.get("result", ""),
        unit=data.get("unit", ""),
        reference=data.get("reference", ""),
    )


def create_check(data: dict[str, Any]) -> Flowable:
    """Maak een CheckBlock flowable.

    Vertaalt schema-velden naar component parameters:
    - required_value → required
    - calculated_value → calculated
    """
    from bm_reports.components.check_block import CheckBlock

    return CheckBlock(
        description=data["description"],
        required=data.get("required_value", ""),
        calculated=data.get("calculated_value", ""),
        unity_check=data.get("unity_check"),
        limit=data.get("limit", 1.0),
        result=data.get("result"),
        reference=data.get("reference", ""),
    )


def create_table(data: dict[str, Any]) -> Flowable:
    """Maak een TableBlock flowable.

    Vertaalt schema-velden naar component parameters:
    - column_widths → col_widths_mm
    - style "striped" → zebra=True
    """
    from bm_reports.components.table_block import TableBlock

    style = data.get("style", "default")
    zebra = style in ("default", "striped")

    return TableBlock(
        headers=data["headers"],
        rows=data["rows"],
        title=data.get("title", ""),
        col_widths_mm=data.get("column_widths"),
        zebra=zebra,
    )


def create_image(
    data: dict[str, Any],
    *,
    base_dir: Path | None = None,
) -> Flowable:
    """Maak een ImageBlock flowable.

    Vertaalt schema-velden naar component parameters:
    - src → path (via resolve_image_source)
    - alignment → align

    Bij ontbrekend bestand wordt een placeholder Paragraph geretourneerd.
    """
    from bm_reports.components.image_block import ImageBlock

    try:
        path = resolve_image_source(data["src"], base_dir=base_dir)
        return ImageBlock(
            path=path,
            width_mm=data.get("width_mm"),
            caption=data.get("caption", ""),
            align=data.get("alignment", "center"),
        )
    except (FileNotFoundError, ValueError) as e:
        logger.warning("Image block kon niet geladen worden: %s", e)
        caption = data.get("caption", "")
        src_desc = data.get("src", "onbekend")
        if isinstance(src_desc, dict):
            src_desc = src_desc.get("filename", "base64 data")
        return Paragraph(
            f"<i>[Afbeelding niet beschikbaar: {src_desc}]</i>"
            + (f"<br/><i>{caption}</i>" if caption else ""),
            BM_STYLES["Caption"],
        )


def create_map(data: dict[str, Any]) -> Flowable:
    """Maak een KadasterMap flowable.

    Vertaalt schema-velden naar component parameters:
    - center.lat → latitude
    - center.lon → longitude
    """
    from bm_reports.components.map_block import KadasterMap

    center = data.get("center", {})
    return KadasterMap(
        latitude=center.get("lat", 0.0),
        longitude=center.get("lon", 0.0),
        radius_m=data.get("radius_m", 100.0),
        width_mm=data.get("width_mm", 120.0),
        height_mm=data.get("height_mm", 90.0),
        layers=data.get("layers"),
        caption=data.get("caption", ""),
    )


def create_spacer(data: dict[str, Any]) -> Flowable:
    """Maak een Spacer flowable."""
    height_mm = data.get("height_mm", 5)
    return Spacer(1, height_mm * MM_TO_PT)


def create_page_break(data: dict[str, Any]) -> Flowable:
    """Maak een PageBreak flowable."""
    return PageBreak()


def create_raw_flowable(data: dict[str, Any]) -> Flowable:
    """Maak een dynamische Flowable via class naam (library-only).

    Ondersteunt alleen classes uit reportlab.platypus.
    """
    import reportlab.platypus as platypus

    class_name = data["class_name"]
    cls = getattr(platypus, class_name, None)
    if cls is None:
        raise ValueError(f"Onbekende ReportLab Flowable class: {class_name}")

    kwargs = data.get("kwargs", {})
    return cls(**kwargs)


# ============================================================
# Registry
# ============================================================

BLOCK_REGISTRY: dict[str, Any] = {
    "paragraph": create_paragraph,
    "calculation": create_calculation,
    "check": create_check,
    "table": create_table,
    "image": create_image,
    "map": create_map,
    "spacer": create_spacer,
    "page_break": create_page_break,
    "raw_flowable": create_raw_flowable,
}


def create_block(
    data: dict[str, Any],
    *,
    base_dir: Path | None = None,
    styles=None,
) -> Flowable:
    """Maak een content block flowable op basis van JSON data.

    Args:
        data: Dict met minimaal een 'type' veld.
        base_dir: Basis directory voor relatieve paden (images).
        styles: Optionele stylesheet (StyleSheet1) voor paragraph styles.

    Returns:
        ReportLab Flowable object.

    Raises:
        ValueError: Als het block type onbekend is.
    """
    block_type = data.get("type")
    if block_type is None:
        raise ValueError("Content block mist 'type' veld")

    factory = BLOCK_REGISTRY.get(block_type)
    if factory is None:
        raise ValueError(f"Onbekend content block type: {block_type!r}")

    # Factories die base_dir ondersteunen
    if block_type == "image":
        return factory(data, base_dir=base_dir)

    # Factories die styles ondersteunen
    if block_type == "paragraph":
        return factory(data, styles=styles)

    return factory(data)
