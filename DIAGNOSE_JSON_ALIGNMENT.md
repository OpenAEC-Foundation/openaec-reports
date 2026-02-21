# Diagnose: Frontend → Renderer_v2 JSON Alignment

**Datum:** 2026-02-21
**Doel:** Exact in kaart brengen waarom de frontend JSON 422-errors geeft bij `/api/generate/v2`

---

## 🔴 KRITIEK — Blokkerende issues

### 1. `template` veld wordt misbruikt als brand selector

**Frontend export:**
```json
{ "template": "custom" }
```

**API endpoint (`api.py` regel ~192):**
```python
brand = data.get("template", data.get("brand", "default"))
```

**Renderer (`TemplateSet.__init__`):**
```python
self.dir = TEMPLATES_DIR / brand  # → assets/templates/custom/ → BESTAAT NIET
```

**Probleem:** De frontend gebruikt `template` voor het rapport-type (bijv. "custom", "structural"), maar de API stuurt deze waarde door als brand/directory naam. Er is geen `assets/templates/custom/` directory → `FileNotFoundError`.

**Fix:** De API moet `template` en `brand` ontkoppelen. Hardcode brand op `"default"` of voeg een apart `brand` veld toe aan de frontend.

---

### 2. Paragraph blocks bevatten HTML, renderer verwacht plain text

**Frontend export (vanuit Tiptap editor):**
```json
{ "type": "paragraph", "text": "<p>Dit is <strong>vetgedrukt</strong> en een <em>schuine</em> tekst.</p>" }
```

**Renderer_v2.paragraph():**
```python
def paragraph(self, text: str) -> None:
    lines = self.fonts.wrap_text(text, ...)  # Wrap op ruwe string inclusief HTML tags
    self._text(s["x"], self.y, line, ...)    # Rendert "<p>Dit is <strong>..." letterlijk
```

**Probleem:** HTML tags verschijnen letterlijk in de PDF output. De renderer heeft geen HTML-stripper/parser.

**Fix (twee opties):**
- **A) Backend:** Voeg een `strip_html(text)` helper toe die tags verwijdert vóór rendering. Simpelste fix.
- **B) Frontend:** Strip HTML bij export in `toSchemaBlock()`. Beter voor data-integriteit, maar verliest opmaak.
- **C) Ideaal (later):** Parse HTML naar rich text flowables (bold/italic/links). Grote klus.

---

### 3. Cover image: base64 dict niet afgehandeld

**Frontend kan sturen:**
```json
{ "cover": { "image": { "data": "iVBOR...", "media_type": "image/png" } } }
```

**CoverGenerator.generate():**
```python
cover_image = data.get("cover", {}).get("image")
if cover_image and Path(cover_image).exists():  # ← Path(dict) → TypeError!
```

**Probleem:** `ContentRenderer._resolve_image()` handelt base64 dicts WEL correct af, maar `CoverGenerator` doet dat NIET. Als de frontend een geüploade cover-afbeelding als base64 meestuurt → crash.

**Fix:** Gebruik dezelfde `_resolve_image()` logica in CoverGenerator, of maak het een shared utility.

---

## 🟡 MEDIUM — Functionele gaps

### 4. `map` block type niet geïmplementeerd in renderer

**Frontend kan exporteren:**
```json
{ "type": "map", "center": { "lat": 52.08, "lon": 4.31 }, "layers": ["percelen"] }
```

**Renderer_v2._render_block():** Geen `map` case → `logger.warning("Unsupported block type: map")` en wordt overgeslagen.

**Fix:** Voeg een `map()` method toe aan ContentRenderer, of render een placeholder "[Kaart: niet beschikbaar in v2]".

---

### 5. `style` veld op ParagraphBlock wordt genegeerd

**Frontend kan sturen:**
```json
{ "type": "paragraph", "text": "Hoofdstuktitel", "style": "Heading1" }
```

