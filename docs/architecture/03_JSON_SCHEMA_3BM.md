# JSON Input Schema — 3BM Coöperatie

## Overzicht

3BM Coöperatie gebruikt een andere template-structuur dan Symitech.
De documenten zijn flow-based (lopende tekst met secties) in plaats van
fixed-page layouts.

> ⚠️ **STATUS:** 3BM templates draaien op V1 (engine.py) en V2 (renderer_v2.py).
> Migratie naar V3 (template_engine.py) is nog niet gestart.
> Dit schema beschrijft het HUIDIGE formaat voor V1/V2.

## Verplichte Top-Level Velden

```json
{
  "template": "structural_report",      // Template naam (zonder tenant prefix)
  "project": "Constructieve beoordeling woning",
  "project_number": "2786.01",
  "client": "Particulier",
  "author": "3BM Coöperatie",
  "date": "2025-12-15",
  "version": "1.0",
  "status": "DEFINITIEF"
}
```

## Beschikbare Templates

| Template | Type | Beschrijving |
|---|---|---|
| `structural_report` | Flow | Constructief rapport |
| `building_code` | Flow | Bouwbesluit toets |
| `daylight` | Flow | Daglichtberekening |
| `standaard` | Flow | Standaard rapport |

## Secties Structuur

3BM gebruikt een geneste `sections` structuur met content blocks:

```json
{
  "sections": [
    {
      "title": "Inleiding",
      "level": 1,
      "content": [
        {
          "type": "paragraph",
          "text": "Lopende tekst..."
        }
      ]
    },
    {
      "title": "Berekeningen",
      "level": 1,
      "content": [
        {
          "type": "calculation",
          "description": "Draagvermogen HEA 200",
          "formula": "M_Ed / M_Rd",
          "input_values": { "M_Ed": 45.2, "M_Rd": 56.5 },
          "result": 0.80,
          "unit": "UC",
          "check": "OK"
        },
        {
          "type": "table",
          "headers": ["Profiel", "M_Rd [kNm]", "V_Rd [kN]"],
          "rows": [
            ["HEA 200", "56.5", "210.3"],
            ["HEA 240", "83.4", "285.1"]
          ]
        },
        {
          "type": "image",
          "src": "/uploads/detail_01.png",
          "caption": "Detail ligger-kolom verbinding",
          "width": 400
        }
      ]
    }
  ]
}
```

## Content Block Types

| Type | Gebruik | Verplichte velden |
|---|---|---|
| `paragraph` | Lopende tekst | `text` |
| `calculation` | Berekening met check | `description`, `formula`, `result`, `check` |
| `table` | Data tabel | `headers`, `rows` |
| `image` | Afbeelding | `src` |
| `check_block` | Toetsingsresultaat | `description`, `result`, `norm_ref` |
| `map` | Kadastrale kaart | `address` of `cadastral_id` |

## Cover en Speciale Pagina's

```json
{
  "cover": {
    "subtitle": "Constructieve beoordeling",
    "image": "/uploads/project_foto.jpg"
  },
  "colofon": {
    "enabled": true
  },
  "toc": {
    "enabled": true,
    "depth": 2
  },
  "backcover": {
    "enabled": true
  }
}
```

## Stationery

3BM gebruikt 4 stationery PDF's:
- `colofon.pdf` — Colofon achtergrond
- `standaard.pdf` — Content pagina's
- `bijlagen.pdf` — Bijlagen pagina's
- `achterblad.pdf` — Achterblad

## Verschil met Symitech

| Aspect | 3BM Coöperatie | Symitech |
|---|---|---|
| Engine | V1/V2 (legacy) | V3 (template_engine) |
| Page model | Flow (ReportLab flowables) | Fixed (pixel-exact coords) |
| Content | Lopende tekst + berekeningen | Tabellen + kostenoverzichten |
| Stationery | 4 generieke PDF's | 5 specifieke PDF's per pagina |
| Page types | N.v.t. (engine bepaalt layout) | YAML per pagina type |
| Data transform | Niet nodig (direct) | `data_transform.py` genest→flat |

## Toekomst: V3 Migratie

Wanneer 3BM naar V3 migreert:
1. Maak `tenants/3bm_cooperatie/page_types/` aan
2. Definieer page_types per rapport type
3. Maak template YAML's (welke pagina's in welke volgorde)
4. Verplaats stationery naar `tenants/3bm_cooperatie/stationery/`
5. Schrijf `data_transform` regels voor 3BM content blocks
