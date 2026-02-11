# 3BM Report Generator — `bm-reports`

Modulaire Python library voor het genereren van professionele A4/A3 engineering rapporten in 3BM huisstijl.

---

## Doel

Een herbruikbare, configureerbare PDF report generator die:
- Professionele rapporten genereert (constructie, daglicht, bouwbesluit, etc.)
- Integreert met Revit via pyRevit en JSON exchange
- Later inzetbaar is in eigen 3BM software
- Modulair opgebouwd is met YAML-configureerbare templates

---

## Tech Stack

- **Python 3.10+** (compatibel met pyRevit CPython engine)
- **ReportLab** (BSD) — PDF engine + Platypus layout
- **svglib** (BSD) — SVG naar ReportLab conversie
- **PyYAML** — Template configuratie
- **Pillow** — Image processing
- **requests** — PDOK/Kadaster API

---

## Architectuur

```
src/bm_reports/
├── core/         # Engine, document, page templates, styles, TOC
├── components/   # Header, footer, titelblok, tabellen, checks, kaarten
├── reports/      # Rapporttype definities (structural, daylight, building_code)
├── data/         # Adapters: Revit, ERPNext, JSON, Kadaster
└── assets/       # Templates (YAML), fonts, graphics, logos
```

**Kernprincipe:** Data-interface is altijd JSON. Rendering is verwisselbaar.

---

## Scope / Fasering

- [x] Fase 0: Projectstructuur + CI
- [ ] Fase 1: Core engine — A4 document, header/footer, simpele content blocks
- [ ] Fase 2: Templates — Voorblad, achterblad, colofon, YAML config, TOC
- [ ] Fase 3: Components — Berekeningsblokken, toetsing, tabellen, afbeeldingen
- [ ] Fase 4: Kadaster — PDOK integratie, kaartgeneratie
- [ ] Fase 5: Rapporten — Constructie, daglicht, bouwbesluit definities
- [ ] Fase 6: Revit — pyRevit commands, RevitAdapter, JSON exchange
- [ ] Fase 7: Polish — A3 support, huisstijl fine-tuning

---

## Belangrijke Bestanden

| Bestand | Doel |
|---------|------|
| `src/bm_reports/core/engine.py` | ReportLab wrapper, PDF assembly |
| `src/bm_reports/core/document.py` | Document class (A4/A3, margins) |
| `src/bm_reports/core/styles.py` | Huisstijl: fonts, kleuren, spacing |
| `src/bm_reports/core/toc.py` | Inhoudsopgave generator |
| `src/bm_reports/assets/templates/` | YAML rapport definities |
| `pyproject.toml` | Package config + dependencies |

---

## Conventies

1. **Code:** Python, type hints, docstrings (Google style)
2. **Eenheden:** mm voor afmetingen (ReportLab werkt intern in points, conversie in engine)
3. **Naming:** snake_case voor functies/variabelen, PascalCase voor classes
4. **Templates:** YAML bestanden in `src/bm_reports/assets/templates/`
5. **Assets:** SVG voor vectorgraphics, PNG voor rasterafbeeldingen
6. **Tests:** pytest, één testfile per module

---

## Notities

- ReportLab 1 point = 1/72 inch. Conversie: mm × 2.8346 = points
- PDOK WMS is gratis, geen API key nodig
- pyRevit CPython engine = Python 3.8+, geen IronPython beperkingen
- JSON exchange is de primaire data-interface (niet Revit-specifiek)
- ERPNext projectdata via bestaande MCP server (niet in deze library)
