"""
Board scene for the Abalone game.
"""
import pygame
from typing import Optional
from src.constants import FPS, BG_COLOR, CELL_RADIUS, BLACK_COLOR, WHITE_COLOR
from src.ui.board_renderer import BoardRenderer


class BoardScene:
    """
    Main game board scene.
    """

    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock, invert_colors: bool = False, board_layout: str = 'standard'):
        """
        Initialize the board scene.

        Args:
            screen: Pygame surface to draw on
            clock: Pygame clock for timing
            invert_colors: If True, swap black and white marble positions
            board_layout: Board layout type ('standard', 'german', or 'belgian')
        """
        self.screen = screen
        self.clock = clock
        self.invert_colors = invert_colors
        self.board_layout = board_layout
        self.running = True
        self.go_back = False

        # Turn tracking (True = human turn, False = computer turn)
        self.is_human_turn = True

        # Drag and drop state
        self.dragging = False
        self.dragged_marble = None  # (row, col) of the marble being dragged
        self.drag_offset = (0, 0)  # Offset from marble center to mouse position
        self.mouse_down_pos = None  # Position where mouse button was pressed (for click vs drag detection)
        self._marble_before_drag = None  # Selection state before the current mouse-down
        self.player_color = BLACK_COLOR if not invert_colors else WHITE_COLOR  # Player's chosen color

        # Game state management
        self.game_paused = False  # Whether the game is currently paused
        self.game_started = False  # Game needs START button to begin
        self.initial_marble_positions = None  # Store initial board state for reset
        self.show_pause_modal = False  # Whether to show pause modal
        self.show_stop_modal = False  # Whether to show stop confirmation modal

        # Button tooltip tracking
        self.tooltip_text = None  # Current tooltip text to display
        self.tooltip_position = (0, 0)  # Tooltip position
        # Selection state - persistent selection that shows valid moves
        self.selected_marble = None  # (row, col) of the currently selected marble


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
        self.move_history = []  # List of tuples: (move_notation, marble_color)

        # Score tracking
        self.player_score = 0
        self.opponent_score = 0

        # Timer variables
        self.total_time = 15 * 60  # 15 minutes in seconds
        self.move_time_computer = 5  # 5 seconds per move
        self.move_time_player = 5
        self.is_game_timer_running = False
        self.start_ticks = 0

        # Move limit variables (set by game configuration)
        self.max_moves_per_player = 40  # Default move limit per player
        self.player_moves_remaining = 40  # Player's remaining moves
        self.computer_moves_remaining = 40  # Computer's remaining moves

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


    def _update_timers(self) -> None:
        """Update game timers."""
        if not self.is_game_timer_running:
            return

        elapsed = (pygame.time.get_ticks() - self.start_ticks) // 1000
        self.total_time = max(0, 15 * 60 - elapsed)

        # Update move timer for current player
        move_elapsed = elapsed % 10
        if move_elapsed < 5:
            self.move_time_player = max(0, 5 - move_elapsed)
            self.move_time_computer = 5
        else:
            self.move_time_computer = max(0, 10 - move_elapsed)
            self.move_time_player = 5

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
            self.undo_icon_image = pygame.image.load("undo.png")
            # Scale to fit in circular button
            icon_size = 28  # Icon size for button
            self.undo_icon_scaled = pygame.transform.scale(self.undo_icon_image, (icon_size, icon_size))
        except (FileNotFoundError, pygame.error) as e:
            print(f"Warning: Could not load undo.png: {e}")

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
        """Setup the score displays above and below the board."""
        # Font for score text
        self.score_font = pygame.font.Font(None, 28)
        self.score_text_color = (50, 50, 50)  # Dark gray text

        # Player score label text (below board)
        self.player_score_label_text = self.score_font.render("Your Score:", True, self.score_text_color)

        # Opponent score label text (above board)
        self.opponent_score_label_text = self.score_font.render("Opponent Score:", True, self.score_text_color)

        # Circular button properties
        self.score_button_radius = 20  # Radius of circular button (40px diameter)
        self.score_button_bg_color = (255, 255, 255)  # White background
        self.score_button_border_color = (100, 100, 100)  # Gray border
        self.score_button_text_color = (50, 50, 50)  # Dark gray text

        # Position will be calculated dynamically in draw methods
        # based on the actual board hexagon edges


    def _cell_to_notation(self, cell: tuple) -> str:
        """
        Convert (row, col) to cell notation.
        Rows are labeled A-I where row 0 (top in display) = I, row 8 (bottom in display) = A.
        Columns are numbered 1-9 from left to right.

        Based on the standard Abalone notation:
        - Row I (top, 5 cells): I1, I2, I3, I4, I5
        - Row E (middle, 9 cells): E1, E2, E3, E4, E5, E6, E7, E8, E9
        - Row A (bottom, 5 cells): A1, A2, A3, A4, A5

        Args:
            cell: Tuple (row, col) where row 0 is top

        Returns:
            Cell notation string (e.g., 'I1', 'E5', 'A1')
        """
        row, col = cell

        # Row labels: I-A (top to bottom, row 0 = I, row 8 = A)
        # Invert the row: A is at bottom (row 8), I is at top (row 0)
        row_label = chr(ord('I') - row)

        # Column number: Simply 1-indexed position (left to right)
        col_number = col + 1

        return f"{row_label}{col_number}"

    @staticmethod
    def _notation_to_cell(notation: str) -> Optional[tuple[int, int]]:
        """
        Convert cell notation to (row, col) coordinates.
        Reverse operation of _cell_to_notation.

        Args:
            notation: Cell notation string (e.g., 'I1', 'E5', 'A1')

        Returns:
            Tuple (row, col) or None if notation is invalid
        """
        if len(notation) != 2:
            return None

        row_label = notation[0]
        col_str = notation[1]

        try:
            # Convert row label back to row number (I=0, H=1, ..., A=8)
            row = ord('I') - ord(row_label)

            # Convert column string to column number (1-indexed to 0-indexed)
            col = int(col_str) - 1

            # Validate ranges
            if row < 0 or row > 8 or col < 0 or col > 8:
                return None

            return (row, col)
        except (ValueError, TypeError):
            return None

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
            self.reset_icon_image = pygame.image.load("reset_icon.png")
            # Scale to fit within button (slightly smaller than button size for padding)
            icon_size = int(button_size * 0.7)
            self.reset_icon_scaled = pygame.transform.scale(self.reset_icon_image, (icon_size, icon_size))
        except (FileNotFoundError, pygame.error) as e:
            print(f"Warning: Could not load reset_icon.png: {e}")
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
                    self.tooltip_text = "Start"
                elif button['type'] == 'pause':
                    self.tooltip_text = "Pause"
                elif button['type'] == 'stop':
                    self.tooltip_text = "Stop"
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
            if event.type == pygame.MOUSEBUTTONDOWN:
                # If pause modal is showing, handle modal button clicks
                if self.show_pause_modal:
                    self._handle_pause_modal_click(event.pos)
                    # If quit was clicked in modal, running will be False
                    if not self.running:
                        return False
                    continue

                # If stop modal is showing, handle modal button clicks
                if self.show_stop_modal:
                    self._handle_stop_modal_click(event.pos)
                    # If yes was clicked in modal, running will be False
                    if not self.running:
                        return False
                    continue

                # Check if back button was clicked
                if self.back_button_rect.collidepoint(event.pos):
                    self.go_back = True
                    return False

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

                # Check if a destination ball was clicked to move the selected marble
                if self.is_human_turn and self.game_started and not self.game_paused and self.selected_marble:
                    clicked_cell = self._get_cell_at_position(event.pos)
                    if clicked_cell and clicked_cell in self._get_valid_destinations(self.selected_marble):
                        # Move the selected marble to the clicked destination
                        from_notation = self._cell_to_notation(self.selected_marble)
                        to_notation = self._cell_to_notation(clicked_cell)
                        move_notation = f"{from_notation}{to_notation}"
                        marble_color = self.marble_positions[self.selected_marble]
                        self.move_history.append((move_notation, marble_color))

                        self.marble_positions[clicked_cell] = self.marble_positions[self.selected_marble]
                        del self.marble_positions[self.selected_marble]

                        self.player_moves_remaining -= 1
                        print(f"Player move made! Remaining moves: {self.player_moves_remaining}")

                        if self.player_moves_remaining <= 0:
                            print("Player has reached move limit!")
                            self.game_paused = True
                            self.show_pause_modal = True

                        self.selected_marble = None
                        continue

                # Check if a marble was clicked for dragging (only if game is started and not paused)
                if self.is_human_turn and self.game_started and not self.game_paused:
                    marble_at_pos = self._get_marble_at_position(event.pos)
                    if marble_at_pos and self.marble_positions.get(marble_at_pos) == self.player_color:
                        # Always start dragging; deselection is resolved on MOUSEBUTTONUP
                        self.mouse_down_pos = event.pos
                        self._marble_before_drag = self.selected_marble  # remember prior selection
                        self.selected_marble = marble_at_pos
                        self.dragging = True
                        self.dragged_marble = marble_at_pos
                        marble_center = self._get_marble_screen_position(marble_at_pos)
                        self.drag_offset = (event.pos[0] - marble_center[0], event.pos[1] - marble_center[1])

            if event.type == pygame.MOUSEBUTTONUP:
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
                        # It was a plain click — deselect only if this marble was already
                        # selected before the mouse-down (i.e. the user tapped to deselect)
                        released_on = self._get_marble_at_position(event.pos)
                        if released_on == self.dragged_marble and self._marble_before_drag == self.dragged_marble:
                            self.selected_marble = None  # deselect
                        # else: marble stays selected (new selection on tap)
                        self.dragging = False
                        self.dragged_marble = None
                        self.drag_offset = (0, 0)
                        self.mouse_down_pos = None
                        self._marble_before_drag = None
                        continue
                    # Try to drop the marble
                    drop_cell = self._get_cell_at_position(event.pos)
                    if drop_cell and self._is_valid_move(self.dragged_marble, drop_cell):
                        # Record the move in history
                        from_notation = self._cell_to_notation(self.dragged_marble)
                        to_notation = self._cell_to_notation(drop_cell)
                        move_notation = f"{from_notation}{to_notation}"
                        marble_color = self.marble_positions[self.dragged_marble]
                        self.move_history.append((move_notation, marble_color))

                        # Move the marble
                        self.marble_positions[drop_cell] = self.marble_positions[self.dragged_marble]
                        del self.marble_positions[self.dragged_marble]

                        # Decrement player's move limit
                        self.player_moves_remaining -= 1
                        print(f"Player move made! Remaining moves: {self.player_moves_remaining}")

                        # Check if player reached move limit
                        if self.player_moves_remaining <= 0:
                            print("Player has reached move limit!")
                            self.game_paused = True
                            self.show_pause_modal = True
                            # TODO: Show game over message or end game

                        # Clear selection after a successful move
                        self.selected_marble = None

                    # Reset dragging state (but keep selection if move wasn't made)
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

    def _start_game(self) -> None:
        """Start or resume the game."""
        if not self.game_started:
            # Start the game
            self.game_started = True
            self.game_paused = False
            self.is_game_timer_running = True
            self.start_ticks = pygame.time.get_ticks()
            print("Game started!")
        elif self.game_paused:
            # Resume if paused
            self.game_paused = False
            self.show_pause_modal = False
            self.is_game_timer_running = True
            self.start_ticks = pygame.time.get_ticks()
            print("Game resumed!")
        else:
            print("Game is already running!")

    def _pause_game(self) -> None:
        """Pause or resume the game."""
        if not self.game_paused:
            # Pausing the game
            self.game_paused = True
            self.show_pause_modal = True
            self.is_game_timer_running = False
            print("Game paused!")
        else:
            # Resuming the game (called from modal resume button)
            self.game_paused = False
            self.show_pause_modal = False
            self.is_game_timer_running = True
            self.start_ticks = pygame.time.get_ticks()
            print("Game resumed!")

    def _stop_game(self) -> None:
        """Show stop confirmation modal."""
        self.show_stop_modal = True
        print("Stop confirmation modal shown")

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
            self.is_game_timer_running = False
            self.total_time = 15 * 60
            self.move_time_computer = 5
            self.move_time_player = 5
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

        # Get the last move from history
        last_move_notation, marble_color = self.move_history.pop()

        # Parse the move notation to get from and to positions
        # Format: e.g., "I1I2" (from I1 to I2)
        from_notation = last_move_notation[:2]  # e.g., "I1"
        to_notation = last_move_notation[2:]    # e.g., "I2"

        # Convert notation back to (row, col)
        from_cell = self._notation_to_cell(from_notation)
        to_cell = self._notation_to_cell(to_notation)

        if from_cell is None or to_cell is None:
            print("Error: Could not parse move notation")
            self.move_history.append((last_move_notation, marble_color))
            return

        # Move the marble back from to_cell to from_cell
        if to_cell in self.marble_positions:
            self.marble_positions[from_cell] = self.marble_positions[to_cell]
            del self.marble_positions[to_cell]
            print(f"Undo successful! Reversed move: {last_move_notation}")
        else:
            print("Error: Could not undo move - target cell not found")
            self.move_history.append((last_move_notation, marble_color))

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

        # Draw the score displays above and below the board
        self._draw_opponent_score_display()  # Above board
        self._draw_player_score_display()    # Below board

        # Draw timers
        self._draw_timers()

        # Draw the gray sidebar on the right
        pygame.draw.rect(self.screen, self.sidebar_color, self.sidebar_rect)

        # Draw the lighter gray horizontal box on top of the sidebar
        pygame.draw.rect(self.screen, self.horizontal_box_color, self.horizontal_box_rect)

        # Draw turn indicator text in the center of the horizontal box
        turn_text = self.human_turn_text if self.is_human_turn else self.computer_turn_text
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

        # Draw pause modal if showing
        if self.show_pause_modal:
            self._draw_pause_modal()

        # Draw tooltip if exists
        if self.tooltip_text:
            self._draw_tooltip()

        # Draw stop confirmation modal if showing
        if self.show_stop_modal:
            self._draw_stop_modal()

        pygame.display.flip()

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
        from src.constants import CELL_MARGIN, RIM_WIDTH, BORDER_COLOR, BOARD_FILL, EMPTY_COLOR

        # Inner hex should fully contain all circles (radius + margin)
        inner_hex = self.board_renderer._hex_polygon_around_cells(extra=CELL_MARGIN)
        # Outer hex is inner hex expanded by rim width
        outer_hex = self.board_renderer._hex_polygon_around_cells(extra=CELL_MARGIN + RIM_WIDTH)

        # Draw rim and inner fill
        pygame.draw.polygon(self.screen, BORDER_COLOR, outer_hex)
        pygame.draw.polygon(self.screen, BOARD_FILL, inner_hex)

        # Get valid destinations for selected or dragged marble
        valid_destinations = []
        marble_to_show_moves = self.dragged_marble if self.dragging else self.selected_marble
        if marble_to_show_moves:
            valid_destinations = self._get_valid_destinations(marble_to_show_moves)

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

                    # If this marble is selected (but not being dragged), highlight it
                    if self.selected_marble == cell and not self.dragging:
                        pygame.draw.circle(self.screen, (255, 215, 0), (x, y), CELL_RADIUS + 4, 3)  # Gold ring


                    # If this is a valid destination, draw a small white solid ball inside
                    if cell in valid_destinations:
                        # Draw a small white solid ball to indicate valid destination
                        ball_radius = 6  # Small solid ball
                        pygame.draw.circle(self.screen, (255, 255, 255), (x, y), ball_radius)  # White solid ball

    def _draw_move_history(self) -> None:
        """Draw the move history header text and list of moves with colored indicators."""
        # Draw header text at the left side of the move history section
        text_x = self.move_history_rect.x + 10  # Small left padding
        text_y = self.move_history_rect.centery - (self.move_history_text.get_height() // 2)
        self.screen.blit(self.move_history_text, (text_x, text_y))

        # Draw move history entries below the header
        if self.move_history:
            # Font for move entries
            move_font = pygame.font.Font(None, 22)
            move_text_color = (50, 50, 50)  # Dark gray text
            ball_radius = 5  # Small solid ball indicator

            # Starting position for move list (below the header)
            list_start_y = self.move_history_y + self.move_history_height + 5
            line_height = 25  # Height for each move entry

            # Calculate the area available for move history
            available_height = self.undo_section_y - list_start_y - 10
            max_moves_to_display = int(available_height / line_height)

            # Display moves from most recent backwards (up to max that fit)
            moves_to_show = self.move_history[-max_moves_to_display:] if len(self.move_history) > max_moves_to_display else self.move_history

            for i, (move_notation, marble_color) in enumerate(moves_to_show):
                # Position for this move entry
                entry_y = list_start_y + i * line_height

                # Draw colored ball indicator
                ball_x = self.move_history_rect.x + 15
                ball_y = entry_y + line_height // 2
                pygame.draw.circle(self.screen, marble_color, (ball_x, ball_y), ball_radius)

                # Draw move notation text
                move_text = move_font.render(move_notation, True, move_text_color)
                text_x = ball_x + ball_radius + 8  # Position text after the ball
                text_y = entry_y + (line_height - move_text.get_height()) // 2
                self.screen.blit(move_text, (text_x, text_y))

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
        """Draw the opponent score display above the board."""
        from src.constants import CELL_MARGIN, RIM_WIDTH, CELL_RADIUS
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
        score_display_y = score_display_bottom_y - self.opponent_score_label_text.get_height()

        # Calculate horizontal center based on board center
        window_w, _ = self.screen.get_size()
        available_width = window_w - self.sidebar_width
        board_center_x = available_width // 2

        # Calculate positions for text and button
        text_button_spacing = 15  # Space between text and button
        total_width = self.opponent_score_label_text.get_width() + text_button_spacing + (self.score_button_radius * 2)

        # Center the entire score display
        start_x = board_center_x - (total_width // 2)
        text_x = start_x
        button_center_x = start_x + self.opponent_score_label_text.get_width() + text_button_spacing + self.score_button_radius

        # Draw "Opponent Score:" text
        self.screen.blit(self.opponent_score_label_text, (text_x, score_display_y))

        # Draw circular button with score
        button_center = (button_center_x, score_display_y + self.opponent_score_label_text.get_height() // 2)

        # Draw white circle with gray border
        pygame.draw.circle(self.screen, self.score_button_bg_color, button_center, self.score_button_radius)
        pygame.draw.circle(self.screen, self.score_button_border_color, button_center, self.score_button_radius, 2)

        # Draw score text in the center of the circle
        score_text = self.score_font.render(str(self.opponent_score), True, self.score_button_text_color)
        score_text_rect = score_text.get_rect(center=button_center)
        self.screen.blit(score_text, score_text_rect)

    def _draw_player_score_display(self) -> None:
        """Draw the player score display below the board."""
        from src.constants import CELL_MARGIN, RIM_WIDTH, CELL_RADIUS
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
        total_width = self.player_score_label_text.get_width() + text_button_spacing + (self.score_button_radius * 2)

        # Center the entire score display
        start_x = board_center_x - (total_width // 2)
        text_x = start_x
        button_center_x = start_x + self.player_score_label_text.get_width() + text_button_spacing + self.score_button_radius

        # Draw "Your Score:" text
        self.screen.blit(self.player_score_label_text, (text_x, score_display_y))

        # Draw circular button with score
        button_center = (button_center_x, score_display_y + self.player_score_label_text.get_height() // 2)

        # Draw white circle with gray border
        pygame.draw.circle(self.screen, self.score_button_bg_color, button_center, self.score_button_radius)
        pygame.draw.circle(self.screen, self.score_button_border_color, button_center, self.score_button_radius, 2)

        # Draw score text in the center of the circle
        score_text = self.score_font.render(str(self.player_score), True, self.score_button_text_color)
        score_text_rect = score_text.get_rect(center=button_center)
        self.screen.blit(score_text, score_text_rect)

    def _draw_control_buttons(self) -> None:
        """Draw the control buttons (start, pause, stop, reset) with icons."""
        for button in self.control_buttons:
            # Choose color based on hover state
            color = self.button_hover_color if button['hover'] else self.button_bg_color

            # Draw circular button background
            center = button['rect'].center
            radius = button['rect'].width // 2
            pygame.draw.circle(self.screen, color, center, radius)

            # Draw button icon based on type
            if button['type'] == 'start':
                self._draw_play_icon(center, radius)
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

    def _draw_play_icon(self, center: tuple, radius: int) -> None:
        """Draw a play/start triangle icon."""
        # Triangle pointing right
        size = radius * 0.5
        points = [
            (center[0] - size * 0.4, center[1] - size),
            (center[0] - size * 0.4, center[1] + size),
            (center[0] + size * 0.8, center[1])
        ]
        pygame.draw.polygon(self.screen, self.button_icon_color, points)

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

        total_box_width = int(200 * scale_factor)
        total_box_height = int(70 * scale_factor)
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

        # Draw total time text with responsive font
        label_font = pygame.font.Font(None, int(20 * scale_factor))
        total_label = label_font.render("Total Game Time:", True, self.timer_text_color)
        total_label_rect = total_label.get_rect(center=(total_box_rect.centerx, total_box_rect.centery - int(15 * scale_factor)))
        self.screen.blit(total_label, total_label_rect)

        # Draw total time value
        value_font = pygame.font.Font(None, int(38 * scale_factor))
        minutes = self.total_time // 60
        seconds = self.total_time % 60
        total_value = value_font.render(f"{minutes}:{seconds:02d}", True, self.timer_text_color)
        total_value_rect = total_value.get_rect(center=(total_box_rect.centerx, total_box_rect.centery + int(15 * scale_factor)))
        self.screen.blit(total_value, total_value_rect)

        # Draw first 5 sec timer on TOP RIGHT (under total time)
        timer1_box_x = board_center_x + right_offset
        timer1_box_y = total_box_y + total_box_height + int(20 * scale_factor)
        timer1_box_rect = pygame.Rect(timer1_box_x, timer1_box_y, timer_box_width, timer_box_height)
        pygame.draw.rect(self.screen, (211, 211, 211), timer1_box_rect, border_radius=8)
        pygame.draw.rect(self.screen, (0, 0, 0), timer1_box_rect, width=2, border_radius=8)

        # Draw only the timer value (5 sec) centered in box
        timer1_value = value_font.render(f"{self.move_time_computer}s", True, self.timer_text_color)
        timer1_value_rect = timer1_value.get_rect(center=timer1_box_rect.center)
        self.screen.blit(timer1_value, timer1_value_rect)

        # Draw second 5 sec timer on BOTTOM RIGHT (facing top-right timer)
        timer2_box_x = board_center_x + right_offset
        timer2_box_y = window_h - bottom_padding
        timer2_box_rect = pygame.Rect(timer2_box_x, timer2_box_y, timer_box_width, timer_box_height)
        pygame.draw.rect(self.screen, (211, 211, 211), timer2_box_rect, border_radius=8)
        pygame.draw.rect(self.screen, (0, 0, 0), timer2_box_rect, width=2, border_radius=8)

        # Draw only the timer value (5 sec) centered in box
        timer2_value = value_font.render(f"{self.move_time_player}s", True, self.timer_text_color)
        timer2_value_rect = timer2_value.get_rect(center=timer2_box_rect.center)
        self.screen.blit(timer2_value, timer2_value_rect)

        # Draw move limit displays below the timer boxes
        move_limit_font = pygame.font.Font(None, int(26 * scale_factor))

        # Computer move limit (below top-right timer) - aligned with timer box
        computer_move_text = move_limit_font.render(f"Moves: {self.computer_moves_remaining}/{self.max_moves_per_player}", True, self.timer_text_color)
        computer_move_rect = computer_move_text.get_rect(topleft=(timer1_box_x, timer1_box_y + timer_box_height + int(8 * scale_factor)))
        self.screen.blit(computer_move_text, computer_move_rect)

        # Player move limit (below bottom-right timer) - aligned with timer box
        player_move_text = move_limit_font.render(f"Moves: {self.player_moves_remaining}/{self.max_moves_per_player}", True, self.timer_text_color)
        player_move_rect = player_move_text.get_rect(topleft=(timer2_box_x, timer2_box_y - move_limit_font.get_height() - int(8 * scale_factor)))
        self.screen.blit(player_move_text, player_move_rect)

    def run(self) -> None:
        """Run the board scene game loop."""
        while self.running:
            self.running = self._handle_events()
            self._update_timers()
            self._draw()
            self.clock.tick(FPS)

