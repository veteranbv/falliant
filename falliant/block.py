"""
Block definitions for Falliant
"""

from dataclasses import dataclass
from typing import List

from .constants import BLOCK_COLORS, BLOCK_SHAPES


@dataclass
class Block:
    """Represents a falling block in the game"""

    shape_index: int  # Index into BLOCK_SHAPES
    rotation: int  # Current rotation state (index into the specific shape array)
    x: int  # X position (column)
    y: int  # Y position (row)

    @property
    def shape(self) -> List[str]:
        """Get current shape based on rotation"""
        return BLOCK_SHAPES[self.shape_index][self.rotation]

    @property
    def color(self) -> int:
        """Get color for this block type"""
        return BLOCK_COLORS[self.shape_index]

    @property
    def width(self) -> int:
        """Get width of current shape"""
        return len(self.shape[0])

    @property
    def height(self) -> int:
        """Get height of current shape"""
        return len(self.shape)
