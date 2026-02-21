# 3BM Huisstijl Specificatie — Volledige Layout

Geëxtraheerd uit `2707_BBLrapportage_v01.pdf` (36 pagina's, A4 portrait).
Alle coördinaten in **points** (1 pt = 0.3528 mm). Pagina = 595.3 × 841.9 pt (210 × 297 mm).

---

## 1. COVER (pagina 1) — ✅ AL GEÏMPLEMENTEERD

Geen wijzigingen nodig. Werkt via `special_pages.py → draw_cover_page()`.

---

## 2. COLOFON (pagina 2) — ⚠️ MOET HERSCHREVEN

### 2.1 Header zone (bovenin)

| Element | Font | Size | Kleur | X (pt) | Y_top (pt) |
|---------|------|------|-------|---------|-------------|
| Rapport type titel | GothamBold | 22.0 | #401246 | 70.9 | 57.3 |
| Project subtitel | GothamBook | 14.0 | #38BDAB | 70.9 | 86.8 |

### 2.2 Informatieblok

Twee kolommen: labels (x=103.0) en waarden (x=229.1).
Eerste twee velden = projectinfo (GothamBold, #401246), rest = metadata (GothamBold, #38BDAB).
Waarden altijd GothamBook 10pt #401246.

| Label | Y_top (pt) | Label kleur | Voorbeeld waarde |
|-------|------------|-------------|------------------|
| **Project** | 320.8 | #401246 (paars) | 2707 - Transformatie... |
| **In opdracht van** | 368.8 | #401246 (paars) | Mounir Riffi MSc / Sping Real Estate / Adres |
| — scheidslijn — | 517 | — | lijn x=102→420, stroke 0.25pt, #401146 |
| **Adviseur** | 488.8 | #38BDAB (turquoise) | 3BM Cooperatie / J. Kolthof |
| **Toegepaste Normen** | 524.8 | #38BDAB | BBL, NEN 2057, NEN 2580... |
| — scheidslijn — | 542 | — | |
| **Documentgegevens** | 548.8 | #38BDAB | BBL-toetsing, pg 1-19... |
| — scheidslijn — | 566 | — | |
| **Datum rapport** | 572.8 | #38BDAB | 05-07-2025 |
| — scheidslijn — | 590 | — | |
| **Fase in bouwproces** | 596.8 | #38BDAB | Haalbaarheidsstudie |
| — scheidslijn — | 614 | — | |
| **Rapportstatus** | 620.8 | #38BDAB | concept |
| — scheidslijn — | 638 | — | |
| **Documentkenmerk** | 644.8 | #38BDAB | 2707-BBL-01 |

Scheidingslijnen: `x1=102, x2=420, y=<value>`, stroke_width=0.25, kleur #401146.

### 2.3 Footer

- Turquoise rechthoek: `[0, 771, 282, 842]` → x=0, y=0 (from bottom), w=282pt (99.5mm), h=71pt (25mm)
- 3BM logo (pixelblokjes): paars/turquoise rond x=346-468, y=768-811
- "Coöperatie" tekst: diverse kleine blokjes (logo-onderdeel)
- Paginanummer: "2" bij x=534, y_top=796.3, SegoeUI-Bold 8pt, kleur #38BDAB

---

## 3. INHOUDSOPGAVE / TOC (pagina 3) — ⚠️ MOET HERSCHREVEN

### 3.1 Titel

| Element | Font | Size | Kleur | X | Y_top |
|---------|------|------|-------|---|-------|
| "Inhoud" | Gotham-Book | 18.0 | #45243D | 90.0 | 74.9 |

### 3.2 Hoofdstuk entries (level 1)

| Eigenschap | Waarde |
|------------|--------|
| Font | Gotham-Book |
| Size | 12.0 pt |
| Kleur | #56B49B (licht turquoise) |
| Nummer X | 90.0 |
| Titel X | 160.9 |
| Pagina X | 515.4 (rechts uitgelijnd) |
| Verticale spacing | ~39-40 pt tussen hoofdstukken |

### 3.3 Sub-entries (level 2)

| Eigenschap | Waarde |
|------------|--------|
| Font | Gotham-Book |
| Size | 9.5 pt |
| Kleur | #45243D (donkerpaars tekst) |
| Nummer X | 90.0 |
| Titel X | 160.9 |
| Pagina X | 515.4 |
| Verticale spacing | ~17 pt tussen sub-items |

### 3.4 Footer

- Alleen paginanummer: x=532.9, y_top=793.5, Gotham-Book 9.5pt, kleur #45243D
- **GEEN** turquoise blok, **GEEN** logo
- Achtergrondafbeelding (watermerk/decoratief element) aanwezig

---

## 4. CONTENT PAGINA'S (pagina's 4-20) — ⚠️ KRITIEK: FOOTER MOET ANDERS

### 4.1 Header

**GEEN HEADER.** `header.height = 0` is correct.

### 4.2 Footer — ALLEEN paginanummer

**⚡ KRITIEK VERSCHIL MET HUIDIGE IMPLEMENTATIE:**
De huidige `3bm_cooperatie.yaml` tekent een turquoise blok + logo + paginanummer in de footer.
In het referentiedocument hebben content pagina's **ALLEEN** een paginanummer rechtsonder.

| Eigenschap | Waarde |
|------------|--------|
| Font | Gotham-Book |
| Size | 9.5 pt |
| Kleur | #45243D |
| X positie | ~533 pt (rechts uitgelijnd naar rechter marge) |
| Y_top | 793.5 pt (= ca. 17 mm vanaf onderkant pagina) |

**Geen turquoise blok. Geen logo. Alleen het paginanummer.**

### 4.3 Content marges

| Marge | Waarde (pt) | Waarde (mm) |
|-------|-------------|-------------|
| Links | 90.0 | 31.7 |
| Rechts | 53.7 (= 595.3 - 541.6) | 18.9 |
| Boven | ~74.9 (eerste tekst) | 26.4 |
| Onder | ~38.9 (= 841.9 - 803) | 13.7 |

### 4.4 Heading 1 (sectietitel)

| Eigenschap | Waarde |
|------------|--------|
| Font | Gotham-Book (NIET Bold!) |
| Size | 18.0 pt |
| Kleur | #45243D |
| X nummer | 90.0 |
| X titel | 108.0 |
| Voorbeeld | "2  Inleiding" |
| spaceBefore | 0 (start bovenaan content area) |

### 4.5 Heading 2 (sub-sectie)

| Eigenschap | Waarde |
|------------|--------|
| Font | Gotham-Book |
| Size | 13.0 pt |
| Kleur | #56B49B |
| X nummer | 125.4 |
| X titel | 147.0 |
| Voorbeeld | "1.1  Toegepaste documenten:" |
| spaceBefore | ~20-24 pt |

### 4.6 Body tekst

| Eigenschap | Waarde |
|------------|--------|
| Font | Gotham-Book |
| Size | 9.5 pt |
| Leading | ~12 pt |
| Kleur | #45243D |
| X links | 125.4 pt (normale tekst) |
| X links | 143.4 pt (ingesprongen / na bullet) |
| X rechts max | 541.6 pt |

### 4.7 Bullet points

| Eigenschap | Waarde |
|------------|--------|
| Bullet char | • (SymbolMT) |
| Bullet X | 125.4 |
| Tekst X | 143.4 |
| Bullet size | 9.5 pt |
| Kleur | #45243D |

### 4.8 Tabellen

Uit pagina 5:

| Eigenschap | Waarde |
|------------|--------|
| Header achtergrond | #45233C (donkerpaars) |
| Header tekst | Gotham-Book 12pt, wit (#FFFFFF) |
| Body tekst | Gotham-Book 9pt, #45243D |
| Totaal/footer rij achtergrond | #55B49B (turquoise) |
| Tabel X start | 127 pt |
| Tabel X eind | 543 pt |
| Tabel breedte | 416 pt |
| Kolom scheiding | ~5 pt padding |

---

## 5. BIJLAGE SCHEIDINGSPAGINA (pagina 21) — ⚠️ MOET HERSCHREVEN

### 5.1 Achtergrond

- Volledig turquoise: `#37BCAB` over hele pagina
- Paars blok onderaan: `[0, 771, 282, 842]` = x=0, y_bottom=0, w=282, h=71 → **zelfde als colofon footer**

### 5.2 Tekst

| Element | Font | Size | Kleur | X | Y_top |
|---------|------|------|-------|---|-------|
| "Bijlage 1" | GothamBold | 41.4 | #401246 | 103.0 | 193.9 |
| Bijlage titel regel 1 | GothamBook | 41.4 | #FFFFFF | 136.1 | 262.2 |
| Bijlage titel regel 2 | GothamBook | 41.4 | #FFFFFF | 136.1 | 328.6 |
| "Projecten die inspireren" | GothamBold | 17.9 | #401246 | 330.5 | 785.1 |

---

## 6. BACKCOVER (pagina 36) — ✅ AL GEÏMPLEMENTEERD

Geen wijzigingen nodig. Werkt via `special_pages.py → draw_backcover_page()`.

---

## 7. KLEURENPALET (bevestigd)

| Naam | Hex | Gebruik |
|------|-----|---------|
| primary | #401246 | Titels, labels, tabel headers |
| secondary / turquoise | #38BDAB | Subtitels, H2 headings, colofon footer |
| text | #45243D | Body tekst, H1 headings, paginanummers |
| text_green | #56B49B | TOC chapters, H2 sub-secties, tabel footer |
| wit | #FFFFFF | Achtergrond, tekst op kleurvlakken |

**Let op:** #56B49B (content H2/TOC) verschilt van #38BDAB (cover subtitle/colofon labels). Twee turquoise tinten!

---

## 8. FONT GEBRUIK (bevestigd)

| Context | Font | Gewicht |
|---------|------|---------|
| Cover titel | GothamBold | Bold |
| Cover subtitle | GothamBook | Regular |
| Colofon labels | GothamBold | Bold |
| Colofon waarden | GothamBook | Regular |
| H1 sectie titel | Gotham-Book | Regular (!) |
| H2 sub-sectie | Gotham-Book | Regular |
| Body tekst | Gotham-Book | Regular |
| Bijlage nummer | GothamBold | Bold |
| Bijlage titel | GothamBook | Regular |
| Paginanummer | Gotham-Book | Regular |

**Opvallend:** H1 gebruikt Gotham-Book (regular), NIET Bold. Dit verschilt van de huidige styles.py die GothamBold gebruikt voor headings.

---

## 9. SAMENVATTING: WAT MOET GEWIJZIGD WORDEN

### 9.1 Brand YAML (`3bm_cooperatie.yaml`)

**Footer moet ALLEEN paginanummer bevatten:**
```yaml
footer:
  height: 17   # was 25 — nu alleen ruimte voor paginanummer
  elements:
    - type: text
      content: "{page}"
      x: 188      # rechts uitgelijnd (~533pt)
      y: 5
      font: "$body"
      size: 9.5
      color: "$text"
      align: right
```

**Verwijder:** turquoise rect, logo image, bold font reference in footer.

### 9.2 Styles (`styles.py`)

| Style | Huidig | Moet worden |
|-------|--------|-------------|
| Normal/body | fontSize=9.0, Helvetica | fontSize=9.5, GothamBook |
| Heading1 | GothamBold 16pt, #40124A | GothamBook 18pt, #45243D |
| Heading2 | GothamBold 13pt, #40124A | GothamBook 13pt, #56B49B |
| Heading3 | GothamBold 11pt, #38BDA0 | (optioneel, niet in referentie) |
| textColor default | #45243D | #45243D ✅ correct |

### 9.3 Colofon (`special_pages.py`)

Volledig herschrijven met exact de 2-kolom layout:
- Header: titel + subtitel
- Info tabel met scheidingslijnen
- Footer met turquoise blok + logo (ALLEEN op colofon, niet op content)

### 9.4 TOC rendering

Herschrijven met juiste typografie:
- Titel "Inhoud" in Gotham-Book 18pt
- Level 1 entries in 12pt turquoise (#56B49B)
- Level 2 entries in 9.5pt paars (#45243D)
- Nummer kolom, titel kolom, paginanummer kolom

### 9.5 Bijlage scheidingspagina

Toevoegen aan special_pages.py:
- Turquoise achtergrond
- Paars blok onderaan
- Bijlage nummer + titel
