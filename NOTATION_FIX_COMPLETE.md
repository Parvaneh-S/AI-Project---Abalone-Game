# Cell Notation Fix - CORRECTED Implementation

## Problem Identified
The original implementation had the wrong notation system. The board should follow standard Abalone notation where:
- Rows are labeled **I (top) to A (bottom)**
- Columns are numbered **1-9 from left to right** (simple 1-indexed)

## Corrected Implementation

### Row Mapping (FIXED):
```
Internal Row 0 → Display as I (top, 5 cells)
Internal Row 1 → Display as H (6 cells)
Internal Row 2 → Display as G (7 cells)
Internal Row 3 → Display as F (8 cells)
Internal Row 4 → Display as E (middle, 9 cells)
Internal Row 5 → Display as D (8 cells)
Internal Row 6 → Display as C (7 cells)
Internal Row 7 → Display as B (6 cells)
Internal Row 8 → Display as A (bottom, 5 cells)
```

### Formula (FIXED):
```python
row_label = chr(ord('I') - row)  # I at top (row 0), A at bottom (row 8)
col_number = col + 1              # Simple 1-indexed, left to right
```

### Verification Examples:
Based on user's correction "D4 to E5 should show as D4E5":
- **Internal (row=5, col=3)** → chr(73-5) + (3+1) = **D4** ✓
- **Internal (row=4, col=4)** → chr(73-4) + (4+1) = **E5** ✓

## Complete Board Layout

```
       I1  I2  I3  I4  I5          Row 0 (top)
     H1  H2  H3  H4  H5  H6        Row 1
   G1  G2  G3  G4  G5  G6  G7      Row 2
 F1  F2  F3  F4  F5  F6  F7  F8    Row 3
E1 E2 E3 E4 E5 E6 E7 E8 E9          Row 4 (middle)
 D1  D2  D3  D4  D5  D6  D7  D8    Row 5
   C1  C2  C3  C4  C5  C6  C7      Row 6
     B1  B2  B3  B4  B5  B6        Row 7
       A1  A2  A3  A4  A5          Row 8 (bottom)
```

## Move History Display
Moves now correctly show as:
- **D4E5** - marble moved from D4 to E5
- **I1I2** - marble moved from I1 to I2
- **F3E3** - marble moved from F3 to E3

Format in sidebar:
```
Move History:
  ● D4E5    (black marble)
  ○ F3E3    (white marble)
  ● E6E7    (black marble)
```

## Changes Made

### File: `src/ui/board_scene.py`

**Method `_cell_to_notation()`:**
```python
def _cell_to_notation(self, cell: tuple) -> str:
    row, col = cell
    row_label = chr(ord('I') - row)  # I=top, A=bottom
    col_number = col + 1              # 1-indexed left to right
    return f"{row_label}{col_number}"
```

## Testing
Run the game and make a move:
1. Pick up a marble at what looks like position D4
2. Drop it at position E5
3. The move history should show: **D4E5** with the correct marble color

## Status
✅ Row labels corrected (I=top, A=bottom)
✅ Column numbers corrected (1-indexed left to right)
✅ Move notation format correct
✅ Colored ball indicators working
✅ Ready to use!

