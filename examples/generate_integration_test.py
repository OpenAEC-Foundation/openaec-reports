"""End-to-end integratie test — Genereer rapport met ALLE features.

Valideert de volledige pipeline:
  - Cover page (met logo, projecttitel, ondertitel)
  - Colofon page (projectinfo, revisiegeschiedenis)
  - Inhoudsopgave (TOC)
  - ParagraphBlocks
  - CalculationBlock (formule + substitutie + resultaat)
  - CheckBlock (VOLDOET + VOLDOET NIET)
  - TableBlock (zebra striping)
  - ImageBlock (logo als test image)
  - Backcover page
"""

from pathlib import Path

from openaec_reports import Report, A4
from openaec_reports.components import CalculationBlock, CheckBlock, ImageBlock, TableBlock

OUTPUT_DIR = Path(__file__).parent.parent / "output"
LOGO_PATH = Path(__file__).parent.parent / "src" / "openaec_reports" / "assets" / "logos" / "default.png"


def main():
    """Genereer een volledig integratierapport."""
    report = Report(
        format=A4,
        project="Woonhuis Van der Berg",
        project_number="2026-042",
        client="Fam. Van der Berg",
        author="Ir. J.K. de Vries",
        report_type="structural",
    )

    # ---- Cover ----
    report.add_cover(subtitle="Constructieve berekening hoofddraagconstructie")

    # ---- Colofon ----
    report._colofon = {
        "subtitle": "Constructieve berekening hoofddraagconstructie",
        "Versie": "1.0",
        "Datum": "18 februari 2026",
        "Status": "CONCEPT",
        "Gecontroleerd door": "Ir. A.B. Jansen",
    }
    report.add_colofon()

    # ---- Sectie 1: Uitgangspunten (Paragraphs) ----
    report.add_section("Uitgangspunten", level=1, content=[
        "Dit rapport beschrijft de constructieve berekening voor het project "
        "Woonhuis Van der Berg te Zwijndrecht. Het betreft een nieuwbouw "
        "eengezinswoning met twee bouwlagen en een kap.",
        "Alle berekeningen zijn uitgevoerd conform de Eurocode "
        "(NEN-EN 1990 t/m NEN-EN 1999) met de Nederlandse Nationale Bijlagen.",
        "De volgende materialen zijn toegepast:",
    ])

    # ---- Sectie 2: Materiaaloverzicht (Table) ----
    materials_table = TableBlock(
        headers=["Onderdeel", "Materiaal", "Sterkteklasse", "γ [kN/m³]"],
        rows=[
            ["Fundering", "Gewapend beton", "C20/25", "25.0"],
            ["Vloer BG", "Gewapend beton", "C28/35", "25.0"],
            ["Vloer 1e", "Kanaalplaatvloer", "C45/55", "25.0"],
            ["Liggers", "Constructiestaal", "S235", "78.5"],
            ["Kolommen", "Constructiestaal", "S355", "78.5"],
            ["Metselwerk", "Baksteen + spouw", "CS IV", "18.0"],
        ],
        zebra=True,
    )
    report.add_section("Materiaaloverzicht", level=2, content=[
        "In onderstaande tabel zijn de toegepaste materialen samengevat.",
        materials_table,
    ])

    # ---- Sectie 3: Belastingen (Paragraphs + subsecties) ----
    report.add_section("Belastingen", level=1, content=[
        "De belastingen zijn bepaald conform NEN-EN 1991. "
        "Hieronder volgt een overzicht per belastingcategorie.",
    ])

    report.add_section("Permanente belastingen", level=2, content=[
        "Eigen gewicht betonvloer (200mm): 5.0 kN/m²",
        "Dekvloer (50mm): 1.2 kN/m²",
        "Plafondafwerking: 0.3 kN/m²",
        "Leidingwerk: 0.2 kN/m²",
        "Totaal permanent: 6.7 kN/m²",
    ])

    report.add_section("Veranderlijke belastingen", level=2, content=[
        "Nuttige belasting woonfunctie (cat. A): 1.75 kN/m²",
        "Niet-dragende scheidingswanden: 0.5 kN/m²",
        "Totaal veranderlijk: 2.25 kN/m²",
    ])

    # ---- Sectie 4: Staalligger berekening (Calculations) ----
    calc_med = CalculationBlock(
        title="Maatgevend veldmoment L1",
        formula="M_Ed = q_d × L² / 8",
        substitution="M_Ed = (1.2×6.7 + 1.5×2.25) × 3.0 × 6.0² / 8",
        result="M_Ed = 128.3",
        unit="kNm",
        reference="NEN-EN 1991-1-1 §6.3",
    )

    calc_mrd = CalculationBlock(
        title="Momentcapaciteit HEA 240",
        formula="M_Rd = W_pl,y × f_y / γ_M0",
        substitution="M_Rd = 744.6×10³ × 235 / 1.0 × 10⁻⁶",
        result="M_Rd = 175.0",
        unit="kNm",
        reference="NEN-EN 1993-1-1 §6.2.5",
    )

    calc_deflection = CalculationBlock(
        title="Doorbuiging in GGT",
        formula="δ = 5 × q_k × L⁴ / (384 × E × I)",
        substitution="δ = 5 × 6.75 × 3.0 × 6000⁴ / (384 × 210000 × 7763×10⁴)",
        result="δ = 18.2",
        unit="mm",
        reference="NEN-EN 1993-1-1 §7.2",
    )

    report.add_section(
        "Staalligger L1 — HEA 240",
        level=1,
        page_break_before=True,
        content=[
            "De staalligger L1 overspant 6.0 m en draagt een vloerstrook van 3.0 m breed. "
            "Profiel: HEA 240, staalsoort S235.",
            calc_med,
            calc_mrd,
            calc_deflection,
        ],
    )

    # ---- Sectie 5: Toetsingen (Checks) ----
    check_bending = CheckBlock(
        description="Buigingscontrole liggers",
        required="UC ≤ 1.0",
        calculated="M_Ed / M_Rd = 128.3 / 175.0",
        unity_check=0.73,
        reference="NEN-EN 1993-1-1 §6.2.5",
    )

    check_shear = CheckBlock(
        description="Dwarskrachtcontrole",
        required="UC ≤ 1.0",
        calculated="V_Ed / V_Rd = 85.5 / 312.4",
        unity_check=0.27,
        reference="NEN-EN 1993-1-1 §6.2.6",
    )

    check_deflection = CheckBlock(
        description="Doorbuigingscontrole",
        required="δ ≤ L/250 = 24.0 mm",
        calculated="δ = 18.2 mm",
        unity_check=0.76,
        reference="NEN-EN 1990 §A1.4.3",
    )

    check_fail = CheckBlock(
        description="Knikcontrole kolom K3",
        required="UC ≤ 1.0",
        calculated="N_Ed / N_b,Rd = 342.1 / 298.7",
        unity_check=1.15,
        reference="NEN-EN 1993-1-1 §6.3.1",
    )

    report.add_section(
        "Toetsingsoverzicht",
        level=1,
        page_break_before=True,
        content=[
            "Hieronder de toetsingsresultaten van de maatgevende elementen.",
            check_bending,
            check_shear,
            check_deflection,
            check_fail,
        ],
    )

    # ---- Sectie 6: Resultaten samenvatting (Table) ----
    results_table = TableBlock(
        headers=["Element", "Profiel", "Toets", "UC", "Status"],
        rows=[
            ["Ligger L1", "HEA 240", "Buiging", "0.73", "Voldoet"],
            ["Ligger L1", "HEA 240", "Dwarskracht", "0.27", "Voldoet"],
            ["Ligger L1", "HEA 240", "Doorbuiging", "0.76", "Voldoet"],
            ["Ligger L2", "HEA 200", "Buiging", "0.58", "Voldoet"],
            ["Ligger L2", "HEA 200", "Doorbuiging", "0.92", "Voldoet"],
            ["Kolom K1", "HEB 160", "Knik", "0.64", "Voldoet"],
            ["Kolom K2", "HEB 200", "Knik", "0.51", "Voldoet"],
            ["Kolom K3", "HEB 140", "Knik", "1.15", "Voldoet niet"],
        ],
        zebra=True,
    )

    report.add_section(
        "Samenvatting resultaten",
        level=1,
        page_break_before=True,
        content=[
            "Onderstaande tabel geeft een overzicht van alle toetsingsresultaten.",
            results_table,
            "Kolom K3 (HEB 140) voldoet niet aan de knikcontrole. "
            "Advies: opwaarderen naar HEB 160 (UC = 0.64).",
        ],
    )

    # ---- Sectie 7: Afbeelding (ImageBlock) ----
    if LOGO_PATH.exists():
        logo_image = ImageBlock(
            path=LOGO_PATH,
            width_mm=60,
            caption="Figuur 1 — OpenAEC logo (test afbeelding)",
            align="center",
        )
        report.add_section(
            "Bijlagen",
            level=1,
            page_break_before=True,
            content=[
                "Ter illustratie van de ImageBlock functionaliteit is hieronder "
                "het OpenAEC logo opgenomen als testafbeelding.",
                logo_image,
            ],
        )

    # ---- Backcover ----
    report.add_backcover()

    # ---- Build ----
    output_path = OUTPUT_DIR / "full_integration_test.pdf"
    result = report.build(output_path)
    print(f"Integratierapport gegenereerd: {result}")
    print(f"  Bestandsgrootte: {result.stat().st_size:,} bytes")
    print(f"  Secties: {len(report._sections)}")


if __name__ == "__main__":
    main()
