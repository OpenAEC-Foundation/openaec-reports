# Symitech API Handleiding

> API voor het genereren van Symitech BIC- en saneringsrapporten als PDF.

**Base URL:** `https://report.3bm.co.nl`

---

## Authenticatie

Alle endpoints (behalve `/api/health`) vereisen authenticatie via **API Key**:

```
X-API-Key: sym_xxxxxxxxxxxxxxxxxxxxxx
```

Of via **Bearer token**:

```
Authorization: Bearer <jwt_token>
```

API keys worden aangemaakt door de admin via het admin panel of CLI.

---

## Workflow

```
1. GET  /api/health                          → check of API draait
2. GET  /api/templates                       → beschikbare templates
3. GET  /api/templates/{name}/scaffold       → leeg rapport als startpunt
4. POST /api/validate                        → valideer JSON (optioneel)
5. POST /api/generate                        → genereer PDF
```

---

## Endpoints

### `GET /api/health`

Geen auth nodig.

```json
{"status": "ok", "version": "0.1.0"}
```

### `GET /api/templates`

```json
{
  "templates": [
    {"name": "symitech_bic_factuur", "type": "bic_factuur"},
    {"name": "symitech_bic_rapport", "type": "bic_rapport"},
    {"name": "symitech_sanering", "type": "sanering"}
  ]
}
```

### `GET /api/templates/symitech_bic_rapport/scaffold`

Retourneert een leeg rapport-JSON als startpunt. Vul de velden in en stuur naar `/api/generate`.

### `POST /api/validate`

Valideer rapport-JSON tegen het schema. Retourneert:

```json
{"valid": true, "errors": []}
```

Of bij fouten:

```json
{
  "valid": false,
  "errors": [
    {"path": "sections/0/content/0", "message": "..."}
  ]
}
```

### `POST /api/generate`

Stuur rapport-JSON, ontvang PDF.

- **Content-Type:** `application/json`
- **Response:** `application/pdf` (binary)
- **Filename:** afgeleid uit `project_number` + `project`

---

## Rapport JSON Structuur

### Verplichte velden

| Veld | Type | Beschrijving |
|------|------|-------------|
| `template` | string | `"symitech_bic_rapport"` of `"symitech_sanering"` |
| `project` | string | Projectnaam |

### Optionele velden

| Veld | Type | Default | Beschrijving |
|------|------|---------|-------------|
| `tenant` | string | — | `"symitech"` (activeert tenant modules) |
| `brand` | string | `"3bm_cooperatie"` | `"symitech"` voor Symitech huisstijl |
| `project_number` | string | — | Projectnummer |
| `client` | string | — | Opdrachtgever |
| `author` | string | `"3BM Bouwkunde"` | Auteur |
| `date` | string | vandaag | ISO 8601 datum (`"2026-03-15"`) |
| `version` | string | `"1.0"` | Versienummer |
| `status` | string | `"CONCEPT"` | `CONCEPT`, `DEFINITIEF`, of `REVISIE` |
| `cover` | object | — | Voorblad configuratie |
| `colofon` | object | — | Colofon / documentinfo |
| `toc` | object | — | Inhoudsopgave |
| `sections` | array | `[]` | Rapport secties |
| `backcover` | object | — | Achterblad |

---

## Symitech Block Types

Naast de standaard blocks (`paragraph`, `table`, `image`, etc.) heeft Symitech 4 eigen block types:

### `location_detail` — Locatiegegevens

```json
{
  "type": "location_detail",
  "title": "Locatie",
  "client": {
    "section_title": "Opdrachtgever",
    "name": "Gemeente Amsterdam",
    "address": "Amstel 1",
    "city": "1011 PN Amsterdam"
  },
  "location": {
    "section_title": "Locatie van uitvoer",
    "name": "Depot Noord",
    "address": "Industrieweg 10",
    "city": "1013 AB Amsterdam",
    "code": "LOC-2026-001",
    "provision": "Grondwatermonitoring",
    "object": "Peilbuis PB-01"
  },
  "photo_path": null
}
```

### `bic_table` — BIC Controle Tabel

Twee kolommen: "Conform opdracht" en "Werkelijke kosten".

