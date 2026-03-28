# Symitech BIC Rapport — Schema Documentatie

> **Schema:** `schemas/bic_rapport.schema.json`
> **Template:** `tenants/symitech/templates/bic_rapport.yaml`
> **Voorbeeld:** `schemas/example_bic_rapport.json`

---

## 1. Overzicht

Het BIC (Bedrijfsinterne Controle) rapport is een gestandaardiseerd rapporttype voor Symitech B.V.
Het documenteert jaarlijkse inspecties van vloeistofdichte voorzieningen conform milieuwetgeving.

**Kenmerken:**
- 17 pagina's vaste structuur (portrait + landscape)
- Stationery-based rendering (PDF achtergronden per paginatype)
- Data-binding: JSON velden worden op exacte X/Y posities geplaatst
- Auto-repeat pagina's voor tabellen die niet op één pagina passen

---

## 2. Paginastructuur

| Pag | Hoofdstuk | Page Type | Orientatie | Opmerkingen |
|-----|-----------|-----------|------------|-------------|
| 1 | Voorblad | `voorblad_bic` | Portrait | Stationery: cover |
| 2 | Inhoudsopgave | `inhoudsopgave` | Portrait | Stationery: content |
| 3 | 1 Locatie | `locatie` | Portrait | Stationery: colofon |
| 4 | 2+3 Voorziening, Object, VVV | `voorziening_object` | Portrait | Flow layout |
| 5 | 4 BIC Details | `bic_rapport_details` | Portrait | Flow layout |
| 6 | 5 Herstelwerkzaamheden | `herstelwerkzaamheden` | Portrait | |
| 7 | 6.1 Overzichtstekening | `tekening_overzicht` | Portrait | Afbeelding of kaart |
| 8 | 6.2 Detailtekening | `tekening_detail` | Portrait | Afbeelding |
| 9 | 6.3 Kadastrale kaart | `tekening_kadaster` | Portrait | Afbeelding of kaart |
| 10 | 7.1 Controlelijst | `controlelijst_bic` | **Landscape** | Auto-repeat |
| 11 | 7.2.1 Inspecties historie | `onderhouds_inspecties` | **Landscape** | |
| 12 | 7.2.2 BIC controles historie | `historie_bic` | **Landscape** | Auto-repeat |
| 13 | 7.2.3 Herstel historie | `historie_herstel` | **Landscape** | Auto-repeat |
| 14 | 8.1 VVV Verklaring | `vvv_verklaring` | Portrait | Bijlage afbeelding |
| 15 | 8.2 BIC foto's | `foto_bijlage` | Portrait | Links/rechts foto layout |
| 16 | 8.3 Schade foto's | `schade_fotos` | Portrait | Schade/herstel fotopaar |
| 17 | Achterblad | `achterblad` | Portrait | Stationery: backcover |

---

## 3. Schema Structuur

### 3.1 Verplichte velden (top-level)

```json
{
  "template": "bic_rapport",        // Altijd "bic_rapport" (const)
  "project": "string",              // Projectnaam
  "meta": { ... },                  // Voorblad metadata
  "client": { ... },                // Opdrachtgever
  "location": { ... },              // Inspectielocatie
  "voorziening": { ... },           // Voorziening details
  "object": { ... },                // Object details
  "vvv": { ... },                   // VVV verklaring
  "controleur": { ... },            // Controleur gegevens
  "bic": { ... }                    // BIC controle details
}
```

### 3.2 Optionele velden (top-level)

