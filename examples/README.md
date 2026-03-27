# Voorbeelden — openaec-reports

Voorbeeld JSON-bestanden per tenant, direct bruikbaar via API, CLI of frontend.

## Structuur

```
examples/
├── 3bm_cooperatie/           V1/V2 engine rapporten
│   ├── structural_report.json
│   ├── constructieve_berekening.json
│   ├── bouwkundige_opname.json
│   ├── haalbaarheidsadvies.json
│   ├── bbl_toetsing.json
│   └── adviesbrief.json
├── symitech/                 V3 template engine rapporten
│   ├── bic_factuur.json          BIC factuur (kort)
│   ├── bic_rapport.json          BIC rapport (volledig, 17 pagina's)
│   ├── bic_rapport_kort.json     BIC rapport (minimaal)
│   └── bic_rapport_minimal.json  BIC rapport (schema-conform, beknopt)
├── openaec_foundation/       OpenAEC branded rapporten
│   └── structural_report.json
└── scripts/                  Python voorbeeldscripts
    ├── example_structural.py
    ├── generate_showcase.py
    ├── generate_integration_test.py
    └── pyrevit_generate_report.py
```

## Gebruik

### CLI
```bash
openaec-report generate \
  --template structural \
  --data examples/3bm_cooperatie/structural_report.json \
  --output output/test.pdf
```

### API
```bash
curl -X POST https://report.3bm.co.nl/api/generate/v2 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d @examples/3bm_cooperatie/constructieve_berekening.json \
  -o rapport.pdf
```

### Template Engine (Symitech)
```bash
curl -X POST https://report.3bm.co.nl/api/generate/template \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d @examples/symitech/bic_rapport.json \
  -o bic_rapport.pdf
```

### Python
```python
from openaec_reports.core.template_engine import TemplateEngine
import json

with open("examples/symitech/bic_rapport.json") as f:
    data = json.load(f)

engine = TemplateEngine()
engine.build(template_name="bic_rapport", tenant="symitech",
             data=data, output_path="output/test.pdf")
```

## Engines

| Tenant | Engine | Endpoint |
|--------|--------|----------|
| `3bm_cooperatie` | V1/V2 (ReportLab/PyMuPDF) | `/api/generate` of `/api/generate/v2` |
| `symitech` | V3 (TemplateEngine) | `/api/generate/template` |
| `openaec_foundation` | V3 (TemplateEngine) | `/api/generate/template` |
