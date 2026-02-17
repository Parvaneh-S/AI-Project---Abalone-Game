"""Verify all three board layouts"""
from src.game.layouts import standard_layout, german_daisy_layout, belgian_daisy_layout, valid_abalone_cells

cells = set(valid_abalone_cells(4))

def check_layout(name, board):
    print(f"\n{'='*60}")
    print(f"Testing {name}")
    print('='*60)

    black_count = sum(1 for p in board.values() if p == "B")
    white_count = sum(1 for p in board.values() if p == "W")
    empty_count = sum(1 for p in board.values() if p is None)

    print(f"Black pieces: {black_count}")
    print(f"White pieces: {white_count}")
    print(f"Empty cells: {empty_count}")
    print(f"Total cells: {len(board)}")

    # Check all positions are valid
    invalid_black = []
    invalid_white = []

    for coord, piece in board.items():
        if coord not in cells:
            if piece == "B":
                invalid_black.append(coord)
            elif piece == "W":
                invalid_white.append(coord)

    if invalid_black:
        print(f"\n❌ INVALID BLACK positions: {invalid_black}")
    else:
        print(f"\n✓ All black pieces on valid cells")

    if invalid_white:
        print(f"❌ INVALID WHITE positions: {invalid_white}")
    else:
        print(f"✓ All white pieces on valid cells")

    # Visualize
    from collections import defaultdict
    rows = defaultdict(list)
    for coord in cells:
        q, r = coord
        rows[r].append((q, board.get(coord, None)))

    print("\nBoard visualization:")
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

    if black_count == 14 and white_count == 14:
        print("\n✅ Layout is CORRECT (14 black, 14 white)")
    else:
        print(f"\n⚠️  Expected 14 pieces per side, got {black_count} black and {white_count} white")

# Test all layouts
check_layout("STANDARD", standard_layout())
check_layout("GERMAN DAISY", german_daisy_layout())
check_layout("BELGIAN DAISY", belgian_daisy_layout())

print("\n" + "="*60)
print("SUMMARY")
print("="*60)
print("All layouts have been verified!")

