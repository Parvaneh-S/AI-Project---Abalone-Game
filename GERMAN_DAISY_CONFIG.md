"""
German Daisy Configuration - Visual Representation
"""

# Board Layout (Rows 0-8, with variable column counts)
# Row counts: [5, 6, 7, 8, 9, 8, 7, 6, 5]

Row 0: [5 positions]  . . . . .

Row 1: [6 positions]  W W . . B B
                      0 1 2 3 4 5

Row 2: [7 positions]  W W W . B B B
                      0 1 2 3 4 5 6

Row 3: [8 positions]  . W W . . B B .
                      0 1 2 3 4 5 6 7

Row 4: [9 positions]  . . . . . . . . .
                      0 1 2 3 4 5 6 7 8

Row 5: [8 positions]  . B B . . . W W .
                      0 1 2 3 4 5 6 7

Row 6: [7 positions]  B B B . W W W
                      0 1 2 3 4 5 6

Row 7: [6 positions]  B B . . W W
                      0 1 2 3 4 5

Row 8: [5 positions]  . . . . .


WHITE MARBLES (14 total):
- Row 1: positions 0, 1 (2 marbles)
- Row 2: positions 0, 1, 2 (3 marbles)
- Row 3: positions 1, 2 (2 marbles)
- Row 5: positions 5, 6 (2 marbles) [Note: Row 5 has 8 positions total, 0-7]
- Row 6: positions 4, 5, 6 (3 marbles)
- Row 7: positions 4, 5 (2 marbles)

BLACK MARBLES (14 total):
- Row 1: positions 4, 5 (2 marbles)
- Row 2: positions 4, 5, 6 (3 marbles)
- Row 3: positions 5, 6 (2 marbles)
- Row 5: positions 1, 2 (2 marbles)
- Row 6: positions 0, 1, 2 (3 marbles)
- Row 7: positions 0, 1 (2 marbles)

This creates a symmetric "daisy" pattern where:
- White marbles occupy the LEFT side (upper and lower)
- Black marbles occupy the RIGHT side (upper and lower)
- The center (Row 4) is completely empty
- Mirror symmetry exists between upper and lower halves

