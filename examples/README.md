# Voorbeelden — openaec-reports

Voorbeeld JSON-bestanden bruikbaar via API, CLI of frontend.

## Structuur

```
examples/
├── openaec_foundation/       OpenAEC Foundation branded rapport
│   └── structural_report.json
└── scripts/                  Python voorbeeldscripts
    ├── example_structural.py
    ├── generate_showcase.py
    ├── generate_integration_test.py
    └── pyrevit_generate_report.py
```

> Tenant-specifieke klantrapporten worden NIET in de public repo gecommit.
> Productie-deployments leveren hun eigen tenant-data via bind-mounts
> (zie `deploy/docker-compose.yml`).

## Gebruik

### CLI
```bash
openaec-report generate \
  --template structural \
  --data examples/openaec_foundation/structural_report.json \
  --output output/test.pdf
```

### API
```bash
curl -X POST https://report.example.com/api/generate/v2 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d @examples/openaec_foundation/structural_report.json \
  -o rapport.pdf
```

### Python
```python
from openaec_reports.core.template_engine import TemplateEngine
import json

with open("examples/openaec_foundation/structural_report.json") as f:
    data = json.load(f)

engine = TemplateEngine()
engine.build(
    template_name="structural_report",
    tenant="default",
    data=data,
    output_path="output/test.pdf",
)
```

## Engines

| Engine | Endpoint | Gebruik |
|--------|----------|---------|
| V1 (`Report.from_dict()`) | `/api/generate` | Flow-based content-block rapporten |
| V2 (`ReportGeneratorV2`) | `/api/generate/v2` | Pixel-perfect `renderer_v2` |
| V3 (`TemplateEngine`) | `/api/generate/template` | YAML page_types, fixed-page layouts |
