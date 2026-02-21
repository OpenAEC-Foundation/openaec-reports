"""Components — Herbruikbare bouwblokken voor rapporten."""

from bm_reports.components.calculation import CalculationBlock
from bm_reports.components.check_block import CheckBlock
from bm_reports.components.image_block import ImageBlock
from bm_reports.components.map_block import KadasterMap
from bm_reports.components.table_block import TableBlock
from bm_reports.components.title_block import TitleBlock

__all__ = [
    "TitleBlock",
    "ImageBlock",
    "TableBlock",
    "CalculationBlock",
    "CheckBlock",
    "KadasterMap",
]