| Veld | Type | Doel |
|------|------|------|
| `tenant` | string | Tenant identifier (default: `"symitech"`) |
| `format` | string | Papierformaat (default: `"A4"`) |
| `project_number` | string | Projectnummer / BIC nummer |
| `author` | string | Auteur (default: `"Symitech B.V."`) |
| `date` | string | Rapportdatum ISO 8601 (`YYYY-MM-DD`) |
| `version` | string | Versie (default: `"1.0"`) |
| `status` | enum | `"CONCEPT"`, `"DEFINITIEF"`, of `"REVISIE"` |
| `toc` | object | Inhoudsopgave items en paginanummers |
| `reiniging` | object | Reinigingsactiviteiten |
| `additioneel` | object | Additionele activiteiten |
| `herstel` | object | Herstelwerkzaamheden |
| `herstel_reiniging` | object | Reiniging bij herstel |
| `herstel_additioneel` | object | Additionele activiteiten bij herstel |
| `tekening_overzicht` | object | Regionale overzichtstekening |
| `tekening_detail` | object | Detailtekening |
| `tekening_kadaster` | object | Kadastrale kaart |
| `controlelijst` | object | Controlelijst context header |
| `controlelijst_items` | array | Controlelijst rijen |
| `inspecties` | object | Inspecties voetnoot |
| `inspecties_items` | array | Inspecties historie rijen |
| `historie_bic_items` | array | BIC controles historie rijen |
| `historie_herstel_items` | array | Herstelwerkzaamheden historie rijen |
| `vvv_verklaring` | object | VVV verklaring bijlage |
| `foto_bijlage` | object | BIC ondersteunende foto's |
| `schade_fotos` | object | Schade/herstel foto's |

---

## 4. Secties in Detail

### 4.1 `meta` — Voorblad metadata

Bepaalt de tekst op het voorblad en de footer van elke pagina.

```json
{
  "meta": {
    "factuur_kop": "Eindrapportage Bedrijfsinterne Controle",
    "datum": "MAART 2026",
    "factuurnummer": "336.01-2026-0042",
    "type_offerte": "Voorziening:Object",
    "offerte_regel": "VZ-042:OBJ-042-A Vloeistofdichte vloer dieselopslagplaats",
    "rapportkop_locatie": "Eindrapportage Bedrijfsinterne Controle: 336.01-2026-0042"
  }
}
```

| Veld | Verplicht | Beschrijving |
|------|-----------|-------------|
| `factuur_kop` | Ja | Rapport titel op voorblad |
| `datum` | Ja | Maand + jaar op voorblad (bijv. `"FEBRUARI 2025"`) |
| `factuurnummer` | Ja | BIC nummer op voorblad |
| `type_offerte` | Nee | Label boven voorziening:object |
| `offerte_regel` | Nee | Voorziening:Object beschrijving |
| `rapportkop_locatie` | Nee | Footer tekst op elke pagina |

### 4.2 `client` — Opdrachtgever

```json
{
  "client": {
    "name": "Rijkswaterstaat West-Nederland Zuid",
    "address": "Boompjes 200",
    "postcode_plaats": "3011 XD Rotterdam"
  }
}
```

| Veld | Verplicht | Type |
|------|-----------|------|
| `name` | Ja | string |
| `address` | Nee | string |
| `postcode_plaats` | Nee | string |

### 4.3 `location` — Inspectielocatie

```json
{
  "location": {
    "name": "Depot Dordrecht",
    "address": "Industrieweg 42",
    "postcode_plaats": "3316 AG Dordrecht",
    "code": "VZ-042",
    "provision_label": "Voorziening",
    "provision": "Dieselopslagplaats",
    "object_label": "Object",
    "object": "OBJ-042-A",
    "photo_path": "pad/naar/locatiefoto.png"
  }
}
```

| Veld | Verplicht | Beschrijving |
|------|-----------|-------------|
| `name` | Ja | Locatienaam |
| `address` | Nee | Straat + huisnummer |
| `postcode_plaats` | Nee | Postcode + plaatsnaam |
| `code` | Nee | Locatiecode (bijv. `"UNIP0105"`) |
| `provision_label` | Nee | Label (default: `"Voorziening"`) |
| `provision` | Nee | Voorziening omschrijving |
| `object_label` | Nee | Label (default: `"Object"`) |
| `object` | Nee | Object code |
| `photo_path` | Nee | Pad, URL, of base64 van locatiefoto |

### 4.4 `voorziening` — Voorziening details (Hfdst. 2)

```json
{
  "voorziening": {
    "code": "VZ-042",
    "beschrijving": "Vloeistofdichte vloer met epoxy coating",
    "vereiste_status": "Vloeistofdicht",
    "huidige_status": "Vloeistofdicht",
    "notitie": "Lichte slijtage coating bij laadplaats",
    "foto": "pad/naar/foto.png"
  }
}
```

