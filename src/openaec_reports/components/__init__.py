"""Components — Herbruikbare bouwblokken voor rapporten."""

from openaec_reports.components.calculation import CalculationBlock
from openaec_reports.components.check_block import CheckBlock
from openaec_reports.components.image_block import ImageBlock
from openaec_reports.components.map_block import KadasterMap
from openaec_reports.components.table_block import TableBlock
from openaec_reports.components.title_block import TitleBlock

__all__ = [
    "TitleBlock",
    "ImageBlock",
    "TableBlock",
    "CalculationBlock",
    "CheckBlock",
    "KadasterMap",
]
