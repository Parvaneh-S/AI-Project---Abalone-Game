# Abalone AI - Complete GUI Features Documentation

## Overview

This document provides a comprehensive overview of all GUI features implemented in the Abalone AI application.

## GUI Layout

The application window (1200x760 pixels) is divided into three main sections:

1. **Left Panel**: Configuration and Controls (360px wide)
2. **Center Area**: Hexagonal Game Board
3. **Right Panel**: Game Information Display (360px wide)

---

## 1. INPUT COMPONENTS

### A. Configuration Panel (Top-Left)

Located at the top of the left side panel, this allows pre-game setup.

#### Board Layout Dropdown
- **Options**: 
  - Standard (traditional Abalone setup)
  - German Daisy (corner-clustered setup)
  - Belgian Daisy (center-focused setup)
- **Default**: Standard
- **When to use**: Before starting a new game
- **Effect**: Determines initial marble placement on the board

#### Game Mode Dropdown
- **Options**:
  - Human vs Computer
  - Human vs Human
  - Computer vs Computer
- **Default**: Human vs Computer
- **Effect**: Controls who plays (human or AI)

#### Player Color Dropdown
- **Options**: BLACK, WHITE
- **Default**: BLACK
- **Purpose**: Select which color you want to play as (when playing vs Computer)
- **Note**: BLACK always moves first

#### Move Limit Configuration
- **Enable Checkbox**: Turn move limit on/off
- **Text Input**: Enter maximum moves per player (numeric only)
- **Default**: 50 (when enabled)
- **Purpose**: Set a maximum number of moves to end the game
- **Behavior**: Game ends when either player reaches the limit

#### Time Limit Configuration (Per Player)
- **BLACK Time Limit**:
  - Enable Checkbox
  - Text Input (accepts decimals, e.g., 30.0)
  - Sets maximum seconds per move for BLACK player
  
- **WHITE Time Limit**:
  - Enable Checkbox
  - Text Input (accepts decimals, e.g., 30.0)
  - Sets maximum seconds per move for WHITE player

- **Note**: Time limits can be different for each player
- **Purpose**: Control how long AI/player can think per move

### B. Control Panel (Bottom-Left)

Five buttons for game control:

1. **Start Button**
   - Initiates a new game
   - Resets timers and history
   - Applies current configuration
   - Game status changes to RUNNING

2. **Pause / Resume Button**
   - Toggles between PAUSED and RUNNING states
   - Freezes game when paused
   - Resumes from same position

3. **Reset Button**
   - Resets game to initial state
   - Maintains current configuration
   - Clears all history and timers
   - Returns to STOPPED status

4. **Undo Button**
   - Reverts the last move
   - Restores previous board state
   - Maintains full move history
   - Can undo multiple times

5. **Stop Button**
   - Stops the current game
   - Returns to STOPPED status
   - Allows reconfiguration

### C. Board Interaction (Center)

#### Click-to-Move Method
1. **First Click**: Select your marble (must be your color)
   - Marble gets yellow highlight ring
   - Only valid during your turn
2. **Second Click**: Select destination
   - Must be adjacent empty cell
   - Move executes if valid
   - Selection clears after move

#### Drag-and-Drop Method
1. **Mouse Down**: Click and hold on your marble
   - Marble becomes selected
   - Starts drag operation
2. **Drag**: Move mouse while holding button
   - Marble follows cursor with semi-transparent effect
   - Original position shows empty
3. **Mouse Up**: Release on destination cell
   - Move executes if valid
   - Drag operation ends
   - Selection clears

#### Visual Feedback
- **Hover**: Yellow ring on cell under cursor
- **Selected**: Thicker yellow ring on selected marble
- **Dragging**: Semi-transparent marble at cursor position
- **Valid Cells**: Hexagonal grid with clear borders
- **Marbles**: 
  - BLACK: Dark gray circles
  - WHITE: Light gray circles

---

## 2. OUTPUT COMPONENTS

### A. Game Information Section (Top-Right)

#### Status Display
- **Status**: Current game state (STOPPED, RUNNING, PAUSED, GAMEOVER)
- **Mode**: Active game mode
- **Layout**: Current board layout name
- **To move**: Which player's turn it is (BLACK or WHITE)

### B. Score Display

Shows the primary win condition:

- **Black off-board**: Number of BLACK marbles pushed off the board
- **White off-board**: Number of WHITE marbles pushed off the board
- **Win Condition**: First player to push 6 opponent marbles off wins

### C. Moves Taken Display

Tracks move count per player:

- **Black**: Total moves made by BLACK
- **White**: Total moves made by WHITE
- **Limit**: Shows move limit if configured (e.g., "Limit: 50 per player")
- **Purpose**: Track game progress and enforce move limits

### D. Time Per Move (Agent) Display

Comprehensive timing information:

#### Aggregate Times
- **Total BLACK**: Cumulative time spent by BLACK player/agent
- **Total WHITE**: Cumulative time spent by WHITE player/agent
- **Format**: Displays in seconds with 3 decimal places (e.g., "2.456s")

#### Time Limits (if configured)
- Shows per-move time limits for each player
- Format: "BLACK limit: 30.0s/move"

#### Recent AI Moves
- Displays last 5 AI moves in reverse chronological order
- **Format**: `{time}s - {move_description}`
- **Example**: `0.023s - (2, -1) -> (3, -1)`
- **Purpose**: See how long each AI move took

### E. Next AI Move Display

Shows upcoming AI move before execution:

- **Format**: Move notation like "(2, -1) -> (3, -1)"
- **Timing**: Updates immediately before AI executes move
- **Default**: Shows "N/A" when not applicable
- **Purpose**: Preview what the AI is about to do

