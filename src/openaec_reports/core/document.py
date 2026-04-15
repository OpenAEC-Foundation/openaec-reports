"""Document model — paginaformaten, marges, document configuratie."""

from dataclasses import dataclass, field
from typing import Literal

# ReportLab werkt in points (1 pt = 1/72 inch)
MM_TO_PT = 2.8346456693


@dataclass(frozen=True)
class PageFormat:
    """Paginaformaat definitie in millimeters."""

    name: str
    width_mm: float
    height_mm: float

    @property
    def width_pt(self) -> float:
        return self.width_mm * MM_TO_PT

    @property
    def height_pt(self) -> float:
        return self.height_mm * MM_TO_PT

    @property
    def size_pt(self) -> tuple[float, float]:
        """ReportLab-compatibele (width, height) tuple in points."""
        return (self.width_pt, self.height_pt)


# Standaard paginaformaten
A4 = PageFormat(name="A4", width_mm=210, height_mm=297)
A3 = PageFormat(name="A3", width_mm=297, height_mm=420)


@dataclass
class Margins:
    """Marges in millimeters."""

    top: float = 25.0
    bottom: float = 20.0
    left: float = 20.0
    right: float = 15.0

    @property
    def top_pt(self) -> float:
        return self.top * MM_TO_PT

    @property
    def bottom_pt(self) -> float:
        return self.bottom * MM_TO_PT

    @property
    def left_pt(self) -> float:
        return self.left * MM_TO_PT

    @property
    def right_pt(self) -> float:
        return self.right * MM_TO_PT


@dataclass
class DocumentConfig:
    """Volledige document configuratie."""

    format: PageFormat = field(default_factory=lambda: A4)
    margins: Margins = field(default_factory=Margins)
    orientation: Literal["portrait", "landscape"] = "portrait"

    # Projectinformatie
    project: str = ""
    project_number: str = ""
    client: str = ""
    author: str = ""
    report_type: str = ""
    subtitle: str = ""

    @property
    def effective_pagesize(self) -> tuple[float, float]:
        """Retourneer (width, height) in points, rekening houdend met oriëntatie."""
        if self.orientation == "landscape":
            return (self.format.height_pt, self.format.width_pt)
        return self.format.size_pt

    @property
    def effective_width_pt(self) -> float:
        """Effectieve paginabreedte in points (rekening houdend met oriëntatie)."""
        return self.effective_pagesize[0]

    @property
    def effective_height_pt(self) -> float:
        """Effectieve paginahoogte in points (rekening houdend met oriëntatie)."""
        return self.effective_pagesize[1]

    @property
    def content_width_pt(self) -> float:
        """Beschikbare breedte voor content in points."""
        return self.effective_width_pt - self.margins.left_pt - self.margins.right_pt

    @property
    def content_height_pt(self) -> float:
        """Beschikbare hoogte voor content in points."""
        return self.effective_height_pt - self.margins.top_pt - self.margins.bottom_pt


class Document:
    """Basis document container.

    Bevat configuratie en de lijst van content elementen
    die door de Engine worden gerenderd naar PDF.
    """

    def __init__(self, config: DocumentConfig | None = None, **kwargs):
        if config is not None:
            self.config = config
        else:
            self.config = DocumentConfig(**kwargs)

        self.elements: list = []
        self.metadata: dict = {}

    def add_element(self, element) -> None:
        """Voeg een content element toe aan het document."""
        self.elements.append(element)

    def __repr__(self) -> str:
        return (
            f"Document({self.config.format.name}, "
            f"project={self.config.project!r}, "
            f"elements={len(self.elements)})"
        )
