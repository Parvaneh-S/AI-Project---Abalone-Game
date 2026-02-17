# Abalone AI - GUI Implementation

An Abalone game implementation with a comprehensive GUI for playing against an AI agent or other players.

## Features

### Configuration Panel (Left Side - Top)

The configuration panel allows you to set up the game before starting:

#### 1. Board Layout Selection
- **Standard**: Traditional Abalone starting position with 14 marbles per player
- **German Daisy**: Clustered starting position with marbles in opposite corners
- **Belgian Daisy**: Center-focused starting position

#### 2. Game Mode Selection
- **Human vs Computer**: Play against the AI agent
- **Human vs Human**: Two human players take turns
- **Computer vs Computer**: Watch two AI agents play against each other

#### 3. Player Color Selection
- Choose to play as **BLACK** or **WHITE**
- BLACK always moves first

#### 4. Move Limit Configuration
- Enable/disable move limit per player
- Set the maximum number of moves each player can make
- When limit is reached, game ends

#### 5. Time Limit Configuration
- **BLACK Time Limit**: Set maximum time per move for BLACK player (in seconds)
- **WHITE Time Limit**: Set maximum time per move for WHITE player (in seconds)
- Can be set independently for each player
- Enable/disable checkboxes control whether limits are enforced

### Control Panel (Left Side - Bottom)

Game control buttons:

1. **Start**: Begin a new game with current configuration
2. **Pause / Resume**: Pause or resume the game
3. **Reset**: Reset the game to initial state with current configuration
4. **Undo**: Undo the last move (maintains history)
5. **Stop**: Stop the game and return to configuration mode

### Game Board (Center)

The hexagonal Abalone board with interactive features:

#### Move Input Methods

**Method 1: Click-to-Move**
1. Click on one of your marbles to select it (highlighted in yellow)
2. Click on an adjacent empty cell to move there

**Method 2: Drag-and-Drop**
1. Click and hold on one of your marbles
2. Drag to the destination cell
3. Release to complete the move
4. The dragged marble follows your cursor with a semi-transparent effect

#### Visual Feedback
- **Hover Highlight**: Yellow ring appears when hovering over cells
- **Selected Highlight**: Yellow ring with thicker border on selected marble
- **Drag Visual**: Semi-transparent marble follows cursor during drag

### Information Panel (Right Side)

Comprehensive game information display:

#### 1. Game Information
- Current game status (STOPPED, RUNNING, PAUSED, GAMEOVER)
- Active game mode
- Current board layout
- Current player's turn

#### 2. Score Display
- **Black off-board**: Number of BLACK marbles pushed off
- **White off-board**: Number of WHITE marbles pushed off
- In Abalone, pushing 6 opponent marbles off the board wins the game

#### 3. Moves Taken
- Total moves made by BLACK player
- Total moves made by WHITE player
- Shows move limit if configured

#### 4. Time Per Move (Agent)
- **Total BLACK**: Aggregate time spent by BLACK player/agent
- **Total WHITE**: Aggregate time spent by WHITE player/agent
- Shows time limits if configured
- **Recent AI Moves**: Last 5 AI moves with individual timing
  - Format: `{time}s - {move description}`

#### 5. Next AI Move
- Shows the AI's planned next move before execution
- Updates before each AI move
- Shows "N/A" when not applicable

#### 6. Move History
- Complete history of all moves made in the game
- Shows last 10 moves (most recent first)
- Format for human moves: `HUMAN (q, r) -> (q, r)`
- Format for AI moves: `AI(agent_name) (q, r) -> (q, r) (time_s)`
- Scroll through to see all moves

## How to Play

1. **Configure Your Game**
   - Select desired board layout from dropdown
   - Choose game mode
   - Select your color if playing vs computer
   - Optionally set move and time limits
   
2. **Start the Game**
   - Click "Start" button
   - The game begins with BLACK's turn
   
3. **Make Your Move**
   - Use click-to-move or drag-and-drop to move your marbles
   - Only adjacent empty cells are valid moves (in this basic version)
   
4. **Monitor Progress**
   - Watch the score, moves, and timing information
   - Review move history to see what happened
   - See AI's next planned move before it executes
   
5. **Control the Game**
   - Pause if you need a break
   - Undo if you made a mistake
   - Reset to start over with same configuration
   - Stop to return to configuration

## Technical Details

### Architecture

- **src/ui/**: User interface components
  - `app.py`: Main application and game loop
  - `scene.py`: Game scene management and event handling
  - `panels.py`: Configuration, control, and HUD panels
  - `widgets.py`: Reusable UI widgets (buttons, dropdowns, text inputs, checkboxes)
  - `board_renderer.py`: Hexagonal board rendering and interaction

- **src/game/**: Game logic and state
  - `game_state.py`: Game state data structure
  - `layouts.py`: Board layout definitions
  - `rules.py`: Game rules and move validation
  - `history.py`: Move history management
  - `timer.py`: Timing and performance tracking

- **src/ai/**: AI agents
  - `agent_base.py`: Base agent interface
  - `random_agent.py`: Simple random move agent

### Dependencies

- **pygame**: For graphics and user interface
- **Python 3.10+**: Modern Python features used throughout

### Running the Application

```bash
python main.py
```

or

```bash
py main.py
```

## Setup

Install dependencies:
```bash
pip install pygame>=2.5
```

## Future Enhancements

- Advanced move mechanics (pushing, multi-marble moves)
- Smarter AI agents with search strategies
- Game saving and loading
- Network multiplayer support
- Move animation and effects
- Sound effects
- Tutorial mode

## Notes

- Currently implements basic single-marble moves only
- AI uses simple random strategy for moves
- Full Abalone rules (pushing, multi-marble moves) to be implemented later
- GUI is fully functional and ready for logic enhancements

