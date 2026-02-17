"""
Comprehensive test and documentation of the Abalone board structure.
This verifies that the board has the correct hexagonal shape.
"""
from src.game.layouts import valid_abalone_cells
from collections import defaultdict

def test_board_structure():
    """Test that the board has the correct structure."""
    cells = valid_abalone_cells(4)
    
    # Test 1: Total cell count
    assert len(cells) == 61, f"Expected 61 cells, got {len(cells)}"
    print("✓ Total cells: 61")
    
    # Test 2: Row pattern (5, 6, 7, 8, 9, 8, 7, 6, 5)
    rows = defaultdict(list)
    for q, r in cells:
        rows[r].append(q)
    
    expected_pattern = [5, 6, 7, 8, 9, 8, 7, 6, 5]
    actual_pattern = [len(rows[r]) for r in range(-4, 5)]
    
    assert actual_pattern == expected_pattern, \
        f"Expected pattern {expected_pattern}, got {actual_pattern}"
    print(f"✓ Row pattern: {actual_pattern}")
    
    # Test 3: Hexagonal symmetry
    # Check that the board forms a proper hexagon in cube coordinates
    for q, r in cells:
        s = -q - r
        assert max(abs(q), abs(r), abs(s)) <= 4, \
            f"Cell ({q}, {r}) violates hexagon constraint"
    print("✓ Hexagonal symmetry (cube coordinate constraint)")
    
    # Test 4: Row structure
    print("\n Row structure:")
    for r in range(-4, 5):
        qs = sorted(rows[r])
        row_label = "top" if r == -4 else "middle" if r == 0 else "bottom" if r == 4 else ""
        print(f"   r={r:2}: {len(qs)} cells, q in [{min(qs):2}, {max(qs):2}] {row_label}")
    
    # Test 5: Visual representation
    print("\n Visual board (each ● is a cell):")
    for r in range(-4, 5):
        qs = sorted(rows[r])
        indent = ' ' * abs(r)
        cells_str = '● ' * len(qs)
        print(f"   {indent}{cells_str}")
    
    print("\n✅ All tests passed! The board structure is correct.")
    print(f"   - Total: 61 cells")
    print(f"   - Shape: Proper hexagon")
    print(f"   - Pattern: 5, 6, 7, 8, 9, 8, 7, 6, 5 cells per row")
    
    return True

if __name__ == "__main__":
    test_board_structure()

