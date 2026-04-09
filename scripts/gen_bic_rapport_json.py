"""Genereer example_customer_bic_rapport.json met voldoende data voor ~17 pagina's."""

import json
from pathlib import Path

data = {
    "template": "customer_bic_rapport",
    "format": "A4",
    "brand": "customer",
    "project": "Jaarlijkse BIC controle 2026",
    "project_number": "336.01",
    "client": "Haagwonen",
    "author": "Customer B.V.",
    "date": "2026-03-15",
    "version": "1.0",
    "status": "DEFINITIEF",
    "report_type": "BIC Rapportage",
    "cover": {
        "subtitle": "BIC Rapportage",
        "extra_fields": {
            "Datum": "Maart 2026",
            "Factuurnummer": "BIC-2026-0336-003",
            "Type offerte": "Voorziening:Object",
            "Offertecode": "DBL-A",
            "Offertenaam": "Stijgleiding 1 Droge blusleiding",
        },
    },
    "colofon": {"enabled": False},
    "toc": {"enabled": False},
    "sections": [],
    "backcover": {"enabled": True},
    "metadata": {
        "software": "Customer Report Generator v1.0",
        "bic_system": "Customer BIC Manager v4.2",
        "location_code": "HW-DH-0336",
    },
}

# === Section 1: Locatie ===
data["sections"].append(
    {
        "title": "Locatie",
        "level": 1,
        "content": [
            {
                "type": "location_detail",
                "client": {
                    "section_title": "Opdrachtgever",
                    "name": "Haagwonen",
                    "address": "Wielingenstraat 22",
                    "city": "2584 XZ Den Haag",
                },
                "location": {
                    "section_title": "Locatie van uitvoer",
                    "name": "Strandbaak Kijkduin",
                    "address": "Kijkduinsestraat 730-798",
                    "city": "2554 EB Den Haag",
                    "code": "HW-DH-0336",
                    "provision": "Droge blusleiding / BMI",
                    "object": "Toren A t/m D (730-798)",
                },
                "photo_path": None,
            }
        ],
    }
)

# === Section 2: BIC Controles ===
data["sections"].append(
    {
        "title": "BIC Controles",
        "level": 1,
        "content": [
            {
                "type": "bic_table",
                "location_name": "Strandbaak Kijkduin",
                "sections": [
                    {
                        "title": "BIC controles",
                        "rows": [
                            {
                                "label": "Aantal BIC controles",
                                "ref_value": "16",
                                "actual_value": "16",
                            },
                            {
                                "label": "Kosten",
                                "ref_value": "\u20ac 4.960,00",
                                "actual_value": "\u20ac 4.960,00",
                            },
                            {
                                "label": "Aantal interne inspecties",
                                "ref_value": "8",
                                "actual_value": "8",
                            },
                            {
                                "label": "Kosten",
                                "ref_value": "\u20ac 1.920,00",
                                "actual_value": "\u20ac 1.920,00",
                            },
                            {
                                "label": "Reiskosten",
                                "ref_value": "\u20ac 720,00",
                                "actual_value": "\u20ac 864,00",
                            },
                            {
                                "label": "Subtotaal",
                                "ref_value": "\u20ac 7.600,00",
                                "actual_value": "\u20ac 7.744,00",
                            },
                        ],
                    },
                    {
                        "title": "Reinigen tijdens BIC",
                        "rows": [
                            {
                                "label": "Aantal reinigingen",
                                "ref_value": "8",
                                "actual_value": "10",
                            },
                            {
                                "label": "Kosten",
                                "ref_value": "\u20ac 1.400,00",
                                "actual_value": "\u20ac 1.750,00",
                            },
                        ],
                    },
                    {
                        "title": "Additioneel tijdens BIC",
                        "rows": [
                            {
                                "label": "Aantal additionele activiteiten",
                                "ref_value": "",
                                "actual_value": "5",
                            },
                            {
                                "label": "Kosten",
                                "ref_value": "",
                                "actual_value": "\u20ac 925,00",
                            },
                        ],
                    },
                ],
                "summary": {
                    "title": "Overzicht samenvatting",
                    "rows": [
                        {
                            "label": "BIC controles",
                            "ref_value": "\u20ac 7.600,00",
                            "actual_value": "\u20ac 7.744,00",
                        },
                        {
                            "label": "Reinigen tijdens BIC",
                            "ref_value": "\u20ac 1.400,00",
                            "actual_value": "\u20ac 1.750,00",
                        },
                        {
                            "label": "Additioneel tijdens BIC",
                            "ref_value": "",
                            "actual_value": "\u20ac 925,00",
                        },
                    ],
                    "total": {
                        "label": "Totaal",
                        "ref_value": "\u20ac 9.000,00",
                        "actual_value": "\u20ac 10.419,00",
                    },
                },
            }
        ],
    }
)

