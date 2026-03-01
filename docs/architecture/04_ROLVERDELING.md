# Rolverdeling — Wie Doet Wat

## Overzicht

```
┌──────────────────────────────────────────────────────────────────┐
│                    JOCHEM (Product Owner)                         │
│                                                                  │
│  ✅ JSON data aanleveren (per project/factuur)                   │
│  ✅ Referentie PDF's aanleveren voor nieuwe pagina-layouts       │
│  ✅ Stationery PDF's maken/uploaden (InDesign/Illustrator)       │
│  ✅ Brand guidelines aanleveren (kleuren, fonts, logo's)         │
│  ✅ Testen en visuele QA: "dit klopt niet, verschuif 2mm"       │
│  ✅ Beslissen welke templates/pagina types nodig zijn            │
│  ✅ Server deployment (git pull + docker compose)                │
│                                                                  │
│  ❌ YAML page_types schrijven (dat doet Claude)                  │
│  ❌ Python code aanpassen                                        │
│  ❌ data_transform.py updaten                                    │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    CLAUDE (Ontwikkelaar)                          │
│                                                                  │
│  ✅ YAML page_types schrijven (coördinaten uit referentie PDF)   │
│  ✅ Template YAML's maken (paginavolgorde)                       │
│  ✅ brand.yaml configureren (kleuren, fonts, styles)             │
│  ✅ data_transform.py updaten voor nieuwe JSON structuren        │
│  ✅ template_engine.py uitbreiden (nieuwe features)              │
│  ✅ template_config.py uitbreiden (nieuwe zone types)            │
│  ✅ Bug fixes in rendering pipeline                              │
│  ✅ Git commits + push                                           │
│                                                                  │
│  ❌ Server deployment (geen SSH toegang)                         │
│  ❌ Stationery PDF's ontwerpen                                   │
│  ❌ InDesign/Illustrator werk                                    │
└──────────────────────────────────────────────────────────────────┘
```

## Workflow: Nieuw Document Type Toevoegen

```
Stap  Wie       Actie
────  ────────  ──────────────────────────────────────────────────
 1    Jochem    Lever referentie PDF aan (bestaand document als voorbeeld)
 2    Jochem    Lever stationery PDF's aan (achtergronden per pagina)
 3    Claude    Extract coördinaten uit referentie PDF (PyMuPDF)
 4    Claude    Schrijf YAML page_types met pixel-exact positioning
 5    Claude    Schrijf template YAML (paginavolgorde)
 6    Claude    Update data_transform.py als JSON formaat nieuw is
 7    Claude    Commit + push naar GitHub
 8    Jochem    Git pull + docker build op server
 9    Jochem    Test met echte data → visuele QA
10    Jochem    Feedback: "tekst 2mm naar rechts", "font te groot"
11    Claude    YAML aanpassen op basis van feedback
12              Herhaal 7-11 tot pixel-perfect
```

## Workflow: Nieuwe Tenant Toevoegen

```
Stap  Wie       Actie
────  ────────  ──────────────────────────────────────────────────
 1    Jochem    Lever brand guidelines aan (PDF of beschrijving)
 2    Jochem    Lever font bestanden aan (.ttf/.otf)
 3    Jochem    Lever logo's aan (PNG/SVG)
 4    Jochem    Lever stationery PDF's aan (per pagina type)
 5    Jochem    Lever referentie documenten aan
 6    Claude    Maak tenant directory: tenants/[naam]/
 7    Claude    Schrijf brand.yaml (kleuren, fonts, styles)
 8    Claude    Kopieer fonts naar tenants/[naam]/fonts/
 9    Claude    Schrijf page_types en templates
10    Claude    Update data_transform.py indien nodig
11    Claude    Commit + push
12    Jochem    Deploy + test
```

## Workflow: JSON Data Aanleveren (Per Project)

```
Stap  Wie       Actie
────  ────────  ──────────────────────────────────────────────────
 1    Jochem    Open admin panel of maak JSON bestand
 2    Jochem    Vul verplichte velden in:
                  - template (bepaalt welk document type)
                  - project (projectnaam)
                  - sections met juiste content blocks
 3    Jochem    Upload/submit via admin panel of API
 4    Server    data_transform zet genest → flat
 5    Server    TemplateEngine bouwt PDF
 6    Server    PDF wordt geretourneerd
```

## Wat Mag je NIET Veranderen (Zonder Overleg)

| Bestand | Reden |
|---|---|
| `data_transform.py` | Bepaalt hoe JSON → flat dict gaat. Verkeerde mapping = lege pagina's |
| `template_engine.py` | Core rendering. Bug = alle tenants kapot |
| `template_config.py` | Dataclasses. Wijziging = alle YAML's moeten mee |
| `api.py` | Routes + auth. Wijziging = frontend breekt |
| `brand.yaml` | Font namen moeten matchen met font_files |

## Wat Mag je WEL Vrij Aanpassen

| Bestand | Toelichting |
|---|---|
| Test JSON's (`schemas/test_*.json`) | Experimenteer vrij met data |
| Stationery PDF's | Vervang wanneer je wilt |
| Logo's | Vervang wanneer je wilt |
| `page_types/*.yaml` coördinaten | Verschuif tekst/lijnen |
| Template YAML paginavolgorde | Voeg pagina's toe/verwijder |
