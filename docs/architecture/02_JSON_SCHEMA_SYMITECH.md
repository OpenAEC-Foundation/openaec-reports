# JSON Input Schema — Symitech BIC Factuur

## Overzicht

De JSON die je naar `/api/generate/template` stuurt heeft een **genest formaat**.
De `data_transform.py` op de server zet dit om naar het **platte formaat** dat
de YAML page_types verwachten.

```
JSON (jij stuurt)          data_transform           YAML bind-paths
─────────────────          ──────────────           ───────────────
sections[].content[]  ───▶  bic.aantal_conform  ───▶  text_zone bind
  type: "bic_table"         reiniging.kosten_       
  sections[].rows[]         samenvatting.totaal_
```

## Verplichte Top-Level Velden

```json
{
  "template": "symitech_bic_factuur",   // VERPLICHT — bepaalt tenant + document type
  "project": "Naam van het project",     // VERPLICHT — gebruikt in PDF metadata
  "brand": "symitech",                   // Optioneel — fallback naar tenant
  "format": "A4",                        // Optioneel
  "project_number": "336.01",            // Optioneel — voor bestandsnaam
  "client": "Klantnaam",                 // Top-level client string
  "author": "Symitech B.V.",             // Auteur
  "date": "2025-12-15",                  // ISO datum
  "version": "1.0",
  "status": "DEFINITIEF",
  "report_type": "BIC Factuur"           // Wordt meta.factuur_kop
}
```

## Cover (Voorblad)

```json
{
  "cover": {
    "subtitle": "BIC Factuur",
    "extra_fields": {
      "Factuurnummer": "F2025-1247",         // → meta.factuurnummer
      "Datum": "15 december 2025",           // → meta.datum
      "Type offerte": "BIC Controle",        // → meta.type_offerte (+ ":")
      "Offertecode": "336.01",               // ─┐
      "Offertenaam": "Jaarlijkse BIC ..."    // ─┘→ meta.offerte_regel = "336.01: Jaarlijkse..."
    }
  }
}
```

### Mapping naar YAML bind-paths:

| JSON pad | Transform output | YAML bind | Pagina |
|---|---|---|---|
| `report_type` | `meta.factuur_kop` | `meta.factuur_kop` | Voorblad |
| `cover.extra_fields.Datum` | `meta.datum` | `meta.datum` | Voorblad |
| `cover.extra_fields.Factuurnummer` | `meta.factuurnummer` | `meta.factuurnummer` | Voorblad |
| `cover.extra_fields.Type offerte` | `meta.type_offerte` | `meta.type_offerte` | Voorblad |
| `Offertecode + Offertenaam` | `meta.offerte_regel` | `meta.offerte_regel` | Voorblad |
| `report_type + location.code` | `meta.rapportkop_locatie` | `meta.rapportkop_locatie` | Footer |

## Locatie Sectie

```json
{
  "sections": [
    {
      "title": "Locatie",
      "content": [
        {
          "type": "location_detail",              // ← TRIGGER voor locatie parsing
          "client": {
            "name": "Haagwonen",                  // → client.name
            "address": "Wielingenstraat 22",      // → client.address
            "city": "2584 XZ Den Haag"            // → client.postcode_plaats
          },
          "location": {
            "name": "Strandbaak Kijkduin",        // → location.name
            "address": "Kijkduinsestraat 730-798", // → location.address
            "city": "2554 EB Den Haag",            // → location.postcode_plaats
            "code": "HW-DH-0336",                 // → location.code
            "provision": "Droge blusleiding / BMI", // → location.provision
            "object": "Flatgebouw Strandbaak"      // → location.object
          },
          "photo_path": null                       // pad naar luchtfoto (optioneel)
        }
      ]
    }
  ]
}
```

### Mapping:

