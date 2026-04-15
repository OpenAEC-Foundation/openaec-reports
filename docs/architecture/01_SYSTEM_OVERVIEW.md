# Systeemarchitectuur — BM Reports

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GEBRUIKER / KLANT                            │
│                                                                     │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐     │
│   │  Admin Panel  │    │  JSON Upload  │    │  API Integratie  │     │
│   │  (React UI)   │    │  (direct)     │    │  (extern systeem)│     │
│   └──────┬───────┘    └──────┬───────┘    └────────┬─────────┘     │
│          │                   │                      │               │
└──────────┼───────────────────┼──────────────────────┼───────────────┘
           │                   │                      │
           ▼                   ▼                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     FASTAPI SERVER (api.py)                          │
│                     report.open-aec.com                                │
│                                                                     │
│   /api/generate/template ◄── De route die we gebruiken              │
│   /api/generate          ◄── Legacy V1 (ReportLab)                  │
│   /api/generate/v2       ◄── Legacy V2 (PyMuPDF direct)             │
│                                                                     │
│   ┌─────────────────────────────────────────────────────────────┐   │
│   │  1. Auth check (JWT token)                                   │   │
│   │  2. Template naam → Tenant detectie                          │   │
│   │     "customer_bic_factuur" → tenant=customer, tpl=bic_factuur│   │
│   │  3. data_transform.py  ← TRANSFORMATIE LAAG                  │   │
│   │     JSON (genest) → flat dict (dot-notatie)                  │   │
│   │  4. TemplateEngine.build()                                   │   │
│   └─────────────────────────────────────────────────────────────┘   │
│                              │                                      │
└──────────────────────────────┼──────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    TEMPLATE ENGINE (core)                            │
│                                                                     │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐       │
│   │ template_     │     │ template_    │     │ brand.yaml   │       │
│   │ config.py     │     │ engine.py    │     │ (per tenant) │       │
│   │               │     │              │     │              │       │
│   │ Parseert:     │     │ Bouwt PDF:   │     │ Definieert:  │       │
│   │ - PageType    │────▶│ - Stationery │◄────│ - Kleuren    │       │
│   │ - TextZone    │     │ - TextZones  │     │ - Fonts      │       │
│   │ - LineZone    │     │ - LineZones  │     │ - Styles     │       │
│   │ - TableConfig │     │ - Tables     │     │ - Logos      │       │
│   └──────────────┘     │ - Pages      │     └──────────────┘       │
│                         └──────┬───────┘                            │
│                                │                                    │
└────────────────────────────────┼────────────────────────────────────┘
                                 ▼
                            📄 PDF OUTPUT
```

## Data Flow — Van JSON naar PDF

```
JSON Input                data_transform.py           Template Engine
(genest formaat)         (transformatie laag)         (flat dict binding)
────────────────         ──────────────────           ─────────────────

{                        Detecteert formaat:
  "template": "...",     ┌─────────────────┐
  "project": "...",      │ Heeft 'sections' │──YES──▶ Transformeer
  "sections": [          │ list?            │         genest → flat
    {                    │                  │
      "content": [       │ Heeft 'bic' dict │──YES──▶ Pass-through
        {                │ zonder sections? │         (al flat)
          "type":        └─────────────────┘
            "bic_table", 
          "sections":              │
            [...]                  ▼
        }                ┌─────────────────┐
      ]                  │  FLAT OUTPUT:    │
    }                    │                  │
  ]                      │  meta.factuur_kop│──▶ YAML bind: meta.factuur_kop
}                        │  bic.aantal_     │──▶ YAML bind: bic.aantal_conform
                         │    conform       │
                         │  samenvatting.   │──▶ YAML bind: samenvatting.
                         │    totaal_       │      totaal_werkelijk
                         │    werkelijk     │
                         └─────────────────┘
