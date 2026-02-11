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
    report.add_colofon()

    # Secties handmatig opbouwen
    report.add_section("Uitgangspunten", level=1)
    report.add_table(
        headers=["Onderdeel", "Materiaal", "Sterkteklasse"],
        rows=[
            ["Fundering", "Beton", "C20/25"],
            ["Vloer BG", "Beton", "C28/35"],
        ],
        title="Materialen",
    )

    report.add_section("Staalligger L1", level=1)
    report.add_calculation(
        title="Veldmoment",
        formula="M_Ed = q_d × l² / 8",
        result="39.1",
        unit="kNm",
    )
    report.add_check(
        description="Unity check buiging",
        unity_check=0.58,
        limit=1.0,
    )

    report.add_backcover()

    output_path = OUTPUT_DIR / "voorbeeld_handmatig.pdf"
    report.build(output_path)
    print(f"Rapport gegenereerd: {output_path}")


if __name__ == "__main__":
    main()
