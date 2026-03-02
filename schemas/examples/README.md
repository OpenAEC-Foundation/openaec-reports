# Voorbeeld JSON's — 3BM Rapporten

Voorbeelddata voor de 3BM Report Generator. Elk bestand is direct te gebruiken via de API of frontend.

## Bestanden

| Bestand | Type | Beschrijving |
|---------|------|-------------|
| `voorbeeld_constructieve_berekening.json` | Constructief rapport | Berekening uitbouw woning — latei, dakliggers, fundering. Met calculations en unity checks. |
| `voorbeeld_bouwkundige_opname.json` | Inspectie rapport | Aankoopkeuring bestaande woning — gevels, dak, installaties, kostenoverzicht. |
| `voorbeeld_haalbaarheidsadvies.json` | Haalbaarheidsadvies | Dakopbouw VvE — funderingsreserve, planologie, bouwfysica. Mix van berekeningen en advies. |
| `voorbeeld_bbl_toetsing.json` | Bbl toetsing | Hoofdstuk 4 toetsing nieuwbouw — daglicht, ventilatie, geluid, toegankelijkheid. Veel tabellen. |
| `voorbeeld_adviesbrief.json` | Adviesbrief | Funderingsherstel — briefstijl, geen inhoudsopgave, twee opties met kostenraming. |

## Gebruik

### Via API
```bash
curl -X POST https://report.3bm.co.nl/api/generate/v2 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d @voorbeeld_constructieve_berekening.json \
  -o rapport.pdf
```

### Via frontend
Upload het JSON bestand op report.3bm.co.nl → "Rapport data laden".

### Lokaal testen
```bash
python -c "
from openaec_reports.core.renderer_v2 import ReportGeneratorV2
import json
data = json.loads(open('schemas/examples/voorbeeld_adviesbrief.json').read())
gen = ReportGeneratorV2(brand='3bm_cooperatie')
gen.generate(data, 'src/openaec_reports/assets/stationery/3bm_cooperatie', 'output/test.pdf')
"
```
