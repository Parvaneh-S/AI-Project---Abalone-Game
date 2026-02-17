from __future__ import annotations

from typing import Dict, Tuple, Literal

Coord = Tuple[int, int]
Piece = Literal["B", "W"]


def valid_abalone_cells(radius: int = 4) -> list[Coord]:
    # axial hex of radius 4 => 61 cells (real Abalone board size)
    cells: list[Coord] = []
    for q in range(-radius, radius + 1):
        for r in range(-radius, radius + 1):
            s = -q - r
            if max(abs(q), abs(r), abs(s)) <= radius:
                cells.append((q, r))
    return cells


def standard_layout() -> Dict[Coord, Piece | None]:
    """Standard Abalone starting position."""
    cells = valid_abalone_cells(4)
    board: Dict[Coord, Piece | None] = {c: None for c in cells}

    # Black pieces (14 marbles)
    black_positions = [
        # Front row (r = -4)
        (-4, -4), (-3, -4), (-2, -4), (-1, -4), (0, -4),
        # Second row (r = -3)
        (-4, -3), (-3, -3), (-2, -3), (-1, -3), (0, -3), (1, -3),
        # Third row (r = -2)
        (-2, -2), (-1, -2), (0, -2),
    ]

    # White pieces (14 marbles)
    white_positions = [
        # Third row (r = 2)
        (0, 2), (1, 2), (2, 2),
        # Second row (r = 3)
        (-1, 3), (0, 3), (1, 3), (2, 3), (3, 3), (4, 3),
        # Front row (r = 4)
        (0, 4), (1, 4), (2, 4), (3, 4), (4, 4),
    ]

    for pos in black_positions:
        if pos in board:
            board[pos] = "B"
    for pos in white_positions:
        if pos in board:
            board[pos] = "W"

    return board


def german_daisy_layout() -> Dict[Coord, Piece | None]:
    """German Daisy starting position."""
    cells = valid_abalone_cells(4)
    board: Dict[Coord, Piece | None] = {c: None for c in cells}

    # Black pieces - clustered in upper left
    black_positions = [
        (-4, 0), (-4, 1), (-4, 2), (-4, 3), (-4, 4),
        (-3, -1), (-3, 0), (-3, 1), (-3, 2),
        (-2, -2), (-2, -1), (-2, 0),
        (-1, -3), (-1, -2),
    ]

    # White pieces - clustered in lower right
    white_positions = [
        (4, 0), (4, -1), (4, -2), (4, -3), (4, -4),
        (3, 1), (3, 0), (3, -1), (3, -2),
        (2, 2), (2, 1), (2, 0),
        (1, 3), (1, 2),
    ]

    for pos in black_positions:
        if pos in board:
            board[pos] = "B"
    for pos in white_positions:
        if pos in board:
            board[pos] = "W"

    return board


def belgian_daisy_layout() -> Dict[Coord, Piece | None]:
    """Belgian Daisy starting position."""
    cells = valid_abalone_cells(4)
    board: Dict[Coord, Piece | None] = {c: None for c in cells}

    # Black pieces - center-left cluster
    black_positions = [
        (-2, -2), (-2, -1), (-2, 0), (-2, 1), (-2, 2),
        (-1, -3), (-1, -2), (-1, -1),
        (0, -4), (0, -3), (0, -2),
        (1, -4), (1, -3), (2, -4),
    ]

    # White pieces - center-right cluster
    white_positions = [
        (2, 2), (2, 1), (2, 0), (2, -1), (2, -2),
        (1, 3), (1, 2), (1, 1),
        (0, 4), (0, 3), (0, 2),
        (-1, 4), (-1, 3), (-2, 4),
    ]

    for pos in black_positions:
        if pos in board:
            board[pos] = "B"
    for pos in white_positions:
        if pos in board:
            board[pos] = "W"

    return board


def get_layout_by_name(name: str) -> Dict[Coord, Piece | None]:
    """Get layout by name."""
    if name == "Standard":
        return standard_layout()
    elif name == "German Daisy":
        return german_daisy_layout()
    elif name == "Belgian Daisy":
        return belgian_daisy_layout()
    else:
        return standard_layout()

