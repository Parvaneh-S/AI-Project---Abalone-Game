"""Visualize the Abalone board shape to verify it's correct"""
from src.game.layouts import valid_abalone_cells

cells = valid_abalone_cells(4)
print(f'Total cells: {len(cells)}\n')

# Group by rows
from collections import defaultdict
rows = defaultdict(list)
for q, r in cells:
    rows[r].append(q)

# Create a 2D visual representation
print('Visual board layout (top view):')
print('(Each ● represents a cell)\n')

for r in range(-4, 5):
    if r not in rows:
        continue
    qs = sorted(rows[r])
    # Calculate indentation for hexagonal shape
    spaces = abs(r)
    line = ' ' * spaces
    for q in qs:
        line += '● '
    print(f'{line}  (row r={r}, {len(qs)} cells)')

print('\n' + '='*50)
print('Expected Abalone board: 5, 6, 7, 8, 9, 8, 7, 6, 5')
print('Actual board from top:  ', end='')
for r in range(-4, 5):
    print(len(rows[r]), end=', ' if r < 4 else '\n')

print('\nCoordinate ranges per row:')
for r in range(-4, 5):
    qs = sorted(rows[r])
    print(f'Row r={r:2}: q from {min(qs):2} to {max(qs):2} (span: {max(qs)-min(qs)+1}, cells: {len(qs)})')

