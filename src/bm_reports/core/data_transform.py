"""Data transformatie: API JSON → TemplateEngine flat dict.

Transformeert de geneste JSON structuur (sections/content blocks) naar het
flat dot-notatie formaat dat de template engine verwacht voor bind-resolution.
"""

from __future__ import annotations

from typing import Any


def transform_json_to_engine_data(raw: dict[str, Any]) -> dict[str, Any]:
    """Transformeer API JSON naar het flat formaat dat de TemplateEngine verwacht.

    De template engine resolvet bind-paden via dot-notatie op de data dict.
    Page types verwachten:

    - ``meta.factuur_kop``, ``meta.datum``, ``meta.factuurnummer``, etc.
    - ``project.name``, ``client.name``, ``client.address``, etc.
    - ``location.name``, ``location.address``, ``location.code``, etc.
    - ``bic_sections`` — flat list van dicts met label/ref_value/actual_value
    - ``detail_items`` — flat list van dicts met header-namen als keys
    - ``objecten`` — flat list van dicts (Type2 voor 2e "Type" kolom)

    Args:
        raw: JSON data dict zoals ontvangen van de API/frontend.

    Returns:
        Flat dict geschikt voor ``TemplateEngine.build(data=...)``.
    """
    # Cover extra fields
    cover = raw.get("cover", {})
    extra = cover.get("extra_fields", {})

    # Client + Location data uit sections
    client_data: dict[str, Any] = {
        "name": raw.get("client", ""),
        "address": "",
        "postcode_plaats": "",
    }
    location_data: dict[str, Any] = {}
    bic_sections_flat: list[dict[str, Any]] = []
    detail_items: list[dict[str, Any]] = []
    objecten: list[dict[str, Any]] = []

    for section in raw.get("sections", []):
        for content_block in section.get("content", []):
            block_type = content_block.get("type", "")

            if block_type == "location_detail":
                cl = content_block.get("client", {})
                loc = content_block.get("location", {})
                client_data = {
                    "name": cl.get("name", raw.get("client", "")),
                    "address": cl.get("address", ""),
                    "postcode_plaats": cl.get("city", ""),
                }
                location_data = {
                    "name": loc.get("name", ""),
                    "address": loc.get("address", ""),
                    "postcode_plaats": loc.get("city", ""),
                    "code": loc.get("code", ""),
                    "provision": loc.get("provision", ""),
                    "object": loc.get("object", ""),
                }

            elif block_type == "bic_table":
                for bic_section in content_block.get("sections", []):
                    for row in bic_section.get("rows", []):
                        bic_sections_flat.append(row)
                summary = content_block.get("summary", {})
                for row in summary.get("rows", []):
                    bic_sections_flat.append(row)
                total = summary.get("total")
                if total:
                    bic_sections_flat.append(total)

            elif block_type == "table":
                title = section.get("title", "")
                headers = content_block.get("headers", [])
                rows = content_block.get("rows", [])

                if "Detail" in title:
                    for row_values in rows:
                        detail_items.append({
                            headers[i] if i < len(headers) else f"col_{i}": v
                            for i, v in enumerate(row_values)
                        })
                elif "objecten" in title.lower() or "Voorziening" in title:
                    for row_values in rows:
                        item: dict[str, Any] = {}
                        type_count = 0
                        for i, v in enumerate(row_values):
                            key = headers[i] if i < len(headers) else f"col_{i}"
                            # Handle duplicate "Type" header: 2nd becomes "Type2"
                            if key == "Type":
                                type_count += 1
                                if type_count > 1:
                                    key = "Type2"
                            item[key] = v
                        objecten.append(item)

    # Compose derived fields
    type_offerte = extra.get("Type offerte", "")
    offerte_code = extra.get("Offertecode", raw.get("project_number", ""))
    offerte_naam = extra.get("Offertenaam", "")
    offerte_regel = f"{offerte_code}: {offerte_naam}" if offerte_naam else offerte_code
    report_type = raw.get("report_type", "BIC Factuur")
    loc_code = location_data.get("code", "")
    rapportkop_locatie = f"{report_type}: {loc_code}" if loc_code else report_type

    return {
        "meta": {
            "factuur_kop": report_type,
            "datum": extra.get("Datum", raw.get("date", "")),
            "factuurnummer": extra.get("Factuurnummer", ""),
            "type_offerte": f"{type_offerte}:" if type_offerte else "",
            "offerte_regel": offerte_regel,
            "rapportkop_locatie": rapportkop_locatie,
        },
        "project": {
            "name": raw.get("project", ""),
        },
        "client": client_data,
        "location": location_data,
        "bic_sections": bic_sections_flat,
        "detail_items": detail_items,
        "objecten": objecten,
    }
