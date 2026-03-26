"""
Reproduce the 'J' KeyError crash by simulating game loop round-trips.
"""
import sys
import random
import traceback

# Make sure project root is importable
sys.path.insert(0, '.')

from src.move_engine import (
    generate_moves, axial_to_notation, notation_to_axial,
    Board, Player, CELLS, player_cells, opponent,
    ROW_START, ROW_LEN,
)

# ── Standard opening positions ────────────────────────────────────────────
_STANDARD_SETUP = (
    "A1b,A2b,A3b,A4b,A5b,"
    "B1b,B2b,B3b,B4b,B5b,B6b,"
    "C3b,C4b,C5b,"
    "I5w,I6w,I7w,I8w,I9w,"
    "H4w,H5w,H6w,H7w,H8w,H9w,"
    "G5w,G6w,G7w"
)

# Mimics board_scene._notation_to_cell
_ROW_START_D = {'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 1,
                'F': 2, 'G': 3, 'H': 4, 'I': 5}
_ROW_LEN_D = {'A': 5, 'B': 6, 'C': 7, 'D': 8, 'E': 9,
              'F': 8, 'G': 7, 'H': 6, 'I': 5}

def notation_to_cell(notation):
    if len(notation) < 2:
        return None
    row_label = notation[0].upper()
    col_str = notation[1:]
    try:
        if row_label not in _ROW_START_D:
            return None
        row = ord('I') - ord(row_label)
        col_num = int(col_str)
        start = _ROW_START_D[row_label]
        length = _ROW_LEN_D[row_label]
        if not (start <= col_num < start + length):
            return None
        col = col_num - start
        return (row, col)
    except (ValueError, TypeError):
        return None

def cell_to_notation(cell):
    row, col = cell
    if not (0 <= row <= 8):
        raise ValueError(f"Display row {row} out of range for cell {cell}")
    row_label = chr(ord('I') - row)
    if row_label not in _ROW_START_D:
        raise ValueError(f"Invalid row label {row_label!r} for cell {cell}")
    col_number = _ROW_START_D[row_label] + col
    return f"{row_label}{col_number}"

def engine_board_to_positions(engine_board):
    positions = {}
    for axial, player_char in engine_board.items():
        notation = axial_to_notation(axial)   # KeyError 'J' possible HERE
        cell = notation_to_cell(notation)
        if cell is not None:
            positions[cell] = player_char
    return positions

def positions_to_engine_board(positions):
    engine_board = {}
    for (row, col), player_char in positions.items():
        notation = cell_to_notation((row, col))  # KeyError 'J' possible HERE
        try:
            axial = notation_to_axial(notation)
        except ValueError:
            continue
        engine_board[axial] = player_char
    return engine_board


def parse_board(spec):
    board = {}
    for token in spec.replace(" ", "").split(","):
        token = token.strip()
        if not token:
            continue
        notation = token[:-1]
        color = token[-1].lower()
        board[notation_to_axial(notation)] = color
    return board


def count_color(board, color):
    return sum(1 for v in board.values() if v == color)


def simulate_game(seed, max_turns=200):
    rng = random.Random(seed)
    board = parse_board(_STANDARD_SETUP)
    current = 'b'

    for turn in range(max_turns):
        # 1) Validate board cells
        for cell in board:
            if cell not in CELLS:
                print(f"  [seed={seed}] turn {turn}: Board has invalid axial cell {cell}!", flush=True)
                return True  # Bug found

        # 2) Generate moves (this calls axial_to_notation internally)
        try:
            moves = generate_moves(current, board)
        except (KeyError, ValueError) as e:
            print(f"  [seed={seed}] turn {turn}: generate_moves crashed: {e}", flush=True)
            traceback.print_exc()
            return True

        if not moves:
            break

        move, new_board = rng.choice(moves)

        # 3) Validate the new board
        for cell in new_board:
            if cell not in CELLS:
                print(f"  [seed={seed}] turn {turn}: Move {move.notation()} produced invalid cell {cell}!", flush=True)
                return True

        # 4) Simulate the round-trip through display coordinates
        try:
            display_pos = engine_board_to_positions(new_board)
        except (KeyError, ValueError) as e:
            print(f"  [seed={seed}] turn {turn}: engine_board_to_positions crashed: {e}", flush=True)
            traceback.print_exc()
            return True

        try:
            round_tripped = positions_to_engine_board(display_pos)
        except (KeyError, ValueError) as e:
            print(f"  [seed={seed}] turn {turn}: positions_to_engine_board crashed: {e}", flush=True)
            traceback.print_exc()
            return True

        # 5) Check round-trip fidelity
        if set(round_tripped.keys()) != set(new_board.keys()):
            lost = set(new_board.keys()) - set(round_tripped.keys())
            gained = set(round_tripped.keys()) - set(new_board.keys())
            print(f"  [seed={seed}] turn {turn}: Round-trip mismatch! lost={lost}, gained={gained}", flush=True)
            return True

        # 6) Use the round-tripped board for next turn (like the game does)
        board = round_tripped
        opp = opponent(current)
        if count_color(board, opp) <= 8:  # 6 pushed off (14-6=8)
            break
        current = opp

    return False


def main():
    print("Simulating random games to reproduce 'J' crash...", flush=True)
    bugs_found = 0
    for seed in range(5000):
        if seed % 500 == 0:
            print(f"  Testing seeds {seed}–{seed+499}...", flush=True)
        found = simulate_game(seed)
        if found:
            bugs_found += 1
            if bugs_found >= 5:
                break

    if bugs_found == 0:
        print("No crash reproduced in 5000 seeds.", flush=True)
    else:
        print(f"Found {bugs_found} bug(s).", flush=True)


if __name__ == "__main__":
    main()



