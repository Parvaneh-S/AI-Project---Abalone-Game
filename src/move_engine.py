"""
Abalone State Space Generator.

Reads an input file TestX.input
Produces two output files alongside the input:
  TestX.move  — one legal move per line
  TestX.board — resulting board configuration after each move

Move notation
-------------
  Inline single:        i-An-D
  Inline group (2–3):   i-An-Bm-D   (An = trailing marble, Bm = leading marble)
  Side-step (2–3):      s-An-Bm-D   (An, Bm = group extremities in sorted order)
  D ∈ {1, 3, 5, 7, 9, 11}
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------
Player = str            # 'b' or 'w'
Cell = Tuple[int, int]  # axial coordinate (q, r)
Board = Dict[Cell, Player]

# ---------------------------------------------------------------------------
# Board geometry
# ---------------------------------------------------------------------------
RADIUS = 4

# Direction numbers and their axial (q, r) delta vectors.
DIRS: Dict[int, Cell] = {
    1:  ( 1, -1),   # NE — up-right
    3:  ( 1,  0),   # E  — right
    5:  ( 0,  1),   # SE — down-right
    7:  (-1,  1),   # SW — down-left
    9:  (-1,  0),   # W  — left
    11: ( 0, -1),   # NW — up-left
}
DIR_LIST: List[int] = [1, 3, 5, 7, 9, 11]
OPPOSITE: Dict[int, int] = {1: 7, 3: 9, 5: 11, 7: 1, 9: 3, 11: 5}

# Canonical half-directions used to enumerate side-step line orientations.
CANONICAL_DIRS: Tuple[int, ...] = (1, 3, 11)

# Row metadata: first valid column index and number of columns per row (A–I).
ROW_START: Dict[str, int] = {'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 1,
                              'F': 2, 'G': 3, 'H': 4, 'I': 5}
ROW_LEN:   Dict[str, int] = {'A': 5, 'B': 6, 'C': 7, 'D': 8, 'E': 9,
                              'F': 8, 'G': 7, 'H': 6, 'I': 5}

# Pre-computed set of all valid board cells.
CELLS: Set[Cell] = {
    (q, r)
    for q in range(-RADIUS, RADIUS + 1)
    for r in range(-RADIUS, RADIUS + 1)
    if abs(q) <= RADIUS and abs(r) <= RADIUS and abs(q + r) <= RADIUS
}

# Marble-token pattern used when parsing input files.
_MARBLE_RE = re.compile(r"([A-Ia-i])([1-9][0-9]?)([bwBW])")

# ---------------------------------------------------------------------------
# Axial coordinate helpers
# ---------------------------------------------------------------------------

def cell_add(a: Cell, b: Cell) -> Cell:
    """Return the cell-wise sum of two axial coordinates."""
    return (a[0] + b[0], a[1] + b[1])


def cell_scale(d: Cell, k: int) -> Cell:
    """Scale an axial direction vector by an integer factor."""
    return (d[0] * k, d[1] * k)


def notation_to_axial(coord: str) -> Cell:
    """Convert board notation (e.g. 'C5') to an axial (q, r) cell.

    Raises ValueError for any out-of-range or malformed coordinate.
    """
    row = coord[0].upper()
    col = int(coord[1:])
    if row not in ROW_START:
        raise ValueError(f"Unknown row letter: {row!r}")
    col_min = ROW_START[row]
    col_max = col_min + ROW_LEN[row] - 1
    if not (col_min <= col <= col_max):
        raise ValueError(f"Column {col} out of range [{col_min}, {col_max}] for row {row!r}")

    i = ord(row) - ord('A')          # A=0 … I=8
    r = RADIUS - i                   # A → r=4, I → r=-4
    q_min = max(-RADIUS, -r - RADIUS)
    q = q_min + (col - col_min)
    cell: Cell = (q, r)
    if cell not in CELLS:
        raise ValueError(f"Coordinate {coord!r} maps to invalid cell {cell}")
    return cell


def axial_to_notation(c: Cell) -> str:
    """Convert an axial (q, r) cell to board notation (e.g. 'C5')."""
    q, r = c
    i = RADIUS - r
    row = chr(ord('A') + i)
    q_min = max(-RADIUS, -r - RADIUS)
    col = ROW_START[row] + (q - q_min)
    return f"{row}{col}"


def notation_sort_key(rc: str) -> Tuple[str, int]:
    """Return a comparable sort key for a notation string like 'C5'."""
    return (rc[0], int(rc[1:]))

# ---------------------------------------------------------------------------
# Board helpers
# ---------------------------------------------------------------------------

def opponent(player: Player) -> Player:
    """Return the opposing player colour."""
    return 'w' if player == 'b' else 'b'


def player_cells(board: Board, player: Player) -> List[Cell]:
    """Return all cells occupied by *player*, sorted by board notation."""
    cells = [c for c, v in board.items() if v == player]
    cells.sort(key=lambda c: notation_sort_key(axial_to_notation(c)))
    return cells


def group_cells(origin: Cell, direction: Cell, size: int) -> List[Cell]:
    """Return *size* consecutive cells starting at *origin* along *direction*."""
    return [cell_add(origin, cell_scale(direction, i)) for i in range(size)]


def board_to_output(board: Board) -> str:
    """Serialise *board* to a comma-separated string, black marbles first.

    Within each colour, marbles are sorted by row then column.
    """
    def _sort_key(item: Tuple[Cell, Player]) -> Tuple[int, str, int]:
        cell, color = item
        rc = axial_to_notation(cell)
        return (0 if color == 'b' else 1, rc[0], int(rc[1:]))

    sorted_items = sorted(board.items(), key=_sort_key)
    return ",".join(f"{axial_to_notation(c)}{color}" for c, color in sorted_items)

# ---------------------------------------------------------------------------
# Move dataclass
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Move:
    """Represents a single legal Abalone move.

    Attributes
    ----------
    kind : 'i' (inline) or 's' (side-step)
    a    : Notation of the trailing marble / first extremity.
    b    : Notation of the leading marble / second extremity (None for a
           single-marble inline move).
    d    : Direction number (one of DIR_LIST).
    """
    kind: str
    a: str
    b: Optional[str]
    d: int

    def notation(self) -> str:
        """Return the canonical string representation of this move."""
        parts = [self.kind, self.a]
        if self.b is not None:
            parts.append(self.b)
        parts.append(str(self.d))
        return "-".join(parts)

# ---------------------------------------------------------------------------
# Move application
# ---------------------------------------------------------------------------

def _shift_group(board: Board, group: List[Cell], delta: Cell, player: Player) -> Board:
    """Return a new board with *group* shifted by *delta* (no validation)."""
    nb = dict(board)
    for c in group:
        del nb[c]
    for c in group:
        nb[cell_add(c, delta)] = player
    return nb


def apply_inline(board: Board, player: Player,
                 trailing: Cell, size: int, dnum: int) -> Optional[Board]:
    """Try to move a group of *size* marbles inline in direction *dnum*.

    Returns the new board state, or None if the move is illegal.
    """
    d = DIRS[dnum]
    opp = opponent(player)
    group = group_cells(trailing, d, size)

    if any(board.get(c) != player for c in group):
        return None

    ahead = cell_add(group[-1], d)

    # ── Case 1: move into an empty cell ──────────────────────────────────
    if ahead in CELLS and board.get(ahead) is None:
        return _shift_group(board, group, d, player)

    # ── Case 2: Sumito — push opponent marbles ────────────────────────────
    if ahead not in CELLS or board.get(ahead) != opp:
        return None

    # Count the consecutive opponent marbles ahead.
    opp_chain: List[Cell] = []
    cursor = ahead
    while cursor in CELLS and board.get(cursor) == opp:
        opp_chain.append(cursor)
        cursor = cell_add(cursor, d)

    # Sumito is illegal if the opponent group is as large or larger,
    # or if the cell beyond the opponent chain is occupied.
    if len(opp_chain) >= size:
        return None
    if cursor in CELLS and board.get(cursor) is not None:
        return None

    # Apply the push: remove both groups, then replace in new positions.
    nb = dict(board)
    for c in group + opp_chain:
        del nb[c]
    for c in group:
        nb[cell_add(c, d)] = player
    for c in opp_chain:
        dest = cell_add(c, d)
        if dest in CELLS:       # marble pushed off the board is simply removed
            nb[dest] = opp
    return nb


def apply_sidestep(board: Board, player: Player,
                   trailing: Cell, size: int,
                   line_dnum: int, move_dnum: int) -> Optional[Board]:
    """Try to side-step a group of *size* marbles from *trailing* along
    *line_dnum*, stepping each marble in direction *move_dnum*.

    Returns the new board state, or None if the move is illegal.
    """
    ld = DIRS[line_dnum]
    md = DIRS[move_dnum]
    group = group_cells(trailing, ld, size)

    if any(board.get(c) != player for c in group):
        return None

    dests = [cell_add(c, md) for c in group]
    if any(dest not in CELLS or board.get(dest) is not None for dest in dests):
        return None

    nb = dict(board)
    for c in group:
        del nb[c]
    for dest in dests:
        nb[dest] = player
    return nb

# ---------------------------------------------------------------------------
# Move generation
# ---------------------------------------------------------------------------

def _collect_inline_moves(board: Board, player: Player,
                           seen: Set[str]) -> List[Tuple[Move, Board]]:
    """Generate all legal inline moves for *player*."""
    results: List[Tuple[Move, Board]] = []
    for origin in player_cells(board, player):
        for dnum in DIR_LIST:
            d = DIRS[dnum]
            for size in (1, 2, 3):
                group = group_cells(origin, d, size)
                if any(g not in CELLS or board.get(g) != player for g in group):
                    continue

                nb = apply_inline(board, player, origin, size, dnum)
                if nb is None:
                    continue

                a = axial_to_notation(group[0])
                b = axial_to_notation(group[-1]) if size > 1 else None
                move = Move("i", a, b, dnum)
                notation = move.notation()
                if notation not in seen:
                    seen.add(notation)
                    results.append((move, nb))
    return results


def _collect_sidestep_moves(board: Board, player: Player,
                             seen: Set[str]) -> List[Tuple[Move, Board]]:
    """Generate all legal side-step moves for *player*.

    Only canonical line directions (1, 3, 11) are used so each group is
    enumerated once; the seen-set handles any remaining duplicates.
    """
    results: List[Tuple[Move, Board]] = []
    for origin in player_cells(board, player):
        for line_dnum in CANONICAL_DIRS:
            ld = DIRS[line_dnum]
            for size in (2, 3):
                group = group_cells(origin, ld, size)
                if any(g not in CELLS or board.get(g) != player for g in group):
                    continue

                for move_dnum in DIR_LIST:
                    if move_dnum in (line_dnum, OPPOSITE[line_dnum]):
                        continue

                    nb = apply_sidestep(board, player, origin, size,
                                        line_dnum, move_dnum)
                    if nb is None:
                        continue

                    a = axial_to_notation(group[0])
                    b = axial_to_notation(group[-1])
                    # Normalise extremity order for a stable notation.
                    if notation_sort_key(a) > notation_sort_key(b):
                        a, b = b, a

                    move = Move("s", a, b, move_dnum)
                    notation = move.notation()
                    if notation not in seen:
                        seen.add(notation)
                        results.append((move, nb))
    return results


def generate_moves(player: Player, board: Board) -> List[Tuple[Move, Board]]:
    """Return all legal moves for *player*, sorted by move notation."""
    seen: Set[str] = set()
    results = (
        _collect_inline_moves(board, player, seen)
        + _collect_sidestep_moves(board, player, seen)
    )
    results.sort(key=lambda t: t[0].notation())
    return results

# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------

def parse_input_file(path: str) -> Tuple[Player, Board]:
    """Parse a TestX.input file and return (player, board).

    The input file must contain exactly two non-empty lines:
      1. Player colour ('b' or 'w')
      2. Comma-separated marble tokens, e.g. 'C5b,D4w'
    """
    with open(path, encoding="utf-8") as fh:
        lines = [ln.strip() for ln in fh.read().splitlines() if ln.strip()]

    if len(lines) != 2:
        raise ValueError("Input file must contain exactly two non-empty lines.")

    player = lines[0].lower()
    if player not in ("b", "w"):
        raise ValueError(f"First line must be 'b' or 'w', got {player!r}.")

    board: Board = {}
    for token in (t.strip() for t in lines[1].split(",") if t.strip()):
        m = _MARBLE_RE.fullmatch(token)
        if not m:
            raise ValueError(f"Unrecognised marble token: {token!r}")
        rc = m.group(1).upper() + m.group(2)
        color = m.group(3).lower()
        cell = notation_to_axial(rc)
        if cell in board:
            raise ValueError(f"Duplicate marble position: {rc!r}")
        board[cell] = color

    return player, board


def write_outputs(input_path: str,
                  moves: List[Tuple[Move, Board]]) -> Tuple[str, str]:
    """Write .move and .board output files next to *input_path*.

    Returns the paths of the two created files.
    """
    base = os.path.splitext(os.path.basename(input_path))[0]
    out_dir = os.path.dirname(os.path.abspath(input_path))
    move_path = os.path.join(out_dir, f"{base}.move")
    board_path = os.path.join(out_dir, f"{base}.board")

    with (open(move_path, "w", encoding="utf-8") as fm,
          open(board_path, "w", encoding="utf-8") as fb):
        for mv, nb in moves:
            fm.write(mv.notation() + "\n")
            fb.write(board_to_output(nb) + "\n")

    return move_path, board_path

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main(argv: List[str]) -> int:
    if len(argv) != 2:
        print("Usage: python move_engine.py <TestX.input>")
        return 2

    input_path = os.path.abspath(argv[1])
    player, board = parse_input_file(input_path)
    moves = generate_moves(player, board)

    if not moves:
        print("No valid moves found.")
        return 1

    move_path, board_path = write_outputs(input_path, moves)
    print(f"Player to move : {player}")
    print(f"Moves generated: {len(moves)}")
    print(f"Move file      : {move_path}")
    print(f"Board file     : {board_path}")
    return 0


if __name__ == "__main__":
    import sys
    raise SystemExit(main(sys.argv))
