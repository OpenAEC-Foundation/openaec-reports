"""Voorbeeld: Constructief rapport genereren vanuit JSON data."""

from pathlib import Path
from bm_reports import Report, A4

# Pad naar voorbeeld data
DATA_FILE = Path(__file__).parent / "example_data.json"
OUTPUT_DIR = Path(__file__).parent.parent / "output"


def main():
    """Genereer een voorbeeld constructief rapport."""
    # Methode 1: Vanuit JSON
    report = Report.from_json(DATA_FILE, template="structural")
    report.add_cover(subtitle="Constructieve berekening hoofddraagconstructie")
    report.add_colofon()

    # Secties worden gevuld vanuit JSON data
    # (In werkelijke implementatie parsed de engine de JSON secties)

    report.add_backcover()

    output_path = OUTPUT_DIR / "voorbeeld_constructie.pdf"
    report.build(output_path)
    print(f"Rapport gegenereerd: {output_path}")


def main_manual():
    """Genereer rapport met handmatige API calls (voor pyRevit integratie)."""
    report = Report(
        format=A4,
        project="Voorbeeld Woonhuis",
        project_number="2026-001",
        client="Particuliere Opdrachtgever",
        report_type="structural",
    )

    report.add_cover(subtitle="Constructieve berekening")

    # Secties met tekst content
    report.add_section("Uitgangspunten", level=1, content=[
        "Dit rapport beschrijft de constructieve berekening voor het project Voorbeeld Woonhuis.",
        "Alle berekeningen zijn uitgevoerd conform de Eurocode (NEN-EN 1990 t/m 1999).",
        "Materialen: beton C20/25 (fundering), beton C28/35 (vloer BG), staal S235 (liggers).",
    ])

    report.add_section("Belastingen", level=1, content=[
        "De belastingen zijn bepaald conform NEN-EN 1991.",
    ])
    report.add_section("Eigen gewicht", level=2, content=[
        "Gewapend beton: 25 kN/m³",
        "Dekvloer: 0.5 kN/m²",
    ])
    report.add_section("Veranderlijke belasting", level=2, content=[
        "Nuttige belasting (wonen): 1.75 kN/m²",
        "Scheidingswanden: 0.5 kN/m²",
    ])

    report.add_section("Staalligger L1", level=1, content=[
        "HEA 200, staal S235, overspanning 6.0 m.",
        "Veldmoment M_Ed = 39.1 kNm",
        "Unity check buiging: 0.58 — VOLDOET",
    ])

    report.add_backcover()

    output_path = OUTPUT_DIR / "voorbeeld_handmatig.pdf"
    report.build(output_path)
    print(f"Rapport gegenereerd: {output_path}")


if __name__ == "__main__":
    main()
