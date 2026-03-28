"""Test-PDF genereren met Customer BIC Rapport template."""
from pathlib import Path
from openaec_reports.core.template_engine import TemplateEngine

tenants_dir = Path("tenants")

data = {
    "meta": {
        "factuur_kop": "BIC Inspectie Rapport",
        "datum": "Maart 2026",
        "factuurnummer": "BIC-2026-TEST-001",
        "type_offerte": "BIC Controle:",
        "offerte_regel": "336.01: BIC Rapport Test",
        "rapportkop_locatie": "BIC Rapport: BIC-2026-TEST-001",
    },
    "client": {
        "name": "Test Opdrachtgever B.V.",
        "address": "Teststraat 123",
        "postcode_plaats": "1012 AB Amsterdam",
    },
    "location": {
        "name": "Testlocatie Noord",
        "address": "Industrieweg 10",
        "postcode_plaats": "1234 AB Teststad",
        "code": "LOC-001",
        "provision_label": "Voorziening",
        "provision": "Tank 001",
        "object_label": "Object",
        "object": "OBJ-001",
        "photo_path": "",
    },
    "toc": {
        "item_1": "1    Locatie..........................................................",
        "item_2": "2    Voorziening......................................................",
        "item_3": "3    Object...........................................................",
        "item_4": "4    Bedrijfsinterne controle (BIC)....................................",
        "item_5": "5    Herstelwerkzaamheden.............................................",
        "item_6": "6    Tekeningen.......................................................",
        "item_6_1": "6.1    Regionale overzichtstekening.................................",
        "item_6_2": "6.2    Detailtekening...............................................",
        "item_6_3": "6.3    Kadastrale kaart.............................................",
        "item_7": "7    Onderhoudsdossier................................................",
        "item_7_1": "7.1    Controlelijst BIC............................................",
        "item_7_2": "7.2    Onderhoudsoverzicht..........................................",
        "item_7_2_1": "7.2.1    Historie inspectie.......................................",
        "item_7_2_2": "7.2.2    Historie BIC controles...................................",
        "item_7_2_3": "7.2.3    Historie herstelwerkzaamheden...........................",
        "item_8": "8    Bijlagen.........................................................",
        "item_8_1": "8.1    Verklaring VVV...............................................",
        "item_8_2": "8.2    Ondersteunende fotos BIC.....................................",
        "item_8_3": "8.3    Schadefoto herstel...........................................",
    },
    "voorziening": {
        "code": "VZ-001",
        "beschrijving": "Vloeistofdichte vloer met coating",
        "vereiste_status": "Vloeistofdicht",
        "huidige_status": "Vloeistofdicht",
        "notitie": "Geen bijzonderheden",
        "foto": "",
    },
    "object": {
        "code": "OBJ-001",
        "beschrijving": "Opslagtank diesel",
        "ruimte": "Hal A",
        "type": "Bovengrondse tank",
    },
    "vvv": {
        "geldigheid": "Geldig tot 01-01-2028",
        "nummer": "VVV-2024-1234",
        "instantie": "KIWA",
        "opmerkingen": "Geen",
        "onderhoudsdossier_ref": "Zie: 7.2.1 Historie inspectie",
        "bijlage_ref": "Zie: 8.1 Verklaring VVV",
    },
    "controleur": {
        "bedrijf": "Customer B.V.",
        "adres": "Landsweg 4",
        "postcode_plaats": "3237 KG Vierpolders",
        "telefoon": "+31 (0) 181 390 036",
        "email": "info@customer.nl",
        "naam": "J. de Tester",
    },
    "bic": {
        "nummer": "BIC-2026-TEST-001",
        "datum_controle": "15-03-2026",
        "datum_geldigheid": "15-03-2027",
        "bijzonderheden": "Geen bijzonderheden",
        "ref_controlelijst": "Zie: 7.1 Controlelijst BIC",
        "ref_historie": "Zie: 7.2.2 Historie BIC",
        "ref_fotos": "Zie: 8.2 Ondersteunende fotos",
        "rapportagedatum": "21-03-2026",
    },
    "reiniging": {
        "nummer": "RN-001",
        "omschrijving": "Reiniging vloercoating",
        "type": "Hogedrukreiniging",
        "datum": "15-03-2026",
    },
    "additioneel": {
        "nummer": "ADD-001",
        "omschrijving": "Visuele inspectie leidingwerk",
        "datum": "15-03-2026",
    },
    "herstel": {
        "nummer": "HW-001",
        "ref_controlelijst": "Zie: 7.1 Controlelijst BIC",
        "ref_historie": "Zie: 7.2.3 Historie herstel",
        "ref_fotos": "Zie: 8.3 Schadefoto herstel",
    },
    "herstel_reiniging": {
        "nummer": "HRN-001",
        "omschrijving": "Reiniging na herstel",
        "type": "Handmatig",
        "datum": "16-03-2026",
    },
    "herstel_additioneel": {
        "nummer": "HADD-001",
        "omschrijving": "Extra verflaag aangebracht",
        "datum": "16-03-2026",
    },
    "heading": {"number": "6", "title": "Tekeningen"},
    "subheading": {"number": "6.1", "title": "Regionale overzichtstekening"},
    "tekening": {"image": ""},
    "controlelijst": {
        "context": "VZ-001:OBJ-001 Opslagtank diesel. Datum controle: 15-03-2026",
    },
    "controlelijst_items": [
        {"Onderdeel": "Vloer", "Aspect": "Coating intact", "Antwoord": "Ja", "Bodemrisico": "Laag", "Schadenummer": "-"},
        {"Onderdeel": "Wanden", "Aspect": "Geen scheuren", "Antwoord": "Ja", "Bodemrisico": "Laag", "Schadenummer": "-"},
        {"Onderdeel": "Afvoer", "Aspect": "Vrij van obstakels", "Antwoord": "Nee", "Bodemrisico": "Midden", "Schadenummer": "S-001"},
    ],
    "inspecties": {
        "voetnoot": "Voor laatste versie VVV zie bijlage 8.1",
    },
    "inspecties_items": [
        {"Inspectiebedrijf": "Customer", "Inspecteur": "J. Tester", "Aard": "BIC", "Onderdeel": "Vloer", "Datum": "15-03-2026", "SIKB": "SIKB-001", "Uiterste datum": "15-03-2027"},
    ],
    "historie_bic_items": [
        {"Controlerend bedrijf": "Customer", "Controleur": "J. Tester", "Onderdeel": "Tank", "Datum": "15-03-2025", "Controle nummer": "BIC-2025-01", "Uiterste datum": "15-03-2026"},
        {"Controlerend bedrijf": "Customer", "Controleur": "P. Ansen", "Onderdeel": "Vloer", "Datum": "15-03-2024", "Controle nummer": "BIC-2024-01", "Uiterste datum": "15-03-2025"},
    ],
    "historie_herstel_items": [
        {"Uitvoerend bedrijf": "Bouw BV", "Uitvoerder": "K. Bakker", "Onderdeel": "Vloer", "Hersteldatum": "01-06-2025", "Schadenummer": "S-001", "Aard werkzaamheden": "Coating herstel"},
    ],
    "foto_bijlage": {
        "nummer": "8.2",
        "titel": "Ondersteunende fotos bedrijfsinterne controle",
        "context_1": "VZ-001:OBJ-001 Opslagtank diesel.",
        "context_2": "Datum uitvoering controle: 15-03-2026",
        "context_3": "",
        "label_links": "[Foto 1]",
        "caption_links": "Overzicht vloer",
        "label_rechts": "[Foto 2]",
        "caption_rechts": "Detail coating",
        "foto_links": "",
        "foto_rechts": "",
    },
}

engine = TemplateEngine(tenants_dir=tenants_dir)
output = engine.build(
    template_name="bic_rapport",
    tenant="customer",
    data=data,
    output_path="output/test_bic_rapport.pdf",
)
print(f"PDF gegenereerd: {output}")
