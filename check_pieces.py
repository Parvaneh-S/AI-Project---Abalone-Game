"""Check if the piece positions in standard_layout are valid"""
from src.game.layouts import valid_abalone_cells, standard_layout

cells = valid_abalone_cells(4)
board = standard_layout()

print("Checking standard layout piece positions...\n")

# Count pieces
black_count = sum(1 for p in board.values() if p == "B")
white_count = sum(1 for p in board.values() if p == "W")
empty_count = sum(1 for p in board.values() if p is None)

print(f"Black pieces: {black_count}")
print(f"White pieces: {white_count}")
print(f"Empty cells: {empty_count}")
print(f"Total cells: {black_count + white_count + empty_count}")
print()

# Check if all piece positions are valid (from updated standard_layout)
black_positions = [
    # Row r = -4 (5 cells: q from 0 to 4)
    (0, -4), (1, -4), (2, -4), (3, -4), (4, -4),
    # Row r = -3 (6 cells: q from -1 to 4)
    (-1, -3), (0, -3), (1, -3), (2, -3), (3, -3), (4, -3),
    # Row r = -2 (7 cells: q from -2 to 4) - only middle 3
    (0, -2), (1, -2), (2, -2),
]

white_positions = [
    # Row r = 2 (7 cells: q from -4 to 2) - only middle 3
    (-2, 2), (-1, 2), (0, 2),
    # Row r = 3 (6 cells: q from -4 to 1)
    (-4, 3), (-3, 3), (-2, 3), (-1, 3), (0, 3), (1, 3),
    # Row r = 4 (5 cells: q from -4 to 0)
    (-4, 4), (-3, 4), (-2, 4), (-1, 4), (0, 4),
]

print("Checking black piece positions:")
for pos in black_positions:
    if pos not in cells:
        print(f"  ❌ INVALID: {pos} is not in the board!")
    else:
        print(f"  ✓ {pos}")

print("\nChecking white piece positions:")
for pos in white_positions:
    if pos not in cells:
        print(f"  ❌ INVALID: {pos} is not in the board!")
    else:
        print(f"  ✓ {pos}")

# Show the board with pieces
from collections import defaultdict
print("\n\nBoard visualization with pieces:")
print("(B = Black, W = White, . = empty)\n")

rows = defaultdict(list)
for coord in cells:
    q, r = coord
    rows[r].append((q, board[coord]))

for r in range(-4, 5):
    row_data = sorted(rows[r], key=lambda x: x[0])
    indent = ' ' * abs(r)
    cells_str = ''
    for q, piece in row_data:
        if piece == "B":
            cells_str += 'B '
        elif piece == "W":
            cells_str += 'W '
        else:
            cells_str += '· '
    print(f"   {indent}{cells_str}")

