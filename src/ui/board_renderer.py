"""
Board renderer for the Abalone game.
"""
import math
import pygame
from typing import List, Tuple, Dict
from src.constants import (
    CELL_RADIUS, CELL_MARGIN, RIM_WIDTH, DX, DY,
    ROW_COUNTS, BORDER_COLOR, BOARD_FILL,
    EMPTY_COLOR, WHITE_COLOR, BLACK_COLOR
)


class BoardRenderer:
    """
    Handles rendering of the Abalone game board.
    """

    def __init__(self, center_xy: Tuple[int, int]):
        """
        Initialize the board renderer.

        Args:
            center_xy: Center coordinates (x, y) for the board
        """
        self.center_xy = center_xy
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

        # Top whites
        for c in range(ROW_COUNTS[0]):
            colors[(0, c)] = WHITE_COLOR
        for c in range(ROW_COUNTS[1]):
            colors[(1, c)] = WHITE_COLOR
        for c in range(2, 5):  # middle whites on row 2
            colors[(2, c)] = WHITE_COLOR

        # Bottom blacks
        last = len(ROW_COUNTS) - 1
        for c in range(ROW_COUNTS[last]):
            colors[(last, c)] = BLACK_COLOR
        for c in range(ROW_COUNTS[last - 1]):
            colors[(last - 1, c)] = BLACK_COLOR
        for c in range(2, 5):  # middle blacks on row 6
            colors[(6, c)] = BLACK_COLOR

        return colors

    def draw(self, screen: pygame.Surface) -> None:
        """
        Draw the board on the given surface.

        Args:
            screen: Pygame surface to draw on
        """
        # Inner hex should fully contain all circles (radius + margin)
        inner_hex = self._hex_polygon_around_cells(extra=CELL_MARGIN)

        # Outer hex is inner hex expanded by rim width
        outer_hex = self._hex_polygon_around_cells(extra=CELL_MARGIN + RIM_WIDTH)

        # Draw rim and inner fill
        pygame.draw.polygon(screen, BORDER_COLOR, outer_hex)
        pygame.draw.polygon(screen, BOARD_FILL, inner_hex)

        # Draw circles (all will sit inside inner_hex now)
        marble_map = self._get_example_marbles()
        for r, row in enumerate(self.cell_centers):
            for c, (x, y) in enumerate(row):
                color = marble_map.get((r, c), EMPTY_COLOR)
                pygame.draw.circle(screen, (120, 120, 120), (x, y), CELL_RADIUS + 1)
                pygame.draw.circle(screen, color, (x, y), CELL_RADIUS)

