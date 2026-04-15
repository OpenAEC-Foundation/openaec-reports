# pyRevit Integratie — OpenAEC Report Generator API

> Versie: 2026-02-21 | API: `POST /api/generate/v2`

---

## Overzicht

De OpenAEC Report Generator API accepteert JSON en retourneert een PDF.
Vanuit pyRevit (CPython 3.8+) stuur je een HTTP POST met de rapportdata.

```
pyRevit script  →  bouwt JSON dict  →  POST naar API  →  ontvangt PDF bytes  →  slaat op
```

**API Base URL:** `https://report.open-aec.com`

---

## Minimaal Voorbeeld (alleen berekeningen)

```python
import json
import requests

API_URL = "https://report.open-aec.com/api/generate/v2"

data = {
    "project": "Kijkduin Reddingspost",
    "report_type": "Berekening",

    # Schakel speciale pagina's uit voor een kaal rekenblad:
    "cover":     {"enabled": False},
    "colofon":   {"enabled": False},
    "toc":       {"enabled": False},
    "backcover": {"enabled": False},

    "sections": [
        {
            "number": "1",
            "title": "Staalligger L1 — HEA 200",
            "level": 1,
            "content": [
                {
                    "type": "paragraph",
                    "text": "Ligger overspant 6.0 m. Profiel: HEA 200, S235."
                },
                {
                    "type": "calculation",
                    "title": "Veldmoment M_Ed",
                    "formula": "M_Ed = q * l^2 / 8",
                    "substitution": "M_Ed = 8.7 * 6.0^2 / 8",
                    "result": "39.1",
                    "unit": "kNm",
                    "reference": "NEN-EN 1993-1-1"
                },
                {
                    "type": "check",
                    "description": "Unity check buiging L1",
                    "required_value": "UC <= 1.0",
                    "calculated_value": "M_Ed / M_Rd = 39.1 / 100.9",
                    "unity_check": 0.39,
                    "result": "VOLDOET"
                }
            ]
        }
    ]
}

response = requests.post(API_URL, json=data)
response.raise_for_status()

output_path = r"C:\Temp\berekening.pdf"
with open(output_path, "wb") as f:
    f.write(response.content)
print(f"PDF opgeslagen: {output_path}")
```

---

## Volledig Voorbeeld (met voorblad, colofon, etc.)

```python
data = {
    # --- Verplicht ---
    "project": "Kijkduin Reddingspost",

    # --- Optioneel: metadata ---
    "report_type": "Constructieve berekening",
    "project_number": "2026-031",
    "client": "Gemeente Den Haag",
    "author": "Default Author",
    "date": "2026-02-21",
    "version": "1.0",
    "status": "CONCEPT",            # CONCEPT | DEFINITIEF | REVISIE
    "brand": "default",             # Huisstijl (default: value of OPENAEC_DEFAULT_BRAND)

    # --- Voorblad ---
    "cover": {
        "enabled": True,             # False = geen voorblad
        "subtitle": "Constructieve berekening hoofddraagconstructie",
        "extra_fields": {
            "Kenmerk": "OA-2026-031-R01",
            "Classificatie": "Vertrouwelijk"
        }
        # "image": { ... }          # Zie sectie "Afbeeldingen" hieronder
    },

    # --- Colofon ---
    "colofon": {
        "enabled": True,
        "revision_history": [
            {"version": "0.1", "date": "2026-01-15", "author": "J. Kolthof", "description": "Eerste concept"},
            {"version": "1.0", "date": "2026-02-21", "author": "J. Kolthof", "description": "Definitief"}
        ]
    },

    # --- Inhoudsopgave ---
    "toc": {
        "enabled": True,
        "max_depth": 3               # 1=alleen H1, 2=H1+H2, 3=alles
    },

    # --- Inhoud ---
    "sections": [ ... ],             # Zie "Content Blocks" hieronder

    # --- Achterblad ---
    "backcover": {
        "enabled": True
    },

    # --- Vrije metadata (wordt niet gerenderd) ---
    "metadata": {
        "revit_model": "2026-031_Kijkduin_S.rvt",
        "software": "Technosoft Frilo R-2024.1"
    }
}
```

