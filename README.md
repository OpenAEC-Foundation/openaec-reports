# openaec-reports

Modulaire Python library voor het genereren van professionele A4/A3 engineering rapporten.

## Features

- **Pixel-perfecte PDF output** via ReportLab
- **Modulaire componenten**: headers, footers, berekeningsblokken, toetsingsblokken, tabellen
- **YAML-configureerbare templates** voor verschillende rapporttypen
- **Inhoudsopgave** automatisch gegenereerd
- **Kadaster integratie** via PDOK API
- **Revit integratie** via pyRevit en JSON exchange
- **A4 en A3** ondersteuning

## Rapporttypen

- Constructieve berekeningen
- Daglichtberekeningen
- Bouwbesluit toetsingen
- Vrij configureerbare rapporten

## Installatie

```bash
pip install -e ".[dev]"
```

## Snel starten

```python
from openaec_reports import Report, A4

report = Report(
    format=A4,
    project="Mijn Project",
    project_number="2026-001",
    client="Opdrachtgever",
    report_type="structural",
)

report.add_cover(subtitle="Constructieve berekening")
report.add_section("Uitgangspunten", content=[...])
report.add_check("UC buiging", unity_check=0.73, limit=1.0)
report.build("output/rapport.pdf")
```

## Projectstructuur

```
src/openaec_reports/
├── core/         # Engine, document, templates, styles, TOC
├── components/   # Herbruikbare bouwblokken
├── reports/      # Rapporttype definities
├── data/         # Data adapters (Revit, JSON, Kadaster)
└── assets/       # Templates, fonts, graphics
```

## Licentie

MIT
