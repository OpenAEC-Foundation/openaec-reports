"""Warmteverlies rapport — conditionele voetnoot voor water-grensvlakken.

Injecteert een Nederlandstalige voetnoot in de "Uitgangspunten" sectie van
een warmteverlies-rapport wanneer het project ten minste één constructie
met een water-grensvlak bevat.

De voetnoot-tekst komt letterlijk uit spec §11.5 van
``warmteverlies_adjacent_room_temp_spec.md`` — NIET herformuleren.

Deze module werkt als pre-processor op de JSON-payload die binnenkomt bij
``Report.from_dict()``. De mutatie gebeurt in-place op de data-dict, vóór
de engine de blocks converteert naar Flowables.

Ontwerpprincipes:
- **Defensief**: oude payloads zonder ``theta_water`` of zonder water-info
  mogen niet crashen; de functie doet dan niets.
- **Idempotent**: tweemaal aanroepen op dezelfde dict voegt niet twee keer
  dezelfde voetnoot toe.
- **Engine-agnostisch**: herkent alleen warmteverlies-rapporten via
  ``metadata.engine == "isso51-core"`` en laat andere rapporten met rust.
"""

from __future__ import annotations

from typing import Any

# Default watertemperatuur in °C, conform spec §11.3.
# Gebruikt als fallback wanneer de payload geen expliciete waarde levert.
DEFAULT_THETA_WATER_C: float = 5.0

# Marker waarmee een reeds-geïnjecteerde voetnoot wordt herkend.
# Voorkomt dubbele injectie bij herhaalde aanroepen.
_FOOTNOTE_MARKER: str = "data-warmteverlies-water-footnote"

# Engine-identifier die de warmteverlies-frontend meestuurt in
# ``metadata.engine``.
_WARMTEVERLIES_ENGINE: str = "isso51-core"

# Titelfragmenten (hoofdletterongevoelig) waarmee de Uitgangspunten /
# Aannames sectie wordt herkend.
_UITGANGSPUNTEN_TITLE_KEYWORDS: tuple[str, ...] = (
    "uitgangspunten",
    "aannames",
)

# Labels in een tabel die aangeven dat het om water-transmissie gaat.
_WATER_TABLE_LABEL_FRAGMENTS: tuple[str, ...] = (
    "h_t,iw",
    "h_t,w",
    "water",
)


def inject_water_footnote_if_needed(data: dict[str, Any]) -> bool:
    """Voeg de water-voetnoot toe aan de Uitgangspunten sectie indien nodig.

    De functie muteert ``data`` in-place. Retourneert ``True`` als er een
    voetnoot is toegevoegd, ``False`` als de trigger niet voldaan is of de
    voetnoot al aanwezig was.

    Trigger: het rapport is een warmteverlies-rapport (``isso51-core``) én
    het project heeft ten minste één water-grensvlak, te herkennen aan
    één van:

    - ``metadata.water_boundaries_present == True`` (expliciete flag)
    - ``metadata.theta_water`` is aanwezig (impliciet signaal)
    - Een tabelrij in een sectie bevat een water-transmissie-label
      (``H_T,iw``, ``H_T,w`` of "water").

    Args:
        data: JSON-dict conform ``report.schema.json``, zoals ontvangen
            door ``Report.from_dict()``.

    Returns:
        ``True`` als de voetnoot is geïnjecteerd, anders ``False``.
    """
    if not isinstance(data, dict):
        return False

    if not _is_warmteverlies_report(data):
        return False

    if not _has_water_boundary(data):
        return False

    sections = data.get("sections")
    if not isinstance(sections, list):
        return False

    target_section = _find_uitgangspunten_section(sections)
    if target_section is None:
        return False

    content = target_section.setdefault("content", [])
    if not isinstance(content, list):
        return False

    if _footnote_already_present(content):
        return False

    theta_water = _resolve_theta_water(data)
    footnote_block = _build_footnote_block(theta_water)
    content.append(footnote_block)
    return True


def _is_warmteverlies_report(data: dict[str, Any]) -> bool:
    """Check of de payload afkomstig is van de warmteverlies-engine."""
    metadata = data.get("metadata")
    if not isinstance(metadata, dict):
        return False
    engine = metadata.get("engine")
    return isinstance(engine, str) and engine == _WARMTEVERLIES_ENGINE


