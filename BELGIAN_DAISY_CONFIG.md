# Belgian Daisy Board Configuration

## Overview
The Belgian Daisy board layout has been successfully implemented for the Abalone game. When users select the "Belgian Daisy" button on the board_layout_page, the board will display with the correct marble configuration.

## Configuration Details

### White Marbles (Upper Left and Lower Right Clusters)
The white marbles are positioned in two clusters:

```
Row 0: Positions 0, 1            (2 marbles)
Row 1: Positions 0, 1, 2         (3 marbles)
Row 2: Positions 1, 2            (2 marbles)
Row 6: Positions 4, 5            (2 marbles)
Row 7: Positions 3, 4, 5         (3 marbles)
Row 8: Positions 3, 4            (2 marbles)

Total: 14 marbles
```

### Black Marbles (Upper Right and Lower Left Clusters)
The black marbles are positioned in two clusters:

```
Row 0: Positions 3, 4            (2 marbles)
Row 1: Positions 3, 4, 5         (3 marbles)
Row 2: Positions 4, 5            (2 marbles)
Row 6: Positions 1, 2            (2 marbles)
Row 7: Positions 0, 1, 2         (3 marbles)
Row 8: Positions 0, 1            (2 marbles)

Total: 14 marbles
```

## Visual Representation
```
Row 0: [5]              W W . B B          (positions 0-4)
Row 1: [6]            W W W B B B          (positions 0-5)
Row 2: [7]          . W W . B B .          (positions 0-6)
Row 3: [8]        . . . . . . . .          (positions 0-7)
Row 4: [9]      . . . . . . . . .          (positions 0-8)
Row 5: [8]        . . . . . . . .          (positions 0-7)
Row 6: [7]          . B B . W W .          (positions 0-6)
Row 7: [6]            B B B W W W          (positions 0-5)
Row 8: [5]              B B . W W          (positions 0-4)

Legend:
- W = White marble
- B = Black marble
- . = Empty cell
```

## Color Inversion
The implementation supports color inversion when the user selects to play as black:
- If `invert_colors=False` (player is white): White marbles appear as shown above, Black marbles in opposite positions
- If `invert_colors=True` (player is black): Black marbles appear where white marbles are shown above

## Implementation
The configuration is implemented in the `BoardRenderer` class in `src/ui/board_renderer.py`, specifically in the `_get_example_marbles()` method under the `elif self.board_layout == 'belgian':` condition.

The board layout selection is handled in `src/ui/board_layout_page.py` (GameModePage class), where users can:
1. Select "Belgian Daisy" button
2. Choose their color (black or white circles)
3. Click "Next" to proceed to the game with the Belgian Daisy configuration

