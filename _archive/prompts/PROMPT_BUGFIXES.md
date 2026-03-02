# Fix: Backend bugfixes uit code review

Er zijn 4 bugs gevonden in de backend. Fix ze in deze volgorde:

## Fix 1: Kleur typfout in special_pages.py (SNEL)

**Probleem:** `_BADGE_TEXT_DARK` gebruikt `#401246` maar de huisstijl primary kleur is `#40124A`. Twee hex-tekens omgedraaid.

**Huidige code:**
```python
_BADGE_TEXT_DARK = HexColor("#401246")
```

**Fix:** Vervang door een verwijzing naar de bestaande constante:
```python
_BADGE_TEXT_DARK = _COLOR_PRIMARY
```

Dat elimineert de duplicatie én de typfout in één keer.

---

## Fix 2: extra_fields schema mismatch tussen frontend en backend (KRITIEK)

**Probleem:** De frontend (conform het JSON schema) stuurt `extra_fields` als een `Record<string, string>` (dict), bijv:
```json
{"extra_fields": {"Constructeur": "Ing. Jansen", "Tekenaar": "P. de Vries"}}
```

Maar `_build_colofon_rows()` in `special_pages.py` verwacht een list van dicts:
```python
for ef in data.get("extra_fields", []):
    if isinstance(ef, dict) and ef.get("label") and ef.get("value"):
```

Dit betekent dat extra_fields vanuit de frontend **stilzwijgend genegeerd worden**.

**Fix:** Pas `_build_colofon_rows()` aan om beide formaten te accepteren:

```python
# Vervang het huidige extra_fields blok door:
extra_fields = data.get("extra_fields", {})
if isinstance(extra_fields, dict):
    for label, value in extra_fields.items():
        if label and value:
            rows.append((label, str(value)))
elif isinstance(extra_fields, list):
    for ef in extra_fields:
        if isinstance(ef, dict) and ef.get("label") and ef.get("value"):
            rows.append((ef["label"], str(ef["value"])))
```

---

## Fix 3: cover_image relatief pad wordt niet geresolved (KRITIEK)

**Probleem:** Als de JSON een relatief pad voor de cover image bevat (`"image": "foto.jpg"`), wordt dit ongeresolved doorgegeven aan `draw_cover_page()`. De `Path(image_path).exists()` check in `_draw_clipped_photo()` faalt dan als het script vanuit een andere working directory draait.

De `from_dict()` methode in `engine.py` ontvangt een `base_dir` parameter en resolved image paden voor content blocks via `create_block(block_data, base_dir=base_dir)`. Maar voor de cover image ontbreekt deze resolutie.

**Fix:** In `engine.py`, methode `Report.from_dict()`, pas het cover blok aan:

Zoek:
```python
cover = data.get("cover")
if cover is not None:
    report.add_cover(
        subtitle=cover.get("subtitle", ""),
        image=cover.get("image"),
    )
```

Vervang door:
```python
cover = data.get("cover")
if cover is not None:
    cover_image = cover.get("image")
    if cover_image and isinstance(cover_image, str) and base_dir:
        cover_path = Path(cover_image)
        if not cover_path.is_absolute():
            cover_image = str(base_dir / cover_image)
    report.add_cover(
        subtitle=cover.get("subtitle", ""),
        image=cover_image,
    )
```

Let op: `Path` moet al geïmporteerd zijn bovenaan engine.py (check dit, zo niet: `from pathlib import Path`).

---

## Fix 4: Hardcoded contactgegevens naar brand YAML (ONDERHOUD)

**Probleem:** De backcover contactgegevens staan hardcoded in `draw_backcover_page()`:
```python
canvas.drawString(contact_x, contact_y, "3bm Coöperatie U.A.")
canvas.drawString(..., "Wattstraat 17  |  3335 LV Zwijndrecht  |  T. 078 7400 250")
canvas.drawString(..., "Ontdek ons  →  3bm.co.nl")
```

Als het adres of telefoonnummer verandert, moet je Python code aanpassen in plaats van YAML config.