```

## Tenant Directory Structuur

```
tenants/
├── customer/                          ◄── TENANT
│   ├── brand.yaml                     ◄── Huisstijl definitie
│   ├── fonts/                         ◄── Font bestanden (.ttf/.otf)
│   │   ├── arial.ttf
│   │   └── arialbd.ttf
│   ├── stationery/                    ◄── Achtergrond PDF's per pagina
│   │   ├── cover_stationery.pdf
│   │   ├── content_portrait_stationery.pdf
│   │   ├── content_landscape_stationery.pdf
│   │   └── backcover_stationery.pdf
│   ├── templates/                     ◄── Document templates
│   │   └── bic_factuur.yaml           ◄── Welke pagina's in welke volgorde
│   ├── page_types/                    ◄── Pagina layout definities
│   │   ├── voorblad_bic.yaml          ◄── Exact waar tekst/lijnen komen
│   │   ├── locatie.yaml
│   │   ├── bic_controles.yaml
│   │   ├── detail_weergave.yaml
│   │   ├── objecten.yaml
│   │   └── achterblad.yaml
│   └── modules/                       ◄── (Legacy, niet gebruikt door V3)
│
├── default/                           ◄── DEFAULT TENANT (public)
│   ├── brand.yaml
│   ├── fonts/
│   ├── stationery/
│   └── templates/
│
└── [nieuwe_tenant]/                   ◄── ZO VOEG JE EEN TENANT TOE
    ├── brand.yaml
    ├── fonts/
    ├── stationery/
    ├── templates/
    └── page_types/
```

## Pagina Type Hiërarchie

```
Template YAML (bic_factuur.yaml)
│
│  Definieert de VOLGORDE van pagina's
│  en hun type (special / fixed / flow)
│
├── Page 1: special → voorblad_bic.yaml
│   └── Stationery: cover_stationery.pdf
│       Engine rendert: alleen gebonden waarden
│
├── Page 2: fixed → locatie.yaml  
│   └── Stationery: content_portrait_stationery.pdf
│       Engine rendert: labels + waarden + foto placeholder
│
├── Page 3: fixed (repeat:none) → bic_controles.yaml
│   └── Stationery: content_portrait_stationery.pdf (SCHOON canvas)
│       Engine rendert: ALLES (labels, waarden, lijnen)
│
├── Page 4: fixed (repeat:auto) → detail_weergave.yaml
│   └── Stationery: content_landscape_stationery.pdf
│       Engine rendert: tabel met header + rijen + lijnen
│       Auto-paginering bij overflow
│
├── Page 5: fixed (repeat:auto) → objecten.yaml
│   └── Stationery: content_landscape_stationery.pdf
│       Engine rendert: tabel met header + rijen + lijnen
│       Auto-paginering bij overflow
│
└── Page 6: special → achterblad.yaml
    └── Stationery: backcover_stationery.pdf
        Engine rendert: statische tekst + footer
```

## Pagina Types Uitgelegd

```
┌─────────────────────────────────────────────────────────────────┐
│ TYPE: special                                                    │
│ Gebruik: Cover, achterblad, colofon                             │
│ Kenmerken:                                                       │
│   - Stationery bevat veel grafische elementen                   │
│   - Engine rendert alleen dynamische waarden                    │
│   - Geen herhaling / paginering                                 │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ TYPE: fixed (repeat: none)                                       │
│ Gebruik: BIC controles, kostenoverzichten                       │
│ Kenmerken:                                                       │
│   - Stationery = schoon canvas (alleen header/footer balk)      │
│   - Engine rendert ALLES: text_zones + line_zones               │
│   - Exact 1 pagina, geen herhaling                              │
│   - Alle coördinaten pixel-exact in YAML                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ TYPE: fixed (repeat: auto)                                       │
│ Gebruik: Detail tabellen, objecten lijsten                      │
│ Kenmerken:                                                       │
│   - Stationery = schoon canvas                                  │
│   - Engine rendert: tabel (table: config) + text_zones + lines  │
│   - Automatische paginering als data niet past                  │
│   - Tabel rijen komen uit array in JSON (detail_items, objecten)│
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ TYPE: flow                                                       │
│ Gebruik: Lopende tekst, mixed content                           │
│ Kenmerken:                                                       │
│   - ReportLab Flowables (Paragraph, Table, etc.)                │
│   - Automatische paginering door ReportLab zelf                 │
│   - Niet gebruikt bij Customer BIC (alles is fixed)             │
└─────────────────────────────────────────────────────────────────┘
```
