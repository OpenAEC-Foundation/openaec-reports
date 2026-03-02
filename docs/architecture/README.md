# 📐 BM Reports — Architecture Docs

Documentatie over de systeemarchitectuur van de PDF report generator.

## Documenten

| # | Document | Inhoud |
|---|---|---|
| 01 | [System Overview](01_SYSTEM_OVERVIEW.md) | High-level architectuur, data flow, directory structuur, pagina types |
| 02 | [JSON Schema Symitech](02_JSON_SCHEMA_SYMITECH.md) | Exact JSON formaat voor Symitech BIC Factuur met alle bind-path mappings |
| 03 | [JSON Schema 3BM](03_JSON_SCHEMA_3BM.md) | JSON formaat voor 3BM Coöperatie (V1/V2 legacy) |
| 04 | [Rolverdeling](04_ROLVERDELING.md) | Wie doet wat: Jochem vs Claude, workflows |
| 05 | [YAML Guide](05_YAML_GUIDE.md) | Hoe YAML configuratie werkt: brand, template, page_type |
| 06 | [Nieuwe Tenant Checklist](06_NIEUWE_TENANT_CHECKLIST.md) | Stap-voor-stap een nieuwe tenant/brand toevoegen |

## Quick Reference

### API Endpoint
```
POST https://report.3bm.co.nl/api/generate/template
Header: Authorization: Bearer <JWT token>
Body: JSON conform schema
Response: application/pdf
```

### Minimale JSON
```json
{
  "template": "symitech_bic_factuur",
  "project": "Projectnaam"
}
```

### Rendering Pipeline
```
JSON → data_transform → TemplateEngine → PDF
                ↑               ↑
          Genest→Flat    YAML configs + Stationery PDF's
```

### Bestanden die ertoe doen

| Bestand | Functie |
|---|---|
| `src/openaec_reports/api.py` | HTTP endpoints, tenant detectie |
| `src/openaec_reports/core/data_transform.py` | JSON genest → flat |
| `src/openaec_reports/core/template_engine.py` | PDF rendering |
| `src/openaec_reports/core/template_config.py` | YAML parsing (dataclasses) |
| `tenants/[naam]/brand.yaml` | Huisstijl per tenant |
| `tenants/[naam]/templates/*.yaml` | Paginavolgorde per document |
| `tenants/[naam]/page_types/*.yaml` | Pixel-exact layout per pagina |
| `tenants/[naam]/stationery/*.pdf` | Achtergrond PDF's |