**Renderer:** Kijkt alleen naar `block.get("text")`, negeert `style` volledig. Een paragraph met `style: "Heading2"` wordt als normale tekst gerenderd.

**Fix:** Check `style` in `_render_block()` en dispatch naar `heading_1/heading_2` als style dat aangeeft. Of: frontend moet heading-style paragraphs als aparte `heading_1`/`heading_2` blocks exporteren.

---

### 6. Colofon `status_colofon` vs root `status`

**Frontend Colofon type heeft:**
```typescript
status_colofon?: string;  // In colofon object
```

**Renderer leest:**
```python
"status": data.get("status", "CONCEPT"),  # Van ROOT object, niet colofon
```

**Probleem:** Als de frontend status alleen in `colofon.status_colofon` zet en niet op root level, wordt het niet opgepakt.

**Fix:** Renderer ook `colofon.get("status_colofon", ...)` checken als fallback.

---

## 🟢 MINOR — Werkt maar niet optimaal

### 7. Section level altijd 1, sub-sections via heading_2 blocks

**Frontend export:** Alle sections krijgen `level: 1` (of level wordt weggelaten als het 1 is). Sub-secties worden als `heading_2` blocks IN de content van een section gezet.

**Renderer:** Werkt prima — `render_section()` rendered de section heading_1, en heading_2 blocks in content worden correct afgehandeld. ✅ Geen actie nodig.

---

### 8. Section nummering is string, niet nested

**Frontend export:** `number: "1"`, `number: "2"` (simpele string-index)

**Renderer:** Gebruikt `number` direct als string in heading. Werkt, maar sub-section nummering (1.1, 1.2) moet handmatig in heading_2 blocks gezet worden.

**Geen blocker**, maar auto-nummering zou een nice-to-have zijn.

---

### 9. Appendix content_sections formaat is compatibel ✅

Frontend `toContentSections()` exporteert exact het formaat dat `_render_content()` verwacht:
```json
{
  "content_sections": [
    { "number": "B1", "title": "...", "level": 1, "content": [...] }
  ]
}
```
Geen actie nodig.

---

## Prioriteit Fix-Volgorde

| # | Issue | Impact | Effort |
|---|-------|--------|--------|
| 1 | Template/brand ontkoppeling | 🔴 Crash | 15 min |
| 2 | HTML strip in paragraphs | 🔴 Onleesbare PDF | 30 min |
| 3 | Cover base64 image handling | 🔴 Crash bij upload | 20 min |
| 4 | Map block placeholder | 🟡 Stille skip | 15 min |
| 5 | Paragraph style dispatch | 🟡 Verkeerde rendering | 20 min |
| 6 | Status colofon fallback | 🟡 Ontbrekend veld | 5 min |

**Geschatte totale effort:** ~2 uur voor een Claude Code sessie.

---

## Opdracht voor Claude Code

```
Lees DIAGNOSE_JSON_ALIGNMENT.md en fix de issues in volgorde van prioriteit:

1. In api.py: ontkoppel template/brand - gebruik altijd "default" als brand,
   of voeg een apart "brand" veld toe. Template is het rapport-type, niet de brand.

2. In renderer_v2.py ContentRenderer.paragraph(): strip HTML tags uit text
   vóór word-wrapping. Gebruik een simpele regex of html.parser.

3. In renderer_v2.py CoverGenerator.generate(): gebruik dezelfde image resolve
   logica als ContentRenderer._resolve_image() voor cover images.

4. In renderer_v2.py ContentRenderer._render_block(): voeg een "map" case toe
   die een placeholder rendert.

5. In renderer_v2.py ContentRenderer._render_block(): check paragraph block
   "style" veld en dispatch naar heading methods als style Heading1/Heading2 is.

6. In renderer_v2.py ColofonGenerator._build_field_map(): voeg fallback toe
   voor colofon.status_colofon naast data.status.

Test na elke fix met: python -m pytest tests/test_renderer_v2.py -v
Commit na elke fix.
```
