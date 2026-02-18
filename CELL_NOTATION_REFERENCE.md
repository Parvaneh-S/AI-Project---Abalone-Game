# Abalone Board Cell Notation Reference

## Board Structure (ROW_COUNTS = [5, 6, 7, 8, 9, 8, 7, 6, 5])

```
                    I1  I2  I3  I4  I5      <- Row 0 (Top, 5 cells)
                  H1  H2  H3  H4  H5  H6    <- Row 1 (6 cells)
                G1  G2  G3  G4  G5  G6  G7  <- Row 2 (7 cells)
              F1  F2  F3  F4  F5  F6  F7  F8  <- Row 3 (8 cells)
            E1  E2  E3  E4  E5  E6  E7  E8  E9  <- Row 4 (Middle, 9 cells)
              D1  D2  D3  D4  D5  D6  D7  D8  <- Row 5 (8 cells)
                C1  C2  C3  C4  C5  C6  C7  <- Row 6 (7 cells)
                  B1  B2  B3  B4  B5  B6    <- Row 7 (6 cells)
                    A1  A2  A3  A4  A5      <- Row 8 (Bottom, 5 cells)
```

## Notation System Explanation

### Row Labels (I-A, top to bottom):
- **I** = Row 0 (top row, 5 cells)
- **H** = Row 1 (6 cells)
- **G** = Row 2 (7 cells)
- **F** = Row 3 (8 cells)
- **E** = Row 4 (middle/widest row, 9 cells)
- **D** = Row 5 (8 cells)
- **C** = Row 6 (7 cells)
- **B** = Row 7 (6 cells)
- **A** = Row 8 (bottom row, 5 cells)

### Column Numbers (1-9, left to right):
- Numbers increase from left to right within each row
- Simply 1-indexed: position 0 = column 1, position 1 = column 2, etc.
- Formula: `column_number = position + 1`

### Internal to Display Mapping:
- Internal row 0 → Display as **I** (top)
- Internal row 4 → Display as **E** (middle)
- Internal row 8 → Display as **A** (bottom)
- Formula: `row_label = chr(ord('I') - row)`

### Position Mapping Examples:

**Row I (internal row 0, 5 cells):**
- Position 0 → I1 (leftmost)
- Position 1 → I2
- Position 2 → I3
- Position 3 → I4
- Position 4 → I5 (rightmost)

**Row E (internal row 4, 9 cells, middle row):**
- Position 0 → E1 (leftmost)
- Position 1 → E2
- Position 2 → E3
- Position 3 → E4
- Position 4 → E5
- Position 5 → E6
- Position 6 → E7
- Position 7 → E8
- Position 8 → E9 (rightmost)

**Row A (internal row 8, 5 cells):**
- Position 0 → A1 (leftmost)
- Position 1 → A2
- Position 2 → A3
- Position 3 → A4
- Position 4 → A5 (rightmost)

## Move Notation Format

Moves are written as: `[from_cell][to_cell]`

### Examples:
- **D4E5** - Move from D4 to E5
- **I1I2** - Move from I1 to I2 (horizontal move in top row)
- **C3C4** - Move from C3 to C4
- **E6E7** - Move from E6 to E7 (in middle row)
- **D5E6** - Move from D5 to E6 (diagonal move between rows)

## Visual in Move History

Each move appears in the sidebar as:

```
Move History:
  ● D4E5
  ○ F3E3
  ● E6E7
  ○ G4F4
```

Where:
- ● = Black marble move (solid black circle)
- ○ = White marble move (solid white circle)

