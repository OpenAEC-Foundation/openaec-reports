"""TOC generator — Automatische inhoudsopgave."""

from __future__ import annotations

from reportlab.lib.colors import HexColor
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus.tableofcontents import TableOfContents

from openaec_reports.core.styles import BM_COLORS, BM_FONTS

# Heading style names die de TOC moet detecteren.
# Gebruikt door BMDocTemplate.afterFlowable() om automatisch
# TOC entries te registreren wanneer een heading wordt gerenderd.
TOC_HEADING_STYLES = ("Heading1", "Heading2", "Heading3")


class TOCBuilder:
    """Inhoudsopgave generator.

    Gebruikt ReportLab's TableOfContents met OpenAEC styling.
    De TOC wordt in twee passes gegenereerd:
    1. Eerste pass: Render rapport, verzamel heading posities
    2. Tweede pass: Vul TOC in met paginanummers

    Usage:
        toc = TOCBuilder()
        elements = [toc.placeholder()]  # Voeg toe op gewenste positie
        # ... voeg secties toe met toc.notify()
        # ReportLab multi-pass vult paginanummers automatisch in
    """

    def __init__(self):
        self._entry_count: int = 0
        self._toc = TableOfContents()
        self._configure_styles()

    def _configure_styles(self):
        """Configureer TOC stijlen per heading level."""
        self._toc.levelStyles = [
            ParagraphStyle(
                name="TOCLevel1",
                fontName=BM_FONTS.heading,
                fontSize=BM_FONTS.body_size + 1,
                leading=14,
                leftIndent=0,
                spaceBefore=4,
                textColor=HexColor(BM_COLORS.secondary),
            ),
            ParagraphStyle(
                name="TOCLevel2",
                fontName=BM_FONTS.body,
                fontSize=BM_FONTS.body_size,
                leading=12,
                leftIndent=15,
                spaceBefore=2,
            ),
            ParagraphStyle(
                name="TOCLevel3",
                fontName=BM_FONTS.body,
                fontSize=BM_FONTS.body_size - 0.5,
                leading=11,
                leftIndent=30,
                spaceBefore=1,
            ),
        ]

    def placeholder(self) -> TableOfContents:
        """Retourneer TOC flowable (placeholder voor eerste pass).

        Plaats dit element op de gewenste positie in het document.
        """
        return self._toc

    def notify(self, canvas, title: str, level: int = 0):
        """Registreer een heading voor de TOC.

        Wordt aangeroepen door BMDocTemplate.afterFlowable() voor elke
        sectietitel.

        Args:
            canvas: ReportLab canvas.
            title: Sectietitel.
            level: Heading level (0 = H1, 1 = H2, 2 = H3).
        """
        # ReportLab TOC entry format
        key = f"toc-{self._entry_count}"
        self._entry_count += 1

        # Bookmark voor TOC linking
        canvas.bookmarkPage(key)
        canvas.addOutlineEntry(title, key, level=level)