| JSON pad | Transform output | YAML bind | Pagina |
|---|---|---|---|
| `content[].client.name` | `client.name` | `client.name` | Locatie, BIC footer |
| `content[].client.address` | `client.address` | `client.address` | Locatie |
| `content[].client.city` | `client.postcode_plaats` | `client.postcode_plaats` | Locatie |
| `content[].location.name` | `location.name` | `location.name` | Locatie, BIC header |
| `content[].location.address` | `location.address` | `location.address` | Locatie |
| `content[].location.city` | `location.postcode_plaats` | `location.postcode_plaats` | Locatie |
| `content[].location.code` | `location.code` | `location.code` | Locatie |
| `content[].location.provision` | `location.provision` | `location.provision` | Locatie |
| `content[].location.object` | `location.object` | `location.object` | Locatie |

## BIC Controles Sectie

```json
{
  "sections": [
    {
      "title": "BIC Controles",
      "content": [
        {
          "type": "bic_table",                     // ← TRIGGER voor BIC parsing
          "location_name": "Strandbaak Kijkduin",  // (informatief, niet getransformeerd)
          "sections": [
            {
              "title": "BIC controles",            // → match op "bic controle" → bic.*
              "rows": [
                { "label": "Aantal BIC controles",
                  "ref_value": "6",                // → bic.aantal_conform
                  "actual_value": "6" },           // → bic.aantal_werkelijk
                { "label": "Kosten",
                  "ref_value": "€ 1.860,00",       // → bic.kosten_conform (1e "Kosten")
                  "actual_value": "€ 1.860,00" },  // → bic.kosten_werkelijk
                { "label": "Aantal interne inspecties",
                  "ref_value": "3",                // → bic.hydro_aantal_conform
                  "actual_value": "4" },           // → bic.hydro_aantal_werkelijk
                { "label": "Kosten",
                  "ref_value": "€ 720,00",         // → bic.hydro_kosten_conform (2e "Kosten")
                  "actual_value": "€ 960,00" },    // → bic.hydro_kosten_werkelijk
                { "label": "Reiskosten",
                  "ref_value": "€ 270,00",         // → bic.reiskosten_conform
                  "actual_value": "€ 324,00" },    // → bic.reiskosten_werkelijk
                { "label": "Subtotaal",
                  "ref_value": "€ 2.850,00",       // → bic.subtotaal_conform
                  "actual_value": "€ 3.144,00" }   // → bic.subtotaal_werkelijk
              ]
            },
            {
              "title": "Reinigen tijdens BIC",     // → match op "reinig" → reiniging.*
              "rows": [
                { "label": "Aantal reinigingen", "ref_value": "3", "actual_value": "4" },
                { "label": "Kosten",
                  "ref_value": "€ 525,00",         // → reiniging.kosten_conform
                  "actual_value": "€ 700,00" }     // → reiniging.kosten_werkelijk
              ]
            },
            {
              "title": "Additioneel tijdens BIC",  // → match op "additioneel" → additioneel.*
              "rows": [
                { "label": "Aantal additionele activiteiten", "ref_value": "", "actual_value": "2" },
                { "label": "Kosten",
                  "ref_value": "",                 // → additioneel.kosten_conform
                  "actual_value": "€ 430,00" }     // → additioneel.kosten_werkelijk
              ]
            }
          ],
          "summary": {
            "title": "Overzicht samenvatting",
            "rows": [
              { "label": "BIC controles",          // → match "bic" → samenvatting.bic_*
                "ref_value": "€ 2.850,00",
                "actual_value": "€ 3.144,00" },
              { "label": "Reinigen tijdens BIC",   // → match "reinig" → samenvatting.reinigen_*
                "ref_value": "€ 525,00",
                "actual_value": "€ 700,00" },
              { "label": "Additioneel tijdens BIC", // → match "additioneel" → samenvatting.additioneel_*
                "ref_value": "",
                "actual_value": "€ 430,00" }
            ],
            "total": {
              "label": "Totaal",
              "ref_value": "€ 3.375,00",           // → samenvatting.totaal_conform
              "actual_value": "€ 4.274,00"          // → samenvatting.totaal_werkelijk
            }
          }
        }
      ]
    }
  ]
}
```

### BIC Mapping (volledig):

