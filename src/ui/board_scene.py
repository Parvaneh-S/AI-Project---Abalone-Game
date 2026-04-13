"""
Board scene for the Abalone game.
"""
import math
import threading
import time
import pygame
from typing import Optional, List, Dict, Tuple, Set
from src.ui.constants import FPS, BG_COLOR, CELL_RADIUS, BLACK_COLOR, WHITE_COLOR
from src.ui.board_renderer import BoardRenderer
from src.logic.move_engine import (
    generate_moves, notation_to_axial, axial_to_notation,
    Move, Board as EngineBoard, Player as EnginePlayer, CELLS as ENGINE_CELLS,
    DIRS, cell_add, group_cells, CANONICAL_DIRS, OPPOSITE,
)
from src.logic.ai_agent import AIAgent


class BoardScene:
    """
    Main game board scene.
    """

    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock, invert_colors: bool = False, board_layout: str = 'standard',
                 game_mode: Optional[int] = None, player1_time: Optional[int] = None,
                 player2_time: Optional[int] = None, move_limit: Optional[int] = None):
        """
        Initialize the board scene.

        Args:
            screen: Pygame surface to draw on
            clock: Pygame clock for timing
            invert_colors: If True, the human player controls white marbles
            board_layout: Board layout type ('standard', 'german', or 'belgian')
            game_mode: Game mode (0=Human vs AI, 1=AI vs AI, 2=Human vs Human)
            player1_time: Time per move for player 1 (seconds)
            player2_time: Time per move for player 2 (seconds)
            move_limit: Move limit for both players
        """
        self.screen = screen
        self.clock = clock
        self.invert_colors = invert_colors
        self.board_layout = board_layout
        self.game_mode = game_mode if game_mode is not None else 0
        self.running = True
        self.go_back = False

        # Set player color first (needed before other initializations)
        self.player_color = BLACK_COLOR if not invert_colors else WHITE_COLOR  # Player's chosen color

        # Turn tracking - black always starts first in Abalone
        # is_human_turn should reflect if it's the human player's turn, not just starting position
        self.current_turn_color = BLACK_COLOR  # Black always starts first
        self.is_human_turn = (self.player_color == BLACK_COLOR)  # True if human is playing black

        # Drag and drop state
        self.dragging = False
        self.dragged_marble = None  # (row, col) of the marble being dragged
        self.drag_offset = (0, 0)  # Offset from marble center to mouse position
        self.mouse_down_pos = None  # Position where mouse button was pressed (for click vs drag detection)
        self._marble_before_drag = None  # Selection state before the current mouse-down

        # Game state management
        self.game_paused = False  # Whether the game is currently paused
        self.game_started = False  # Game needs START button to begin
        self.initial_marble_positions = None  # Store initial board state for reset
        self.show_pause_modal = False  # Whether to show pause modal
        self.show_stop_modal = False  # Whether to show stop confirmation modal
        self.setup_mode = False  # Whether the game is in free setup mode (stop button)

        # Timeout (move time limit exceeded) state
        self.show_timeout_modal = False  # Whether to show the timeout game-over modal
        self.timeout_loser_color = None  # BLACK_COLOR or WHITE_COLOR – who ran out of time
        self.timeout_winner_color = None  # Winner determined by score comparison
        self.timeout_reason = ''  # Human-readable reason for the outcome

        # Move-limit exhausted state
        self.show_move_limit_modal = False  # Whether to show the move-limit game-over modal
        self.move_limit_loser_color = None  # BLACK_COLOR or WHITE_COLOR – who ran out of moves
        self.move_limit_winner_color = None  # Winner determined by score comparison
        self.move_limit_reason = ''  # Human-readable reason for the outcome

        # Win condition state (score reaches 6)
        self.show_win_modal = False  # Whether to show the win game-over modal
        self.winner_color = None  # BLACK_COLOR or WHITE_COLOR – who reached 6 points

        # Button tooltip tracking
        self.tooltip_text = None  # Current tooltip text to display
        self.tooltip_position = (0, 0)  # Tooltip position

        # Selection state - supports 1, 2, or 3 marble group selection
        self.selected_marbles: List[Tuple[int, int]] = []  # list of (row, col)
        # Cached legal moves from move_engine for the current board state & turn
        self._legal_moves_cache: List[Tuple[Move, EngineBoard]] = []
        # Maps destination (row, col) → (Move, EngineBoard) for the current selection
        self._dest_to_move: Dict[Tuple[int, int], Tuple[Move, EngineBoard]] = {}

        # Last-move arrow overlay: show direction arrows on marbles that just moved
        # until the opponent selects or moves new marbles.
        self._last_moved_cells: List[Tuple[int, int]] = []   # display (row, col)
        self._last_move_direction: Optional[int] = None       # DIRS key (1..11)
        self._last_move_color: Optional[Tuple[int, int, int]] = None  # color of mover

        # ── AI agent setup (Human vs AI / AI vs AI modes) ─────────────────
        self.ai_agent: Optional[AIAgent] = None
        self.ai_agent_black: Optional[AIAgent] = None   # AI vs AI: black agent
        self.ai_agent_white: Optional[AIAgent] = None   # AI vs AI: white agent
        self._ai_thinking = False        # True while the delay is ticking
        self._ai_think_start: int = 0    # pygame tick when the "thinking" began
        self._ai_think_delay: int = 600  # milliseconds to pause before AI plays

        # Background thread for AI computation so the UI stays responsive
        self._ai_thread: Optional[threading.Thread] = None
        self._ai_result: Optional[Tuple[Move, EngineBoard]] = None
        self._ai_thread_done = False     # set True by the worker thread when finished

        if self.game_mode == 0:  # Human vs AI
            # The AI controls whichever colour the human did NOT pick
            ai_color = WHITE_COLOR if self.player_color == BLACK_COLOR else BLACK_COLOR
            ai_player_char = 'b' if ai_color == BLACK_COLOR else 'w'
            # Give the AI a time budget that fits within the per-move clock.
            # Subtract a safety margin (1.2 s) to account for the cosmetic
            # "thinking" delay (~0.6 s) plus overhead / scheduling jitter.
            ai_move_time = player2_time if player2_time is not None else 5
            ai_time_budget = max(0.5, ai_move_time - 1.2)
            self.ai_agent = AIAgent(ai_player_char, time_limit=ai_time_budget)
        elif self.game_mode == 1:  # AI vs AI
            p1_time = player1_time if player1_time is not None else 5
            p2_time = player2_time if player2_time is not None else 5
            self.ai_agent_black = AIAgent('b', time_limit=max(0.5, p1_time - 1.2))
            self.ai_agent_white = AIAgent('w', time_limit=max(0.5, p2_time - 1.2))


        self._setup_back_button()
        self._setup_sidebar()
        self._setup_turn_text()
        self._setup_score_displays()

        # Calculate board center in the middle of free space (left edge to sidebar)
        window_w, window_h = self.screen.get_size()
        available_width = window_w - self.sidebar_width
        board_center = (available_width // 2, window_h // 2)
        self.board_renderer = BoardRenderer(board_center, invert_colors=invert_colors, board_layout=board_layout)

        # Initialize marble positions from board renderer
        self.marble_positions = self.board_renderer._get_example_marbles().copy()
        self.initial_marble_positions = self.marble_positions.copy()  # Save initial state

        # Move history tracking
        self.move_history = []  # List of tuples: (move_notation, marble_color, old_positions, time_us)

        # Per-move timing (microseconds)
        self._move_turn_start_us: int = time.perf_counter_ns() // 1000  # µs when current turn began
        self._last_move_time_us: Optional[int] = None  # µs elapsed for the most recent move

        # Score tracking
        self.player_score = 0
        self.opponent_score = 0

        # Timer variables - set from player configuration
        self.move_time_player = player1_time if player1_time is not None else 5  # Time per move in seconds
        self.move_time_computer = player2_time if player2_time is not None else 5  # Time per move for opponent

        # Store original move times for reference during timer updates
        self._original_move_time_player = self.move_time_player
        self._original_move_time_computer = self.move_time_computer

        self.total_time_limit = None  # User-configurable total game time in seconds (None = not set yet)
        self.total_time = 0  # Current remaining total time (set when user enters value)
        self.is_game_timer_running = False
        self.start_ticks = 0

        # Total game time input field state
        self.total_time_input_text = ""  # Text currently in the input field
        self.total_time_input_active = False  # Whether the input field is focused
        self.total_time_input_confirmed = False  # Whether a valid time has been confirmed

        # Move limit variables - set from shared player configuration
        self.move_limit = move_limit if move_limit is not None else 40
        self.max_moves_per_player = self.move_limit  # For compatibility
        self.player_moves_remaining = self.move_limit
        self.computer_moves_remaining = self.move_limit

        self._setup_timers()

    def _setup_timers(self) -> None:
        """Setup timer display elements."""
        # Font for timer text
        self.timer_font_large = pygame.font.Font(None, 44)
        self.timer_font_small = pygame.font.Font(None, 24)
        self.timer_text_color = (0, 0, 0)

        # Total time box properties
        self.total_time_box_width = 200
        self.total_time_box_height = 80
        self.total_time_box_color = (180, 140, 100)  # Tan/brown color

        # Input field properties for total game time
        self.total_time_input_font = pygame.font.Font(None, 32)
        self.total_time_input_color_active = (255, 255, 255)  # White when focused
        self.total_time_input_color_inactive = (220, 220, 220)  # Light gray when not focused
        self.total_time_input_border_active = (60, 140, 60)  # Green border when focused
        self.total_time_input_border_inactive = (100, 100, 100)  # Gray border when not focused
        self.total_time_input_rect = pygame.Rect(0, 0, 80, 30)  # Will be positioned dynamically


    def _reset_timer_for_next_turn(self) -> None:
        """Reset ONLY the per-move timer when switching to next player's turn."""
        # Reset ONLY the per-move timer, NOT the total game timer
        self.move_start_ticks = pygame.time.get_ticks()
        self._move_turn_start_us = time.perf_counter_ns() // 1000  # reset µs timer
        self.is_game_timer_running = True

    def _update_timers(self) -> None:
        """Update game timers."""
        if not self.is_game_timer_running:
            return

        # Total game time - never resets, counts continuously from game start
        if self.total_time_limit is not None:
            total_elapsed = (pygame.time.get_ticks() - self.start_ticks) // 1000
            self.total_time = max(0, self.total_time_limit - total_elapsed)
            # If total game time expired, trigger timeout for the current turn's player
            if self.total_time <= 0 and not self.show_timeout_modal:
                self._trigger_move_timeout(self.current_turn_color)

        # Per-move timer - resets for each player's turn (float for tenths of a second)
        move_elapsed = (pygame.time.get_ticks() - self.move_start_ticks) / 1000.0

        # Store the selected times (time per move, not move limits)
        selected_time_black = 5  # Default
        selected_time_white = 5  # Default

        # Use the move_time values that were set from configuration
        # Determine which player is black and which is white
        if self.player_color == BLACK_COLOR:
            # Human is black, so opponent is white
            selected_time_black = self._original_move_time_player if hasattr(self, '_original_move_time_player') else 5
            selected_time_white = self._original_move_time_computer if hasattr(self, '_original_move_time_computer') else 5
        else:
            # Human is white, so opponent is black
            selected_time_black = self._original_move_time_computer if hasattr(self, '_original_move_time_computer') else 5
            selected_time_white = self._original_move_time_player if hasattr(self, '_original_move_time_player') else 5

        # Update move timer based on whose turn it is (by color)
        if self.current_turn_color == BLACK_COLOR:
            # Black's turn - show black's time
            current_time = max(0.0, selected_time_black - move_elapsed)
            if self.player_color == BLACK_COLOR:
                self.move_time_player = current_time
            else:
                self.move_time_computer = current_time
            # Trigger timeout if time ran out
            if current_time <= 0 and not self.show_timeout_modal:
                self._trigger_move_timeout(BLACK_COLOR)
        else:
            # White's turn - show white's time
            current_time = max(0.0, selected_time_white - move_elapsed)
            if self.player_color == WHITE_COLOR:
                self.move_time_player = current_time
            else:
                self.move_time_computer = current_time
            # Trigger timeout if time ran out
            if current_time <= 0 and not self.show_timeout_modal:
                self._trigger_move_timeout(WHITE_COLOR)

    def _trigger_move_timeout(self, loser_color) -> None:
        """Stop the game because a player exceeded their per-move time limit.

        The player who ran out of time is *not* automatically the loser.
        Instead, the winner is determined by score comparison, and if scores
        are equal, by total time used (less is better).

        Args:
            loser_color: The color constant (BLACK_COLOR / WHITE_COLOR) of the player who ran out of time.
        """
        print(f"Move timeout! {'Black' if loser_color == BLACK_COLOR else 'White'} ran out of time.")
        self.timeout_loser_color = loser_color

        # Determine winner by score comparison
        winner, reason = self._determine_winner_by_score()
        self.timeout_winner_color = winner
        self.timeout_reason = reason

        self.show_timeout_modal = True
        self.game_paused = True
        self.is_game_timer_running = False

    def _setup_back_button(self) -> None:
        """Setup the back button in the top-left corner."""
        # Button properties
        button_width = 80
        button_height = 35
        button_x = 20  # Left margin
        button_y = 20  # Top margin

        # Create button rectangle
        self.back_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

        # Button colors
        self.back_button_color = (164, 182, 156)  # Sage green
        self.back_button_hover_color = (184, 202, 176)  # Lighter sage green
        self.back_button_text_color = (255, 255, 255)  # White
        self.current_back_button_color = self.back_button_color

        # Create button text
        font = pygame.font.Font(None, 28)
        self.back_button_text = font.render("Back", True, self.back_button_text_color)
        self.back_button_text_rect = self.back_button_text.get_rect(center=self.back_button_rect.center)

    def _setup_sidebar(self) -> None:
        """Setup the gray sidebar on the right side of the screen."""
        # Get current window dimensions
        window_w, window_h = self.screen.get_size()

        # Sidebar properties
        self.sidebar_width = 250  # Width of the sidebar
        self.sidebar_color = (128, 128, 128)  # Gray color

        # Horizontal box properties (lighter gray on top)
        self.horizontal_box_height = 80  # Height of the horizontal box
        self.horizontal_box_color = (180, 180, 180)  # Lighter gray color
        self.horizontal_box_margin = 15  # Margin from the sidebar edges

        # Bottom control box properties (lighter gray at bottom)
        self.bottom_box_height = 100  # Height of the bottom control box
        self.bottom_box_color = (180, 180, 180)  # Lighter gray color (same as top)

        # Create sidebar rectangle on the right side
        self.sidebar_rect = pygame.Rect(window_w - self.sidebar_width, 0, self.sidebar_width, window_h)

        # Create horizontal box rectangle on top of the sidebar with margins
        self.horizontal_box_rect = pygame.Rect(
            window_w - self.sidebar_width + self.horizontal_box_margin,  # Left margin
            self.horizontal_box_margin,  # Top margin
            self.sidebar_width - (2 * self.horizontal_box_margin),  # Width with left and right margins
            self.horizontal_box_height - self.horizontal_box_margin  # Height with top margin (bottom touches sidebar)
        )

        # Move history section properties (under the top box)
        self.move_history_height = 40  # Height for move history header
        self.move_history_y = self.horizontal_box_height + self.horizontal_box_margin  # Position below top box

        # Setup move history text
        self.move_history_font = pygame.font.Font(None, 28)
        self.move_history_text_color = (50, 50, 50)  # Dark gray text
        self.move_history_text = self.move_history_font.render("Move History:", True, self.move_history_text_color)

        # Create move history section rectangle
        self.move_history_rect = pygame.Rect(
            window_w - self.sidebar_width + self.horizontal_box_margin,  # Left margin
            self.move_history_y,  # Below the top box
            self.sidebar_width - (2 * self.horizontal_box_margin),  # Width with margins
            self.move_history_height
        )

        # Create bottom control box rectangle at the bottom of the sidebar with margins
        self.bottom_box_rect = pygame.Rect(
            window_w - self.sidebar_width + self.horizontal_box_margin,  # Left margin
            window_h - self.bottom_box_height,  # Position at bottom
            self.sidebar_width - (2 * self.horizontal_box_margin),  # Width with left and right margins
            self.bottom_box_height - self.horizontal_box_margin  # Height with bottom margin
        )

        # Undo section properties (above the bottom control box)
        self.undo_section_height = 60  # Height for undo section
        self.undo_section_y = window_h - self.bottom_box_height - self.undo_section_height - self.horizontal_box_margin

        # Create undo section rectangle
        self.undo_section_rect = pygame.Rect(
            window_w - self.sidebar_width + self.horizontal_box_margin,  # Left margin
            self.undo_section_y,  # Above the bottom box
            self.sidebar_width - (2 * self.horizontal_box_margin),  # Width with margins
            self.undo_section_height
        )

        # Load undo icon
        self.undo_icon_image = None
        self.undo_icon_scaled = None
        try:
            self.undo_icon_image = pygame.image.load("images/undo.png")
            # Scale to fit in circular button
            icon_size = 28  # Icon size for button
            self.undo_icon_scaled = pygame.transform.scale(self.undo_icon_image, (icon_size, icon_size))
        except (FileNotFoundError, pygame.error) as e:
            print(f"Warning: Could not load images/undo.png: {e}")

        # Setup undo text
        self.undo_font = pygame.font.Font(None, 28)
        self.undo_text_color = (50, 50, 50)  # Dark gray text
        self.undo_text = self.undo_font.render("Undo last Move", True, self.undo_text_color)

        # Setup undo button (circular button next to text)
        self.undo_button_size = 40  # Diameter of circular button
        self.undo_button_bg_color = (255, 255, 255)  # White background
        self.undo_button_hover_color = (230, 230, 230)  # Light gray on hover
        self.undo_button_hover = False

        # Position button to the right of the text
        text_width = self.undo_text.get_width()
        button_spacing = 15  # Space between text and button
        total_width = text_width + button_spacing + self.undo_button_size

        # Calculate button center position
        start_x = self.undo_section_rect.centerx - (total_width // 2)
        button_center_x = start_x + text_width + button_spacing + (self.undo_button_size // 2)
        button_center_y = self.undo_section_rect.centery

        self.undo_button_rect = pygame.Rect(
            button_center_x - self.undo_button_size // 2,
            button_center_y - self.undo_button_size // 2,
            self.undo_button_size,
            self.undo_button_size
        )

        # Setup control buttons
        self._setup_control_buttons()

    def _setup_turn_text(self) -> None:
        """Setup the turn indicator text."""
        # Font for turn text
        self.turn_font = pygame.font.Font(None, 36)
        self.turn_text_color = (50, 50, 50)  # Dark gray text

        # Pre-render both text options
        self.human_turn_text = self.turn_font.render("Your Turn", True, self.turn_text_color)
        self.computer_turn_text = self.turn_font.render("Computer Turn", True, self.turn_text_color)

    def _setup_score_displays(self) -> None:
        """Setup the score displays above and below the board.

        White is always displayed at the top, Black at the bottom.
        """
        # Font for score text
        self.score_font = pygame.font.Font(None, 28)
        self.score_text_color = (50, 50, 50)  # Dark gray text

        # Top = White, Bottom = Black (always)
        # White score label text (above board / top)
        self.white_score_label_text = self.score_font.render("White Score:", True, self.score_text_color)

        # Black score label text (below board / bottom)
        self.black_score_label_text = self.score_font.render("Black Score:", True, self.score_text_color)

        # Keep old names pointing to the new ones for compatibility
        self.opponent_score_label_text = self.white_score_label_text
        self.player_score_label_text = self.black_score_label_text

        # Circular button properties
        self.score_button_radius = 20  # Radius of circular button (40px diameter)
        self.score_button_bg_color = (255, 255, 255)  # White background
        self.score_button_border_color = (100, 100, 100)  # Gray border
        self.score_button_text_color = (50, 50, 50)  # Dark gray text

        # Position will be calculated dynamically in draw methods
        # based on the actual board hexagon edges


    # ------------------------------------------------------------------
    # Black / White display helpers (black = bottom, white = top, always)
    # ------------------------------------------------------------------

    @property
    def _black_score(self) -> int:
        """Score of the black player (points scored BY black, i.e. white marbles pushed off)."""
        if self.player_color == BLACK_COLOR:
            return self.player_score
        else:
            return self.opponent_score

    @property
    def _white_score(self) -> int:
        """Score of the white player (points scored BY white, i.e. black marbles pushed off)."""
        if self.player_color == WHITE_COLOR:
            return self.player_score
        else:
            return self.opponent_score

    @property
    def _black_move_time(self) -> float:
        """Current move timer value for the black player."""
        if self.player_color == BLACK_COLOR:
            return self.move_time_player
        else:
            return self.move_time_computer

    @property
    def _white_move_time(self) -> float:
        """Current move timer value for the white player."""
        if self.player_color == WHITE_COLOR:
            return self.move_time_player
        else:
            return self.move_time_computer

    @property
    def _black_moves_remaining(self) -> int:
        """Moves remaining for the black player."""
        if self.player_color == BLACK_COLOR:
            return self.player_moves_remaining
        else:
            return self.computer_moves_remaining

    @property
    def _white_moves_remaining(self) -> int:
        """Moves remaining for the white player."""
        if self.player_color == WHITE_COLOR:
            return self.player_moves_remaining
        else:
            return self.computer_moves_remaining

    # Row-start column numbers per row letter, matching the move_engine's
    # standard Abalone coordinate system.
    _ROW_START = {'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 1,
                  'F': 2, 'G': 3, 'H': 4, 'I': 5}
    _ROW_LEN = {'A': 5, 'B': 6, 'C': 7, 'D': 8, 'E': 9,
                'F': 8, 'G': 7, 'H': 6, 'I': 5}

    def _cell_to_notation(self, cell: tuple) -> str:
        """
        Convert (row, col) to standard Abalone cell notation.
        Display row 0 (top) = I, display row 8 (bottom) = A.
        Column numbers follow the standard Abalone scheme where each row's
        leftmost cell has a specific starting column number.

        Examples:
        - Row I (top, 5 cells): I5, I6, I7, I8, I9
        - Row E (middle, 9 cells): E1, E2, …, E9
        - Row A (bottom, 5 cells): A1, A2, A3, A4, A5

        Args:
            cell: Tuple (row, col) where row 0 is the top display row

        Returns:
            Cell notation string (e.g., 'I5', 'E1', 'A1')
        """
        row, col = cell
        if not (0 <= row <= 8):
            raise ValueError(f"Display row {row} out of range for cell {cell}")
        row_label = chr(ord('I') - row)
        if row_label not in self._ROW_START:
            raise ValueError(f"Invalid row label {row_label!r} for cell {cell}")
        col_number = self._ROW_START[row_label] + col
        return f"{row_label}{col_number}"

    @staticmethod
    def _notation_to_cell(notation: str) -> Optional[tuple[int, int]]:
        """
        Convert standard Abalone cell notation to (row, col) coordinates.
        Reverse operation of _cell_to_notation.

        Args:
            notation: Cell notation string (e.g., 'I5', 'E1', 'A1')

        Returns:
            Tuple (row, col) or None if notation is invalid
        """
        if len(notation) < 2:
            return None

        row_label = notation[0].upper()
        col_str = notation[1:]

        _ROW_START = {'A': 1, 'B': 1, 'C': 1, 'D': 1, 'E': 1,
                      'F': 2, 'G': 3, 'H': 4, 'I': 5}
        _ROW_LEN = {'A': 5, 'B': 6, 'C': 7, 'D': 8, 'E': 9,
                    'F': 8, 'G': 7, 'H': 6, 'I': 5}

        try:
            if row_label not in _ROW_START:
                return None

            row = ord('I') - ord(row_label)
            col_num = int(col_str)
            start = _ROW_START[row_label]
            length = _ROW_LEN[row_label]

            if not (start <= col_num < start + length):
                return None

            col = col_num - start
            return (row, col)
        except (ValueError, TypeError):
            return None

    # ------------------------------------------------------------------
    # Coordinate / state conversion helpers  (board_scene ↔ move_engine)
    # ------------------------------------------------------------------

    def _color_to_player(self, color: Tuple[int, int, int]) -> EnginePlayer:
        """Map a display colour tuple to engine player char ('b' / 'w')."""
        return 'b' if color == BLACK_COLOR else 'w'

    def _player_to_color(self, player: EnginePlayer) -> Tuple[int, int, int]:
        """Map engine player char to display colour tuple."""
        return BLACK_COLOR if player == 'b' else WHITE_COLOR

    def _board_to_engine_state(self) -> EngineBoard:
        """Convert self.marble_positions → move_engine Board (axial coords)."""
        engine_board: EngineBoard = {}
        for (row, col), color in self.marble_positions.items():
            try:
                notation = self._cell_to_notation((row, col))
                axial = notation_to_axial(notation)
            except (ValueError, KeyError):
                continue
            engine_board[axial] = self._color_to_player(color)
        return engine_board

    def _engine_board_to_positions(self, engine_board: EngineBoard) -> Dict[Tuple[int, int], Tuple[int, int, int]]:
        """Convert an engine Board → marble_positions dict."""
        positions: Dict[Tuple[int, int], Tuple[int, int, int]] = {}
        for axial, player in engine_board.items():
            try:
                notation = axial_to_notation(axial)
            except (ValueError, KeyError):
                continue
            cell = self._notation_to_cell(notation)
            if cell is not None:
                positions[cell] = self._player_to_color(player)
        return positions

    # ------------------------------------------------------------------
    # Legal-move cache
    # ------------------------------------------------------------------

    def _recompute_legal_moves(self) -> None:
        """Recompute and cache all legal moves for the current turn."""
        engine_board = self._board_to_engine_state()
        current_player = self._color_to_player(self.current_turn_color)
        self._legal_moves_cache = generate_moves(current_player, engine_board)

    # ------------------------------------------------------------------
    # AI turn helper
    # ------------------------------------------------------------------

    def _maybe_ai_move(self) -> None:
        """If it is the AI's turn, start a short "thinking" delay and then play.

        Called once per frame from the main ``run`` loop.  The AI computation
        runs in a background thread so that the game loop (timers, drawing)
        continues uninterrupted.

        Handles both Human vs AI (mode 0) and AI vs AI (mode 1).
        """
        if not self.game_started or self.game_paused or self.setup_mode:
            return
        if self.show_pause_modal or self.show_timeout_modal or self.show_win_modal or self.show_move_limit_modal:
            return

        # ── If a background AI thread has finished, apply its result ──
        if self._ai_thread is not None and self._ai_thread_done:
            result = self._ai_result
            self._ai_thread = None
            self._ai_result = None
            self._ai_thread_done = False
            self._ai_thinking = False

            if result is None:
                print("AI has no legal moves!")
                return

            move, new_board = result
            color_name = "Black" if self.current_turn_color == BLACK_COLOR else "White"
            print(f"AI ({color_name}) plays: {move.notation()}")
            self._apply_engine_move(move, new_board)
            return

        # ── If an AI thread is already running, just wait ──
        if self._ai_thread is not None:
            return

        # Determine which AI agent (if any) should act this turn
        active_agent: Optional[AIAgent] = None

        if self.game_mode == 0:
            # Human vs AI: AI acts only on non-human turns
            if self.ai_agent is None:
                return
            if self.current_turn_color == self.player_color:
                self._ai_thinking = False
                return
            active_agent = self.ai_agent

        elif self.game_mode == 1:
            # AI vs AI: pick the agent matching the current turn colour
            if self.current_turn_color == BLACK_COLOR:
                active_agent = self.ai_agent_black
            else:
                active_agent = self.ai_agent_white
            if active_agent is None:
                return
        else:
            # Human vs Human – no AI involvement
            return

        # Start the "thinking" timer on the first frame of the AI's turn
        if not self._ai_thinking:
            self._ai_thinking = True
            self._ai_think_start = pygame.time.get_ticks()
            return  # wait for the delay to elapse

        # Wait until the cosmetic delay has elapsed
        elapsed = pygame.time.get_ticks() - self._ai_think_start
        if elapsed < self._ai_think_delay:
            return

        # --- Launch AI computation in a background thread ---
        engine_board = self._board_to_engine_state()
        legal_moves = list(self._legal_moves_cache)  # snapshot for thread safety

        # Compute endgame context for the AI agent
        black_us, white_us = self._get_total_times_us()
        if self.current_turn_color == BLACK_COLOR:
            if self.player_color == BLACK_COLOR:
                ai_remaining = self.player_moves_remaining
                opp_remaining = self.computer_moves_remaining
            else:
                ai_remaining = self.computer_moves_remaining
                opp_remaining = self.player_moves_remaining
            ai_time_us = black_us
            opp_time_us = white_us
        else:
            if self.player_color == WHITE_COLOR:
                ai_remaining = self.player_moves_remaining
                opp_remaining = self.computer_moves_remaining
            else:
                ai_remaining = self.computer_moves_remaining
                opp_remaining = self.player_moves_remaining
            ai_time_us = white_us
            opp_time_us = black_us

        def _worker(agent: AIAgent, board: EngineBoard,
                    moves: List[Tuple[Move, EngineBoard]],
                    rem: int, opp_rem: int,
                    my_time: int, opp_time: int) -> None:
            self._ai_result = agent.select_move(
                board, moves,
                remaining_moves=rem,
                opp_remaining_moves=opp_rem,
                my_total_time_us=my_time,
                opp_total_time_us=opp_time,
            )
            self._ai_thread_done = True

        self._ai_thread_done = False
        self._ai_result = None
        self._ai_thread = threading.Thread(
            target=_worker,
            args=(active_agent, engine_board, legal_moves,
                  ai_remaining, opp_remaining, ai_time_us, opp_time_us),
            daemon=True,
        )
        self._ai_thread.start()

    # ------------------------------------------------------------------
    # Multi-marble selection helpers
    # ------------------------------------------------------------------

    def _cells_form_valid_group(self, cells: List[Tuple[int, int]]) -> bool:
        """Return True if *cells* (1–3) are collinear and contiguous on the hex grid."""
        if len(cells) <= 1:
            return True
        if len(cells) > 3:
            return False

        # Convert to notation then axial for direction checking
        axials = []
        for c in cells:
            try:
                axials.append(notation_to_axial(self._cell_to_notation(c)))
            except ValueError:
                return False

        # For 2 marbles, they must be adjacent along one of the 6 hex directions.
        dq = axials[1][0] - axials[0][0]
        dr = axials[1][1] - axials[0][1]
        if (dq, dr) not in DIRS.values() and (-dq, -dr) not in DIRS.values():
            return False

        if len(cells) == 3:
            # Third marble must continue the same direction from either end.
            dq2 = axials[2][0] - axials[1][0]
            dr2 = axials[2][1] - axials[1][1]
            if (dq2, dr2) != (dq, dr):
                # Try the other ordering: maybe axials[2] is before axials[0]
                dq3 = axials[0][0] - axials[2][0]
                dr3 = axials[0][1] - axials[2][1]
                if (dq3, dr3) != (dq, dr) and (-dq3, -dr3) != (dq, dr):
                    return False
        return True

    def _recompute_valid_destinations(self) -> None:
        """Filter legal-moves cache for the current selection and build dest map.

        For each legal move whose marble group matches self.selected_marbles,
        we determine a *clickable destination cell* and map it to the (Move, Board) pair.

        Destination cell logic:
        - For an inline move we show the cell just beyond the leading marble.
        - For a side-step move we show the new positions that are NOT in the group.
        """
        self._dest_to_move = {}
        if not self.selected_marbles:
            return

        # Build set of notations for current selection
        sel_notations: Set[str] = set()
        for c in self.selected_marbles:
            sel_notations.add(self._cell_to_notation(c))

        for move, new_board in self._legal_moves_cache:
            # Reconstruct the group of marbles involved in this move
            move_notations: Set[str] = set()

            if move.b is None:
                # Single marble inline
                move_notations.add(move.a)
            elif move.kind == 'i':
                # Inline group: trailing=a, leading=b, line direction=d
                a_ax = notation_to_axial(move.a)
                d = DIRS[move.d]
                # Walk from a toward d until we reach b
                for size in (2, 3):
                    grp = group_cells(a_ax, d, size)
                    if any(g not in ENGINE_CELLS for g in grp):
                        continue
                    if axial_to_notation(grp[-1]) == move.b:
                        for g in grp:
                            move_notations.add(axial_to_notation(g))
                        break
            else:
                # Side-step: a and b are extremities in sorted order
                # Line direction is one of CANONICAL_DIRS or its opposite
                a_ax = notation_to_axial(move.a)
                b_ax = notation_to_axial(move.b)
                found = False
                for ld_num in list(CANONICAL_DIRS) + [OPPOSITE[cd] for cd in CANONICAL_DIRS]:
                    ld = DIRS[ld_num]
                    for size in (2, 3):
                        grp = group_cells(a_ax, ld, size)
                        if any(g not in ENGINE_CELLS for g in grp):
                            continue
                        if axial_to_notation(grp[-1]) == move.b:
                            for g in grp:
                                move_notations.add(axial_to_notation(g))
                            found = True
                            break
                    if found:
                        break

            if move_notations != sel_notations:
                continue

            # This move matches our selection — compute destination cell(s)
            if move.kind == 'i':
                # Inline: destination is one cell beyond the leading marble
                d = DIRS[move.d]
                leading_ax = notation_to_axial(move.b if move.b else move.a)
                dest_ax = cell_add(leading_ax, d)
                if dest_ax in ENGINE_CELLS:
                    dest_cell = self._notation_to_cell(axial_to_notation(dest_ax))
                    if dest_cell is not None:
                        self._dest_to_move[dest_cell] = (move, new_board)
            else:
                # Side-step: show new positions that are NOT part of the group
                d = DIRS[move.d]
                for sel_cell in self.selected_marbles:
                    sel_ax = notation_to_axial(self._cell_to_notation(sel_cell))
                    dest_ax = cell_add(sel_ax, d)
                    if dest_ax in ENGINE_CELLS:
                        dest_cell = self._notation_to_cell(axial_to_notation(dest_ax))
                        if dest_cell is not None and dest_cell not in self.selected_marbles:
                            if dest_cell not in self._dest_to_move:
                                self._dest_to_move[dest_cell] = (move, new_board)

    def _apply_engine_move(self, move: Move, new_engine_board: EngineBoard) -> None:
        """Apply a validated engine move: update positions, scores, history, turn."""
        # Measure elapsed time for this move in microseconds
        move_end_us = time.perf_counter_ns() // 1000
        elapsed_us = move_end_us - self._move_turn_start_us
        self._last_move_time_us = elapsed_us

        old_positions = self.marble_positions.copy()
        new_positions = self._engine_board_to_positions(new_engine_board)

        # Count marbles before and after to detect push-offs
        def _count(positions, color):
            return sum(1 for c in positions.values() if c == color)

        opp_color = WHITE_COLOR if self.current_turn_color == BLACK_COLOR else BLACK_COLOR
        old_opp = _count(old_positions, opp_color)
        new_opp = _count(new_positions, opp_color)
        pushed_off = old_opp - new_opp  # number of opponent marbles pushed off

        # Update scores
        if self.current_turn_color == self.player_color:
            self.player_score += pushed_off
        else:
            self.opponent_score += pushed_off

        # Check win condition (first to 6 points wins)
        if self.player_score >= 6:
            self._trigger_win(self.player_color)
        elif self.opponent_score >= 6:
            opp = WHITE_COLOR if self.player_color == BLACK_COLOR else BLACK_COLOR
            self._trigger_win(opp)

        # Record move in history — store board snapshot for undo
        marble_color = self.current_turn_color
        self.move_history.append((move.notation(), marble_color, old_positions, elapsed_us))

        # ── Record last-moved marbles & direction for arrow overlay ──
        # Determine which display cells were part of this move's group
        moved_cells: List[Tuple[int, int]] = []
        if move.b is None:
            # Single marble inline
            cell = self._notation_to_cell(move.a)
            if cell is not None:
                moved_cells.append(cell)
        elif move.kind == 'i':
            # Inline group: trailing=a, leading=b
            a_ax = notation_to_axial(move.a)
            d = DIRS[move.d]
            for size in (2, 3):
                grp = group_cells(a_ax, d, size)
                if any(g not in ENGINE_CELLS for g in grp):
                    continue
                if axial_to_notation(grp[-1]) == move.b:
                    for g in grp:
                        c = self._notation_to_cell(axial_to_notation(g))
                        if c is not None:
                            moved_cells.append(c)
                    break
        else:
            # Side-step
            a_ax = notation_to_axial(move.a)
            b_ax = notation_to_axial(move.b)
            found = False
            for ld_num in list(CANONICAL_DIRS) + [OPPOSITE[cd] for cd in CANONICAL_DIRS]:
                ld = DIRS[ld_num]
                for size in (2, 3):
                    grp = group_cells(a_ax, ld, size)
                    if any(g not in ENGINE_CELLS for g in grp):
                        continue
                    if axial_to_notation(grp[-1]) == move.b:
                        for g in grp:
                            c = self._notation_to_cell(axial_to_notation(g))
                            if c is not None:
                                moved_cells.append(c)
                        found = True
                        break
                if found:
                    break

        # The arrows should appear on the NEW positions of the moved marbles
        # (i.e. after the move). Shift each cell by the move direction.
        dest_cells: List[Tuple[int, int]] = []
        d_vec = DIRS[move.d]
        for mc in moved_cells:
            try:
                ax = notation_to_axial(self._cell_to_notation(mc))
                dest_ax = cell_add(ax, d_vec)
                if dest_ax in ENGINE_CELLS:
                    dc = self._notation_to_cell(axial_to_notation(dest_ax))
                    if dc is not None:
                        dest_cells.append(dc)
            except (ValueError, KeyError):
                pass

        self._last_moved_cells = dest_cells if dest_cells else moved_cells
        self._last_move_direction = move.d
        self._last_move_color = marble_color

        # Apply new board
        self.marble_positions = new_positions

        # Decrement move counts (never go below 0)
        if marble_color == self.player_color:
            self.player_moves_remaining = max(0, self.player_moves_remaining - 1)
        else:
            self.computer_moves_remaining = max(0, self.computer_moves_remaining - 1)

        # Switch turn
        self.current_turn_color = WHITE_COLOR if self.current_turn_color == BLACK_COLOR else BLACK_COLOR

        # Reset timer for next turn
        self._reset_timer_for_next_turn()

        # Clear selection and recompute legal moves for next player
        self.selected_marbles = []
        self._dest_to_move = {}
        self._recompute_legal_moves()

        # Check if the player whose turn it now is has exhausted their moves
        if self.current_turn_color == self.player_color:
            if self.player_moves_remaining <= 0:
                self._trigger_move_limit_loss(self.current_turn_color)
        else:
            if self.computer_moves_remaining <= 0:
                self._trigger_move_limit_loss(self.current_turn_color)

    def _setup_control_buttons(self) -> None:
        """Setup the control buttons (start, pause, stop, reset) in the bottom box."""
        # Button dimensions - made smaller to fit better
        button_size = 40  # Circular buttons (reduced from 50)
        button_spacing = 8  # Space between buttons (reduced from 10)

        # Calculate positions for 4 buttons in a row
        total_width = (button_size * 4) + (button_spacing * 3)
        start_x = self.bottom_box_rect.centerx - (total_width // 2)
        button_y = self.bottom_box_rect.centery

        # Button colors - white circles with black icons
        self.button_bg_color = (255, 255, 255)  # White for button background
        self.button_hover_color = (230, 230, 230)  # Light gray on hover
        self.button_icon_color = (0, 0, 0)  # Black icons

        # Load reset icon image
        self.reset_icon_image = None
        self.reset_icon_scaled = None
        try:
            self.reset_icon_image = pygame.image.load("images/reset_icon.png")
            # Scale to fit within button (slightly smaller than button size for padding)
            icon_size = int(button_size * 0.7)
            self.reset_icon_scaled = pygame.transform.scale(self.reset_icon_image, (icon_size, icon_size))
        except (FileNotFoundError, pygame.error) as e:
            print(f"Warning: Could not load images/reset_icon.png: {e}")
            # Will fall back to drawing the icon programmatically

        # Create button rectangles (circular)
        self.start_button = pygame.Rect(start_x, button_y - button_size // 2, button_size, button_size)
        self.pause_button = pygame.Rect(start_x + button_size + button_spacing, button_y - button_size // 2, button_size, button_size)
        self.stop_button = pygame.Rect(start_x + (button_size + button_spacing) * 2, button_y - button_size // 2, button_size, button_size)
        self.reset_button = pygame.Rect(start_x + (button_size + button_spacing) * 3, button_y - button_size // 2, button_size, button_size)

        # Store all buttons for easy iteration
        self.control_buttons = [
            {'rect': self.start_button, 'type': 'start', 'hover': False},
            {'rect': self.pause_button, 'type': 'pause', 'hover': False},
            {'rect': self.stop_button, 'type': 'stop', 'hover': False},
            {'rect': self.reset_button, 'type': 'reset', 'hover': False}
        ]

    def _update_positions(self) -> None:
        """Update positions based on current window size."""
        # Get current window dimensions
        window_w, window_h = self.screen.get_size()

        # Calculate board center in the middle of free space (left edge to sidebar)
        available_width = window_w - self.sidebar_width
        new_board_center = (available_width // 2, window_h // 2)

        # Update board renderer but keep marble positions
        old_positions = self.marble_positions.copy()
        self.board_renderer = BoardRenderer(new_board_center, invert_colors=self.invert_colors, board_layout=self.board_layout)
        self.marble_positions = old_positions

        # Back button stays in top-left corner, no need to update

        # Update sidebar position and size
        self.sidebar_rect = pygame.Rect(window_w - self.sidebar_width, 0, self.sidebar_width, window_h)

        # Update horizontal box position and size with margins
        self.horizontal_box_rect = pygame.Rect(
            window_w - self.sidebar_width + self.horizontal_box_margin,  # Left margin
            self.horizontal_box_margin,  # Top margin
            self.sidebar_width - (2 * self.horizontal_box_margin),  # Width with left and right margins
            self.horizontal_box_height - self.horizontal_box_margin  # Height with top margin (bottom touches sidebar)
        )

        # Update move history section position
        self.move_history_y = self.horizontal_box_height + self.horizontal_box_margin
        self.move_history_rect = pygame.Rect(
            window_w - self.sidebar_width + self.horizontal_box_margin,  # Left margin
            self.move_history_y,  # Below the top box
            self.sidebar_width - (2 * self.horizontal_box_margin),  # Width with margins
            self.move_history_height
        )

        # Update bottom control box position and size with margins
        self.bottom_box_rect = pygame.Rect(
            window_w - self.sidebar_width + self.horizontal_box_margin,  # Left margin
            window_h - self.bottom_box_height,  # Position at bottom
            self.sidebar_width - (2 * self.horizontal_box_margin),  # Width with left and right margins
            self.bottom_box_height - self.horizontal_box_margin  # Height with bottom margin
        )

        # Update undo section position (above the bottom control box)
        self.undo_section_y = window_h - self.bottom_box_height - self.undo_section_height - self.horizontal_box_margin
        self.undo_section_rect = pygame.Rect(
            window_w - self.sidebar_width + self.horizontal_box_margin,  # Left margin
            self.undo_section_y,  # Above the bottom box
            self.sidebar_width - (2 * self.horizontal_box_margin),  # Width with margins
            self.undo_section_height
        )

        # Rescale undo icon if it exists
        if self.undo_icon_image:
            icon_size = 28
            self.undo_icon_scaled = pygame.transform.scale(self.undo_icon_image, (icon_size, icon_size))

        # Update undo button position
        text_width = self.undo_text.get_width()
        button_spacing = 15
        total_width = text_width + button_spacing + self.undo_button_size

        start_x = self.undo_section_rect.centerx - (total_width // 2)
        button_center_x = start_x + text_width + button_spacing + (self.undo_button_size // 2)
        button_center_y = self.undo_section_rect.centery

        self.undo_button_rect = pygame.Rect(
            button_center_x - self.undo_button_size // 2,
            button_center_y - self.undo_button_size // 2,
            self.undo_button_size,
            self.undo_button_size
        )


        # Update control button positions - using smaller size to fit better
        button_size = 40  # Reduced from 50
        button_spacing = 8  # Reduced from 10
        total_width = (button_size * 4) + (button_spacing * 3)
        start_x = self.bottom_box_rect.centerx - (total_width // 2)
        button_y = self.bottom_box_rect.centery

        # Rescale reset icon for new button size
        if self.reset_icon_image:
            icon_size = int(button_size * 0.7)
            self.reset_icon_scaled = pygame.transform.scale(self.reset_icon_image, (icon_size, icon_size))

        self.start_button = pygame.Rect(start_x, button_y - button_size // 2, button_size, button_size)
        self.pause_button = pygame.Rect(start_x + button_size + button_spacing, button_y - button_size // 2, button_size, button_size)
        self.stop_button = pygame.Rect(start_x + (button_size + button_spacing) * 2, button_y - button_size // 2, button_size, button_size)
        self.reset_button = pygame.Rect(start_x + (button_size + button_spacing) * 3, button_y - button_size // 2, button_size, button_size)

        # Update control_buttons list
        self.control_buttons = [
            {'rect': self.start_button, 'type': 'start', 'hover': False},
            {'rect': self.pause_button, 'type': 'pause', 'hover': False},
            {'rect': self.stop_button, 'type': 'stop', 'hover': False},
            {'rect': self.reset_button, 'type': 'reset', 'hover': False}
        ]

    def _handle_events(self) -> bool:
        """
        Handle user input events.

        Returns:
            True to continue running, False to quit
        """
        mouse_pos = pygame.mouse.get_pos()

        # Reset tooltip
        self.tooltip_text = None
        self.tooltip_position = mouse_pos

        # Update back button hover state and tooltip
        if self.back_button_rect.collidepoint(mouse_pos):
            self.current_back_button_color = self.back_button_hover_color
            self.tooltip_text = "Back"
        else:
            self.current_back_button_color = self.back_button_color

        # Update control buttons hover state and tooltips
        for button in self.control_buttons:
            if button['rect'].collidepoint(mouse_pos):
                button['hover'] = True
                # Set tooltip based on button type
                if button['type'] == 'start':
                    if not self.total_time_input_confirmed and not self.game_started:
                        self.tooltip_text = "Enter total time first"
                    else:
                        self.tooltip_text = "Start"
                elif button['type'] == 'pause':
                    self.tooltip_text = "Pause"
                elif button['type'] == 'stop':
                    if self.game_mode != 0:
                        self.tooltip_text = "Setup (Human vs AI only)"
                    elif self.setup_mode:
                        self.tooltip_text = "In Setup Mode"
                    else:
                        self.tooltip_text = "Setup Mode"
                elif button['type'] == 'reset':
                    self.tooltip_text = "Reset"
            else:
                button['hover'] = False

        # Update undo button hover state and tooltip
        if self.undo_button_rect.collidepoint(mouse_pos):
            self.undo_button_hover = True
            if not self.tooltip_text:  # Only set if not already set by control button
                self.tooltip_text = "Undo"
        else:
            self.undo_button_hover = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.VIDEORESIZE:
                # Window was resized, update positions
                self._update_positions()

            # Handle keyboard events for total time input field
            if event.type == pygame.KEYDOWN and self.total_time_input_active:
                if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                    # Confirm the entered value
                    self._confirm_total_time_input()
                elif event.key == pygame.K_BACKSPACE:
                    self.total_time_input_text = self.total_time_input_text[:-1]
                elif event.key == pygame.K_ESCAPE:
                    self.total_time_input_active = False
                else:
                    # Only allow digits
                    if event.unicode.isdigit() and len(self.total_time_input_text) < 4:
                        self.total_time_input_text += event.unicode

            if event.type == pygame.MOUSEBUTTONDOWN:
                # If timeout modal is showing, handle modal button clicks and block everything else
                if self.show_timeout_modal:
                    self._handle_timeout_modal_click(event.pos)
                    if not self.running:
                        return False
                    continue

                # If move-limit modal is showing, handle modal button clicks and block everything else
                if self.show_move_limit_modal:
                    self._handle_move_limit_modal_click(event.pos)
                    if not self.running:
                        return False
                    continue

                # If win modal is showing, handle modal button clicks and block everything else
                if self.show_win_modal:
                    self._handle_win_modal_click(event.pos)
                    if not self.running:
                        return False
                    continue

                # If pause modal is showing, handle modal button clicks
                if self.show_pause_modal:
                    self._handle_pause_modal_click(event.pos)
                    # If quit was clicked in modal, running will be False
                    if not self.running:
                        return False
                    continue


                # Check if back button was clicked
                if self.back_button_rect.collidepoint(event.pos):
                    self.go_back = True
                    return False

                # Check if total time input field was clicked (only when not yet confirmed)
                if not self.total_time_input_confirmed and self.total_time_input_rect.collidepoint(event.pos):
                    self.total_time_input_active = True
                    continue
                else:
                    # Clicked outside the input field – deactivate it
                    if self.total_time_input_active:
                        self.total_time_input_active = False
                        # Auto-confirm if there is valid text
                        if self.total_time_input_text.strip():
                            self._confirm_total_time_input()

                # Check if control buttons were clicked
                for button in self.control_buttons:
                    if button['rect'].collidepoint(event.pos):
                        self._handle_control_button_click(button['type'])
                        # If stop was clicked, running will be False, so return False
                        if not self.running:
                            return False
                        continue

                # Check if undo button was clicked
                if self.undo_button_rect.collidepoint(event.pos):
                    self._handle_undo_button_click()
                    continue

                # ── Setup mode: free marble placement (any marble, any empty cell) ──
                if self.setup_mode:
                    marble_at_pos = self._get_marble_at_position(event.pos)
                    if marble_at_pos is not None:
                        # Start dragging this marble (any colour)
                        self._setup_dragging = True
                        self._setup_dragged_marble = marble_at_pos
                        marble_center = self._get_marble_screen_position(marble_at_pos)
                        self._setup_drag_offset = (
                            event.pos[0] - marble_center[0],
                            event.pos[1] - marble_center[1],
                        )
                    continue  # block normal game interaction while in setup mode

                # Determine whether the human player is allowed to interact
                # In Human vs AI (mode 0) or AI vs AI (mode 1), only allow
                # interaction when it is the human player's turn.
                # In Human vs Human (mode 2), both turns allow interaction.
                _human_can_interact = (
                    self.game_mode == 2
                    or (self.game_mode == 0 and self.current_turn_color == self.player_color)
                )

                # Check if a destination dot was clicked to execute the move
                if self.game_started and not self.game_paused and _human_can_interact and self.selected_marbles:
                    clicked_cell = self._get_cell_at_position(event.pos)
                    if clicked_cell and clicked_cell in self._dest_to_move:
                        move, new_board = self._dest_to_move[clicked_cell]
                        self._apply_engine_move(move, new_board)
                        continue

                # Marble click handling: multi-select up to 3 same-color marbles
                if self.game_started and not self.game_paused and _human_can_interact:
                    marble_at_pos = self._get_marble_at_position(event.pos)
                    if marble_at_pos and self.marble_positions.get(marble_at_pos) == self.current_turn_color:
                        # Clear last-move arrows when the opponent starts selecting
                        if self._last_move_color is not None and self._last_move_color != self.current_turn_color:
                            self._last_moved_cells = []
                            self._last_move_direction = None
                            self._last_move_color = None
                        if marble_at_pos in self.selected_marbles:
                            # Toggle off: deselect this marble
                            self.selected_marbles.remove(marble_at_pos)
                            # After removing, remaining marbles must still form a valid group
                            if not self._cells_form_valid_group(self.selected_marbles):
                                self.selected_marbles = []
                            self._recompute_valid_destinations()
                        else:
                            # Try adding to the current selection
                            candidate = self.selected_marbles + [marble_at_pos]
                            if len(candidate) <= 3 and self._cells_form_valid_group(candidate):
                                self.selected_marbles = candidate
                                self._recompute_valid_destinations()
                            else:
                                # Start a new selection with just this marble
                                self.selected_marbles = [marble_at_pos]
                                self._recompute_valid_destinations()

                        # Also start drag for single marble
                        if len(self.selected_marbles) == 1 and marble_at_pos in self.selected_marbles:
                            self.mouse_down_pos = event.pos
                            self._marble_before_drag = list(self.selected_marbles)
                            self.dragging = True
                            self.dragged_marble = marble_at_pos
                            marble_center = self._get_marble_screen_position(marble_at_pos)
                            self.drag_offset = (event.pos[0] - marble_center[0], event.pos[1] - marble_center[1])
                    elif marble_at_pos is None:
                        # Clicked empty space / non-current-turn marble → deselect
                        clicked_cell = self._get_cell_at_position(event.pos)
                        if clicked_cell is None or clicked_cell not in self._dest_to_move:
                            self.selected_marbles = []
                            self._dest_to_move = {}

            if event.type == pygame.MOUSEBUTTONUP:
                # ── Setup mode drop ──
                if self.setup_mode and getattr(self, '_setup_dragging', False) and self._setup_dragged_marble is not None:
                    drop_cell = self._get_cell_at_position(event.pos)
                    if drop_cell is not None and drop_cell not in self.marble_positions:
                        # Move marble to the new empty cell
                        color = self.marble_positions.pop(self._setup_dragged_marble)
                        self.marble_positions[drop_cell] = color
                    # Reset setup drag state
                    self._setup_dragging = False
                    self._setup_dragged_marble = None
                    self._setup_drag_offset = (0, 0)
                    continue

                if self.dragging and self.dragged_marble:
                    # Determine if the mouse moved enough to count as a drag
                    drag_threshold = 5  # pixels
                    if self.mouse_down_pos:
                        dx = event.pos[0] - self.mouse_down_pos[0]
                        dy = event.pos[1] - self.mouse_down_pos[1]
                        was_drag = (dx * dx + dy * dy) > drag_threshold * drag_threshold
                    else:
                        was_drag = True

                    if not was_drag:
                        # Plain click — selection was already handled on MOUSEBUTTONDOWN
                        self.dragging = False
                        self.dragged_marble = None
                        self.drag_offset = (0, 0)
                        self.mouse_down_pos = None
                        self._marble_before_drag = None
                        continue

                    # Try to drop the marble onto a valid destination
                    drop_cell = self._get_cell_at_position(event.pos)
                    if drop_cell and drop_cell in self._dest_to_move:
                        move, new_board = self._dest_to_move[drop_cell]
                        self._apply_engine_move(move, new_board)

                    # Reset dragging state (selection persists if move wasn't made)
                    self.dragging = False
                    self.dragged_marble = None
                    self.drag_offset = (0, 0)
                    self.mouse_down_pos = None
                    self._marble_before_drag = None

        return True

    def _handle_control_button_click(self, button_type: str) -> None:
        """
        Handle control button clicks.

        Args:
            button_type: Type of button clicked ('start', 'pause', 'stop', 'reset')
        """
        if button_type == 'start':
            self._start_game()
        elif button_type == 'pause':
            self._pause_game()
        elif button_type == 'stop':
            self._stop_game()
        elif button_type == 'reset':
            self._reset_game()

    def _confirm_total_time_input(self) -> None:
        """Validate and confirm the total game time entered by the user."""
        text = self.total_time_input_text.strip()
        if not text:
            return
        try:
            minutes = int(text)
            if minutes <= 0:
                print("Total game time must be a positive number!")
                return
            self.total_time_limit = minutes * 60  # Convert minutes to seconds
            self.total_time = self.total_time_limit
            self.total_time_input_confirmed = True
            self.total_time_input_active = False
            print(f"Total game time set to {minutes} minutes ({self.total_time_limit} seconds)")
        except ValueError:
            print("Invalid input for total game time!")

    def _start_game(self) -> None:
        """Start or resume the game."""
        if not self.game_started:
            # Cannot start unless the user has entered a valid total game time
            if not self.total_time_input_confirmed:
                print("Cannot start: Please enter a total game time first!")
                return
            # Start the game
            self.game_started = True
            self.game_paused = False
            self.is_game_timer_running = True
            self.start_ticks = pygame.time.get_ticks()  # Total game time starts here (never resets)
            self.move_start_ticks = pygame.time.get_ticks()  # Per-move timer starts here (will reset per turn)
            self._move_turn_start_us = time.perf_counter_ns() // 1000  # µs timer for move duration
            self._recompute_legal_moves()
            print("Game started!")
        elif self.setup_mode:
            # Resuming from setup mode – AI plays next
            self.setup_mode = False
            self.game_paused = False
            self.is_game_timer_running = True

            # Discard any in-flight AI computation from before setup mode
            self._ai_thread = None
            self._ai_result = None
            self._ai_thread_done = False
            self._ai_thinking = False

            # Set the turn to the AI's colour so the agent moves next
            ai_color = WHITE_COLOR if self.player_color == BLACK_COLOR else BLACK_COLOR
            self.current_turn_color = ai_color

            # Restore timers so they continue from where they were paused
            now = pygame.time.get_ticks()
            paused_move_elapsed = getattr(self, '_paused_move_elapsed_ms', 0)
            paused_total_elapsed = getattr(self, '_paused_total_elapsed_ms', 0)
            self.move_start_ticks = now - paused_move_elapsed
            self.start_ticks = now - paused_total_elapsed
            self._move_turn_start_us = time.perf_counter_ns() // 1000 - paused_move_elapsed * 1000

            # Reset the per-move timer for the AI's turn
            self._reset_timer_for_next_turn()

            # Recompute legal moves for the AI
            self._recompute_legal_moves()

            # Clear selection state
            self.selected_marbles = []
            self._dest_to_move = {}

            print("Setup mode ended – AI's turn to move.")
        elif self.game_paused:
            # Resume if paused
            self.game_paused = False
            self.show_pause_modal = False
            self.is_game_timer_running = True
            # Restore timers so they continue from where they were paused
            now = pygame.time.get_ticks()
            paused_move_elapsed = getattr(self, '_paused_move_elapsed_ms', 0)
            paused_total_elapsed = getattr(self, '_paused_total_elapsed_ms', 0)
            self.move_start_ticks = now - paused_move_elapsed  # Continue per-move timer
            self.start_ticks = now - paused_total_elapsed       # Continue total game timer
            # Also restore the µs-precision move timer
            self._move_turn_start_us = time.perf_counter_ns() // 1000 - paused_move_elapsed * 1000
            print("Game resumed!")
        else:
            print("Game is already running!")

    def _pause_game(self) -> None:
        """Pause the game (resume is handled by the play/start button)."""
        if not self.game_paused:
            # Save how much of the per-move time has already elapsed (in ms)
            self._paused_move_elapsed_ms = pygame.time.get_ticks() - self.move_start_ticks
            # Save how much total-game time has already elapsed (in ms)
            self._paused_total_elapsed_ms = pygame.time.get_ticks() - self.start_ticks
            # Pausing the game — no modal, just pause
            self.game_paused = True
            self.is_game_timer_running = False
            print("Game paused!")

    def _stop_game(self) -> None:
        """Enter setup mode (only in Human vs AI mode).

        Pauses timers and allows the user to freely rearrange all marbles
        (both black and white). Pressing Start again will resume the game
        with the AI making the next move.
        """
        if self.game_mode != 0:
            print("Setup mode is only available in Human vs AI mode.")
            return
        if not self.game_started:
            print("Cannot enter setup mode: game has not started.")
            return
        if self.setup_mode:
            print("Already in setup mode.")
            return

        # Pause timers (same as pause)
        self._paused_move_elapsed_ms = pygame.time.get_ticks() - self.move_start_ticks
        self._paused_total_elapsed_ms = pygame.time.get_ticks() - self.start_ticks
        self.game_paused = True
        self.is_game_timer_running = False
        self.setup_mode = True

        # Clear any current selection
        self.selected_marbles = []
        self._dest_to_move = {}

        # If the AI thread is running, we still flag setup mode;
        # _maybe_ai_move will not apply results while setup_mode is True.
        self._setup_dragging = False
        self._setup_dragged_marble = None
        self._setup_drag_offset = (0, 0)

        print("Setup mode activated – rearrange marbles freely, then press Start.")

    def _confirm_stop_game(self) -> None:
        """Actually stop the game and go back to menu."""
        print("Game stopped. Going back to menu...")
        self.game_started = False
        self.game_paused = False
        self.show_stop_modal = False
        self.is_game_timer_running = False
        self.go_back = True
        self.running = False

    def _handle_stop_modal_click(self, pos: tuple) -> None:
        """Handle clicks on stop modal buttons."""
        geom = self._get_stop_modal_geometry()

        # Check clicks
        if geom['yes_button'].collidepoint(pos):
            # User confirmed - stop the game
            self._confirm_stop_game()
        elif geom['no_button'].collidepoint(pos):
            # User cancelled - just close the modal
            self.show_stop_modal = False
            print("Stop cancelled")

    def _get_total_times_us(self) -> Tuple[int, int]:
        """Return raw total µs spent by (black, white) from move history."""
        black_us = sum(entry[3] for entry in self.move_history if entry[1] == BLACK_COLOR and len(entry) >= 4)
        white_us = sum(entry[3] for entry in self.move_history if entry[1] == WHITE_COLOR and len(entry) >= 4)
        return black_us, white_us

    def _get_scores_by_color(self) -> Tuple[int, int]:
        """Return (black_score, white_score) regardless of which side is 'player'."""
        if self.player_color == BLACK_COLOR:
            return self.player_score, self.opponent_score
        else:
            return self.opponent_score, self.player_score

    def _determine_winner_by_score(self) -> Tuple[Optional[Tuple[int, int, int]], str]:
        """Determine who wins when the game ends by limit / timeout.

        Returns
        -------
        (winner_color_or_None, reason_string)
            winner_color is BLACK_COLOR / WHITE_COLOR, or *None* for a draw.
            reason_string is a human-readable explanation.
        """
        black_score, white_score = self._get_scores_by_color()

        if black_score > white_score:
            return BLACK_COLOR, f"Black wins with {black_score} vs {white_score} points!"
        elif white_score > black_score:
            return WHITE_COLOR, f"White wins with {white_score} vs {black_score} points!"

        # Scores are equal — tiebreaker: less total time wins
        black_us, white_us = self._get_total_times_us()
        if black_us < white_us:
            return BLACK_COLOR, f"Scores tied {black_score}-{white_score}. Black wins by less time used!"
        elif white_us < black_us:
            return WHITE_COLOR, f"Scores tied {black_score}-{white_score}. White wins by less time used!"

        # Absolute tie (same score AND same time) — declare a draw
        return None, f"It's a draw! Scores {black_score}-{white_score}, equal time used."

    def _get_timeout_modal_geometry(self) -> dict:
        """Get timeout game-over modal dimensions and button position."""
        window_w, window_h = self.screen.get_size()

        modal_width = 560
        modal_height = 320
        modal_x = (window_w - modal_width) // 2
        modal_y = (window_h - modal_height) // 2

        button_width = 160
        button_height = 50
        button_x = modal_x + (modal_width - button_width) // 2
        button_y = modal_y + modal_height - 75

        return {
            'modal_x': modal_x,
            'modal_y': modal_y,
            'modal_width': modal_width,
            'modal_height': modal_height,
            'ok_button': pygame.Rect(button_x, button_y, button_width, button_height),
        }

    def _handle_timeout_modal_click(self, pos: tuple) -> None:
        """Handle clicks on the timeout game-over modal."""
        geom = self._get_timeout_modal_geometry()
        if geom['ok_button'].collidepoint(pos):
            # Go back to menu
            self.show_timeout_modal = False
            self.go_back = True
            self.running = False

    def _get_total_times(self) -> Tuple[str, str]:
        """Compute total time spent by each player from move history.

        Returns:
            (black_time_str, white_time_str) formatted in microseconds.
        """
        black_us, white_us = self._get_total_times_us()
        return f"{black_us:,} µs", f"{white_us:,} µs"

    def _draw_timeout_modal(self) -> None:
        """Draw the move-timeout game-over modal."""
        window_w, window_h = self.screen.get_size()
        geom = self._get_timeout_modal_geometry()

        # Semi-transparent overlay
        overlay = pygame.Surface((window_w, window_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # Modal background
        modal_rect = pygame.Rect(geom['modal_x'], geom['modal_y'], geom['modal_width'], geom['modal_height'])
        pygame.draw.rect(self.screen, (240, 240, 240), modal_rect, border_radius=15)
        pygame.draw.rect(self.screen, (180, 60, 60), modal_rect, width=4, border_radius=15)

        # Title: "Game Over"
        title_font = pygame.font.Font(None, 60)
        title_text = title_font.render("Game Over!", True, (180, 60, 60))
        title_rect = title_text.get_rect(center=(geom['modal_x'] + geom['modal_width'] // 2,
                                                  geom['modal_y'] + 60))
        self.screen.blit(title_text, title_rect)

        # Determine loser name (who timed out)
        loser_name = "Black" if self.timeout_loser_color == BLACK_COLOR else "White"

        # Message: who timed out
        msg_font = pygame.font.Font(None, 34)
        line1 = msg_font.render(f"Time's up! {loser_name} ran out of time.", True, (50, 50, 50))
        line1_rect = line1.get_rect(center=(geom['modal_x'] + geom['modal_width'] // 2,
                                             geom['modal_y'] + 120))
        self.screen.blit(line1, line1_rect)

        # Winner determined by score (with time tiebreaker)
        winner_color = getattr(self, 'timeout_winner_color', None)
        reason = getattr(self, 'timeout_reason', '')
        result_font = pygame.font.Font(None, 32)
        if winner_color is not None:
            winner_name = "Black" if winner_color == BLACK_COLOR else "White"
            line2 = result_font.render(reason, True, (50, 50, 50))
        else:
            line2 = result_font.render(reason, True, (50, 50, 50))
        line2_rect = line2.get_rect(center=(geom['modal_x'] + geom['modal_width'] // 2,
                                             geom['modal_y'] + 155))
        self.screen.blit(line2, line2_rect)

        # Score line
        black_score, white_score = self._get_scores_by_color()
        score_font = pygame.font.Font(None, 28)
        score_line = score_font.render(f"Score — Black: {black_score}  |  White: {white_score}", True, (80, 80, 80))
        score_rect = score_line.get_rect(center=(geom['modal_x'] + geom['modal_width'] // 2,
                                                  geom['modal_y'] + 190))
        self.screen.blit(score_line, score_rect)

        # Total time per player
        black_time, white_time = self._get_total_times()
        time_font = pygame.font.Font(None, 28)
        time_line = time_font.render(f"Time — Black: {black_time}  |  White: {white_time}", True, (80, 80, 80))
        time_rect = time_line.get_rect(center=(geom['modal_x'] + geom['modal_width'] // 2,
                                                geom['modal_y'] + 220))
        self.screen.blit(time_line, time_rect)

        # OK button
        mouse_pos = pygame.mouse.get_pos()
        ok_color = (184, 202, 176) if geom['ok_button'].collidepoint(mouse_pos) else (164, 182, 156)
        pygame.draw.rect(self.screen, ok_color, geom['ok_button'], border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), geom['ok_button'], width=2, border_radius=10)

        ok_font = pygame.font.Font(None, 38)
        ok_text = ok_font.render("OK", True, (255, 255, 255))
        ok_text_rect = ok_text.get_rect(center=geom['ok_button'].center)
        self.screen.blit(ok_text, ok_text_rect)

    # ------------------------------------------------------------------
    # Move-limit exhausted (player ran out of moves)
    # ------------------------------------------------------------------

    def _trigger_move_limit_loss(self, loser_color) -> None:
        """Stop the game because a player exhausted their move limit.

        The player who ran out of moves is *not* automatically the loser.
        Instead, the winner is determined by score comparison, and if scores
        are equal, by total time used (less is better).

        Args:
            loser_color: The color constant (BLACK_COLOR / WHITE_COLOR) of the player who has no moves left.
        """
        loser_name = "Black" if loser_color == BLACK_COLOR else "White"
        print(f"Move limit reached! {loser_name} has no remaining moves.")
        self.move_limit_loser_color = loser_color

        # Determine winner by score comparison
        winner, reason = self._determine_winner_by_score()
        self.move_limit_winner_color = winner
        self.move_limit_reason = reason

        self.show_move_limit_modal = True
        self.game_paused = True
        self.is_game_timer_running = False

    def _get_move_limit_modal_geometry(self) -> dict:
        """Get move-limit game-over modal dimensions and button position."""
        window_w, window_h = self.screen.get_size()

        modal_width = 560
        modal_height = 320
        modal_x = (window_w - modal_width) // 2
        modal_y = (window_h - modal_height) // 2

        button_width = 160
        button_height = 50
        button_x = modal_x + (modal_width - button_width) // 2
        button_y = modal_y + modal_height - 75

        return {
            'modal_x': modal_x,
            'modal_y': modal_y,
            'modal_width': modal_width,
            'modal_height': modal_height,
            'ok_button': pygame.Rect(button_x, button_y, button_width, button_height),
        }

    def _handle_move_limit_modal_click(self, pos: tuple) -> None:
        """Handle clicks on the move-limit game-over modal."""
        geom = self._get_move_limit_modal_geometry()
        if geom['ok_button'].collidepoint(pos):
            self.show_move_limit_modal = False
            self.go_back = True
            self.running = False

    def _draw_move_limit_modal(self) -> None:
        """Draw the move-limit game-over modal."""
        window_w, window_h = self.screen.get_size()
        geom = self._get_move_limit_modal_geometry()

        # Semi-transparent overlay
        overlay = pygame.Surface((window_w, window_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # Modal background
        modal_rect = pygame.Rect(geom['modal_x'], geom['modal_y'], geom['modal_width'], geom['modal_height'])
        pygame.draw.rect(self.screen, (240, 240, 240), modal_rect, border_radius=15)
        pygame.draw.rect(self.screen, (180, 60, 60), modal_rect, width=4, border_radius=15)

        # Title
        title_font = pygame.font.Font(None, 60)
        title_text = title_font.render("Game Over!", True, (180, 60, 60))
        title_rect = title_text.get_rect(center=(geom['modal_x'] + geom['modal_width'] // 2,
                                                  geom['modal_y'] + 60))
        self.screen.blit(title_text, title_rect)

        # Who ran out of moves
        loser_name = "Black" if self.move_limit_loser_color == BLACK_COLOR else "White"

        # Message: who ran out of moves
        msg_font = pygame.font.Font(None, 34)
        line1 = msg_font.render(f"{loser_name} has no remaining moves!", True, (50, 50, 50))
        line1_rect = line1.get_rect(center=(geom['modal_x'] + geom['modal_width'] // 2,
                                             geom['modal_y'] + 120))
        self.screen.blit(line1, line1_rect)

        # Winner determined by score (with time tiebreaker)
        winner_color = getattr(self, 'move_limit_winner_color', None)
        reason = getattr(self, 'move_limit_reason', '')
        result_font = pygame.font.Font(None, 32)
        line2 = result_font.render(reason, True, (50, 50, 50))
        line2_rect = line2.get_rect(center=(geom['modal_x'] + geom['modal_width'] // 2,
                                             geom['modal_y'] + 155))
        self.screen.blit(line2, line2_rect)

        # Score line
        black_score, white_score = self._get_scores_by_color()
        score_font = pygame.font.Font(None, 28)
        score_line = score_font.render(f"Score — Black: {black_score}  |  White: {white_score}", True, (80, 80, 80))
        score_rect = score_line.get_rect(center=(geom['modal_x'] + geom['modal_width'] // 2,
                                                  geom['modal_y'] + 190))
        self.screen.blit(score_line, score_rect)

        # Total time per player
        black_time, white_time = self._get_total_times()
        time_font = pygame.font.Font(None, 28)
        time_line = time_font.render(f"Time — Black: {black_time}  |  White: {white_time}", True, (80, 80, 80))
        time_rect = time_line.get_rect(center=(geom['modal_x'] + geom['modal_width'] // 2,
                                                geom['modal_y'] + 220))
        self.screen.blit(time_line, time_rect)

        # OK button
        mouse_pos = pygame.mouse.get_pos()
        ok_color = (184, 202, 176) if geom['ok_button'].collidepoint(mouse_pos) else (164, 182, 156)
        pygame.draw.rect(self.screen, ok_color, geom['ok_button'], border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), geom['ok_button'], width=2, border_radius=10)

        ok_font = pygame.font.Font(None, 38)
        ok_text = ok_font.render("OK", True, (255, 255, 255))
        ok_text_rect = ok_text.get_rect(center=geom['ok_button'].center)
        self.screen.blit(ok_text, ok_text_rect)

    # ------------------------------------------------------------------
    # Win condition (score reaches 6)
    # ------------------------------------------------------------------

    def _trigger_win(self, winner_color) -> None:
        """Stop the game because a player reached 6 points.

        Args:
            winner_color: The color constant (BLACK_COLOR / WHITE_COLOR) of the winning player.
        """
        winner_name = "Black" if winner_color == BLACK_COLOR else "White"
        print(f"Game Over! {winner_name} wins with 6 points!")
        self.winner_color = winner_color
        self.show_win_modal = True
        self.game_paused = True
        self.is_game_timer_running = False

    def _get_win_modal_geometry(self) -> dict:
        """Get win game-over modal dimensions and button position."""
        window_w, window_h = self.screen.get_size()

        modal_width = 560
        modal_height = 320
        modal_x = (window_w - modal_width) // 2
        modal_y = (window_h - modal_height) // 2

        button_width = 160
        button_height = 50
        button_x = modal_x + (modal_width - button_width) // 2
        button_y = modal_y + modal_height - 75

        return {
            'modal_x': modal_x,
            'modal_y': modal_y,
            'modal_width': modal_width,
            'modal_height': modal_height,
            'ok_button': pygame.Rect(button_x, button_y, button_width, button_height),
        }

    def _handle_win_modal_click(self, pos: tuple) -> None:
        """Handle clicks on the win game-over modal."""
        geom = self._get_win_modal_geometry()
        if geom['ok_button'].collidepoint(pos):
            # Go back to menu
            self.show_win_modal = False
            self.go_back = True
            self.running = False

    def _draw_win_modal(self) -> None:
        """Draw the win game-over modal."""
        window_w, window_h = self.screen.get_size()
        geom = self._get_win_modal_geometry()

        # Semi-transparent overlay
        overlay = pygame.Surface((window_w, window_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.screen.blit(overlay, (0, 0))

        # Modal background
        modal_rect = pygame.Rect(geom['modal_x'], geom['modal_y'], geom['modal_width'], geom['modal_height'])
        pygame.draw.rect(self.screen, (240, 240, 240), modal_rect, border_radius=15)
        pygame.draw.rect(self.screen, (60, 140, 60), modal_rect, width=4, border_radius=15)

        # Title: "Game Over!"
        title_font = pygame.font.Font(None, 60)
        title_text = title_font.render("Game Over!", True, (60, 140, 60))
        title_rect = title_text.get_rect(center=(geom['modal_x'] + geom['modal_width'] // 2,
                                                  geom['modal_y'] + 60))
        self.screen.blit(title_text, title_rect)

        # Determine winner name
        if self.winner_color == BLACK_COLOR:
            winner_name = "Black"
        else:
            winner_name = "White"

        # Message
        msg_font = pygame.font.Font(None, 34)
        line1 = msg_font.render(f"{winner_name} player scored 6 points!", True, (50, 50, 50))
        line2 = msg_font.render(f"{winner_name} wins the game!", True, (50, 50, 50))
        line1_rect = line1.get_rect(center=(geom['modal_x'] + geom['modal_width'] // 2,
                                             geom['modal_y'] + 130))
        line2_rect = line2.get_rect(center=(geom['modal_x'] + geom['modal_width'] // 2,
                                             geom['modal_y'] + 165))
        self.screen.blit(line1, line1_rect)
        self.screen.blit(line2, line2_rect)

        # Total time per player
        black_time, white_time = self._get_total_times()
        time_font = pygame.font.Font(None, 28)
        time_line = time_font.render(f"Black total: {black_time}  |  White total: {white_time}", True, (80, 80, 80))
        time_rect = time_line.get_rect(center=(geom['modal_x'] + geom['modal_width'] // 2,
                                                geom['modal_y'] + 205))
        self.screen.blit(time_line, time_rect)

        # OK button
        mouse_pos = pygame.mouse.get_pos()
        ok_color = (184, 202, 176) if geom['ok_button'].collidepoint(mouse_pos) else (164, 182, 156)
        pygame.draw.rect(self.screen, ok_color, geom['ok_button'], border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), geom['ok_button'], width=2, border_radius=10)

        ok_font = pygame.font.Font(None, 38)
        ok_text = ok_font.render("OK", True, (255, 255, 255))
        ok_text_rect = ok_text.get_rect(center=geom['ok_button'].center)
        self.screen.blit(ok_text, ok_text_rect)

    def _reset_game(self) -> None:
        """Reset the game board to initial state."""
        if self.initial_marble_positions:
            self.marble_positions = self.initial_marble_positions.copy()
            self.move_history = []
            self.player_score = 0
            self.opponent_score = 0
            self.is_human_turn = True
            self.game_paused = False
            self.show_pause_modal = False
            self.show_win_modal = False
            self.winner_color = None
            self.show_move_limit_modal = False
            self.move_limit_loser_color = None
            self.show_timeout_modal = False
            self.timeout_loser_color = None
            self.is_game_timer_running = False
            self.total_time = 0
            self.total_time_input_text = ""
            self.total_time_input_active = False
            self.total_time_input_confirmed = False
            self.total_time_limit = None
            self.game_started = False
            self.move_time_computer = 5
            self.move_time_player = 5
            self.player_moves_remaining = self.move_limit
            self.computer_moves_remaining = self.move_limit
            self.selected_marbles = []
            self._dest_to_move = {}
            self._legal_moves_cache = []
            self._last_moved_cells = []
            self._last_move_direction = None
            self._last_move_color = None
            self._last_move_time_us = None
            self._move_turn_start_us = time.perf_counter_ns() // 1000
            self.current_turn_color = BLACK_COLOR
            self.setup_mode = False
            self._ai_thinking = False
            if self.game_started:
                self._recompute_legal_moves()
            print("Game reset to initial state!")

    def _get_pause_modal_geometry(self) -> dict:
        """Get pause modal dimensions and button positions.

        Returns:
            Dictionary with modal and button geometry
        """
        window_w, window_h = self.screen.get_size()

        # Modal dimensions
        modal_width = 400
        modal_height = 250
        modal_x = (window_w - modal_width) // 2
        modal_y = (window_h - modal_height) // 2

        # Button dimensions
        button_width = 150
        button_height = 50
        button_spacing = 20
        buttons_y = modal_y + modal_height - 80

        # Calculate button positions
        resume_x = modal_x + (modal_width - button_width * 2 - button_spacing) // 2
        quit_x = resume_x + button_width + button_spacing

        return {
            'modal_x': modal_x,
            'modal_y': modal_y,
            'modal_width': modal_width,
            'modal_height': modal_height,
            'resume_button': pygame.Rect(resume_x, buttons_y, button_width, button_height),
            'quit_button': pygame.Rect(quit_x, buttons_y, button_width, button_height)
        }

    def _get_stop_modal_geometry(self) -> dict:
        """Get stop modal dimensions and button positions.

        Returns:
            Dictionary with modal and button geometry
        """
        window_w, window_h = self.screen.get_size()

        # Modal dimensions
        modal_width = 450
        modal_height = 250
        modal_x = (window_w - modal_width) // 2
        modal_y = (window_h - modal_height) // 2

        # Button dimensions
        button_width = 150
        button_height = 50
        button_spacing = 20
        buttons_y = modal_y + modal_height - 80

        # Calculate button positions
        yes_x = modal_x + (modal_width - button_width * 2 - button_spacing) // 2
        no_x = yes_x + button_width + button_spacing

        return {
            'modal_x': modal_x,
            'modal_y': modal_y,
            'modal_width': modal_width,
            'modal_height': modal_height,
            'yes_button': pygame.Rect(yes_x, buttons_y, button_width, button_height),
            'no_button': pygame.Rect(no_x, buttons_y, button_width, button_height)
        }

    def _handle_pause_modal_click(self, pos: tuple) -> None:
        """Handle clicks on pause modal buttons."""
        geom = self._get_pause_modal_geometry()

        # Check clicks
        if geom['resume_button'].collidepoint(pos):
            # Resume game
            self.game_paused = False
            self.show_pause_modal = False
            self.is_game_timer_running = True
            # Restore timers so they continue from where they were paused
            now = pygame.time.get_ticks()
            paused_move_elapsed = getattr(self, '_paused_move_elapsed_ms', 0)
            paused_total_elapsed = getattr(self, '_paused_total_elapsed_ms', 0)
            self.move_start_ticks = now - paused_move_elapsed
            self.start_ticks = now - paused_total_elapsed
            self._move_turn_start_us = time.perf_counter_ns() // 1000 - paused_move_elapsed * 1000
            print("Game resumed!")
        elif geom['quit_button'].collidepoint(pos):
            # Quit to menu
            print("Quitting to menu...")
            self.go_back = True
            self.running = False

    def _handle_undo_button_click(self) -> None:
        """Handle undo button click - undo the last move."""
        if not self.move_history:
            print("No moves to undo!")
            return

        if self.game_paused:
            print("Cannot undo while game is paused. Resume first.")
            return

        # History entries are (move_notation, marble_color, old_positions_snapshot, time_us)
        entry = self.move_history.pop()
        if len(entry) >= 3:
            move_notation, marble_color, old_positions = entry[0], entry[1], entry[2]
            # Recompute score delta: count opponent marbles now vs in snapshot
            opp_color = WHITE_COLOR if marble_color == BLACK_COLOR else BLACK_COLOR
            old_opp_count = sum(1 for c in old_positions.values() if c == opp_color)
            cur_opp_count = sum(1 for c in self.marble_positions.values() if c == opp_color)
            pushed_off = old_opp_count - cur_opp_count  # positive = marbles were pushed off

            if marble_color == self.player_color:
                self.player_score = max(0, self.player_score - pushed_off)
                self.player_moves_remaining += 1
            else:
                self.opponent_score = max(0, self.opponent_score - pushed_off)
                self.computer_moves_remaining += 1

            self.marble_positions = old_positions
            # Reverse the turn switch
            self.current_turn_color = marble_color
            self.selected_marbles = []
            self._dest_to_move = {}
            self._last_moved_cells = []
            self._last_move_direction = None
            self._last_move_color = None
            # Update last move time to the previous move's time (or clear it)
            if self.move_history and len(self.move_history[-1]) >= 4:
                self._last_move_time_us = self.move_history[-1][3]
            else:
                self._last_move_time_us = None
            self._recompute_legal_moves()
            print(f"Undo successful! Reversed move: {move_notation}")
        else:
            # Legacy 2-tuple format fallback
            move_notation, marble_color = entry[0], entry[1]
            print(f"Cannot undo legacy move format: {move_notation}")

    def _get_marble_at_position(self, pos: tuple[int, int]) -> Optional[tuple[int, int]]:
        """
        Get the marble (row, col) at the given screen position.

        Args:
            pos: Screen position (x, y)

        Returns:
            Tuple (row, col) if a marble is at that position, None otherwise
        """
        for (row, col), color in self.marble_positions.items():
            marble_center = self._get_marble_screen_position((row, col))
            dist_sq = (pos[0] - marble_center[0])**2 + (pos[1] - marble_center[1])**2
            if dist_sq <= CELL_RADIUS**2:
                return (row, col)
        return None

    def _get_cell_at_position(self, pos: tuple[int, int]) -> Optional[tuple[int, int]]:
        """
        Get the cell (row, col) at the given screen position.

        Args:
            pos: Screen position (x, y)

        Returns:
            Tuple (row, col) if position is over a valid cell, None otherwise
        """
        for row, row_cells in enumerate(self.board_renderer.cell_centers):
            for col, (x, y) in enumerate(row_cells):
                dist_sq = (pos[0] - x)**2 + (pos[1] - y)**2
                if dist_sq <= CELL_RADIUS**2:
                    return (row, col)
        return None

    def _get_marble_screen_position(self, marble: tuple[int, int]) -> tuple[int, int]:
        """
        Get the screen position (x, y) for a given marble (row, col).

        Args:
            marble: Tuple (row, col)

        Returns:
            Tuple (x, y) screen coordinates
        """
        row, col = marble
        if row < len(self.board_renderer.cell_centers) and col < len(self.board_renderer.cell_centers[row]):
            return self.board_renderer.cell_centers[row][col]
        return (0, 0)

    def _is_valid_move(self, from_cell: tuple, to_cell: tuple) -> bool:
        """
        Check if a move from from_cell to to_cell is valid.
        A move is valid if:
        1. The destination cell is empty
        2. The destination cell is adjacent to the source cell

        Args:
            from_cell: Source cell (row, col)
            to_cell: Destination cell (row, col)

        Returns:
            True if the move is valid, False otherwise
        """
        # Check if destination is empty
        if to_cell in self.marble_positions:
            return False

        # Check if destination is adjacent
        return self._is_adjacent(from_cell, to_cell)

    def _is_adjacent(self, cell1: tuple, cell2: tuple) -> bool:
        """
        Check if two cells are adjacent on the hexagonal board.

        Args:
            cell1: First cell (row, col)
            cell2: Second cell (row, col)

        Returns:
            True if cells are adjacent, False otherwise
        """
        row1, col1 = cell1
        row2, col2 = cell2

        # Same row neighbors
        if row1 == row2 and abs(col1 - col2) == 1:
            return True

        # Adjacent rows
        if abs(row1 - row2) == 1:
            # For hexagonal grid, adjacent row cells can be:
            # - same column
            # - column +1 or -1 depending on which direction
            if row1 < 4:  # Top half of board
                # Moving down increases columns on right side
                if row2 == row1 + 1:
                    return col2 == col1 or col2 == col1 + 1
                else:  # row2 == row1 - 1
                    return col2 == col1 or col2 == col1 - 1
            elif row1 == 4:  # Middle row
                if row2 == row1 + 1:
                    return col2 == col1 or col2 == col1 - 1
                else:  # row2 == row1 - 1
                    return col2 == col1 or col2 == col1 + 1
            else:  # Bottom half of board (row1 > 4)
                # Moving down decreases columns on left side
                if row2 == row1 + 1:
                    return col2 == col1 or col2 == col1 - 1
                else:  # row2 == row1 - 1
                    return col2 == col1 or col2 == col1 + 1

        return False


    def _get_valid_destinations(self, marble: tuple) -> list:
        """
        Get all valid destination cells for a given marble.

        Args:
            marble: Source marble (row, col)

        Returns:
            List of (row, col) tuples representing valid destination cells
        """
        valid_destinations = []

        # Check all cells on the board
        for row, row_cells in enumerate(self.board_renderer.cell_centers):
            for col in range(len(row_cells)):
                cell = (row, col)
                # Check if this cell is a valid destination
                if self._is_valid_move(marble, cell):
                    valid_destinations.append(cell)

        return valid_destinations


    def _draw(self) -> None:
        """Draw the board scene."""
        self.screen.fill(BG_COLOR)

        # Draw the board with current marble positions
        self._draw_board_and_marbles()

        # Draw the score displays above and below the board (white=top, black=bottom)
        self._draw_opponent_score_display()  # White score (top)
        self._draw_player_score_display()    # Black score (bottom)

        # Draw timers
        self._draw_timers()

        # Draw the gray sidebar on the right
        pygame.draw.rect(self.screen, self.sidebar_color, self.sidebar_rect)

        # Draw the lighter gray horizontal box on top of the sidebar
        pygame.draw.rect(self.screen, self.horizontal_box_color, self.horizontal_box_rect)

        # Draw turn indicator text in the center of the horizontal box
        if self.setup_mode:
            setup_text = self.turn_font.render("Setup Mode", True, (0, 140, 140))
            setup_text_rect = setup_text.get_rect(center=self.horizontal_box_rect.center)
            self.screen.blit(setup_text, setup_text_rect)
        else:
            is_human = (self.current_turn_color == self.player_color)
            turn_text = self.human_turn_text if is_human else self.computer_turn_text
            turn_text_rect = turn_text.get_rect(center=self.horizontal_box_rect.center)
            self.screen.blit(turn_text, turn_text_rect)

        # Draw the move history text
        self._draw_move_history()

        # Draw the undo section
        self._draw_undo_section()

        # Draw the bottom control box
        pygame.draw.rect(self.screen, self.bottom_box_color, self.bottom_box_rect)

        # Draw control buttons
        self._draw_control_buttons()

        # Draw the back button
        pygame.draw.rect(self.screen, self.current_back_button_color, self.back_button_rect, border_radius=8)
        # Draw button border
        pygame.draw.rect(self.screen, (255, 255, 255), self.back_button_rect, width=2, border_radius=8)
        # Draw button text
        self.screen.blit(self.back_button_text, self.back_button_text_rect)

        # Draw dragged marble on top if dragging
        if self.dragging and self.dragged_marble:
            mouse_pos = pygame.mouse.get_pos()
            drag_x = mouse_pos[0] - self.drag_offset[0]
            drag_y = mouse_pos[1] - self.drag_offset[1]
            color = self.marble_positions.get(self.dragged_marble)
            if color:
                # Draw highlight ring around the dragged marble (gold)
                pygame.draw.circle(self.screen, (255, 215, 0), (drag_x, drag_y), CELL_RADIUS + 5, 4)
                # Draw shadow
                pygame.draw.circle(self.screen, (120, 120, 120), (drag_x, drag_y), CELL_RADIUS + 1)
                # Draw marble
                pygame.draw.circle(self.screen, color, (drag_x, drag_y), CELL_RADIUS)

        # Draw setup-mode dragged marble on top
        if self.setup_mode and getattr(self, '_setup_dragging', False) and self._setup_dragged_marble is not None:
            mouse_pos = pygame.mouse.get_pos()
            drag_x = mouse_pos[0] - self._setup_drag_offset[0]
            drag_y = mouse_pos[1] - self._setup_drag_offset[1]
            color = self.marble_positions.get(self._setup_dragged_marble)
            if color:
                # Draw highlight ring (cyan to indicate setup mode)
                pygame.draw.circle(self.screen, (0, 200, 200), (drag_x, drag_y), CELL_RADIUS + 5, 4)
                # Draw shadow
                pygame.draw.circle(self.screen, (120, 120, 120), (drag_x, drag_y), CELL_RADIUS + 1)
                # Draw marble
                pygame.draw.circle(self.screen, color, (drag_x, drag_y), CELL_RADIUS)

        # Draw setup mode banner if active
        if self.setup_mode:
            self._draw_setup_mode_banner()

        # Draw pause modal if showing
        if self.show_pause_modal:
            self._draw_pause_modal()

        # Draw tooltip if exists
        if self.tooltip_text:
            self._draw_tooltip()


        # Draw timeout game-over modal if showing
        if self.show_timeout_modal:
            self._draw_timeout_modal()

        # Draw move-limit game-over modal if showing
        if self.show_move_limit_modal:
            self._draw_move_limit_modal()

        # Draw win game-over modal if showing
        if self.show_win_modal:
            self._draw_win_modal()

        pygame.display.flip()

    def _draw_setup_mode_banner(self) -> None:
        """Draw a semi-transparent banner at the top indicating setup mode."""
        window_w, _ = self.screen.get_size()
        available_width = window_w - self.sidebar_width

        banner_height = 40
        banner_surface = pygame.Surface((available_width, banner_height), pygame.SRCALPHA)
        banner_surface.fill((0, 160, 160, 180))  # Teal, semi-transparent
        self.screen.blit(banner_surface, (0, 60))

        font = pygame.font.Font(None, 30)
        text = font.render("SETUP MODE – Drag any marble to rearrange, then press Start", True, (255, 255, 255))
        text_rect = text.get_rect(center=(available_width // 2, 60 + banner_height // 2))
        self.screen.blit(text, text_rect)

    def _draw_tooltip(self) -> None:
        """Draw tooltip at mouse position."""
        if not self.tooltip_text:
            return

        # Create tooltip
        font = pygame.font.Font(None, 24)
        text_surface = font.render(self.tooltip_text, True, (255, 255, 255))

        # Tooltip background
        padding = 8
        tooltip_width = text_surface.get_width() + padding * 2
        tooltip_height = text_surface.get_height() + padding * 2

        # Position tooltip above and to the right of cursor
        tooltip_x = self.tooltip_position[0] + 15
        tooltip_y = self.tooltip_position[1] - tooltip_height - 10

        # Keep tooltip on screen
        window_w, window_h = self.screen.get_size()
        if tooltip_x + tooltip_width > window_w:
            tooltip_x = self.tooltip_position[0] - tooltip_width - 15
        if tooltip_y < 0:
            tooltip_y = self.tooltip_position[1] + 20

        # Draw tooltip background (dark with border)
        tooltip_rect = pygame.Rect(tooltip_x, tooltip_y, tooltip_width, tooltip_height)
        pygame.draw.rect(self.screen, (50, 50, 50), tooltip_rect, border_radius=5)
        pygame.draw.rect(self.screen, (200, 200, 200), tooltip_rect, width=1, border_radius=5)

        # Draw text
        text_x = tooltip_x + padding
        text_y = tooltip_y + padding
        self.screen.blit(text_surface, (text_x, text_y))

    def _draw_pause_modal(self) -> None:
        """Draw pause modal with Resume and Quit buttons."""
        window_w, window_h = self.screen.get_size()
        geom = self._get_pause_modal_geometry()

        # Semi-transparent overlay
        overlay = pygame.Surface((window_w, window_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))  # Darker overlay
        self.screen.blit(overlay, (0, 0))

        # Draw modal background
        modal_rect = pygame.Rect(geom['modal_x'], geom['modal_y'], geom['modal_width'], geom['modal_height'])
        pygame.draw.rect(self.screen, (240, 240, 240), modal_rect, border_radius=15)
        pygame.draw.rect(self.screen, (100, 100, 100), modal_rect, width=3, border_radius=15)

        # Draw "Game Paused" title
        title_font = pygame.font.Font(None, 56)
        title_text = title_font.render("Game Paused", True, (50, 50, 50))
        title_rect = title_text.get_rect(center=(geom['modal_x'] + geom['modal_width'] // 2, geom['modal_y'] + 60))
        self.screen.blit(title_text, title_rect)

        # Get mouse position for hover effects
        mouse_pos = pygame.mouse.get_pos()

        # Draw Resume button - sage green to match project theme
        resume_color = (184, 202, 176) if geom['resume_button'].collidepoint(mouse_pos) else (164, 182, 156)  # Sage green
        pygame.draw.rect(self.screen, resume_color, geom['resume_button'], border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), geom['resume_button'], width=2, border_radius=10)

        resume_font = pygame.font.Font(None, 36)
        resume_text = resume_font.render("Resume", True, (255, 255, 255))
        resume_text_rect = resume_text.get_rect(center=geom['resume_button'].center)
        self.screen.blit(resume_text, resume_text_rect)

        # Draw Quit button - muted brown/red to match board colors
        quit_color = (160, 120, 110) if geom['quit_button'].collidepoint(mouse_pos) else (140, 100, 90)  # Muted brown
        pygame.draw.rect(self.screen, quit_color, geom['quit_button'], border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), geom['quit_button'], width=2, border_radius=10)

        quit_font = pygame.font.Font(None, 36)
        quit_text = quit_font.render("Quit", True, (255, 255, 255))
        quit_text_rect = quit_text.get_rect(center=geom['quit_button'].center)
        self.screen.blit(quit_text, quit_text_rect)

    def _draw_stop_modal(self) -> None:
        """Draw stop confirmation modal with Yes and No buttons."""
        window_w, window_h = self.screen.get_size()
        geom = self._get_stop_modal_geometry()

        # Semi-transparent overlay
        overlay = pygame.Surface((window_w, window_h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))  # Darker overlay
        self.screen.blit(overlay, (0, 0))

        # Draw modal background
        modal_rect = pygame.Rect(geom['modal_x'], geom['modal_y'], geom['modal_width'], geom['modal_height'])
        pygame.draw.rect(self.screen, (240, 240, 240), modal_rect, border_radius=15)
        pygame.draw.rect(self.screen, (100, 100, 100), modal_rect, width=3, border_radius=15)

        # Draw "Stop Game" title
        title_font = pygame.font.Font(None, 56)
        title_text = title_font.render("Stop Game", True, (50, 50, 50))
        title_rect = title_text.get_rect(center=(geom['modal_x'] + geom['modal_width'] // 2, geom['modal_y'] + 40))
        self.screen.blit(title_text, title_rect)

        # Draw confirmation text
        confirm_font = pygame.font.Font(None, 28)
        confirm_text = confirm_font.render("Are you sure you want to stop?", True, (50, 50, 50))
        confirm_rect = confirm_text.get_rect(center=(geom['modal_x'] + geom['modal_width'] // 2, geom['modal_y'] + geom['modal_height'] // 2 - 20))
        self.screen.blit(confirm_text, confirm_rect)

        # Get mouse position for hover effects
        mouse_pos = pygame.mouse.get_pos()

        # Draw Yes button - sage green to match project theme
        yes_color = (184, 202, 176) if geom['yes_button'].collidepoint(mouse_pos) else (164, 182, 156)  # Sage green
        pygame.draw.rect(self.screen, yes_color, geom['yes_button'], border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), geom['yes_button'], width=2, border_radius=10)

        yes_font = pygame.font.Font(None, 36)
        yes_text = yes_font.render("Yes", True, (255, 255, 255))
        yes_text_rect = yes_text.get_rect(center=geom['yes_button'].center)
        self.screen.blit(yes_text, yes_text_rect)

        # Draw No button - muted brown/red to match board colors
        no_color = (160, 120, 110) if geom['no_button'].collidepoint(mouse_pos) else (140, 100, 90)  # Muted brown
        pygame.draw.rect(self.screen, no_color, geom['no_button'], border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), geom['no_button'], width=2, border_radius=10)

        no_font = pygame.font.Font(None, 36)
        no_text = no_font.render("No", True, (255, 255, 255))
        no_text_rect = no_text.get_rect(center=geom['no_button'].center)
        self.screen.blit(no_text, no_text_rect)

    def _draw_board_and_marbles(self) -> None:
        """Draw the board hexagon and all marbles."""
        # Draw the hexagonal board
        from src.ui.constants import CELL_MARGIN, RIM_WIDTH, BORDER_COLOR, BOARD_FILL, EMPTY_COLOR

        # Inner hex should fully contain all circles (radius + margin)
        inner_hex = self.board_renderer._hex_polygon_around_cells(extra=CELL_MARGIN)
        # Outer hex is inner hex expanded by rim width
        outer_hex = self.board_renderer._hex_polygon_around_cells(extra=CELL_MARGIN + RIM_WIDTH)

        # Draw rim and inner fill
        pygame.draw.polygon(self.screen, BORDER_COLOR, outer_hex)
        pygame.draw.polygon(self.screen, BOARD_FILL, inner_hex)

        # Valid destinations come from the move-engine destination map
        valid_destinations = set(self._dest_to_move.keys())

        # Draw all cells and marbles
        for row, row_cells in enumerate(self.board_renderer.cell_centers):
            for col, (x, y) in enumerate(row_cells):
                cell = (row, col)

                # Skip the dragged marble (will be drawn at mouse position)
                if self.dragging and self.dragged_marble == cell:
                    # Draw empty cell where the marble was picked up from
                    pygame.draw.circle(self.screen, (120, 120, 120), (x, y), CELL_RADIUS + 1)
                    pygame.draw.circle(self.screen, EMPTY_COLOR, (x, y), CELL_RADIUS)
                    # Draw a highlight ring at the original position to show it's selected
                    pygame.draw.circle(self.screen, (255, 215, 0), (x, y), CELL_RADIUS + 4, 3)  # Gold ring
                else:
                    # Draw marble or empty cell
                    color = self.marble_positions.get(cell, EMPTY_COLOR)
                    pygame.draw.circle(self.screen, (120, 120, 120), (x, y), CELL_RADIUS + 1)
                    pygame.draw.circle(self.screen, color, (x, y), CELL_RADIUS)

                    # If this marble is in the selected group, highlight it
                    if cell in self.selected_marbles and not self.dragging:
                        pygame.draw.circle(self.screen, (255, 215, 0), (x, y), CELL_RADIUS + 4, 3)  # Gold ring


                    # If this is a valid destination, draw a small yellow solid ball inside
                    if cell in valid_destinations:
                        # Draw a small yellow solid ball to indicate valid destination
                        ball_radius = 6  # Small solid ball
                        pygame.draw.circle(self.screen, (255, 215, 0), (x, y), ball_radius)  # Yellow solid ball

        # ── Draw direction arrows on last-moved marbles ──────────────────
        if self._last_moved_cells and self._last_move_direction is not None:
            self._draw_move_arrows()

    def _draw_move_arrows(self) -> None:
        """Draw direction arrows on the last-moved marbles.

        The arrow colour contrasts with the marble colour so it is always
        visible (white arrow on black marbles, dark arrow on white marbles).
        """
        if not self._last_moved_cells or self._last_move_direction is None:
            return

        # Map engine direction number to a screen-space angle (radians).
        # The display grid spaces adjacent rows by DY vertically and offsets
        # them by 0.5*DX horizontally, giving ~60° diagonal directions.
        # Screen: 0 = right, π/2 = down (pygame Y-axis points downward).
        _dir_angles: Dict[int, float] = {
            1:  -math.pi / 3,              # NE → ~-60°  (up-right)
            3:   0.0,                       # E  →   0°   (right)
            5:   math.pi / 3,              # SE → ~+60°  (down-right)
            7:   math.pi - math.pi / 3,    # SW → ~+120° (down-left)
            9:   math.pi,                  # W  → 180°   (left)
            11: -(math.pi - math.pi / 3),  # NW → ~-120° (up-left)
        }

        angle = _dir_angles.get(self._last_move_direction)
        if angle is None:
            return

        # Choose arrow colour to contrast with marble colour
        if self._last_move_color == BLACK_COLOR:
            arrow_color = (255, 255, 255)  # white arrow on black marble
        else:
            arrow_color = (30, 30, 30)     # dark arrow on white marble

        arrow_len = CELL_RADIUS * 0.55   # length of the arrow shaft
        head_len = CELL_RADIUS * 0.35    # length of the arrowhead
        head_half_w = CELL_RADIUS * 0.22 # half-width of the arrowhead base

        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        for cell in self._last_moved_cells:
            # Only draw on cells that currently have a marble
            if cell not in self.marble_positions:
                continue
            cx, cy = self._get_marble_screen_position(cell)

            # Shaft: from centre offset slightly back to a point forward
            sx = cx - cos_a * arrow_len * 0.4
            sy = cy - sin_a * arrow_len * 0.4
            ex = cx + cos_a * arrow_len * 0.6
            ey = cy + sin_a * arrow_len * 0.6

            # Draw shaft line
            pygame.draw.line(self.screen, arrow_color,
                             (int(sx), int(sy)), (int(ex), int(ey)), 3)

            # Arrowhead (filled triangle) at the tip
            tip_x = ex + cos_a * head_len
            tip_y = ey + sin_a * head_len
            # Perpendicular offsets for the two base corners
            perp_cos = math.cos(angle + math.pi / 2)
            perp_sin = math.sin(angle + math.pi / 2)
            base1 = (ex + perp_cos * head_half_w, ey + perp_sin * head_half_w)
            base2 = (ex - perp_cos * head_half_w, ey - perp_sin * head_half_w)
            pygame.draw.polygon(self.screen, arrow_color, [
                (int(tip_x), int(tip_y)),
                (int(base1[0]), int(base1[1])),
                (int(base2[0]), int(base2[1])),
            ])

    def _draw_move_history(self) -> None:
        """Draw the move history header text and two-column list of moves (Black | White)."""
        # Draw header text at the left side of the move history section
        text_x = self.move_history_rect.x + 10  # Small left padding
        text_y = self.move_history_rect.centery - (self.move_history_text.get_height() // 2)
        self.screen.blit(self.move_history_text, (text_x, text_y))

        # Font for move entries
        move_font = pygame.font.Font(None, 20)

        # Font colors: black text for black moves, white text for white moves
        black_text_color = (15, 15, 15)       # Black font
        white_text_color = (245, 245, 245)    # White font
        white_outline_color = (80, 80, 80)    # Dark outline for white text readability

        # Column layout
        col_left_x = self.move_history_rect.x  # Left column start
        col_width = self.move_history_rect.width // 2
        col_right_x = col_left_x + col_width  # Right column start

        # Separate moves by color, keeping (notation, time_us) pairs
        black_moves = [(entry[0], entry[3] if len(entry) >= 4 else None) for entry in self.move_history if entry[1] == BLACK_COLOR]
        white_moves = [(entry[0], entry[3] if len(entry) >= 4 else None) for entry in self.move_history if entry[1] == WHITE_COLOR]

        # Starting position for move list (below the header)
        list_start_y = self.move_history_y + self.move_history_height + 5
        line_height = 28  # Height for each move entry (includes room for time)

        # Calculate the area available for move history
        available_height = self.undo_section_y - list_start_y - 10
        max_moves_to_display = int(available_height / line_height)

        # Trim to most recent moves if too many
        black_to_show = black_moves[-max_moves_to_display:] if len(black_moves) > max_moves_to_display else black_moves
        white_to_show = white_moves[-max_moves_to_display:] if len(white_moves) > max_moves_to_display else white_moves

        left_padding = 8  # Small padding from the left edge of each column

        # Draw black moves in left column (black font, left-aligned)
        for i, (notation, move_time_us) in enumerate(black_to_show):
            entry_y = list_start_y + i * line_height
            move_text = move_font.render(notation, True, black_text_color)
            tx = col_left_x + left_padding
            ty = entry_y + 1
            self.screen.blit(move_text, (tx, ty))

        # Draw white moves in right column (white font with outline, left-aligned)
        for i, (notation, move_time_us) in enumerate(white_to_show):
            entry_y = list_start_y + i * line_height
            tx = col_right_x + left_padding
            ty = entry_y + 1

            # Draw dark outline by rendering text offset in each direction
            outline_surf = move_font.render(notation, True, white_outline_color)
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.screen.blit(outline_surf, (tx + dx, ty + dy))

            # Draw white text on top
            white_surf = move_font.render(notation, True, white_text_color)
            self.screen.blit(white_surf, (tx, ty))


    def _draw_undo_section(self) -> None:
        """Draw the undo section with text and circular button."""
        # Calculate positions for text and button
        text_width = self.undo_text.get_width()
        button_spacing = 15
        total_width = text_width + button_spacing + self.undo_button_size

        # Starting X position to center the content
        start_x = self.undo_section_rect.centerx - (total_width // 2)
        center_y = self.undo_section_rect.centery

        # Draw text on the left
        text_x = start_x
        text_y = center_y - (self.undo_text.get_height() // 2)
        self.screen.blit(self.undo_text, (text_x, text_y))

        # Draw circular button on the right
        button_center = self.undo_button_rect.center
        button_radius = self.undo_button_size // 2

        # Choose color based on hover state
        button_color = self.undo_button_hover_color if self.undo_button_hover else self.undo_button_bg_color
        pygame.draw.circle(self.screen, button_color, button_center, button_radius)

        # Draw undo icon on button if available
        if self.undo_icon_scaled:
            icon_rect = self.undo_icon_scaled.get_rect(center=button_center)
            self.screen.blit(self.undo_icon_scaled, icon_rect)

    def _draw_opponent_score_display(self) -> None:
        """Draw the white player score display above the board (top = white, always)."""
        from src.ui.constants import CELL_MARGIN, RIM_WIDTH, CELL_RADIUS
        import math

        # Calculate the top edge of the hexagon board
        # Get the top row cells (row 0)
        top_row_cells = self.board_renderer.cell_centers[0]
        top_center_y = top_row_cells[0][1]  # Y coordinate of top row

        # Calculate padding for hexagon (same as used in _hex_polygon_around_cells)
        padding = CELL_RADIUS + CELL_MARGIN + RIM_WIDTH
        cos30 = math.sqrt(3) / 2

        # Top edge of hexagon
        hexagon_top_y = top_center_y - padding * cos30

        # Position score display just above the hexagon (with small gap)
        gap_above_hexagon = 20  # 20px gap between hexagon and score display
        # Position so the bottom of the text/button is at hexagon_top_y - gap
        score_display_bottom_y = int(hexagon_top_y) - gap_above_hexagon

        # Calculate score display y (top of the text)
        score_display_y = score_display_bottom_y - self.white_score_label_text.get_height()

        # Calculate horizontal center based on board center
        window_w, _ = self.screen.get_size()
        available_width = window_w - self.sidebar_width
        board_center_x = available_width // 2

        # Calculate positions for text and button
        text_button_spacing = 15  # Space between text and button
        total_width = self.white_score_label_text.get_width() + text_button_spacing + (self.score_button_radius * 2)

        # Center the entire score display
        start_x = board_center_x - (total_width // 2)
        text_x = start_x
        button_center_x = start_x + self.white_score_label_text.get_width() + text_button_spacing + self.score_button_radius

        # Draw "White Score:" text
        self.screen.blit(self.white_score_label_text, (text_x, score_display_y))

        # Draw circular button with score
        button_center = (button_center_x, score_display_y + self.white_score_label_text.get_height() // 2)

        # Draw white circle with gray border
        pygame.draw.circle(self.screen, self.score_button_bg_color, button_center, self.score_button_radius)
        pygame.draw.circle(self.screen, self.score_button_border_color, button_center, self.score_button_radius, 2)

        # Draw score text in the center of the circle
        score_text = self.score_font.render(str(self._white_score), True, self.score_button_text_color)
        score_text_rect = score_text.get_rect(center=button_center)
        self.screen.blit(score_text, score_text_rect)

    def _draw_player_score_display(self) -> None:
        """Draw the black player score display below the board (bottom = black, always)."""
        from src.ui.constants import CELL_MARGIN, RIM_WIDTH, CELL_RADIUS
        import math

        # Calculate the bottom edge of the hexagon board
        # Get the bottom row cells (row 8)
        bottom_row_cells = self.board_renderer.cell_centers[8]
        bottom_center_y = bottom_row_cells[0][1]  # Y coordinate of bottom row

        # Calculate padding for hexagon (same as used in _hex_polygon_around_cells)
        padding = CELL_RADIUS + CELL_MARGIN + RIM_WIDTH
        cos30 = math.sqrt(3) / 2

        # Bottom edge of hexagon
        hexagon_bottom_y = bottom_center_y + padding * cos30

        # Position score display just below the hexagon (with small gap)
        gap_below_hexagon = 20  # 20px gap between hexagon and score display
        score_display_y = int(hexagon_bottom_y) + gap_below_hexagon

        # Calculate horizontal center based on board center
        window_w, _ = self.screen.get_size()
        available_width = window_w - self.sidebar_width
        board_center_x = available_width // 2

        # Calculate positions for text and button
        text_button_spacing = 15  # Space between text and button
        total_width = self.black_score_label_text.get_width() + text_button_spacing + (self.score_button_radius * 2)

        # Center the entire score display
        start_x = board_center_x - (total_width // 2)
        text_x = start_x
        button_center_x = start_x + self.black_score_label_text.get_width() + text_button_spacing + self.score_button_radius

        # Draw "Black Score:" text
        self.screen.blit(self.black_score_label_text, (text_x, score_display_y))

        # Draw circular button with score
        button_center = (button_center_x, score_display_y + self.black_score_label_text.get_height() // 2)

        # Draw white circle with gray border
        pygame.draw.circle(self.screen, self.score_button_bg_color, button_center, self.score_button_radius)
        pygame.draw.circle(self.screen, self.score_button_border_color, button_center, self.score_button_radius, 2)

        # Draw score text in the center of the circle
        score_text = self.score_font.render(str(self._black_score), True, self.score_button_text_color)
        score_text_rect = score_text.get_rect(center=button_center)
        self.screen.blit(score_text, score_text_rect)

    def _draw_control_buttons(self) -> None:
        """Draw the control buttons (start, pause, stop, reset) with icons."""
        for button in self.control_buttons:
            # Determine if start button should appear disabled
            is_start_disabled = (button['type'] == 'start' and not self.total_time_input_confirmed and not self.game_started)
            # Stop button is disabled when not in Human vs AI mode
            is_stop_disabled = (button['type'] == 'stop' and self.game_mode != 0)
            # Stop button highlighted when setup mode is active
            is_stop_active = (button['type'] == 'stop' and self.setup_mode)

            if is_start_disabled or is_stop_disabled:
                # Draw disabled state (grayed out)
                color = (180, 180, 180)  # Gray
            elif is_stop_active:
                # Highlight the stop button in teal when setup mode is on
                color = (0, 180, 180) if button['hover'] else (0, 160, 160)
            else:
                # Choose color based on hover state
                color = self.button_hover_color if button['hover'] else self.button_bg_color

            # Draw circular button background
            center = button['rect'].center
            radius = button['rect'].width // 2
            pygame.draw.circle(self.screen, color, center, radius)

            # Draw button icon based on type
            icon_color = (160, 160, 160) if (is_start_disabled or is_stop_disabled) else self.button_icon_color
            if button['type'] == 'start':
                self._draw_play_icon(center, radius, icon_color)
            elif button['type'] == 'pause':
                self._draw_pause_icon(center, radius)
            elif button['type'] == 'stop':
                self._draw_stop_icon(center, radius)
            elif button['type'] == 'reset':
                # Use image if available, otherwise draw programmatically
                if self.reset_icon_scaled:
                    # Center the image within the button
                    icon_rect = self.reset_icon_scaled.get_rect(center=center)
                    self.screen.blit(self.reset_icon_scaled, icon_rect)
                else:
                    self._draw_reset_icon(center, radius)

    def _draw_play_icon(self, center: tuple, radius: int, icon_color: tuple = None) -> None:
        """Draw a play/start triangle icon."""
        if icon_color is None:
            icon_color = self.button_icon_color
        # Triangle pointing right
        size = radius * 0.5
        points = [
            (center[0] - size * 0.4, center[1] - size),
            (center[0] - size * 0.4, center[1] + size),
            (center[0] + size * 0.8, center[1])
        ]
        pygame.draw.polygon(self.screen, icon_color, points)

    def _draw_pause_icon(self, center: tuple, radius: int) -> None:
        """Draw a pause (two vertical bars) icon."""
        size = radius * 0.5
        bar_width = size * 0.4
        bar_height = size * 1.6

        # Left bar
        left_bar = pygame.Rect(center[0] - size * 0.6, center[1] - bar_height / 2, bar_width, bar_height)
        pygame.draw.rect(self.screen, self.button_icon_color, left_bar)

        # Right bar
        right_bar = pygame.Rect(center[0] + size * 0.2, center[1] - bar_height / 2, bar_width, bar_height)
        pygame.draw.rect(self.screen, self.button_icon_color, right_bar)

    def _draw_stop_icon(self, center: tuple, radius: int) -> None:
        """Draw a stop (square) icon."""
        size = radius * 0.6
        square = pygame.Rect(center[0] - size / 2, center[1] - size / 2, size, size)
        pygame.draw.rect(self.screen, self.button_icon_color, square)

    def _draw_reset_icon(self, center: tuple, radius: int) -> None:
        """Draw a reset (circular arrow) icon - simple refresh symbol."""
        import math

        size = radius * 0.55
        thickness = 3

        # Draw main circular arc (almost complete circle with gap at top)
        rect = pygame.Rect(center[0] - size, center[1] - size, size * 2, size * 2)

        # Draw arc from about 45 degrees to 315 degrees (clockwise, leaving gap at top-right)
        start_angle = math.pi * 0.25  # 45 degrees
        end_angle = math.pi * 1.75    # 315 degrees
        pygame.draw.arc(self.screen, self.button_icon_color, rect, start_angle, end_angle, thickness)

        # Draw arrow head pointing to the right/clockwise at the top
        arrow_size = size * 0.4
        # Position arrow at the end of the arc (around 315 degrees / -45 degrees)
        arrow_x = center[0] + size * math.cos(-math.pi / 4)
        arrow_y = center[1] + size * math.sin(-math.pi / 4)

        # Arrow pointing clockwise (to the right and slightly down)
        arrow_points = [
            (arrow_x + arrow_size * 0.6, arrow_y),  # Tip pointing right
            (arrow_x - arrow_size * 0.3, arrow_y - arrow_size * 0.5),  # Top back
            (arrow_x - arrow_size * 0.3, arrow_y + arrow_size * 0.5)   # Bottom back
        ]
        pygame.draw.polygon(self.screen, self.button_icon_color, arrow_points)

    def _draw_timers(self) -> None:
        """Draw timer boxes and player indicators around the board."""
        window_w, window_h = self.screen.get_size()
        available_width = window_w - self.sidebar_width
        board_center_x = available_width // 2

        # Responsive sizing based on window dimensions
        # Scale boxes based on available width
        scale_factor = max(0.7, min(available_width / 1200, 1.2))  # Scale between 0.7x and 1.2x

        total_box_width = int(220 * scale_factor)
        total_box_height = int(80 * scale_factor)
        timer_box_width = int(120 * scale_factor)
        timer_box_height = int(60 * scale_factor)

        # Responsive padding
        top_padding = int(30 * scale_factor)
        bottom_padding = int(170 * scale_factor)  # Increased from 120 to move timers and text upward
        right_offset = int(200 * scale_factor)  # Increased from 80 to move timers more right

        # Draw Total Game Time box at TOP CENTER
        total_box_x = board_center_x - (total_box_width // 2)
        total_box_y = top_padding
        total_box_rect = pygame.Rect(total_box_x, total_box_y, total_box_width, total_box_height)
        pygame.draw.rect(self.screen, self.total_time_box_color, total_box_rect, border_radius=10)
        pygame.draw.rect(self.screen, (0, 0, 0), total_box_rect, width=2, border_radius=10)

        label_font = pygame.font.Font(None, int(20 * scale_factor))
        value_font = pygame.font.Font(None, int(38 * scale_factor))

        if self.total_time_input_confirmed:
            # Show label and countdown
            total_label = label_font.render("Total Game Time:", True, self.timer_text_color)
            total_label_rect = total_label.get_rect(center=(total_box_rect.centerx, total_box_rect.centery - int(15 * scale_factor)))
            self.screen.blit(total_label, total_label_rect)

            minutes = self.total_time // 60
            seconds = self.total_time % 60
            total_value = value_font.render(f"{minutes}:{seconds:02d}", True, self.timer_text_color)
            total_value_rect = total_value.get_rect(center=(total_box_rect.centerx, total_box_rect.centery + int(15 * scale_factor)))
            self.screen.blit(total_value, total_value_rect)
        else:
            # Show label and editable input field
            total_label = label_font.render("Total Game Time (min):", True, self.timer_text_color)
            total_label_rect = total_label.get_rect(center=(total_box_rect.centerx, total_box_rect.centery - int(15 * scale_factor)))
            self.screen.blit(total_label, total_label_rect)

            # Draw input field
            input_w = int(70 * scale_factor)
            input_h = int(28 * scale_factor)
            input_x = total_box_rect.centerx - input_w // 2
            input_y = total_box_rect.centery + int(5 * scale_factor)
            self.total_time_input_rect = pygame.Rect(input_x, input_y, input_w, input_h)

            bg_color = self.total_time_input_color_active if self.total_time_input_active else self.total_time_input_color_inactive
            border_color = self.total_time_input_border_active if self.total_time_input_active else self.total_time_input_border_inactive
            pygame.draw.rect(self.screen, bg_color, self.total_time_input_rect, border_radius=5)
            pygame.draw.rect(self.screen, border_color, self.total_time_input_rect, width=2, border_radius=5)

            # Draw text inside input field (or placeholder)
            input_font = pygame.font.Font(None, int(28 * scale_factor))
            if self.total_time_input_text:
                input_surface = input_font.render(self.total_time_input_text, True, (0, 0, 0))
            else:
                input_surface = input_font.render("--", True, (150, 150, 150))
            input_surface_rect = input_surface.get_rect(center=self.total_time_input_rect.center)
            self.screen.blit(input_surface, input_surface_rect)

            # Draw blinking cursor when active
            if self.total_time_input_active and (pygame.time.get_ticks() // 500) % 2 == 0:
                cursor_x = input_surface_rect.right + 2
                cursor_y1 = self.total_time_input_rect.centery - int(10 * scale_factor)
                cursor_y2 = self.total_time_input_rect.centery + int(10 * scale_factor)
                pygame.draw.line(self.screen, (0, 0, 0), (cursor_x, cursor_y1), (cursor_x, cursor_y2), 2)

        # Draw first 5 sec timer on TOP RIGHT (under total time)
        timer1_box_x = board_center_x + right_offset
        timer1_box_y = total_box_y + total_box_height + int(20 * scale_factor)
        timer1_box_rect = pygame.Rect(timer1_box_x, timer1_box_y, timer_box_width, timer_box_height)
        pygame.draw.rect(self.screen, (211, 211, 211), timer1_box_rect, border_radius=8)
        pygame.draw.rect(self.screen, (0, 0, 0), timer1_box_rect, width=2, border_radius=8)

        # Draw only the timer value (5 sec) centered in box – WHITE's time (top)
        timer1_value = value_font.render(f"{self._white_move_time:.1f}s", True, self.timer_text_color)
        timer1_value_rect = timer1_value.get_rect(center=timer1_box_rect.center)
        self.screen.blit(timer1_value, timer1_value_rect)

        # Draw second 5 sec timer on BOTTOM RIGHT (facing top-right timer)
        timer2_box_x = board_center_x + right_offset
        timer2_box_y = window_h - bottom_padding
        timer2_box_rect = pygame.Rect(timer2_box_x, timer2_box_y, timer_box_width, timer_box_height)
        pygame.draw.rect(self.screen, (211, 211, 211), timer2_box_rect, border_radius=8)
        pygame.draw.rect(self.screen, (0, 0, 0), timer2_box_rect, width=2, border_radius=8)

        # Draw only the timer value (5 sec) centered in box – BLACK's time (bottom)
        timer2_value = value_font.render(f"{self._black_move_time:.1f}s", True, self.timer_text_color)
        timer2_value_rect = timer2_value.get_rect(center=timer2_box_rect.center)
        self.screen.blit(timer2_value, timer2_value_rect)

        # Draw move limit displays below the timer boxes
        move_limit_font = pygame.font.Font(None, int(26 * scale_factor))

        # White move limit (below top-right timer) - aligned with timer box
        white_move_text = move_limit_font.render(f"Moves: {self._white_moves_remaining}/{self.move_limit}", True, self.timer_text_color)
        white_move_rect = white_move_text.get_rect(topleft=(timer1_box_x, timer1_box_y + timer_box_height + int(8 * scale_factor)))
        self.screen.blit(white_move_text, white_move_rect)

        # Black move limit (below bottom-right timer) - aligned with timer box
        black_move_text = move_limit_font.render(f"Moves: {self._black_moves_remaining}/{self.move_limit}", True, self.timer_text_color)
        black_move_rect = black_move_text.get_rect(topleft=(timer2_box_x, timer2_box_y - move_limit_font.get_height() - int(8 * scale_factor)))
        self.screen.blit(black_move_text, black_move_rect)

    def run(self) -> None:
        """Run the board scene game loop."""
        while self.running:
            self.running = self._handle_events()
            self._update_timers()
            self._maybe_ai_move()
            self._draw()
            self.clock.tick(FPS)

