# Persistent Marble Selection Feature

## Date: February 18, 2026

## Overview

Implemented a persistent marble selection feature that keeps the selected marble highlighted and shows possible moves until the user either:
1. Selects another marble
2. Drops the marble on a valid destination (completes a move)

## Changes Made

### File Modified: `src/ui/board_scene.py`

#### 1. Added Selection State Variable (Line ~39)
```python
# Selection state - persistent selection that shows valid moves
self.selected_marble = None  # (row, col) of the currently selected marble
```

#### 2. Updated Mouse Click Handler (Lines ~450-458)
- When a player clicks on their marble, it now sets `self.selected_marble`
- This marble stays selected even after releasing the mouse button
- Clicking a different marble will change the selection to the new marble

#### 3. Updated Mouse Release Handler (Lines ~460-480)
- Added logic to clear selection (`self.selected_marble = None`) **only** when a valid move is completed
- If the marble is dropped on an invalid location, it stays selected with valid moves still shown
- Dragging state is reset regardless, but selection persists

#### 4. Updated Drawing Logic (Lines ~665-700)
- Changed to show valid destinations for either the dragged marble OR the selected marble
- Added highlight ring (gold) for selected marble even when not being dragged
- Valid move indicators (white dots) now persist as long as marble is selected

## Behavior

### Before
- Marble shows highlight and valid moves only while being dragged
- Once mouse button is released, all highlights disappear
- User had to drag again to see valid moves

### After
- Click on a marble to select it (shows gold ring highlight)
- Valid moves are shown with white dots
- Marble stays highlighted and valid moves remain visible until:
  - User clicks on a different marble (changes selection)
  - User successfully drops the marble on a valid destination (completes move)
- If dropped on invalid location, marble returns to original position but stays selected

## Testing Notes

✅ Application runs without errors
✅ Selection persists after releasing mouse button
✅ Valid moves remain visible for selected marble
✅ Selection changes when clicking different marble
✅ Selection clears after completing a valid move
✅ Only pre-existing type warnings remain (unrelated to this feature)

## User Experience Improvements

1. **Better Visualization**: Players can now study their move options without holding the mouse button
2. **Easier Decision Making**: Valid moves stay visible, allowing players to plan their strategy
3. **Intuitive Selection**: Clear visual feedback with gold ring on selected marble
4. **Flexible Interaction**: Can change selection by clicking another marble at any time

## Status: ✅ COMPLETE

The persistent marble selection feature has been successfully implemented and tested.

