"""Check block — Toetsingsresultaten (voldoet / voldoet niet)."""

from __future__ import annotations

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle

from bm_reports.components.base import BMFlowable
from bm_reports.core.styles import (
    BLOCK_PADDING,
    BM_COLORS,
    BM_FONTS,
    BM_STYLES,
    block_style_body,
    block_style_heading,
    block_style_reference,
    block_style_result,
)

# Hoogte van de unity check balk in points
_UC_BAR_HEIGHT = 8


class CheckBlock(BMFlowable):
    """Toetsingsblok flowable — visuele weergave van een toetsresultaat.

    Toont:
    - Beschrijving van de toets + referentie (header)
    - Eis en berekende waarde
    - Unity check balk (optioneel, proportionele kleurenbalk)
    - Resultaat met kleurindicatie (groen/rood)

    Layout:
    ┌──────────────────────────────────────┐
    │ Beschrijving                  [REF]  │  ← header (lichte achtergrond)
    ├──────────────────────────────────────┤
    │ Eis: UC ≤ 1.0                        │
    │ Berekend: M_Ed / M_Rd = 39.1 / 100.9│
    │ ████████░░░░░░░░░░  UC = 0.39        │  ← UC balk
    │                            VOLDOET   │  ← resultaat (groen/rood)
    └──────────────────────────────────────┘
    Met groene/rode accent-lijn links.

    Args:
        description: Omschrijving van de toets.
        required: Eis / grenswaarde als tekst.
        calculated: Berekende waarde als tekst.
        unity_check: UC waarde (optioneel, 0.0 - ∞).
        limit: Grenswaarde voor UC (standaard 1.0).
        result: Expliciet resultaat, of automatisch bepaald op basis van UC.
        reference: Normatieve referentie.
    """

    def __init__(
        self,
        description: str,
        required: str = "",
        calculated: str = "",
        unity_check: float | None = None,
        limit: float = 1.0,
        result: str | None = None,
        reference: str = "",
    ):
        super().__init__()
        self.description = description
        self.required = required
        self.calculated = calculated
        self.unity_check = unity_check
        self.limit = limit
        self.reference = reference

        # Bepaal resultaat
        if result is not None:
            self.result = result
        elif unity_check is not None:
            self.result = "VOLDOET" if unity_check <= limit else "VOLDOET NIET"
        else:
            self.result = ""

    @property
    def passes(self) -> bool:
        """Of de toets voldoet."""
        return self.result.upper() == "VOLDOET"

    @property
    def result_color(self) -> str:
        """Kleur op basis van resultaat."""
        return BM_COLORS.accent if self.passes else BM_COLORS.warning

    def _build_uc_bar(self, bar_width: float) -> Table:
        """Bouw een visuele UC balk (proportioneel gevuld)."""
        color = HexColor(self.result_color)
        bg = HexColor(BM_COLORS.background_alt)

        # Bereken vulling (cap op 100% visueel)
        uc_ratio = self.unity_check / self.limit if self.limit > 0 else 0
        filled_w = max(bar_width * min(uc_ratio, 1.0), 1)
        empty_w = max(bar_width - filled_w, 0)

        widths = [filled_w]
        data_row = [""]
        if empty_w > 0:
            widths.append(empty_w)
            data_row.append("")

        bar = Table([data_row], colWidths=widths, rowHeights=[_UC_BAR_HEIGHT])
        cmds = [
            ("BACKGROUND", (0, 0), (0, 0), color),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("BOX", (0, 0), (-1, -1), 0.5, HexColor(BM_COLORS.rule)),
        ]
        if empty_w > 0:
            cmds.append(("BACKGROUND", (1, 0), (1, 0), bg))

        bar.setStyle(TableStyle(cmds))
        return bar

    def _build_content(self, available_width: float) -> Table:
        """Bouw intern Table object met alle toetsingsonderdelen."""
        pad = BLOCK_PADDING
        inner_w = available_width - 2 * pad
        color = HexColor(self.result_color)

        # Paragraph styles (gedeelde factories uit styles.py)
        s_desc = block_style_heading(BM_COLORS.text)
        s_ref = block_style_reference()
        s_detail = block_style_body()
        s_uc_text = ParagraphStyle(
            "_chk_uc",
            parent=BM_STYLES["Normal"],
            fontName=BM_FONTS.mono,
            fontSize=BM_FONTS.body_size,
            leading=BM_FONTS.body_size * 1.3,
            textColor=HexColor(BM_COLORS.text),
            spaceAfter=0,
        )
        s_result = block_style_result(self.result_color)
        s_result.alignment = TA_RIGHT

        rows = []

        # Row 0: header — beschrijving + referentie
        desc_para = Paragraph(self.description, s_desc)
        if self.reference:
            ref_para = Paragraph(self.reference, s_ref)
            header = Table(
                [[desc_para, ref_para]],
                colWidths=[inner_w * 0.6, inner_w * 0.4],
            )
            header.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ]
                )
            )
        else:
            header = desc_para
        rows.append([header])

        # Row 1: eis + berekend (elk op eigen regel)
        if self.required or self.calculated:
            parts = []
            if self.required:
                parts.append(f"<b>Eis:</b> {self.required}")
            if self.calculated:
                parts.append(f"<b>Berekend:</b> {self.calculated}")
            rows.append([Paragraph("<br/>".join(parts), s_detail)])

        # Row 2: UC balk + tekst (alleen als unity_check opgegeven)
        if self.unity_check is not None:
            bar_width = inner_w * 0.5
            bar = self._build_uc_bar(bar_width)
            uc_text = f"UC = {self.unity_check:.2f}"
            uc_row = Table(
                [[bar, Paragraph(uc_text, s_uc_text)]],
                colWidths=[bar_width + 4, inner_w - bar_width - 4],
            )
            uc_row.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                        ("LEFTPADDING", (1, 0), (1, 0), 6),
                    ]
                )
            )
            rows.append([uc_row])

        # Row 3: resultaat
        if self.result:
            rows.append([Paragraph(self.result, s_result)])

        # Bouw tabel
        table = Table(rows, colWidths=[available_width])

        cmds = [
            # Padding
            ("LEFTPADDING", (0, 0), (-1, -1), pad),
            ("RIGHTPADDING", (0, 0), (-1, -1), pad),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            # Header rij
            ("BACKGROUND", (0, 0), (-1, 0), HexColor(BM_COLORS.background_alt)),
            ("TOPPADDING", (0, 0), (-1, 0), 4),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
            # Linker kleur-indicator (groen/rood)
            ("LINEBEFORE", (0, 0), (0, -1), 3, color),
        ]

        table.setStyle(TableStyle(cmds))
        return table

    # wrap() en draw() worden geërfd van BMFlowable
