# Abalone AI - GUI Layout Reference

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         Abalone AI - Game Window (1200x760)                      │
├──────────────────┬───────────────────────────────────────┬──────────────────────┤
│                  │                                       │                      │
│ CONFIGURATION    │                                       │  GAME INFORMATION    │
│ (360x480)        │         GAME BOARD                    │  (360x728)           │
│                  │         (Hexagonal)                   │                      │
│ ┌──────────────┐ │                                       │ Status: RUNNING      │
│ │ Board Layout │ │        ⬡  ⬡  ⬡  ⬡  ⬡               │ Mode: Human vs AI    │
│ │▼ Standard    │ │      ⬡  ●  ●  ●  ●  ⬡              │ Layout: Standard     │
│ └──────────────┘ │    ⬡  ●  ●  ●  ●  ●  ⬡             │ To move: BLACK       │
│                  │  ⬡  ●  ●  ●  ●  ●  ●  ⬡            │                      │
│ ┌──────────────┐ │ ⬡  ⬡  ⬡  ⬡  ⬡  ⬡  ⬡  ⬡  ⬡         │ ──────────────────   │
│ │  Game Mode   │ │  ⬡  ○  ○  ○  ○  ○  ○  ⬡            │ Score:               │
│ │▼ Human vs PC │ │    ⬡  ○  ○  ○  ○  ○  ⬡             │ Black off: 0         │
│ └──────────────┘ │      ⬡  ○  ○  ○  ○  ⬡              │ White off: 0         │
│                  │        ⬡  ⬡  ⬡  ⬡  ⬡               │                      │
│ ┌──────────────┐ │                                       │ ──────────────────   │
│ │ Your Color   │ │    Hover: Yellow ring                │ Moves Taken:         │
│ │▼ BLACK       │ │    Selected: Thick ring              │ Black: 5             │
│ └──────────────┘ │    Dragging: Follows mouse           │ White: 4             │
│                  │                                       │ Limit: 50/player     │
│ ☐ Move Limit     │                                       │                      │
│ [___50______]    │                                       │ ──────────────────   │
│                  │                                       │ Time Per Move:       │
│ ☑ BLACK Time     │                                       │ BLACK: 2.456s        │
│ [___30.0____]    │                                       │ WHITE: 3.102s        │
│                  │                                       │ BLACK limit: 30s     │
│ ☐ WHITE Time     │                                       │                      │
│ [___30.0____]    │                                       │ Recent AI Moves:     │
│                  │                                       │  0.023s - (2,-1)→... │
├──────────────────┤                                       │  0.031s - (3,0)→...  │
│ CONTROLS         │                                       │                      │
│ (360x220)        │                                       │ ──────────────────   │
│                  │                                       │ Next AI Move:        │
│ ┌──────────────┐ │                                       │ (1,-2) -> (2,-2)     │
│ │    Start     │ │                                       │                      │
│ └──────────────┘ │                                       │ ──────────────────   │
│ ┌──────────────┐ │                                       │ Move History:        │
│ │Pause / Resume│ │                                       │ AI (1,-2) -> (2,-2)  │
│ └──────────────┘ │                                       │ HUMAN (3,1) -> (3,2) │
│ ┌──────────────┐ │                                       │ AI (0,-3) -> (0,-2)  │
│ │    Reset     │ │                                       │ HUMAN (2,2) -> (3,2) │
│ └──────────────┘ │                                       │ AI (-1,-2) -> (0,-2) │
│ ┌──────────────┐ │                                       │ HUMAN (4,0) -> (4,1) │
│ │     Undo     │ │                                       │ ... (4 more moves)   │
│ └──────────────┘ │                                       │                      │
│ ┌──────────────┐ │                                       │                      │
│ │     Stop     │ │                                       │                      │
│ └──────────────┘ │                                       │                      │
│                  │                                       │                      │
└──────────────────┴───────────────────────────────────────┴──────────────────────┘

Legend:
  ⬡ = Empty cell
  ● = BLACK marble
  ○ = WHITE marble
  [____] = Text input field
  ▼ = Dropdown menu
  ☐/☑ = Checkbox
  ┌─┐ = Button
```

## Panel Breakdown

### LEFT SIDE (360px wide)

**Top Section - Configuration Panel (480px tall)**
- Board Layout Dropdown
- Game Mode Dropdown  
- Player Color Dropdown
- Move Limit: Checkbox + Text Input
- Time Limits: 2x (Checkbox + Text Input)

**Bottom Section - Controls Panel (220px tall)**
- 5 Buttons (38px each, 10px gap)
  - Start
  - Pause / Resume
  - Reset
  - Undo
  - Stop

### CENTER (480px wide)

**Game Board**
- Hexagonal grid (61 cells)
- Centered vertically and horizontally
- Interactive hover/selection
- Drag-and-drop support
- Visual highlights

### RIGHT SIDE (360px wide)

**Information Panel (full height - 728px)**

Sections (top to bottom):
1. **Game Information** (4 lines)
2. **Score** (2 lines)
3. **Moves Taken** (3 lines)
4. **Time Per Move** (5+ lines)
   - Totals
   - Limits (if set)
   - Recent AI moves (last 5)
5. **Next AI Move** (1-2 lines)
6. **Move History** (10+ lines)
   - Shows last 10 moves
   - Scrolls automatically

## Interaction Points

### Configuration (Before Start)
```
1. Click dropdown → Select option
2. Type in text field → Enter number
3. Check/uncheck boxes → Enable/disable
```

### Game Controls (During Game)
```
1. Click buttons → Execute action
2. Click marble → Select piece
3. Click cell → Move piece
4. Drag marble → Start drag
5. Release on cell → Complete move
```

### Visual Feedback
```
- Hover over board → Yellow ring
- Select marble → Thick yellow ring
- Drag marble → Semi-transparent follows cursor
- Complete move → Board updates, info refreshes
```

## Color Coding

| Element | Color | Hex Code |
|---------|-------|----------|
| Background | Dark Blue-Gray | #121418 |
| Panels | Lighter Gray | #1C1E24 |
| Cells | Medium Gray | #2D303A |
| Cell Borders | Gray | #5A5F6E |
| BLACK Marble | Dark | #232328 |
| WHITE Marble | Light | #E1E1E6 |
| Highlight | Yellow | #FFD25A |
| Text | White | #F5F5F5 |
| Buttons | Light Gray | #DCDCDC |

## Responsive Elements

### Hover States
- Cells: Yellow ring on hover
- Buttons: No visual change (fixed design)
- Inputs: Cursor changes to text input

### Active States
- Selected Marble: Thick yellow border
- Active Text Input: Blue border
- Open Dropdown: Expanded options
- Dragging: Semi-transparent marble at cursor

### Disabled States
- Buttons when game stopped: Lighter gray (not interactive)
- Text inputs: Accept numeric only when specified
- Board: No interaction when not player's turn

## Information Flow

```
User Action → Event Handler → State Update → Visual Update
                    ↓              ↓              ↓
              scene.handle_event  GameState   panel.draw()
                                              board_renderer.draw()
```

### Example: Making a Move

```
1. User clicks marble
   → scene.handle_event()
   → selected = cell

2. User clicks destination  
   → scene.handle_event()
   → rules.apply_move_simple()
   → state.board updated
   → history.push()

3. Next frame
   → scene.draw()
   → board_renderer.draw() [shows new position]
   → hud.draw() [shows updated info]
```

## Summary

The GUI is organized into three clear sections:
- **Left**: Configuration and Control
- **Center**: Interactive Board
- **Right**: Information Display

All components are clearly labeled, color-coded, and provide immediate visual feedback for user actions.