---

## Content Blocks — Referentie

Elke sectie bevat een `content` array met blocks. Elk block heeft een `type` veld.

### `paragraph` — Tekst

```json
{
    "type": "paragraph",
    "text": "Dit is een paragraaf met uitleg."
}
```

| Veld | Type | Verplicht | Toelichting |
|------|------|-----------|-------------|
| `text` | string | ja | Platte tekst (HTML wordt automatisch gestript) |
| `style` | string | nee | `"Heading1"`, `"Heading2"`, of leeg voor normaal |

> **Let op:** Heading1/Heading2 als style maakt er een kopje van.
> Voor sectie-koppen gebruik je liever een aparte `section` met `level: 1` of `level: 2`.

### `calculation` — Berekening

```json
{
    "type": "calculation",
    "title": "Veldmoment M_Ed",
    "formula": "M_Ed = q * l^2 / 8",
    "substitution": "M_Ed = 8.7 * 6.0^2 / 8",
    "result": "39.1",
    "unit": "kNm",
    "reference": "NEN-EN 1993-1-1"
}
```

| Veld | Type | Verplicht | Toelichting |
|------|------|-----------|-------------|
| `title` | string | ja | Naam van de berekening |
| `formula` | string | nee | Wiskundige formule |
| `substitution` | string | nee | Ingevulde waarden |
| `result` | string | nee | Uitkomst (als tekst) |
| `unit` | string | nee | Eenheid: `kNm`, `mm`, `kN/m2`, etc. |
| `reference` | string | nee | Normreferentie |

### `check` — Unity Check

```json
{
    "type": "check",
    "description": "Unity check buiging ligger L1",
    "required_value": "UC <= 1.0",
    "calculated_value": "M_Ed / M_Rd = 39.1 / 100.9",
    "unity_check": 0.39,
    "result": "VOLDOET"
}
```

| Veld | Type | Verplicht | Toelichting |
|------|------|-----------|-------------|
| `description` | string | ja | Omschrijving van de toets |
| `required_value` | string | nee | Eis / grenswaarde (tekst) |
| `calculated_value` | string | nee | Berekende waarde (tekst) |
| `unity_check` | number | nee | UC-waarde (0.0 - ...) |
| `limit` | number | nee | Grens (default: 1.0) |
| `result` | string | nee | `"VOLDOET"` of `"VOLDOET NIET"`. Auto als weggelaten. |
| `reference` | string | nee | Normreferentie |

### `table` — Tabel

```json
{
    "type": "table",
    "title": "Toegepaste materialen",
    "headers": ["Onderdeel", "Materiaal", "Sterkteklasse"],
    "rows": [
        ["Fundering", "Gewapend beton", "C20/25"],
        ["Liggers", "Staal", "S235"]
    ]
}
```

| Veld | Type | Verplicht | Toelichting |
|------|------|-----------|-------------|
| `title` | string | nee | Titel boven de tabel |
| `headers` | string[] | ja | Kolomnamen |
| `rows` | any[][] | ja | Data als 2D array |
| `column_widths` | number[] | nee | Breedtes in mm (auto als weggelaten) |
| `style` | string | nee | `"default"`, `"minimal"`, `"striped"` |

### `image` — Afbeelding

```json
{
    "type": "image",
    "src": {
        "data": "<base64 string>",
        "media_type": "image/png"
    },
    "caption": "Figuur 1: Dwarsdoorsnede ligger L1",
    "width_mm": 150,
    "alignment": "center"
}
```