| Veld | Verplicht | Beschrijving |
|------|-----------|-------------|
| `code` | Ja | BIC/voorziening code |
| `beschrijving` | Ja | Voorziening beschrijving |
| `vereiste_status` | Nee | Vereiste status (bijv. `"Vloeistofdicht"`) |
| `huidige_status` | Nee | Huidige status |
| `notitie` | Nee | Bevindingen/notities |
| `foto` | Nee | Pad, URL, of base64 |

### 4.5 `object` — Object details (Hfdst. 3)

```json
{
  "object": {
    "code": "OBJ-042-A",
    "beschrijving": "Opslagtank 10.000L diesel",
    "ruimte": "Buitenterrein zone A",
    "type": "Bovengrondse tank"
  }
}
```

| Veld | Verplicht |
|------|-----------|
| `code` | Ja |
| `beschrijving` | Ja |
| `ruimte` | Nee |
| `type` | Nee |

### 4.6 `vvv` — Verklaring Vloeistofdichte Voorziening

```json
{
  "vvv": {
    "geldigheid": "15-09-2028",
    "nummer": "VVV-2022-7891",
    "instantie": "KIWA Nederland B.V.",
    "opmerkingen": "Herkeuring gepland Q3 2028",
    "onderhoudsdossier_ref": "Zie: 7.2.1 Inspecties historie",
    "bijlage_ref": "Zie: 8.1 VVV verklaring"
  }
}
```

Alle velden zijn optioneel.

### 4.7 `controleur` — Controlerend bedrijf (Hfdst. 4)

```json
{
  "controleur": {
    "bedrijf": "Symitech B.V.",
    "adres": "Landsweg 4",
    "postcode_plaats": "3237 KG Vierpolders",
    "telefoon": "+31 (0) 181 390 036",
    "email": "info@symitech.nl",
    "naam": "M. van der Berg"
  }
}
```

| Veld | Verplicht |
|------|-----------|
| `bedrijf` | Ja |
| `naam` | Ja |
| `adres` | Nee |
| `postcode_plaats` | Nee |
| `telefoon` | Nee |
| `email` | Nee |

### 4.8 `bic` — BIC controle details (Hfdst. 4)

```json
{
  "bic": {
    "nummer": "336.01-2026-0042",
    "datum_controle": "12-03-2026",
    "datum_geldigheid": "12-03-2027",
    "bijzonderheden": "Lichte slijtage coating laadplaats",
    "ref_controlelijst": "Zie: 7.1 Controlelijst",
    "ref_historie": "Zie: 7.2.2 BIC historie",
    "ref_fotos": "Zie: 8.2 BIC foto's",
    "rapportagedatum": "21-03-2026"
  }
}
```

| Veld | Verplicht | Beschrijving |
|------|-----------|-------------|
| `nummer` | Ja | BIC controlenummer |
| `datum_controle` | Ja | Datum uitvoering (DD-MM-YYYY) |
| `datum_geldigheid` | Nee | Geldigheidsdatum controle |
| `bijzonderheden` | Nee | Bijzonderheden |
| `ref_controlelijst` | Nee | Referentie naar controlelijst |
| `ref_historie` | Nee | Referentie naar historie |
| `ref_fotos` | Nee | Referentie naar foto's |
| `rapportagedatum` | Nee | Datum rapportage (DD-MM-YYYY) |

### 4.9 `reiniging` / `additioneel` — Activiteiten bij BIC

```json
{
  "reiniging": {
    "nummer": "RN-2026-0042",
    "omschrijving": "Reiniging vloer middels HD",
    "type": "Hogedrukreiniging (200 bar)",
    "datum": "12-03-2026"
  },
  "additioneel": {
    "nummer": "ADD-2026-0042",
    "omschrijving": "Visuele inspectie leidingwerk",
    "datum": "12-03-2026"
  }
}
```

Dezelfde structuur geldt voor `herstel_reiniging` en `herstel_additioneel`.

### 4.10 `herstel` — Herstelwerkzaamheden (Hfdst. 5)

```json
{
  "herstel": {
    "nummer": "HW-2026-0042",
    "ref_controlelijst": "Zie: 7.1 Controlelijst",
    "ref_historie": "Zie: 7.2.3 Herstel historie",
    "ref_fotos": "Zie: 8.3 Schade foto's"
  }
}
```

---

## 5. Tekeningen (Hfdst. 6)