# === Section 3: Detail weergave (LANDSCAPE) ===
# ~230 rijen BIC controles over meerdere jaren en voorzieningen
detail_rows: list[list[str]] = []
voorzieningen = [
    ("Droge blusleiding", "DBL-A"),
    ("Droge blusleiding", "DBL-B"),
    ("Droge blusleiding", "DBL-C"),
    ("Droge blusleiding", "DBL-D"),
    ("BMI", "BMI-01"),
    ("BMI", "BMI-02"),
    ("BMI", "BMI-03"),
    ("BMI", "BMI-04"),
    ("Sprinkler", "SPR-A"),
    ("Sprinkler", "SPR-B"),
    ("Noodverlichting", "NVL-01"),
    ("Noodverlichting", "NVL-02"),
    ("Brandslang", "BSL-A"),
    ("Brandslang", "BSL-B"),
    ("Brandslang", "BSL-C"),
    ("Brandslang", "BSL-D"),
]

dates = [
    "15-01",
    "22-01",
    "05-02",
    "12-02",
    "10-04",
    "17-04",
    "08-05",
    "15-05",
    "09-07",
    "16-07",
    "06-08",
    "13-08",
    "08-10",
    "15-10",
    "05-11",
    "12-11",
]

years = ["2024", "2025", "2026"]
counter = 0

for year in years:
    for i, (vz_type, vz_code) in enumerate(voorzieningen):
        date_idx = i % len(dates)
        datum = f"{dates[date_idx]}-{year}"
        counter += 1
        nr = f"BIC-{year}-0336-{counter:03d}"

        bic_k = "\u20ac 310,00"
        insp_k = "\u20ac 240,00" if "BMI" in vz_type or "SPR" in vz_type else ""
        rein_k = "\u20ac 175,00" if counter % 3 == 0 else ""
        add_k = "\u20ac 185,00" if counter % 7 == 0 else ""

        detail_rows.append(
            [nr, f"{vz_type} ({vz_code})", datum, bic_k, insp_k, rein_k, add_k]
        )

# Beperk tot ~230 rijen voor ~10 pagina's
detail_rows = detail_rows[:230]

data["sections"].append(
    {
        "title": "Detail weergave",
        "level": 1,
        "orientation": "landscape",
        "content": [
            {
                "type": "table",
                "title": "Detail weergave",
                "headers": [
                    "BIC Controle nummer",
                    "Type",
                    "Datum",
                    "BIC controle",
                    "Int. inspectie",
                    "Reiniging",
                    "Additioneel",
                ],
                "rows": detail_rows,
                "footer_note": "* Detail weergave exclusief reiskosten.",
            }
        ],
    }
)

# === Section 4: Objecten (LANDSCAPE) ===
# ~60 objecten over 4 torens
objecten_rows: list[list[str]] = []
gebouwen = [
    ("Toren A", "730-752"),
    ("Toren B", "754-770"),
    ("Toren C", "772-784"),
    ("Toren D", "786-798"),
]

