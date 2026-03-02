"""Generate a test report with the OpenAEC Foundation tenant/brand."""

from __future__ import annotations

import os
from pathlib import Path

# Set tenant env vars before importing
os.environ["OPENAEC_TENANT_DIR"] = "tenants/openaec_foundation"
os.environ["OPENAEC_TENANTS_ROOT"] = "tenants"

from openaec_reports.core.brand import BrandLoader
from openaec_reports.core.engine import Report
from openaec_reports.core.fonts import register_tenant_fonts
from openaec_reports.core.tenant import TenantConfig

# --- 1. Load tenant and brand ---
tc = TenantConfig("tenants/openaec_foundation")
bl = BrandLoader(tenant_config=tc, tenants_root=Path("tenants"))
brand = bl.load("openaec_foundation")
print(f"Brand loaded: {brand.name}")

# --- 2. Register tenant fonts ---
if brand.font_files and brand.brand_dir:
    result = register_tenant_fonts(brand.font_files, brand.brand_dir)
    print(f"Fonts registered: {list(result.keys())}")

# --- 3. Test report data ---
data = {
    "template": "structural",
    "format": "A4",
    "project": "Amsterdam Central Station \u2014 Platform Extension",
    "project_number": "OA-2026-001",
    "client": "ProRail B.V.",
    "author": "OpenAEC Foundation",
    "date": "2026-03-02",
    "version": "1.0",
    "status": "DRAFT",
    "cover": {
        "subtitle": "Structural analysis \u2014 primary load-bearing structure",
    },
    "colofon": {
        "enabled": True,
        "revision_history": [
            {
                "version": "0.1",
                "date": "2026-02-15",
                "author": "OpenAEC Contributors",
                "description": "Initial draft",
            },
            {
                "version": "1.0",
                "date": "2026-03-02",
                "author": "OpenAEC Contributors",
                "description": "Final calculation",
            },
        ],
    },
    "toc": {"enabled": True, "max_depth": 3},
    "sections": [
        {
            "title": "Introduction",
            "level": 1,
            "content": [
                {
                    "type": "paragraph",
                    "text": (
                        "This report presents the structural analysis of the "
                        "platform extension at Amsterdam Central Station. The "
                        "extension consists of a steel frame structure supporting "
                        "a new platform roof."
                    ),
                },
                {
                    "type": "paragraph",
                    "text": (
                        "All calculations are performed according to the Eurocode "
                        "(NEN-EN 1990 through 1999) with the Dutch National Annexes."
                    ),
                },
            ],
        },
        {
            "title": "Design basis",
            "level": 1,
            "content": [
                {
                    "type": "paragraph",
                    "text": (
                        "The structural design is based on the following materials "
                        "and specifications."
                    ),
                },
                {
                    "type": "table",
                    "title": "Materials specification",
                    "headers": ["Element", "Material", "Grade"],
                    "rows": [
                        ["Foundation piles", "Reinforced concrete", "C30/37"],
                        ["Pile caps", "Reinforced concrete", "C28/35"],
                        ["Main beams", "Structural steel", "S355"],
                        ["Secondary beams", "Structural steel", "S235"],
                        ["Roof purlins", "Cold-formed steel", "S350GD"],
                        ["Connections", "Grade 10.9 bolts", "M20/M24"],
                    ],
                },
            ],
        },
        {
            "title": "Loading",
            "level": 1,
            "content": [
                {
                    "type": "paragraph",
                    "text": "Loads are determined according to NEN-EN 1991.",
                },
            ],
        },
        {
            "title": "Self-weight",
            "level": 2,
            "content": [
                {
                    "type": "paragraph",
                    "text": (
                        "Steel structure self-weight: calculated automatically. "
                        "Roof cladding (sandwich panel): 0.25 kN/m\u00b2. "
                        "Services and installations: 0.15 kN/m\u00b2."
                    ),
                },
            ],
        },
        {
            "title": "Variable loads",
            "level": 2,
            "content": [
                {
                    "type": "paragraph",
                    "text": (
                        "Snow load (zone 3): s_k = 0.70 kN/m\u00b2. "
                        "Wind load: determined per NEN-EN 1991-1-4, "
                        "terrain category III."
                    ),
                },
                {
                    "type": "table",
                    "title": "Load combinations (ULS)",
                    "headers": ["Combination", "Permanent", "Snow", "Wind"],
                    "rows": [
                        ["LC1 \u2014 Snow dominant", "1.35 G", "1.50 S", "0.90 W"],
                        ["LC2 \u2014 Wind dominant", "1.35 G", "0.75 S", "1.50 W"],
                        ["LC3 \u2014 Permanent only", "1.35 G", "\u2014", "\u2014"],
                    ],
                },
            ],
        },
        {
            "title": "Main beam B1 \u2014 HEB 400",
            "level": 1,
            "page_break_before": True,
            "content": [
                {
                    "type": "paragraph",
                    "text": (
                        "Main beam B1 spans 12.0 m between columns C1 and C2. "
                        "Profile: HEB 400, steel S355. The beam is laterally "
                        "restrained by the roof structure."
                    ),
                },
                {
                    "type": "calculation",
                    "title": "Design bending moment",
                    "formula": "M_Ed = q \u00d7 L\u00b2 / 8",
                    "substitution": "M_Ed = 24.5 \u00d7 12.0\u00b2 / 8",
                    "result": "441.0",
                    "unit": "kNm",
                    "reference": "NEN-EN 1993-1-1",
                },
                {
                    "type": "calculation",
                    "title": "Moment capacity",
                    "formula": "M_Rd = W_pl \u00d7 f_y / \u03b3_M0",
                    "substitution": "M_Rd = 2884e3 \u00d7 355 / 1.0",
                    "result": "1023.8",
                    "unit": "kNm",
                    "reference": "NEN-EN 1993-1-1 \u00a76.2.5",
                },
                {
                    "type": "check",
                    "description": "Unity check \u2014 bending beam B1",
                    "required_value": "UC \u2264 1.0",
                    "calculated_value": "M_Ed / M_Rd = 441.0 / 1023.8",
                    "unity_check": 0.43,
                    "limit": 1.0,
                    "reference": "NEN-EN 1993-1-1 \u00a76.2.5",
                },
                {
                    "type": "check",
                    "description": "Unity check \u2014 deflection beam B1",
                    "required_value": "\u03b4 \u2264 L/250 = 48.0 mm",
                    "calculated_value": "\u03b4 = 32.4 mm",
                    "unity_check": 0.68,
                    "limit": 1.0,
                    "reference": "NEN-EN 1993-1-1 \u00a77.2",
                },
            ],
        },
        {
            "title": "Column C1 \u2014 HEB 300",
            "level": 1,
            "content": [
                {
                    "type": "paragraph",
                    "text": (
                        "Column C1 carries the reaction from beam B1. "
                        "Height: 6.5 m. Profile: HEB 300, steel S355. "
                        "Buckling length: 1.0 L (pinned-pinned)."
                    ),
                },
                {
                    "type": "calculation",
                    "title": "Axial compression",
                    "formula": "N_Ed = R_B1 + G_self",
                    "substitution": "N_Ed = 147.0 + 8.9",
                    "result": "155.9",
                    "unit": "kN",
                    "reference": "NEN-EN 1993-1-1 \u00a76.3.1",
                },
                {
                    "type": "calculation",
                    "title": "Buckling resistance",
                    "formula": "N_b,Rd = \u03c7 \u00d7 A \u00d7 f_y / \u03b3_M1",
                    "substitution": "N_b,Rd = 0.87 \u00d7 14910 \u00d7 355 / 1.0",
                    "result": "4604.2",
                    "unit": "kN",
                    "reference": "NEN-EN 1993-1-1 \u00a76.3.1",
                },
                {
                    "type": "check",
                    "description": "Unity check \u2014 buckling column C1",
                    "required_value": "UC \u2264 1.0",
                    "calculated_value": "N_Ed / N_b,Rd = 155.9 / 4604.2",
                    "unity_check": 0.03,
                    "limit": 1.0,
                    "reference": "NEN-EN 1993-1-1 \u00a76.3.1",
                },
            ],
        },
        {
            "title": "Summary",
            "level": 1,
            "page_break_before": True,
            "content": [
                {
                    "type": "paragraph",
                    "text": (
                        "All structural elements satisfy the requirements of the "
                        "Eurocode. The maximum unity check is 0.68 (deflection "
                        "beam B1), well within acceptable limits."
                    ),
                },
                {
                    "type": "table",
                    "title": "Unity check overview",
                    "headers": ["Element", "Check", "UC", "Status"],
                    "rows": [
                        ["Beam B1", "Bending", "0.43", "OK"],
                        ["Beam B1", "Deflection", "0.68", "OK"],
                        ["Column C1", "Buckling", "0.03", "OK"],
                    ],
                },
            ],
        },
    ],
    "backcover": {"enabled": True},
    "metadata": {
        "software": "OpenAEC Report Generator v1.0",
        "calculation_software": "OpenAEC Structural v0.1",
    },
}

# --- 4. Generate report ---
print("Building report...")
report = Report.from_dict(data, brand=brand)
output_path = report.build("output/openaec_foundation_test.pdf")
print(f"PDF generated: {output_path}")
print(f"Size: {output_path.stat().st_size:,} bytes")
