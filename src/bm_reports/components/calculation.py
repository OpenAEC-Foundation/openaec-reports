"""Calculation block — Berekeningsregels met formule en resultaat."""

from __future__ import annotations

from reportlab.lib.colors import HexColor
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Flowable, Paragraph, Table, TableStyle

from bm_reports.core.styles import BM_COLORS, BM_FONTS, BM_STYLES


class CalculationBlock(Flowable):
    """Berekeningsblok flowable.

    Toont een berekening in standaard engineering notatie:
    - Titel + normatieve referentie (header)
    - Formule (monospace)
    - Substitutie (optioneel, lichter)
    - Scheidingslijn
    - Resultaat met eenheid

    Layout:
    ┌─────────────────────────────────┐
    │ Titel                    Ref    │  ← header (lichte achtergrond)
    ├─────────────────────────────────┤
    │ formule                         │  ← monospace
    │ substitutie                     │  ← monospace, lichter
    │─────────────────────────────────│
    │ resultaat = waarde eenheid      │  ← bold, primaire kleur
    └─────────────────────────────────┘
    Met turquoise accent-lijn links.

    Args:
        title: Naam van de berekening.
        formula: Wiskundige formule (tekst).
        substitution: Ingevulde waarden (optioneel).
        result: Berekend resultaat.
        unit: Eenheid.
        reference: Normatieve referentie (bijv. "NEN-EN 1992-1-1 §6.1").
    """

    def __init__(
        self,
        title: str,
        formula: str = "",
        substitution: str = "",
        result: str = "",
        unit: str = "",
        reference: str = "",
    ):
        super().__init__()
        self.title = title
        self.formula = formula
        self.substitution = substitution
        self.result = result
        self.unit = unit
        self.reference = reference

    def _build_block(self, available_width: float) -> Table:
        """Bouw intern Table object met alle berekeningsonderdelen."""
        pad = 6  # horizontal padding
        inner_w = available_width - 2 * pad

        # Lokale paragraph styles
        s_title = ParagraphStyle(
            "_calc_title",
            parent=BM_STYLES["Normal"],
            fontName=BM_FONTS.heading,
            fontSize=BM_FONTS.body_size,
            leading=BM_FONTS.body_size * 1.3,
            textColor=HexColor(BM_COLORS.primary),
            spaceAfter=0,
        )
        s_ref = ParagraphStyle(
            "_calc_ref",
            parent=BM_STYLES["Normal"],
            fontSize=BM_FONTS.caption_size,
            leading=BM_FONTS.caption_size * 1.3,
            textColor=HexColor(BM_COLORS.text_light),
            alignment=TA_RIGHT,
            spaceAfter=0,
        )
        s_formula = ParagraphStyle(
            "_calc_formula",
            parent=BM_STYLES["Normal"],
            fontName=BM_FONTS.mono,
            fontSize=BM_FONTS.body_size,
            leading=BM_FONTS.body_size * 1.4,
            spaceAfter=0,
        )
        s_sub = ParagraphStyle(
            "_calc_sub",
            parent=s_formula,
            textColor=HexColor(BM_COLORS.text_light),
        )
        s_result = ParagraphStyle(
            "_calc_result",
            parent=BM_STYLES["Normal"],
            fontName=BM_FONTS.heading,
            fontSize=BM_FONTS.body_size + 1,
            leading=(BM_FONTS.body_size + 1) * 1.3,
            textColor=HexColor(BM_COLORS.primary),
            spaceAfter=0,
        )

        rows = []

        # Row 0: header — titel + referentie
        title_para = Paragraph(self.title, s_title)
        if self.reference:
            ref_para = Paragraph(self.reference, s_ref)
            header = Table(
                [[title_para, ref_para]],
                colWidths=[inner_w * 0.6, inner_w * 0.4],
            )
            header.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
        else:
            header = title_para
        rows.append([header])

        # Row 1: formule
        if self.formula:
            rows.append([Paragraph(self.formula, s_formula)])

        # Row 2: substitutie
        if self.substitution:
            rows.append([Paragraph(self.substitution, s_sub)])

        # Row 3: resultaat
        if self.result:
            result_text = self.result
            if self.unit:
                result_text += f" {self.unit}"
            rows.append([Paragraph(result_text, s_result)])

        # Bouw tabel
        table = Table(rows, colWidths=[available_width])
        n = len(rows)
        result_idx = n - 1 if self.result else -1

        cmds = [
            # Padding voor alle cellen
            ("LEFTPADDING", (0, 0), (-1, -1), pad),
            ("RIGHTPADDING", (0, 0), (-1, -1), pad),
            ("TOPPADDING", (0, 0), (-1, -1), 2),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
            # Header rij
            ("BACKGROUND", (0, 0), (-1, 0), HexColor(BM_COLORS.background_alt)),
            ("TOPPADDING", (0, 0), (-1, 0), 4),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 4),
            # Linker accent-lijn (blauw)
            ("LINEBEFORE", (0, 0), (0, -1), 2.5, HexColor(BM_COLORS.secondary)),
        ]

        # Scheidingslijn boven resultaat
        if self.result and n > 1:
            cmds.append(
                ("LINEABOVE", (0, result_idx), (-1, result_idx),
                 0.5, HexColor(BM_COLORS.rule))
            )
            cmds.append(("TOPPADDING", (0, result_idx), (-1, result_idx), 4))

        table.setStyle(TableStyle(cmds))
        return table

    def wrap(self, available_width, available_height):
        self._block = self._build_block(available_width)
        w, h = self._block.wrap(available_width, available_height)
        self.width = w
        self.height = h
        return (self.width, self.height)

    def draw(self):
        """Render het berekeningsblok."""
        if hasattr(self, "_block"):
            self._block.drawOn(self.canv, 0, 0)
