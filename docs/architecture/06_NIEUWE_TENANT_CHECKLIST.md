# Nieuwe Tenant Toevoegen — Checklist

## Voordat je begint: wat heb je nodig?

```
□  Brand guidelines PDF (kleuren, fonts, logo positionering)
□  Font bestanden (.ttf of .otf)
□  Logo's (PNG voor PDF, SVG optioneel)
□  Stationery PDF's (achtergrond per pagina type)
□  Minimaal 1 referentie document (bestaande PDF om na te bouwen)
□  Voorbeeld data (JSON of spreadsheet met echte projectdata)
```

## Stap-voor-stap

### 1. Directory Aanmaken

```
tenants/
└── [tenant_naam]/
    ├── brand.yaml              ← Huisstijl configuratie
    ├── fonts/
    │   ├── font-regular.ttf
    │   └── font-bold.ttf
    ├── logos/
    │   └── logo.png
    ├── stationery/
    │   ├── cover_stationery.pdf
    │   ├── content_portrait_stationery.pdf
    │   ├── content_landscape_stationery.pdf   (optioneel)
    │   └── backcover_stationery.pdf
    ├── templates/
    │   └── [document_type].yaml
    └── page_types/
        ├── cover.yaml
        ├── content_page.yaml
        └── backcover.yaml
```

### 2. brand.yaml Schrijven

Minimaal:
```yaml
brand:
  name: "Bedrijfsnaam"
  slug: "tenant_naam"       # Moet matchen met directory naam

colors:
  primary: "#HEX"           # Hoofdkleur
  secondary: "#HEX"         # Accent kleur
  text: "#000000"
  white: "#FFFFFF"

font_files:
  FontNaam: "fonts/font-regular.ttf"
  FontNaam-Bold: "fonts/font-bold.ttf"

fonts:
  heading: "FontNaam-Bold"
  body: "FontNaam"
```

### 3. Stationery PDF's Maken

**Regels:**
- Exact A4 formaat (210×297mm portrait, 297×210mm landscape)
- Alleen grafische elementen die op ELKE pagina van dat type staan
- GEEN tekst die per document verschilt (dat doet de engine)
- Export als PDF/X-1a voor maximale compatibiliteit

**Typische stationery inhoud:**
- Header balk (kleur + logo)
- Footer balk (kleur)
- Achtergrond patronen
- Vaste labels die NOOIT veranderen

### 4. Template Naam Conventie

Template naam = `[tenant]_[document_type]`

| Voorbeeld | Tenant | Document |
|---|---|---|
| `customer_bic_factuur` | customer | bic_factuur |
| `openaec_structural_report` | default | structural_report |
| `acme_inspectie_rapport` | acme | inspectie_rapport |

De API herkent de tenant uit de template naam:
```
"customer_bic_factuur" → tenant="customer", template="bic_factuur"
```

### 5. JSON Template Naam

In de JSON die gebruikers aanleveren:
```json
{
  "template": "customer_bic_factuur",    // ← tenant_documenttype
  "project": "Projectnaam"               // ← verplicht
}
```

### 6. Data Transform Regels

Als het nieuwe document type dezelfde JSON structuur gebruikt als een
bestaand type → geen wijziging nodig.

Als het een NIEUWE structuur heeft → `data_transform.py` uitbreiden
met een nieuwe parser functie.

### 7. Deployment

```bash
# Op de server (report.open-aec.com)
cd /opt/openaec-reports
git pull origin main
docker compose build --no-cache
docker compose up -d
```

## Troubleshooting

| Symptoom | Oorzaak | Oplossing |
|---|---|---|
| Lege pagina's | bind-paths matchen niet met data | Check data_transform output |
| Verkeerde fonts | font_files pad klopt niet | Check of .ttf in fonts/ staat |
| Geen stationery | PDF naam matcht niet | Check stationery: in page_type YAML |
| "Template not found" | Template naam klopt niet | Check tenant prefix + templates/ |
| Tekst op verkeerde positie | Coördinaten fout | Herextraheer uit referentie PDF |
