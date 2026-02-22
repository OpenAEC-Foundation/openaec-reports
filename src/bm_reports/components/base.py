"""BMFlowable — base class voor content block componenten."""

from __future__ import annotations

from reportlab.platypus import Flowable


class BMFlowable(Flowable):
    """Base class met standaard wrap/draw patroon.

    Subclasses implementeren ``_build_content(available_width)`` die een
    intern ReportLab-object retourneert (Table, Paragraph, etc.).
    wrap() en draw() worden automatisch afgehandeld.
    """

    _content: Flowable | None = None

    def _build_content(self, available_width: float) -> Flowable:
        """Bouw het interne flowable object. Moet door subclass geïmplementeerd worden."""
        raise NotImplementedError

    def wrap(self, available_width: float, available_height: float) -> tuple[float, float]:
        self._content = self._build_content(available_width)
        w, h = self._content.wrap(available_width, available_height)
        self.width = w
        self.height = h
        return (self.width, self.height)

    def draw(self):
        if self._content is not None:
            self._content.drawOn(self.canv, 0, 0)
