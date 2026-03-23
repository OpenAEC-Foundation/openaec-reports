"""Data transformatie: API JSON → TemplateEngine flat dict.

Transformeert de geneste JSON structuur (sections/content blocks) naar het
flat dot-notatie formaat dat de template engine verwacht voor bind-resolution.

Detecteert automatisch of data al in flat formaat is en doet dan pass-through.
"""

from __future__ import annotations

from typing import Any

# Vaste inhoudsopgave voor BIC Rapport templates.
# De BIC Rapportage heeft altijd dezelfde hoofdstukindeling.
_BIC_RAPPORT_TOC: dict[str, str] = {
    "item_1": "1  Locatie",
    "item_2": "2  Voorziening",
    "item_3": "3  Object",
    "item_4": "4  Bedrijfsinterne controle (BIC)",
    "item_5": "5  Herstelwerkzaamheden",
    "item_6": "6  Tekeningen",
    "item_6_1": "6.1  Regionale overzichtstekening",
    "item_6_2": "6.2  Detailtekening",
    "item_6_3": "6.3  Kadastrale kaart",
    "item_7": "7  Onderhoudsdossier",
    "item_7_1": "7.1  Controlelijst BIC",
    "item_7_2": "7.2  Historie",
    "item_7_2_1": "7.2.1  BIC controles",
    "item_7_2_2": "7.2.2  Herstelwerkzaamheden",
    "item_7_2_3": "7.2.3  Onderhouds- en inspectieoverzicht",
    "item_8": "8  Bijlagen",
    "item_8_1": "8.1  Fotobijlage",
    "item_8_2": "8.2  Certificaten",
    "item_8_3": "8.3  Overige documenten",
}


def _is_already_flat(data: dict[str, Any]) -> bool:
    """Detecteer of de JSON data al in flat engine formaat is.

    Flat formaat heeft top-level keys zoals 'bic', 'reiniging', 'samenvatting'
    als dicts (niet als lists of strings). Het geneste formaat heeft 'sections'.
    """
    has_sections = "sections" in data and isinstance(data.get("sections"), list)
    has_flat_bic = isinstance(data.get("bic"), dict)
    has_flat_meta = isinstance(data.get("meta"), dict)

    # Als er flat BIC/meta data is EN geen sections → al flat
    if (has_flat_bic or has_flat_meta) and not has_sections:
        return True
    return False


def transform_json_to_engine_data(raw: dict[str, Any]) -> dict[str, Any]:
    """Transformeer API JSON naar het flat formaat dat de TemplateEngine verwacht.

    Als de data al flat is (bevat top-level 'bic', 'meta', etc. dicts zonder
    'sections' list), wordt de data ongewijzigd doorgegeven.

    Args:
        raw: JSON data dict zoals ontvangen van de API/frontend.

    Returns:
        Flat dict geschikt voor ``TemplateEngine.build(data=...)``.
    """
    if _is_already_flat(raw):
        _inject_toc_if_needed(raw, raw)
        return raw

    result = _transform_nested(raw)
    _inject_toc_if_needed(result, raw)
    return result