```json
{
  "type": "bic_table",
  "location_name": "Amsterdam Noord",
  "sections": [
    {
      "title": "BIC Controles",
      "rows": [
        {"label": "Aantal BIC controles", "ref_value": "12", "actual_value": "14"},
        {"label": "Uren per controle", "ref_value": "2,0", "actual_value": "1,5"},
        {"label": "Reiskosten", "ref_value": "€ 450,00", "actual_value": "€ 525,00"}
      ]
    },
    {
      "title": "Rapportage",
      "rows": [
        {"label": "Tussenrapportages", "ref_value": "4", "actual_value": "4"},
        {"label": "Eindrapportage", "ref_value": "1", "actual_value": "1"}
      ]
    }
  ],
  "summary": {
    "title": "Overzicht samenvatting",
    "rows": [
      {"label": "BIC controles", "ref_value": "€ 3.400,00", "actual_value": "€ 2.975,00"},
      {"label": "Rapportage", "ref_value": "€ 1.150,00", "actual_value": "€ 1.150,00"}
    ],
    "total": {"label": "Totaal excl. BTW", "ref_value": "€ 4.550,00", "actual_value": "€ 4.125,00"}
  }
}
```

### `cost_summary` — Kostenopgave (landscape)

Gebruik in een sectie met `"orientation": "landscape"`.

```json
{
  "type": "cost_summary",
  "title": "Kostenopgave",
  "columns": ["Omschrijving", "Aantal", "Eenheidsprijs", "Totaal"],
  "rows": [
    {"description": "BIC controles", "quantity": 14, "unit_price": 212.50, "total": 2975.00},
    {"description": "Tussenrapportages", "quantity": 4, "unit_price": 225.00, "total": 900.00},
    {"description": "Eindrapportage", "quantity": 1, "unit_price": 250.00, "total": 250.00}
  ],
  "total": 4125.00
}
```

### `object_description` — Objectbeschrijving

```json
{
  "type": "object_description",
  "title": "Objectbeschrijving",
  "object_name": "Peilbuis PB-01",
  "fields": [
    {"label": "Type", "value": "Grondwaterpeilbuis"},
    {"label": "Diameter", "value": "50 mm"},
    {"label": "Diepte", "value": "12,5 m-mv"},
    {"label": "Filterdiepte", "value": "10,0 - 12,0 m-mv"},
    {"label": "Materiaal", "value": "PVC"}
  ],
  "notes": "Geplaatst in 2019. Jaarlijkse controle conform BRL SIKB 2000.",
  "photo_path": null
}
```

---

## Standaard Block Types

Deze zijn beschikbaar voor alle tenants:

| Type | Verplichte velden | Beschrijving |
|------|-------------------|-------------|
| `paragraph` | `text` | Tekst (supports `<b>`, `<i>`, `<sub>`, `<sup>`) |
| `table` | `headers`, `rows` | Tabel met kolomkoppen en rijen |
| `image` | `src` | Afbeelding (pad, URL, of base64) |
| `calculation` | `title` | Berekening met formule/resultaat |
| `check` | `description` | Unity check (voldoet/voldoet niet) |
| `bullet_list` | `items` | Opsommingslijst |
| `heading_2` | `title` | Subkop (H2) |
| `spacer` | — | Witruimte (`height_mm`, default 5) |
| `page_break` | — | Nieuwe pagina |

---

## Sectie Oriëntatie

Secties kunnen per stuk portrait of landscape zijn:

```json
{
  "title": "Kostenopgave",
  "orientation": "landscape",
  "content": [
    {"type": "cost_summary", "...": "..."}
  ]
}
```

De stationery achtergrond wisselt automatisch mee.

---

## Voorbeelden

| Template | Voorbeeld JSON |
|----------|---------------|
| `symitech_bic_factuur` | `docs/symitech_bic_factuur_example.json` |
| `symitech_bic_rapport` | `docs/symitech_bic_example.json` |

---

## Error Responses

| Status | Betekenis |
|--------|-----------|
| 400 | Ongeldige request (ontbrekende velden) |
| 401 | Niet geauthenticeerd |
| 404 | Template of brand niet gevonden |
| 422 | Validatiefout (schema mismatch) |
| 500 | Interne fout |

```json
{"detail": "Veld 'project' is verplicht", "type": "ValueError"}
```

---

## cURL Voorbeelden

### PDF genereren

```bash
curl -X POST https://report.3bm.co.nl/api/generate \
  -H "X-API-Key: sym_xxxxxxxxxxxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d @rapport.json \
  -o rapport.pdf
```

### Valideren

```bash
curl -X POST https://report.3bm.co.nl/api/validate \
  -H "X-API-Key: sym_xxxxxxxxxxxxxxxxxxxxxx" \
  -H "Content-Type: application/json" \
  -d @rapport.json
```

### Templates opvragen

```bash
curl https://report.3bm.co.nl/api/templates \
  -H "X-API-Key: sym_xxxxxxxxxxxxxxxxxxxxxx"
```