objecten_defs = [
    ("Droge blusleiding", "DBL-{t}", "Actief", "Stijgleiding {n}", "Stijgleiding", "Stijgleiding trapportaal {lr}", "Trappenhuis"),
    ("Droge blusleiding", "DBL-{t}", "Actief", "Voedingsaansluiting {n}", "Voedingsaansluiting", "Siamese aansluiting gevel {lr}", "Gevel BG"),
    ("Droge blusleiding", "DBL-{t}", "Actief", "BSA BG-{n}", "Aansluitpunt", "Brandslangaansluiting begane grond", "Hal BG"),
    ("Droge blusleiding", "DBL-{t}", "Actief", "BSA 5e-{n}", "Aansluitpunt", "Brandslangaansluiting 5e verdieping", "Overloop 5"),
    ("BMI", "BMI-{i:02d}", "Actief", "Centrale BMI-{n}", "Brandmeldcentrale", "Esser IQ8Control M", "Hal BG"),
    ("BMI", "BMI-{i:02d}", "Actief", "Doormelding-{n}", "Doormelding", "KPN doormelding RAC", "Hal BG"),
    ("BMI", "BMI-{i:02d}", "Actief", "Lus {n}-1", "Detectielus", "Rookmelders trappenhuis + galerij", "Diverse"),
    ("BMI", "BMI-{i:02d}", "Actief", "Lus {n}-2", "Detectielus", "Rookmelders bergingen + parkeergarage", "Kelder"),
    ("Sprinkler", "SPR-{t}", "Actief", "Sprinklerkop {n}-1", "Sprinklerkop", "Sprinklerkoppen parkeergarage", "Parkeergarage"),
    ("Sprinkler", "SPR-{t}", "Actief", "Sprinklerkop {n}-2", "Sprinklerkop", "Sprinklerkoppen berging", "Berging"),
    ("Noodverlichting", "NVL-{i:02d}", "Actief", "NVL armatuur {n}-T", "Armatuur", "Noodverlichting trappenhuis", "Trappenhuis"),
    ("Noodverlichting", "NVL-{i:02d}", "Actief", "NVL armatuur {n}-G", "Armatuur", "Noodverlichting galerij", "Galerij"),
    ("Brandslang", "BSL-{t}", "Actief", "Haspel BG-{n}", "Brandslanghaspel", "Brandslanghaspel begane grond", "Hal BG"),
    ("Brandslang", "BSL-{t}", "Actief", "Haspel 3e-{n}", "Brandslanghaspel", "Brandslanghaspel 3e verdieping", "Overloop 3"),
    ("Brandslang", "BSL-{t}", "Actief", "Haspel 5e-{n}", "Brandslanghaspel", "Brandslanghaspel 5e verdieping", "Overloop 5"),
]

torenletter = ["A", "B", "C", "D"]
for gi, (gebouw, nrs) in enumerate(gebouwen):
    t = torenletter[gi]
    n = gi + 1
    lr = "links" if gi % 2 == 0 else "rechts"
    for obj_def in objecten_defs:
        vz, vz_type_tmpl, status, obj_name, obj_type, beschr, ruimte = obj_def
        vz_type = vz_type_tmpl.format(t=t, i=gi + 1, n=n)
        obj = obj_name.format(t=t, n=n, lr=lr)
        beschr_f = beschr.format(t=t, n=n, lr=lr)
        row = [vz, vz_type, status, obj, obj_type, beschr_f, f"{gebouw} ({nrs})", ruimte]
        objecten_rows.append(row)

# Voeg 1 defect toe
objecten_rows[19][2] = "Defect"
objecten_rows[19][5] = "Handbrandmelder hoofdingang - defect gemeld 12-04"

data["sections"].append(
    {
        "title": "Voorziening en objecten beschrijving",
        "level": 1,
        "orientation": "landscape",
        "content": [
            {
                "type": "table",
                "title": "Voorziening en objecten beschrijving",
                "headers": [
                    "Voorziening",
                    "Type",
                    "Status",
                    "Object",
                    "Type",
                    "Beschrijving",
                    "Gebouw",
                    "Ruimte",
                ],
                "rows": objecten_rows,
            }
        ],
    }
)

# Schrijf JSON
output = Path("schemas/example_customer_bic_rapport.json")
with output.open("w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

pages_detail = len(detail_rows) // 23 + 1
pages_objecten = len(objecten_rows) // 23 + 1
total = 1 + 1 + 1 + pages_detail + pages_objecten + 1

print(f"Detail rijen: {len(detail_rows)} -> ~{pages_detail} pagina's")
print(f"Objecten rijen: {len(objecten_rows)} -> ~{pages_objecten} pagina's")
print(f"Geschat totaal: {total} pagina's (1 cover + 1 locatie + 1 bic + {pages_detail} detail + {pages_objecten} objecten + 1 achterblad)")
print(f"JSON geschreven: {output}")