### F. Move History Display

Complete game log:

- **Shows**: Last 10 moves (most recent first)
- **Human Move Format**: `HUMAN (q, r) -> (q, r)`
- **AI Move Format**: `AI(agent_name) (q, r) -> (q, r) (time_s)`
- **Coordinates**: Axial hex coordinates (q, r)
- **Scrolling**: Automatically shows most recent moves
- **Purpose**: Review entire game progression

### G. Board Visual Display (Center)

Real-time board representation:

- **Hexagonal Grid**: 61 cells (radius 4)
- **Marble Positions**: Updated after each move
- **Color Coding**:
  - BLACK marbles: Dark color
  - WHITE marbles: Light color
- **Highlights**: Active during interaction
- **Updates**: Immediate after valid moves

---

## 3. CONFIGURATION OPTIONS DETAILS

### Initial Board Layout

#### Standard Layout
- **Description**: Traditional Abalone starting position
- **BLACK Placement**: 14 marbles in rows at top
- **WHITE Placement**: 14 marbles in rows at bottom
- **Use Case**: Standard competitive play

#### German Daisy Layout
- **Description**: Clustered diagonal arrangement
- **BLACK Placement**: Upper-left corner cluster
- **WHITE Placement**: Lower-right corner cluster
- **Use Case**: Alternative starting strategy

#### Belgian Daisy Layout
- **Description**: Center-focused arrangement
- **BLACK Placement**: Center-left cluster
- **WHITE Placement**: Center-right cluster
- **Use Case**: Center-control strategy

### Game Mode Options

#### Human vs Computer
- **Player**: Controls one color
- **AI**: Controls opponent color
- **Turn System**: Alternates between human and AI
- **Use Case**: Single-player practice

#### Human vs Human
- **Player 1**: Controls BLACK
- **Player 2**: Controls WHITE
- **Turn System**: Alternates between players
- **Use Case**: Local multiplayer

#### Computer vs Computer
- **AI 1**: Controls BLACK
- **AI 2**: Controls WHITE
- **Turn System**: Automated
- **Use Case**: AI testing and observation

### Move and Time Limits

#### Move Limit Per Player
- **Type**: Integer
- **Range**: Any positive number
- **Applied To**: Both players equally
- **Enforcement**: Game ends when limit reached
- **Use Case**: Quick games, testing

#### Time Limit Configuration
- **Type**: Float (seconds)
- **Granularity**: 3 decimal places
- **Per Player**: Can be set differently
- **Enforcement**: AI must complete move within time
- **Use Case**: Performance testing, competitive play

---

## 4. INTERACTION FLOWS

### Starting a New Game
1. Configure board layout
2. Select game mode
3. Choose player color (if vs Computer)
4. Set optional limits (moves/time)
5. Click "Start" button
6. Game begins with BLACK's turn

### Making a Move (Human)
1. Wait for your turn
2. Select your marble (click or drag)
3. Choose destination (click or release)
4. Move executes if valid
5. Turn passes to opponent

### Observing AI Move
1. AI's turn begins
2. "Next AI Move" displays planned move
3. Brief delay for visualization
4. AI executes move
5. Timing recorded and displayed
6. Turn passes to player/other AI

### Pausing and Resuming
1. Click "Pause / Resume" during game
2. Game state freezes
3. No moves can be made
4. Click again to resume
5. Game continues from same state

### Undoing Moves
1. Click "Undo" button
2. Last move reverted
3. Board state restored
4. Can undo multiple times
5. History maintained

### Stopping Game
1. Click "Stop" button
2. Game returns to STOPPED state
3. Can reconfigure settings
4. Click "Start" for new game

---

## 5. VISUAL DESIGN

### Color Scheme
- **Background**: Dark blue-gray (#121418)
- **Panels**: Slightly lighter (#1C1E24)
- **Cells**: Medium gray (#2D303A)
- **Marbles**: High contrast (dark/light)
- **Highlights**: Bright yellow (#FFD25A)
- **Text**: White/Light gray

### Typography
- **Main Font**: Consolas (monospace)
- **Size**: 18px for normal text
- **Title Size**: 22px bold
- **Purpose**: Clear, readable information display

### Layout Spacing
- **Margins**: 16px between elements
- **Panel Width**: 360px for side panels
- **Board Area**: Centered with adequate space
- **Button Height**: 38px
- **Input Height**: 32px

---

## 6. TECHNICAL NOTES

### Current Limitations
- Only single-marble moves implemented
- No pushing/sumito mechanics yet
- AI uses simple random strategy
- No move validation beyond adjacency

### Performance
- Runs at 60 FPS
- Smooth drag-and-drop
- Instant move validation
- Minimal AI delay for UX

### Compatibility
- Requires Python 3.10+
- Pygame 2.5.0+
- Windows/Mac/Linux compatible

---

## SUMMARY

The GUI provides a complete, user-friendly interface for playing Abalone with:

✅ **Input Components**:
- 3 dropdown menus for configuration
- 2 checkboxes + text inputs for limits
- 5 control buttons
- 2 move input methods (click/drag)

✅ **Output Components**:
- Game status and information
- Score tracking
- Move counting with limits
- Comprehensive timing data (5 recent + totals)
- AI move preview
- 10-move history display
- Real-time board updates

✅ **Configuration Options**:
- 3 board layouts
- 3 game modes
- 2 color choices
- Move limit (optional)
- Separate time limits per player (optional)

All requirements have been fully implemented with an intuitive, polished interface ready for gameplay and future AI logic enhancements.