def _has_water_boundary(data: dict[str, Any]) -> bool:
    """Detecteer of het project minstens één water-grensvlak heeft.

    Checks in volgorde:

    1. Expliciete flag ``metadata.water_boundaries_present``.
    2. Aanwezigheid van ``metadata.theta_water`` (zonder flag).
    3. Scan van tabel-labels in alle sections op water-transmissie.
    """
    metadata = data.get("metadata", {})
    if isinstance(metadata, dict):
        if metadata.get("water_boundaries_present") is True:
            return True
        if "theta_water" in metadata:
            return True

    sections = data.get("sections", [])
    if not isinstance(sections, list):
        return False

    for section in sections:
        if not isinstance(section, dict):
            continue
        for block in section.get("content", []) or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") != "table":
                continue
            if _table_contains_water_label(block):
                return True

    return False


def _table_contains_water_label(table_block: dict[str, Any]) -> bool:
    """Check of een tabel-block een water-transmissie-rij bevat."""
    rows = table_block.get("rows") or []
    if not isinstance(rows, list):
        return False

    for row in rows:
        if not isinstance(row, (list, tuple)):
            continue
        for cell in row:
            if not isinstance(cell, str):
                continue
            lowered = cell.lower()
            if any(frag in lowered for frag in _WATER_TABLE_LABEL_FRAGMENTS):
                return True
    return False


def _find_uitgangspunten_section(
    sections: list[Any],
) -> dict[str, Any] | None:
    """Zoek de Uitgangspunten / Aannames sectie (case-insensitive)."""
    for section in sections:
        if not isinstance(section, dict):
            continue
        title = section.get("title", "")
        if not isinstance(title, str):
            continue
        lowered = title.lower()
        if any(keyword in lowered for keyword in _UITGANGSPUNTEN_TITLE_KEYWORDS):
            return section
    return None


def _footnote_already_present(content: list[Any]) -> bool:
    """Check of een voetnoot-block met marker al in de content-list zit."""
    for block in content:
        if not isinstance(block, dict):
            continue
        if block.get("type") != "paragraph":
            continue
        text = block.get("text", "")
        if isinstance(text, str) and _FOOTNOTE_MARKER in text:
            return True
    return False


def _resolve_theta_water(data: dict[str, Any]) -> float:
    """Haal de gebruikte watertemperatuur op uit de payload.

    Volgorde:

    1. ``metadata.theta_water`` (float/int).
    2. ``design_conditions.theta_water`` (indien frontend dit meestuurt).
    3. Fallback ``DEFAULT_THETA_WATER_C``.
    """
    metadata = data.get("metadata")
    if isinstance(metadata, dict):
        value = metadata.get("theta_water")
        parsed = _to_float(value)
        if parsed is not None:
            return parsed

    design = data.get("design_conditions")
    if isinstance(design, dict):
        value = design.get("theta_water")
        parsed = _to_float(value)
        if parsed is not None:
            return parsed

    return DEFAULT_THETA_WATER_C


def _to_float(value: Any) -> float | None:
    """Converteer veilig naar float; retourneer ``None`` bij fout."""
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.strip().replace(",", "."))
        except ValueError:
            return None
    return None


def _format_theta_water(theta_water_c: float) -> str:
    """Formatteer de watertemperatuur voor weergave.

    Hele getallen zonder decimaal, anders één decimaal. Komma als
    decimaalteken (Nederlandse notatie).
    """
    if float(theta_water_c).is_integer():
        return f"{int(theta_water_c)}"
    return f"{theta_water_c:.1f}".replace(".", ",")


def _build_footnote_block(theta_water_c: float) -> dict[str, Any]:
    """Bouw het paragraph-block met de Nederlandstalige voetnoot.

    De tekst komt letterlijk uit spec §11.5 van
    ``warmteverlies_adjacent_room_temp_spec.md``. De placeholder
    ``{theta_water}`` wordt vervangen door de effectieve waarde.
    """
    theta_str = _format_theta_water(theta_water_c)
    text = (
        f"<i>Voor grensvlakken aan water is een ontwerp-watertemperatuur "
        f"van <b>{theta_str} °C</b> aangehouden. NEN-EN 12831 en ISSO 51 "
        "bevatten geen voorgeschreven waarde voor deze grensconditie; de "
        "gehanteerde waarde is een engineering-aanname op basis van de "
        "eigenschappen van Nederlands binnenwater onder winter-ontwerp"
        "condities. Voor afwijkende situaties (zoutwater, sterk stromend "
        "water, diepwater) kan deze waarde worden aangepast in de "
        "project-instellingen. De aanname is conservatief: omdat water "
        "een grote thermische massa en sterke convectie heeft, gedraagt "
        "het zich als een warmtesink met een vrijwel constante "
        "temperatuur — anders dan grond (die rond het casco kan "
        "opwarmen) of lucht (die sterk fluctueert).</i>"
        f"<!-- {_FOOTNOTE_MARKER} -->"
    )
    return {
        "type": "paragraph",
        "text": text,
    }
