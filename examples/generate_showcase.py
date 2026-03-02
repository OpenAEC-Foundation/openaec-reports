"""Genereer component_showcase.pdf — demonstratie van alle content block types."""

from pathlib import Path

from openaec_reports import Report, A4
from openaec_reports.components import CalculationBlock, CheckBlock, TableBlock

OUTPUT_DIR = Path(__file__).parent.parent / "output"


def main():
    """Genereer een showcase PDF met alle component types."""
    report = Report(
        format=A4,
        project="Component Showcase",
        project_number="SHOWCASE-001",
        client="OpenAEC",
        report_type="showcase",
    )

    report.add_cover(subtitle="Overzicht van alle content block types")

    # --- Sectie 1: CalculationBlock ---
    calc1 = CalculationBlock(
        title="Buigend moment veldmoment",
        formula="M_Ed = q × L² / 8",
        substitution="M_Ed = 12.5 × 6.0² / 8 = 56.25 kNm",
        result="M_Ed = 56.25",
        unit="kNm",
        reference="NEN-EN 1991-1-1 §6.1",
    )
    calc2 = CalculationBlock(
        title="Momentcapaciteit",
        formula="M_Rd = W_pl × f_y / γ_M0",
        substitution="M_Rd = 429.5e3 × 235 / 1.0 = 100.9 kNm",
        result="M_Rd = 100.9",
        unit="kNm",
        reference="NEN-EN 1993-1-1 §6.2.5",
    )
    report.add_section("Berekeningsblokken", level=1, content=[
        "Voorbeeld van CalculationBlock componenten met formule, substitutie en resultaat.",
        calc1,
        calc2,
    ])

    # --- Sectie 2: CheckBlock ---
    check_pass = CheckBlock(
        description="Buigingscontrole staalligger HEA 200",
        required="UC ≤ 1.0",
        calculated="M_Ed / M_Rd = 56.25 / 100.9",
        unity_check=0.56,
        reference="NEN-EN 1993-1-1",
    )
    check_fail = CheckBlock(
        description="Doorbuigingscontrole",
        required="δ ≤ L/250 = 24.0 mm",
        calculated="δ = 28.3 mm",
        unity_check=1.18,
        reference="NEN-EN 1990 §A1.4",
    )
    check_explicit = CheckBlock(
        description="Brandwerendheid draagconstructie",
        required="REI 60",
        calculated="REI 90 (o.b.v. Eurocode fire design)",
        result="VOLDOET",
        reference="Bouwbesluit §2.9",
    )
    report.add_section("Toetsingsblokken", level=1, content=[
        "Voorbeeld van CheckBlock componenten met UC-balk en voldoet/voldoet niet indicatie.",
        check_pass,
        check_fail,
        check_explicit,
    ])

    # --- Sectie 3: TableBlock ---
    table1 = TableBlock(
        headers=["Onderdeel", "Profiel", "Staalsoort", "UC", "Status"],
        rows=[
            ["Ligger L1", "HEA 200", "S235", "0.56", "Voldoet"],
            ["Ligger L2", "HEA 240", "S235", "0.73", "Voldoet"],
            ["Kolom K1", "HEB 160", "S235", "0.42", "Voldoet"],
            ["Kolom K2", "HEB 200", "S355", "0.88", "Voldoet"],
            ["Windverband", "CHS 88.9×4.0", "S235", "1.12", "Voldoet niet"],
        ],
    )
    report.add_section("Tabellen", level=1, content=[
        "Voorbeeld van TableBlock met header styling en zebra-striping.",
        table1,
    ])

    # --- Sectie 4: Tekst (Paragraph) ---
    report.add_section("Paragrafen", level=1, content=[
        "Dit is een reguliere paragraaf in de Normal stijl.",
        "Meerdere paragrafen worden automatisch onder elkaar geplaatst met de juiste spacing.",
        "De tekst gebruikt de OpenAEC huisstijl kleuren: donkerpaars voor koppen, turquoise voor accenten.",
    ])

    report.add_backcover()

    output_path = OUTPUT_DIR / "component_showcase.pdf"
    report.build(output_path)
    print(f"Showcase gegenereerd: {output_path}")


if __name__ == "__main__":
    main()