def _transform_nested(raw: dict[str, Any]) -> dict[str, Any]:
    """Transformeer geneste sections-structuur naar flat engine formaat.

    De template engine resolvet bind-paden via dot-notatie op de data dict.
    Page types verwachten:

    - ``meta.factuur_kop``, ``meta.datum``, ``meta.factuurnummer``, etc.
    - ``client.name``, ``client.address``, etc.
    - ``location.name``, ``location.address``, ``location.code``, etc.
    - ``bic.*``, ``reiniging.*``, ``additioneel.*``, ``samenvatting.*``
    - ``detail_items`` — flat list van dicts
    - ``objecten`` — flat list van dicts

    Args:
        raw: JSON data dict met geneste sections structuur.

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

    # BIC data — per sectie apart opslaan
    bic_data: dict[str, Any] = {}
    reiniging_data: dict[str, Any] = {}
    additioneel_data: dict[str, Any] = {}
    samenvatting_data: dict[str, Any] = {}

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
                # Parse BIC sections into flat key structure
                bic_data, reiniging_data, additioneel_data = _parse_bic_sections(
                    content_block.get("sections", [])
                )
                samenvatting_data = _parse_bic_summary(
                    content_block.get("summary", {})
                )

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
        "bic": bic_data,
        "reiniging": reiniging_data,
        "additioneel": additioneel_data,
        "samenvatting": samenvatting_data,
        "detail_items": detail_items,
        "objecten": objecten,
    }


def _inject_toc_if_needed(
    result: dict[str, Any], raw: dict[str, Any]
) -> None:
    """Injecteer statische TOC data voor BIC Rapport templates.

    BIC Rapporten hebben een vaste inhoudsopgave. De template definieert
    text_zones (toc.item_1 t/m toc.item_8_3) maar de data moet ook de
    bijbehorende waarden bevatten.

    Muteert ``result`` in-place. Skipt als er al een ``toc`` dict met
    ``item_*`` keys aanwezig is.
    """
    template = raw.get("template", "")
    if "bic_rapport" not in template:
        return

    existing_toc = result.get("toc", {})
    if isinstance(existing_toc, dict) and any(
        k.startswith("item_") for k in existing_toc
    ):
        return

    result["toc"] = dict(_BIC_RAPPORT_TOC)


def _parse_bic_sections(sections: list[dict]) -> tuple[dict, dict, dict]:
    """Parse BIC table sections naar flat dicts per categorie.

    Mapping per sectie-titel:
    - "BIC controles" → bic.aantal_conform, bic.kosten_conform, etc.
    - "Reinigen tijdens BIC" → reiniging.kosten_conform, etc.
    - "Additioneel tijdens BIC" → additioneel.kosten_conform, etc.
    """
    bic: dict[str, str] = {}
    reiniging: dict[str, str] = {}
    additioneel: dict[str, str] = {}

    for sec in sections:
        title = sec.get("title", "").lower()
        rows = sec.get("rows", [])

        if "bic controle" in title:
            _map_bic_rows(rows, bic)
        elif "reinig" in title:
            _map_simple_rows(rows, reiniging)
        elif "additioneel" in title:
            _map_simple_rows(rows, additioneel)

    return bic, reiniging, additioneel


def _map_bic_rows(rows: list[dict], out: dict) -> None:
    """Map BIC controle rijen naar flat keys.

    Verwachte labels:
    - "Aantal BIC controles" → aantal_conform/aantal_werkelijk
    - "Kosten" (1e) → kosten_conform/kosten_werkelijk
    - "Aantal interne inspecties" → hydro_aantal_conform/hydro_aantal_werkelijk
    - "Kosten" (2e) → hydro_kosten_conform/hydro_kosten_werkelijk
    - "Reiskosten" → reiskosten_conform/reiskosten_werkelijk
    - "Subtotaal" → subtotaal_conform/subtotaal_werkelijk
    """
    kosten_idx = 0
    for row in rows:
        label = row.get("label", "").lower()
        ref = row.get("ref_value", "")
        actual = row.get("actual_value", "")

        if "aantal bic" in label:
            out["aantal_conform"] = ref
            out["aantal_werkelijk"] = actual
        elif "aantal interne" in label or "aantal hydro" in label:
            out["hydro_aantal_conform"] = ref
            out["hydro_aantal_werkelijk"] = actual
        elif "reiskosten" in label:
            out["reiskosten_conform"] = ref
            out["reiskosten_werkelijk"] = actual
        elif "subtotaal" in label:
            out["subtotaal_conform"] = ref
            out["subtotaal_werkelijk"] = actual
        elif "kosten" in label:
            kosten_idx += 1
            if kosten_idx == 1:
                out["kosten_conform"] = ref
                out["kosten_werkelijk"] = actual
            else:
                out["hydro_kosten_conform"] = ref
                out["hydro_kosten_werkelijk"] = actual


def _map_simple_rows(rows: list[dict], out: dict) -> None:
    """Map eenvoudige sectie rijen (reiniging/additioneel).

    Mapt zowel 'aantal' als 'kosten' rijen.
    """
    for row in rows:
        label = row.get("label", "").lower()
        ref = row.get("ref_value", "")
        actual = row.get("actual_value", "")

        if "aantal" in label:
            out["aantal_conform"] = ref
            out["aantal_werkelijk"] = actual
        elif "kosten" in label:
            out["kosten_conform"] = ref
            out["kosten_werkelijk"] = actual


def _parse_bic_summary(summary: dict) -> dict[str, str]:
    """Parse BIC summary sectie naar samenvatting dict.

    Mapping:
    - "BIC controles" → bic_conform/bic_werkelijk
    - "Reinigen" → reinigen_conform/reinigen_werkelijk
    - "Additioneel" → additioneel_conform/additioneel_werkelijk
    - total → totaal_conform/totaal_werkelijk
    """
    out: dict[str, str] = {}

    for row in summary.get("rows", []):
        label = row.get("label", "").lower()
        ref = row.get("ref_value", "")
        actual = row.get("actual_value", "")

        if "bic" in label:
            out["bic_conform"] = ref
            out["bic_werkelijk"] = actual
        elif "reinig" in label:
            out["reinigen_conform"] = ref
            out["reinigen_werkelijk"] = actual
        elif "additioneel" in label:
            out["additioneel_conform"] = ref
            out["additioneel_werkelijk"] = actual

    total = summary.get("total", {})
    if total:
        out["totaal_conform"] = total.get("ref_value", "")
        out["totaal_werkelijk"] = total.get("actual_value", "")

    return out