Tekeningen ondersteunen twee modi: **statische afbeelding** of **dynamische kaart**.

### Statische afbeelding

```json
{
  "tekening_detail": {
    "titel": "Detailtekening",
    "image": "pad/naar/tekening.jpg"
  }
}
```

### Dynamische kaart (PDOK WMS)

```json
{
  "tekening_overzicht": {
    "titel": "Regionale overzichtstekening (1: 10.000)",
    "image": {
      "lat": 51.8130,
      "lon": 4.6690,
      "radius": 100,
      "service": "luchtfoto",
      "layers": "2025_orthoHR"
    }
  }
}
```

| Veld | Type | Beschrijving |
|------|------|-------------|
| `lat` | number | Latitude (WGS84) |
| `lon` | number | Longitude (WGS84) |
| `radius` | number | Straal in meters |
| `service` | string | `"luchtfoto"`, `"kadaster"`, `"bgt"` |
| `layers` | string | WMS layer naam (optioneel) |
| `image` | string | Fallback pad als WMS niet beschikbaar |

---

## 6. Tabellen (Arrays)

### 6.1 `controlelijst_items` — Controlelijst BIC (Landscape)

```json
{
  "controlelijst_items": [
    {
      "Onderdeel": "1 Vloer",
      "Aspect": "1.1 Is de coating intact en hechtend?",
      "Antwoord": "Ja",
      "Bodemrisico": "1",
      "Schadenummer": ""
    }
  ]
}
```

| Kolom | Beschrijving |
|-------|-------------|
| `Onderdeel` | Onderdeel van de voorziening |
| `Aspect` | Inspectie-aspect / vraag |
| `Antwoord` | `"Ja"` / `"Nee"` |
| `Bodemrisico` | Risiconiveau (`"1"` = laag, `"2"` = verhoogd) |
| `Schadenummer` | Schadenummer indien van toepassing |

### 6.2 `inspecties_items` — Inspecties historie (Landscape)

```json
{
  "inspecties_items": [
    {
      "Inspectiebedrijf": "KIWA Nederland B.V.",
      "Inspecteur": "A. de Groot",
      "Aard": "Initieel",
      "Onderdeel": "Geheel",
      "Datum": "15-09-2016",
      "SIKB": "SIKB-2016-4521",
      "Uiterste datum": "15-09-2022"
    }
  ]
}
```

### 6.3 `historie_bic_items` — BIC controles historie (Landscape)

```json
{
  "historie_bic_items": [
    {
      "Controlerend bedrijf": "Symitech B.V.",
      "Controleur": "M. van der Berg",
      "Onderdeel": "Geheel",
      "Datum": "12-03-2026",
      "Controle nummer": "336.01-2026-0042",
      "Uiterste datum": "12-03-2027"
    }
  ]
}
```

### 6.4 `historie_herstel_items` — Herstelwerkzaamheden historie (Landscape)

```json
{
  "historie_herstel_items": [
    {
      "Uitvoerend bedrijf": "Coating Solutions B.V.",
      "Uitvoerder": "K. Bakker",
      "Onderdeel": "Vloer",
      "Hersteldatum": "22-09-2022",
      "Schadenummer": "S-2022-003",
      "Aard werkzaamheden": "Volledige epoxy toplaag vernieuwd"
    }
  ]
}
```

---

## 7. Bijlagen (Hfdst. 8)

### 7.1 `vvv_verklaring` — VVV bijlage

```json
{
  "vvv_verklaring": {
    "image": "pad/naar/vvv_document.jpg"
  }
}
```

### 7.2 `foto_bijlage` — BIC ondersteunende foto's

Twee foto's naast elkaar (links/rechts layout).

```json
{
  "foto_bijlage": {
    "nummer": "8.2",
    "titel": "BedrijfsInterne Controle ondersteunende foto's",
    "context_1": "VZ-042:OBJ-042-A Vloeistofdichte vloer dieselopslagplaats.",
    "context_2": "Datum uitvoering controle: 12-03-2026",
    "context_3": "",
    "label_links": "[Foto 1]",
    "caption_links": "Overzicht vloeistofdichte vloer en tank",
    "label_rechts": "[Foto 2]",
    "caption_rechts": "Detail slijtage coating bij laadplaats",
    "foto_links": "pad/naar/foto1.jpg",
    "foto_rechts": "pad/naar/foto2.jpg"
  }
}
```

