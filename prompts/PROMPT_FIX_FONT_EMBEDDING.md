# Fix: Gotham fonts niet embedded in PDF — lege pagina's bij ontvangers

## Probleem

De gegenereerde PDF's tonen tekst alleen als Gotham lokaal geïnstalleerd is. Voor alle andere gebruikers zijn de pagina's LEEG. De fonts worden als referentie opgenomen maar niet als subset embedded.

## Root cause

In `src/bm_reports/core/renderer_v2.py` wordt overal `page.insert_text()` gebruikt met `fontname="GothamBook"` / `"GothamBold"`. PyMuPDF's `insert_text()` met een string fontname embed het font NIET betrouwbaar als subset in de output PDF — het maakt alleen een referentie aan. Als de font niet op het systeem van de lezer staat, is de tekst onzichtbaar.

De juiste aanpak is `fitz.TextWriter` + `page.write_text()` met een `fitz.Font` object. Dit embed WEL een font subset.

## Scope

Alleen `src/bm_reports/core/renderer_v2.py` moet aangepast worden. De overige files (special_pages.py, engine.py) gebruiken ReportLab dat fonts WEL correct embed via `pdfmetrics.registerFont(TTFont(...))`.

## Exacte wijzigingen

### 1. FontManager: voeg helper methode toe

De `FontManager` class heeft al `self.gotham_book` en `self.gotham_bold` als `fitz.Font` objecten. Voeg toe:

```python
def get_fitz_font(self, fontname: str) -> fitz.Font:
    """Return fitz.Font object for given fontname string."""
    if fontname in ("GothamBold",):
        return self.gotham_bold
    return self.gotham_book  # default fallback voor GothamBook, GothamMedium, etc.
```

### 2. ContentRenderer._text(): gebruik TextWriter

Verander de `_text()` methode van:

```python
def _text(self, x, y_td, text, fontname, size, color_hex):
    self.page.insert_text(
        (x, y_td + size * 0.8), text,
        fontname=fontname, fontsize=size,
        color=_hex_to_rgb(color_hex),
    )
```

Naar:

```python
def _text(self, x, y_td, text, fontname, size, color_hex):
    """Insert text met embedded font subset via TextWriter."""
    if not self.page or not text:
        return
    font_obj = self.fonts.get_fitz_font(fontname)
    tw = fitz.TextWriter(self.page.rect)
    tw.append((x, y_td + size * 0.8), text, font=font_obj, fontsize=size)
    self.page.write_text(tw, color=_hex_to_rgb(color_hex))
```

### 3. Alle DIRECTE page.insert_text() calls vervangen

Er zijn nog directe `page.insert_text()` calls buiten `_text()`. Zoek en vervang ze allemaal:

**a) `_add_page_number()`** — gebruikt `self.page.insert_text(...)` → maak er een `_text()` call van.

**b) `bullet_list()`** — de bullet marker "•" wordt met directe `page.insert_text()` geplaatst → gebruik `_text()`.

**c) `table()` methode** — header cells en body cells gebruiken `self.page.insert_text()` → vervang door dezelfde TextWriter pattern. Let op: in de table methode wordt `page` soms als local variable gebruikt, dus gebruik daar ook `fitz.TextWriter(self.page.rect)`.

**d) `ColofonGenerator.generate()`** — alle `page.insert_text()` calls → gebruik hetzelfde TextWriter pattern. De ColofonGenerator heeft `self.fonts` beschikbaar.

### 4. insert_into_page() is niet meer nodig

Na de TextWriter refactor is `self.fonts.insert_into_page(page)` in `_new_page()` niet meer strikt nodig (TextWriter embed fonts zelf). Je MAG deze call laten staan voor backward compatibility, maar het is geen vereiste meer.

### 5. Verwijder NIET

- Verwijder GEEN bestaande methodes of public API
- Verwijder NIET de `insert_into_page()` methode uit FontManager (kan nog elders gebruikt worden)
- Wijzig GEEN YAML templates of stationery bestanden
- Wijzig GEEN files buiten `renderer_v2.py`

## Verificatie

Na de wijziging:

1. `python -m pytest tests/ -v` → alle tests moeten slagen
2. Genereer een test-PDF via de API of CLI
3. Open de PDF op een systeem ZONDER Gotham geïnstalleerd (of in een browser PDF viewer)
4. Alle tekst moet zichtbaar zijn

## Samenvatting van alle plekken met insert_text in renderer_v2.py

Regelnummers (huidige versie):
- Regel ~351, ~366, ~384, ~394: ColofonGenerator.generate() — 4x insert_text
- Regel ~510: ContentRenderer._text() — de centrale helper
- Regel ~529: _add_page_number()  
- Regel ~667: bullet_list() bullet marker
- Regel ~777, ~827: table() header en body cells (in render_header() en body rows loop)

Totaal: **11 insert_text calls** → allemaal vervangen door TextWriter pattern.
