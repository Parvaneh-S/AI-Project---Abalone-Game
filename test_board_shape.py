from src.game.layouts import valid_abalone_cells
from collections import defaultdict

cells = valid_abalone_cells(4)
print(f'Total cells: {len(cells)}')
print()

rows = defaultdict(list)
for q, r in cells:
    rows[r].append(q)

print('Board structure (from top to bottom):')
for r in range(-4, 5):
    qs = sorted(rows[r])
    indent = ' ' * (4 - abs(r))
    print(f'r={r:2} ({len(qs):1} cells): {indent}{"●" * len(qs)}')

print()
print('Detailed coordinates:')
for r in range(-4, 5):
    qs = sorted(rows[r])
    print(f'r={r:2}: q in [{min(qs):2}, {max(qs):2}]')

