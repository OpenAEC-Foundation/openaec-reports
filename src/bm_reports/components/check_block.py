"""Check block — Toetsingsresultaten (voldoet / voldoet niet)."""

from __future__ import annotations

from reportlab.platypus import Flowable
from reportlab.lib.colors import HexColor

from bm_reports.core.document import MM_TO_PT
from bm_reports.core.styles import BM_COLORS


class CheckBlock(Flowable):
    """Toetsingsblok flowable — visuele weergave van een toetsresultaat.

    Toont:
    - Beschrijving van de toets
    - Eis (vereiste waarde)
    - Berekende waarde
    - Unity check waarde (optioneel)
    - Resultaat met kleurindicatie (groen/rood)

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

    def wrap(self, available_width, available_height):
        self.width = available_width
        self.height = 40  # Placeholder
        return (self.width, self.height)

    def draw(self):
        """Render het toetsingsblok.

        Layout:
        ┌──────────────────────────────────────┐
        │ ● Beschrijving                 [REF] │
        │   Eis: ...    Berekend: ...          │
        │   UC = 0.73 ≤ 1.0          VOLDOET  │
        └──────────────────────────────────────┘
        """
        # TODO: Implementeer check block rendering
        # - Kleur indicator (groen/rood balk of dot)
        # - Tekst layout
        # - UC balk (optioneel, visuele balk proportioneel)
        pass
