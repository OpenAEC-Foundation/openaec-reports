"""Base class voor content modules.

Definieert het interface waar alle tenant modules tegen ontwikkelen.
Elke module is een ReportLab Flowable die zichzelf tekent binnen het
standaard content frame. Subclasses implementeren _calculate_height() en draw().
"""

from __future__ import annotations

from dataclasses import dataclass, field

from reportlab.platypus import Flowable


@dataclass
class ModuleConfig:
    """Configuratie voor content modules (fonts, kleuren, maten)."""

    fonts: dict = field(default_factory=lambda: {
        "heading": "Helvetica-Bold",
        "body": "Helvetica",
    })
    colors: dict = field(default_factory=lambda: {
        "primary": "#006FAB",
        "secondary": "#94571E",
        "text": "#000000",
        "white": "#FFFFFF",
    })
    label_size: float = 10.0
    value_size: float = 10.0
    heading_size: float = 14.0
    line_color: str = "#006FAB"
    line_width: float = 0.5


class ContentModule(Flowable):
    """Base class voor alle content modules.

    Elke module is een ReportLab Flowable die zichzelf tekent
    binnen het standaard content frame. Subclasses implementeren
    ``_calculate_height()`` en ``draw()``.
    """

    def __init__(
        self,
        data: dict,
        config: ModuleConfig | None = None,
        available_width: float = 441.3,
    ) -> None:
        super().__init__()
        self.data = data
        self.config = config or ModuleConfig()
        self.available_width = available_width
        self.width = available_width
        self.height = self._calculate_height()

    def _calculate_height(self) -> float:
        raise NotImplementedError

    def draw(self) -> None:
        raise NotImplementedError

    def wrap(self, available_width: float, available_height: float) -> tuple[float, float]:
        self.available_width = available_width
        self.width = available_width
        self.height = self._calculate_height()
        return self.width, self.height
