"""
Board renderer for the Abalone game.
"""
import math
from typing import List, Tuple, Dict
from src.ui.constants import (
    CELL_RADIUS, DX, DY,
    ROW_COUNTS, WHITE_COLOR, BLACK_COLOR
)


class BoardRenderer:
    """
    Handles rendering of the Abalone game board.
    """

    def __init__(self, center_xy: Tuple[int, int], invert_colors: bool = False, board_layout: str = 'standard'):
        """
        Initialize the board renderer.

        Args:
            center_xy: Center coordinates (x, y) for the board
            invert_colors: If True, the human player controls white marbles (does not affect board layout)
            board_layout: Board layout type ('standard', 'german', or 'belgian')
        """
        self.center_xy = center_xy
        self.invert_colors = invert_colors
        self.board_layout = board_layout
        self.cell_centers = self._compute_cell_centers()

    def _compute_cell_centers(self) -> List[List[Tuple[int, int]]]:
        """
        Compute cell centers laid out in rows: 5-6-7-8-9-8-7-6-5.

        Returns:
            List of rows, each containing (x, y) coordinates
        """
        cx, cy = self.center_xy
        rows: List[List[Tuple[int, int]]] = []

        total_rows = len(ROW_COUNTS)
        top_y = cy - (total_rows - 1) * DY // 2

        for r, count in enumerate(ROW_COUNTS):
            y = top_y + r * DY
            row_width = (count - 1) * DX
            start_x = cx - row_width // 2
            rows.append([(start_x + c * DX, y) for c in range(count)])

        return rows

    def _hex_polygon_around_cells(self, extra: int) -> List[Tuple[int, int]]:
        """
        Build a hexagon polygon around all circles.

        Args:
            extra: Expansion distance past the outermost circle boundary

        Returns:
            List of (x, y) vertices for the hexagon polygon
        """
        padding = CELL_RADIUS + extra

        # Get base positions from key cells
        top_left_base = self.cell_centers[0][0]
        top_right_base = self.cell_centers[0][-1]
        mid_right_base = self.cell_centers[4][-1]
        bottom_right_base = self.cell_centers[8][-1]
        bottom_left_base = self.cell_centers[8][0]
        mid_left_base = self.cell_centers[4][0]

        # For our flat-left-right hexagon orientation:
        cos30 = math.sqrt(3) / 2  # ≈ 0.866
        sin30 = 0.5

        # Top-left vertex (120° from center): offset at angle 120° outward
        top_left_x = top_left_base[0] - padding * sin30
        top_left_y = top_left_base[1] - padding * cos30

        # Top-right vertex (60° from center): offset at angle 60° outward
        top_right_x = top_right_base[0] + padding * sin30
        top_right_y = top_right_base[1] - padding * cos30

        # Middle-right vertex (0° from center): offset purely right
        mid_right_x = mid_right_base[0] + padding
        mid_right_y = mid_right_base[1]

        # Bottom-right vertex (300° from center): offset at angle 300° outward
        bottom_right_x = bottom_right_base[0] + padding * sin30
        bottom_right_y = bottom_right_base[1] + padding * cos30

        # Bottom-left vertex (240° from center): offset at angle 240° outward
        bottom_left_x = bottom_left_base[0] - padding * sin30
        bottom_left_y = bottom_left_base[1] + padding * cos30

        # Middle-left vertex (180° from center): offset purely left
        mid_left_x = mid_left_base[0] - padding
        mid_left_y = mid_left_base[1]

        return [
            (int(top_left_x), int(top_left_y)),
            (int(top_right_x), int(top_right_y)),
            (int(mid_right_x), int(mid_right_y)),
            (int(bottom_right_x), int(bottom_right_y)),
            (int(bottom_left_x), int(bottom_left_y)),
            (int(mid_left_x), int(mid_left_y)),
        ]

    def _get_example_marbles(self) -> Dict[Tuple[int, int], Tuple[int, int, int]]:
        """
        Get example marble positions for demonstration.

        Returns:
            Dictionary mapping (row, col) to RGB color tuple
        """
        colors: Dict[Tuple[int, int], Tuple[int, int, int]] = {}

        # In standard Abalone layout, white is always on top and black is always on bottom,
        # regardless of which color the human player chose.
        # For German/Belgian daisy layouts the positions are also fixed.
        top_color = WHITE_COLOR
        bottom_color = BLACK_COLOR


        if self.board_layout == 'standard':
            # Standard layout
            # Top marbles (rows 0, 1, and part of 2)
            for c in range(ROW_COUNTS[0]):
                colors[(0, c)] = top_color
            for c in range(ROW_COUNTS[1]):
                colors[(1, c)] = top_color
            for c in range(2, 5):  # middle marbles on row 2
                colors[(2, c)] = top_color

            # Bottom marbles (rows 8, 7, and part of 6)
            last = len(ROW_COUNTS) - 1
            for c in range(ROW_COUNTS[last]):
                colors[(last, c)] = bottom_color
            for c in range(ROW_COUNTS[last - 1]):
                colors[(last - 1, c)] = bottom_color
            for c in range(2, 5):  # middle marbles on row 6
                colors[(6, c)] = bottom_color

        elif self.board_layout == 'german':
            # German Daisy layout - 14 marbles per player
            # White marbles (14 total) - uses top_color
            # Row 1: positions 0, 1 (2 marbles)
            colors[(1, 0)] = top_color
            colors[(1, 1)] = top_color
            # Row 2: positions 0, 1, 2 (3 marbles)
            colors[(2, 0)] = top_color
            colors[(2, 1)] = top_color
            colors[(2, 2)] = top_color
            # Row 3: positions 1, 2 (2 marbles)
            colors[(3, 1)] = top_color
            colors[(3, 2)] = top_color
            # Row 5: positions 5, 6 (2 marbles)
            colors[(5, 5)] = top_color
            colors[(5, 6)] = top_color
            # Row 6: positions 4, 5, 6 (3 marbles)
            colors[(6, 4)] = top_color
            colors[(6, 5)] = top_color
            colors[(6, 6)] = top_color
            # Row 7: positions 4, 5 (2 marbles) - Total: 14
            colors[(7, 4)] = top_color
            colors[(7, 5)] = top_color

            # Black marbles (14 total) - uses bottom_color
            # Row 1: positions 4, 5 (2 marbles)
            colors[(1, 4)] = bottom_color
            colors[(1, 5)] = bottom_color
            # Row 2: positions 4, 5, 6 (3 marbles)
            colors[(2, 4)] = bottom_color
            colors[(2, 5)] = bottom_color
            colors[(2, 6)] = bottom_color
            # Row 3: positions 5, 6 (2 marbles)
            colors[(3, 5)] = bottom_color
            colors[(3, 6)] = bottom_color
            # Row 5: positions 1, 2 (2 marbles)
            colors[(5, 1)] = bottom_color
            colors[(5, 2)] = bottom_color
            # Row 6: positions 0, 1, 2 (3 marbles)
            colors[(6, 0)] = bottom_color
            colors[(6, 1)] = bottom_color
            colors[(6, 2)] = bottom_color
            # Row 7: positions 0, 1 (2 marbles) - Total: 14
            colors[(7, 0)] = bottom_color
            colors[(7, 1)] = bottom_color

        elif self.board_layout == 'belgian':
            # Belgian Daisy layout
            # Player 1 positions (14 total) - uses top_color
            # Row 0: positions 0, 1 (2 marbles)
            colors[(0, 0)] = top_color
            colors[(0, 1)] = top_color
            # Row 1: positions 0, 1, 2 (3 marbles)
            colors[(1, 0)] = top_color
            colors[(1, 1)] = top_color
            colors[(1, 2)] = top_color
            # Row 2: positions 1, 2 (2 marbles)
            colors[(2, 1)] = top_color
            colors[(2, 2)] = top_color
            # Row 6: positions 4, 5 (2 marbles)
            colors[(6, 4)] = top_color
            colors[(6, 5)] = top_color
            # Row 7: positions 3, 4, 5 (3 marbles)
            colors[(7, 3)] = top_color
            colors[(7, 4)] = top_color
            colors[(7, 5)] = top_color
            # Row 8: positions 3, 4 (2 marbles)
            colors[(8, 3)] = top_color
            colors[(8, 4)] = top_color

            # Player 2 positions (14 total) - uses bottom_color
            # Row 0: positions 3, 4 (2 marbles)
            colors[(0, 3)] = bottom_color
            colors[(0, 4)] = bottom_color
            # Row 1: positions 3, 4, 5 (3 marbles)
            colors[(1, 3)] = bottom_color
            colors[(1, 4)] = bottom_color
            colors[(1, 5)] = bottom_color
            # Row 2: positions 4, 5 (2 marbles)
            colors[(2, 4)] = bottom_color
            colors[(2, 5)] = bottom_color
            # Row 6: positions 1, 2 (2 marbles)
            colors[(6, 1)] = bottom_color
            colors[(6, 2)] = bottom_color
            # Row 7: positions 0, 1, 2 (3 marbles)
            colors[(7, 0)] = bottom_color
            colors[(7, 1)] = bottom_color
            colors[(7, 2)] = bottom_color
            # Row 8: positions 0, 1 (2 marbles)
            colors[(8, 0)] = bottom_color
            colors[(8, 1)] = bottom_color

        return colors


