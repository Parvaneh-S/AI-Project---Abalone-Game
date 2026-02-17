from __future__ import annotations

import math
from typing import Dict, Tuple

import pygame

from src.constants import (
    BOARD_CENTER_X,
    BOARD_CENTER_Y,
    CELL_FILL,
    CELL_OUTLINE,
    HEX_SIZE,
    HIGHLIGHT,
    MARBLE_BLACK,
    MARBLE_WHITE,
)

Coord = Tuple[int, int]


class BoardRenderer:
    def __init__(self) -> None:
        self.radius = HEX_SIZE

    def axial_to_pixel(self, coord: Coord) -> Tuple[int, int]:
        q, r = coord
        x = self.radius * (3 / 2 * q)
        y = self.radius * (math.sqrt(3) * (r + q / 2))
        return int(BOARD_CENTER_X + x), int(BOARD_CENTER_Y + y)

    def hex_corners(self, center: Tuple[int, int]) -> list[Tuple[int, int]]:
        cx, cy = center
        corners: list[Tuple[int, int]] = []
        for i in range(6):
            angle = math.radians(60 * i - 30)
            x = cx + self.radius * math.cos(angle)
            y = cy + self.radius * math.sin(angle)
            corners.append((int(x), int(y)))
        return corners

    def draw(
        self,
        screen: pygame.Surface,
        board: Dict[Coord, str | None],
        selected: Coord | None,
        hover: Coord | None,
        dragging: Coord | None = None,
        drag_pos: Tuple[int, int] | None = None,
    ) -> None:
        # draw cells
        for coord in board.keys():
            center = self.axial_to_pixel(coord)
            poly = self.hex_corners(center)
            pygame.draw.polygon(screen, CELL_FILL, poly)
            pygame.draw.polygon(screen, CELL_OUTLINE, poly, width=2)

        # hover highlight
        if hover is not None and hover in board:
            center = self.axial_to_pixel(hover)
            pygame.draw.circle(screen, HIGHLIGHT, center, int(self.radius * 0.35), width=3)

        # pieces (skip the dragged one)
        for coord, piece in board.items():
            if piece is None or coord == dragging:
                continue
            center = self.axial_to_pixel(coord)
            color = MARBLE_BLACK if piece == "B" else MARBLE_WHITE
            pygame.draw.circle(screen, color, center, int(self.radius * 0.48))
            pygame.draw.circle(screen, (10, 10, 10), center, int(self.radius * 0.48), width=2)

        # selected highlight
        if selected is not None and selected in board and selected != dragging:
            center = self.axial_to_pixel(selected)
            pygame.draw.circle(screen, HIGHLIGHT, center, int(self.radius * 0.55), width=4)

        # Draw dragged piece at mouse position
        if dragging is not None and drag_pos is not None:
            piece = board.get(dragging)
            if piece is not None:
                color = MARBLE_BLACK if piece == "B" else MARBLE_WHITE
                # Draw with slight transparency effect by drawing a shadow
                shadow_surface = pygame.Surface((self.radius * 2, self.radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(shadow_surface, (*color, 180),
                                 (self.radius, self.radius), int(self.radius * 0.48))
                pygame.draw.circle(shadow_surface, (10, 10, 10, 180),
                                 (self.radius, self.radius), int(self.radius * 0.48), width=2)
                screen.blit(shadow_surface,
                          (drag_pos[0] - self.radius, drag_pos[1] - self.radius))

    def pixel_to_cell(self, pos: Tuple[int, int], board: Dict[Coord, str | None]) -> Coord | None:
        # Simple nearest-cell picking (works well enough for skeleton)
        mx, my = pos
        best: Coord | None = None
        best_d2 = 10**12
        for coord in board.keys():
            cx, cy = self.axial_to_pixel(coord)
            d2 = (mx - cx) ** 2 + (my - cy) ** 2
            if d2 < best_d2:
                best_d2 = d2
                best = coord
        # only accept if within a reasonable radius
        if best is None:
            return None
        cx, cy = self.axial_to_pixel(best)
        if (mx - cx) ** 2 + (my - cy) ** 2 <= (self.radius * 0.75) ** 2:
            return best
        return None