### 7.3 `schade_fotos` — Schade/herstel fotopaar

```json
{
  "schade_fotos": {
    "context_1": "VZ-042: Vloeistofdichte vloer dieselopslagplaats",
    "context_2": "S-2026-002: Laadplaats 15-03-2026",
    "schade_label": "[Schade foto]",
    "schade_caption": "Slijtage epoxy coating voor herstel",
    "herstel_label": "[Herstel foto]",
    "herstel_caption": "Nieuwe epoxy toplaag na herstel (2m²)",
    "schade_foto": "pad/naar/schade.jpg",
    "herstel_foto": "pad/naar/herstel.jpg"
  }
}
```

---

## 8. Afbeeldingen — Drie formaten

Alle afbeeldingsvelden (`photo_path`, `foto`, `image`, `foto_links`, etc.) accepteren:

| Formaat | Voorbeeld | Gebruik |
|---------|-----------|---------|
| **Bestandspad** | `"tenants/symitech/assets/foto.png"` | Lokaal / CLI |
| **URL** | `"https://example.com/foto.jpg"` | API / extern |
| **Base64** | `"data:image/png;base64,iVBOR..."` | API / inline |

---

## 9. Inhoudsopgave (`toc`)

De inhoudsopgave wordt handmatig meegegeven als key-value pairs:

```json
{
  "toc": {
    "item_1": "1    Locatie",
    "item_2": "2    Voorziening",
    "item_6_1": "6.1    Regionale overzichtstekening (1: 10.000)",
    "page_1": "1",
    "page_6_1": "5"
  }
}
```

**Conventie:** `item_X` = titel, `page_X` = paginanummer. Nesting via `_` separators (bijv. `item_7_2_1`).

---

## 10. Brand / Huisstijl

De Symitech huisstijl wordt geconfigureerd in `tenants/symitech/brand.yaml`:

| Eigenschap | Waarde |
|------------|--------|
| Primaire kleur | `#006FAB` (blauw) |
| Secundaire kleur | `#94571E` (bruin/oranje) |
| Fonts | Arial (Regular, Bold, Italic) |
| Tabel header achtergrond | `#006FAB` (blauw) |
| Tabel footer achtergrond | `#94571E` (bruin) |
| Stationery | 5 PDF achtergronden |

---

## 11. Minimaal Voorbeeld

Het kleinst mogelijke valide BIC rapport:

```json
{
  "template": "bic_rapport",
  "project": "Mijn Project",
  "meta": {
    "factuur_kop": "Eindrapportage BIC",
    "datum": "MAART 2026",
    "factuurnummer": "B001"
  },
  "client": {
    "name": "Opdrachtgever B.V."
  },
  "location": {
    "name": "Locatie X"
  },
  "voorziening": {
    "code": "VZ-001",
    "beschrijving": "Vloeistofdichte vloer"
  },
  "object": {
    "code": "OBJ-001",
    "beschrijving": "Opslagtank"
  },
  "vvv": {},
  "controleur": {
    "bedrijf": "Symitech B.V.",
    "naam": "J. Doe"
  },
  "bic": {
    "nummer": "B001",
    "datum_controle": "01-03-2026"
  }
}
```

---

## 12. Gerelateerde Bestanden

| Bestand | Beschrijving |
|---------|-------------|
| `schemas/bic_rapport.schema.json` | JSON Schema (bron van waarheid) |
| `schemas/example_bic_rapport.json` | Volledig voorbeeld met alle velden |
| `schemas/example_symitech_bic_rapport.json` | Uitgebreid voorbeeld |
| `tenants/symitech/templates/bic_rapport.yaml` | Template definitie (17 pagina's) |
| `tenants/symitech/templates/bic_factuur.yaml` | BIC Factuur template (6 pagina's) |
| `tenants/symitech/brand.yaml` | Huisstijl configuratie |
| `tenants/symitech/page_types/` | 21 page type YAML's met veld-posities |
| `tenants/symitech/stationery/` | 5 PDF achtergronden |
| `examples/symitech/` | Voorbeeld JSON bestanden |