**Fix stap 1:** Voeg een `contact` sectie toe aan `assets/brands/3bm_cooperatie.yaml`:

```yaml
contact:
  name: "3bm Coöperatie U.A."
  address: "Wattstraat 17  |  3335 LV Zwijndrecht  |  T. 078 7400 250"
  website: "3bm.co.nl"
```

**Fix stap 2:** Voeg `contact` toe aan de `BrandConfig` dataclass in `brand.py`:

```python
@dataclass
class BrandConfig:
    name: str = "Default"
    slug: str = "default"
    colors: dict[str, str] = field(default_factory=dict)
    fonts: dict[str, str] = field(default_factory=dict)
    header: ZoneConfig = field(default_factory=ZoneConfig)
    footer: ZoneConfig = field(default_factory=ZoneConfig)
    logos: dict[str, str] = field(default_factory=dict)
    contact: dict[str, str] = field(default_factory=dict)  # <-- NIEUW
```

Pas ook de `load()` methode in `BrandLoader` aan om `contact` te parsen:
```python
return BrandConfig(
    name=brand_info.get("name", name),
    slug=brand_info.get("slug", name),
    colors=data.get("colors", {}),
    fonts=data.get("fonts", {}),
    header=_parse_zone(data.get("header")),
    footer=_parse_zone(data.get("footer")),
    logos=data.get("logos", {}),
    contact=data.get("contact", {}),  # <-- NIEUW
)
```

**Fix stap 3:** Gebruik `brand.contact` in `draw_backcover_page()` in `special_pages.py`:

```python
# Vervang de hardcoded strings door:
contact = brand.contact
contact_name = contact.get("name", "3bm Coöperatie U.A.")
contact_address = contact.get("address", "")
contact_website = contact.get("website", "3bm.co.nl")

canvas.setFont(heading_font, name_size)
canvas.setFillColor(color_primary)
canvas.drawString(contact_x, contact_y, contact_name)

canvas.setFont(body_font, detail_size)
canvas.setFillColor(_COLOR_TEXT)
if contact_address:
    canvas.drawString(contact_x, contact_y - line_h, contact_address)

canvas.setFillColor(color_secondary)
canvas.drawString(contact_x, contact_y - 2 * line_h, f"Ontdek ons  \u2192  {contact_website}")
```

Voeg ook een `contact` sectie toe aan `assets/brands/default.yaml` met lege defaults:
```yaml
contact:
  name: ""
  address: ""
  website: ""
```

---

## Verificatie

Na alle fixes, run de tests:
```bash
cd X:\10_3BM_bouwkunde\50_Claude-Code-Projects\Report_generator
python -m pytest tests/test_special_pages.py -v
python -m pytest tests/ -v
```

Genereer daarna een test-PDF met alle special pages om visueel te verifiëren:
```python
from openaec_reports import A4, Report

report = Report(
    format=A4,
    project="Review Verificatie",
    project_number="2026-REV",
    client="Test BV",
    author="Ing. Reviewer",
    brand="3bm_cooperatie",
)
report.add_cover(subtitle="Bugfix verificatie rapport")
report.add_colofon(
    versie="1.0",
    status="CONCEPT",
    revision_history=[
        {"version": "0.1", "date": "2026-02-01", "author": "Test", "description": "Eerste opzet"},
        {"version": "1.0", "date": "2026-02-18", "author": "Review", "description": "Bugfixes"},
    ],
    extra_fields={"Constructeur": "Ing. Jansen", "Tekenaar": "P. de Vries"},
)
report.add_section("Test sectie", content=["Verificatie inhoud."])
report.add_backcover()
report.build("output/review_verificatie.pdf")
```

Open de PDF en controleer:
1. **Cover:** Badge teksten moeten dezelfde paarse kleur hebben als de titel
2. **Colofon:** "Constructeur" en "Tekenaar" moeten zichtbaar zijn in de informatietabel
3. **Backcover:** Contactgegevens moeten kloppen met de YAML config