| JSON label match | Transform output | YAML bind |
|---|---|---|
| "Aantal BIC controles" | `bic.aantal_conform` / `bic.aantal_werkelijk` | `bic.aantal_conform` etc. |
| 1e "Kosten" in BIC | `bic.kosten_conform` / `bic.kosten_werkelijk` | `bic.kosten_conform` etc. |
| "Aantal interne inspecties" | `bic.hydro_aantal_conform` / `...werkelijk` | `bic.hydro_aantal_conform` etc. |
| 2e "Kosten" in BIC | `bic.hydro_kosten_conform` / `...werkelijk` | `bic.hydro_kosten_conform` etc. |
| "Reiskosten" | `bic.reiskosten_conform` / `...werkelijk` | `bic.reiskosten_conform` etc. |
| "Subtotaal" | `bic.subtotaal_conform` / `...werkelijk` | `bic.subtotaal_conform` etc. |
| Section "Reinig*" → "Kosten" | `reiniging.kosten_conform` / `...werkelijk` | `reiniging.kosten_conform` etc. |
| Section "Additioneel*" → "Kosten" | `additioneel.kosten_conform` / `...werkelijk` | `additioneel.kosten_conform` etc. |
| Summary "BIC*" | `samenvatting.bic_conform` / `...werkelijk` | `samenvatting.bic_conform` etc. |
| Summary "Reinig*" | `samenvatting.reinigen_conform` / `...werkelijk` | `samenvatting.reinigen_conform` etc. |
| Summary "Additioneel*" | `samenvatting.additioneel_conform` / `...werkelijk` | `samenvatting.additioneel_conform` etc. |
| Summary total | `samenvatting.totaal_conform` / `...werkelijk` | `samenvatting.totaal_conform` etc. |

## Detail Weergave (Tabel)

```json
{
  "sections": [
    {
      "title": "Detail weergave",                  // ← match op "Detail" → detail_items
      "orientation": "landscape",
      "content": [
        {
          "type": "table",                          // ← TRIGGER voor tabel parsing
          "headers": [
            "BIC Controle nummer",                  // → detail_items[].BIC Controle nummer
            "Type",                                 // → detail_items[].Type
            "Datum",                                // → detail_items[].Datum
            "BIC controle",                         // → detail_items[].BIC controle
            "Int. inspectie",                       // → detail_items[].Int. inspectie
            "Reiniging",                            // → detail_items[].Reiniging
            "Additioneel"                           // → detail_items[].Additioneel
          ],
          "rows": [
            ["BIC-2025-0336-001", "Droge blusleiding", "12-03-2025", "€ 310,00", "", "", ""],
            ["BIC-2025-0336-002", "BMI", "12-03-2025", "€ 310,00", "€ 240,00", "€ 175,00", ""]
          ]
        }
      ]
    }
  ]
}
```

**Transform output:** `detail_items` = lijst van dicts:
```json
[
  {"BIC Controle nummer": "BIC-2025-0336-001", "Type": "Droge blusleiding", ...},
  {"BIC Controle nummer": "BIC-2025-0336-002", "Type": "BMI", ...}
]
```

**YAML tabel config** (detail_weergave.yaml) bindt via `data_key: detail_items`.

## Objecten (Tabel)

```json
{
  "sections": [
    {
      "title": "Voorziening en objecten beschrijving",  // ← match op "objecten"/"Voorziening"
      "orientation": "landscape",
      "content": [
        {
          "type": "table",
          "headers": [
            "Voorziening", "Type", "Status", "Object",
            "Type", "Beschrijving", "Gebouw", "Ruimte"
          ],
          "rows": [
            ["Droge blusleiding", "DBL-A", "Actief", "Stijgleiding 1", "Stijgleiding", "...", "...", "..."]
          ]
        }
      ]
    }
  ]
}
```

**Let op:** Dubbele "Type" header → 2e wordt automatisch "Type2" in transform.

**Transform output:** `objecten` = lijst van dicts met key `Type2` voor 2e kolom.

## Overige Secties

```json
{
  "colofon": { "enabled": false },     // Colofon pagina aan/uit
  "toc": { "enabled": false },          // Inhoudsopgave aan/uit
  "backcover": { "enabled": true }      // Achterblad aan/uit
}
```

## Compleet Voorbeeld

Zie: `schemas/test_336_bic_factuur.json`