| Veld | Type | Verplicht | Toelichting |
|------|------|-----------|-------------|
| `src` | string of object | ja | Zie "Afbeeldingen" hieronder |
| `caption` | string | nee | Bijschrift |
| `width_mm` | number | nee | Breedte in mm (auto-fit als weggelaten) |
| `alignment` | string | nee | `"left"`, `"center"`, `"right"` |

### `map` — Kadasterkaart (PDOK)

```json
{
    "type": "map",
    "center": {"lat": 52.0975, "lon": 4.2200},
    "radius_m": 150,
    "layers": ["percelen", "bebouwing", "luchtfoto"],
    "caption": "Kadastrale situering"
}
```

| Veld | Type | Verplicht | Toelichting |
|------|------|-----------|-------------|
| `center.lat` | number | ja | Breedtegraad (WGS84) |
| `center.lon` | number | ja | Lengtegraad (WGS84) |
| `radius_m` | number | nee | Straal in meters (default: 100) |
| `layers` | string[] | nee | `"percelen"`, `"bebouwing"`, `"bestemmingsplan"`, `"luchtfoto"` |
| `width_mm` | number | nee | Kaartbreedte in mm (default: 170) |
| `caption` | string | nee | Bijschrift |

### `spacer` — Witruimte

```json
{"type": "spacer", "height_mm": 15}
```

### `page_break` — Pagina-einde

```json
{"type": "page_break"}
```

---

## Secties (Sections)

Secties zijn de hoofdindeling van het rapport. Elke sectie heeft een titel die in de inhoudsopgave verschijnt.

```json
{
    "number": "3",
    "title": "Staalligger L1 — HEA 200",
    "level": 1,
    "page_break_before": true,
    "content": [ ... ]
}
```

| Veld | Type | Verplicht | Toelichting |
|------|------|-----------|-------------|
| `title` | string | ja | Sectietitel (verschijnt in TOC) |
| `number` | string | nee | Sectienummer (`"1"`, `"2.3"`, etc.) |
| `level` | integer | nee | 1 = Hoofdstuk, 2 = Paragraaf, 3 = Subparagraaf |
| `page_break_before` | boolean | nee | Forceer nieuwe pagina voor deze sectie |
| `content` | block[] | nee | Array van content blocks |

---

## Afbeeldingen

Afbeeldingen (`src` in image block en cover) accepteren drie formaten:

### 1. Base64 (aanbevolen voor API)

```python
import base64

with open("screenshot.png", "rb") as f:
    img_data = base64.b64encode(f.read()).decode()

block = {
    "type": "image",
    "src": {
        "data": img_data,
        "media_type": "image/png"    # image/png | image/jpeg | image/svg+xml
    },
    "caption": "Figuur 1"
}
```

### 2. Bestandspad (alleen library-direct, niet via API)

```json
{"type": "image", "src": "renders/gevel_west.png"}
```

### 3. Upload via API (voor grote bestanden)

```python
UPLOAD_URL = "https://report.open-aec.com/api/upload"

# Stap 1: upload
with open("grote_render.png", "rb") as f:
    resp = requests.post(UPLOAD_URL, files={"file": f})
    upload_path = resp.json()["path"]

# Stap 2: gebruik pad in rapport JSON
block = {"type": "image", "src": upload_path}
```

---

## Speciale Pagina's Aan/Uit

Elk van de vier speciale pagina's kan onafhankelijk worden in- of uitgeschakeld:

```json
{
    "cover":     {"enabled": true},
    "colofon":   {"enabled": true},
    "toc":       {"enabled": true},
    "backcover": {"enabled": true}
}
```

**Typische combinaties:**

| Gebruik | cover | colofon | toc | backcover |
|---------|-------|---------|-----|-----------|
| Volledig rapport | true | true | true | true |
| Rekenblad (kaal) | false | false | false | false |
| Berekening met voorblad | true | false | false | false |
| Intern concept | true | true | false | false |

---

## API Referentie

Alle endpoints op `https://report.open-aec.com`:

| Methode | Endpoint | Omschrijving |
|---------|----------|--------------|
| `POST` | `/api/generate/v2` | **PDF genereren** — JSON in, PDF uit |
| `POST` | `/api/validate` | JSON valideren tegen schema |
| `POST` | `/api/upload` | Afbeelding uploaden |
| `GET` | `/api/templates` | Beschikbare templates |
| `GET` | `/api/templates/{name}/scaffold` | Leeg JSON-startpunt voor template |
| `GET` | `/api/brands` | Beschikbare huisstijlen |
| `GET` | `/api/health` | Health check |

**`POST /api/generate/v2`**
- **Request:** `Content-Type: application/json`
- **Response:** `application/pdf` (binary)
- **Verplicht veld:** `project`

**`POST /api/validate`**
- **Response:** `{"valid": true, "errors": []}`

---

## pyRevit Helper Functie

Kant-en-klare functie voor gebruik in pyRevit scripts:

```python
"""OpenAEC Report Generator — pyRevit helper."""
import json
import base64
import requests


API_URL = "https://report.open-aec.com/api/generate/v2"


def generate_report(data: dict, output_path: str, api_url: str = API_URL) -> str:
    """Stuur rapport JSON naar API en sla PDF op.

    Args:
        data: Rapport dict conform report.schema.json.
        output_path: Pad waar de PDF wordt opgeslagen.
        api_url: API endpoint URL.

    Returns:
        Pad naar de gegenereerde PDF.

    Raises:
        requests.HTTPError: Bij API fout.
    """
    response = requests.post(api_url, json=data, timeout=30)
    response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(response.content)
    return output_path


def image_to_base64(file_path: str) -> dict:
    """Converteer afbeelding naar base64 dict voor gebruik in JSON.

    Args:
        file_path: Pad naar PNG/JPG bestand.

    Returns:
        Dict met 'data' en 'media_type' keys.
    """
    ext = file_path.rsplit(".", 1)[-1].lower()
    media_types = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "svg": "image/svg+xml"}
    media_type = media_types.get(ext, "image/png")

    with open(file_path, "rb") as f:
        data = base64.b64encode(f.read()).decode()

    return {"data": data, "media_type": media_type}
```

**Gebruik in pyRevit:**

```python
from pyrevit import revit, DB
from report_helper import generate_report, image_to_base64

# Bouw rapport data vanuit Revit model
doc = revit.doc
project_info = doc.ProjectInformation

data = {
    "project": project_info.Name,
    "project_number": project_info.Number,
    "report_type": "Constructieve berekening",
    "cover": {"enabled": True},
    "colofon": {"enabled": False},
    "toc": {"enabled": False},
    "backcover": {"enabled": False},
    "sections": [
        {
            "number": "1",
            "title": "Uitgangspunten",
            "level": 1,
            "content": [
                {"type": "paragraph", "text": f"Project: {project_info.Name}"},
                {"type": "paragraph", "text": f"Adres: {project_info.Address}"},
            ]
        }
    ]
}

output = r"C:\Temp\{}_berekening.pdf".format(project_info.Number)
generate_report(data, output)
print("PDF gegenereerd: {}".format(output))
```

---

## JSON Schema

Het volledige JSON Schema staat in `schemas/report.schema.json` in de repo.
Valideer je JSON via de API voordat je genereert:

```python
import requests

data = { ... }  # je rapport JSON
resp = requests.post("https://report.open-aec.com/api/validate", json=data)
result = resp.json()
if not result["valid"]:
    for err in result["errors"]:
        print(f"  {err['path']}: {err['message']}")
```

---

## Lokaal Ontwikkelen

Voor lokaal testen zonder de productieserver:

```bash
pip install -e ".[dev]"
openaec-report serve --port 8000 --reload
```

Pas dan `API_URL` aan naar `http://localhost:8000/api/generate/v2`.
