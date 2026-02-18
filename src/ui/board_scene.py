"""
Board scene for the Abalone game.
"""
import pygame
from src.constants import FPS, BG_COLOR, BOARD_CENTER
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

        self._setup_back_button()
        self._setup_sidebar()
        self._setup_turn_text()

        # Calculate board center in the middle of free space (left edge to sidebar)
        window_w, window_h = self.screen.get_size()
        available_width = window_w - self.sidebar_width
        board_center = (available_width // 2, window_h // 2)
        self.board_renderer = BoardRenderer(board_center, invert_colors=invert_colors, board_layout=board_layout)

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

        # Create sidebar rectangle on the right side
        self.sidebar_rect = pygame.Rect(window_w - self.sidebar_width, 0, self.sidebar_width, window_h)

        # Create horizontal box rectangle on top of the sidebar with margins
        self.horizontal_box_rect = pygame.Rect(
            window_w - self.sidebar_width + self.horizontal_box_margin,  # Left margin
            self.horizontal_box_margin,  # Top margin
            self.sidebar_width - (2 * self.horizontal_box_margin),  # Width with left and right margins
            self.horizontal_box_height - self.horizontal_box_margin  # Height with top margin (bottom touches sidebar)
        )

    def _setup_turn_text(self) -> None:
        """Setup the turn indicator text."""
        # Font for turn text
        self.turn_font = pygame.font.Font(None, 36)
        self.turn_text_color = (50, 50, 50)  # Dark gray text

        # Pre-render both text options
        self.human_turn_text = self.turn_font.render("Your Turn", True, self.turn_text_color)
        self.computer_turn_text = self.turn_font.render("Computer Turn", True, self.turn_text_color)

    def toggle_turn(self) -> None:
        """Toggle between human and computer turns."""
        self.is_human_turn = not self.is_human_turn

    def _update_positions(self) -> None:
        """Update positions based on current window size."""
        # Get current window dimensions
        window_w, window_h = self.screen.get_size()

        # Calculate board center in the middle of free space (left edge to sidebar)
        available_width = window_w - self.sidebar_width
        new_board_center = (available_width // 2, window_h // 2)
        self.board_renderer = BoardRenderer(new_board_center, invert_colors=self.invert_colors, board_layout=self.board_layout)

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

    def _handle_events(self) -> bool:
        """
        Handle user input events.

        Returns:
            True to continue running, False to quit
        """
        mouse_pos = pygame.mouse.get_pos()

        # Update back button hover state
        if self.back_button_rect.collidepoint(mouse_pos):
            self.current_back_button_color = self.back_button_hover_color
        else:
            self.current_back_button_color = self.back_button_color

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.VIDEORESIZE:
                # Window was resized, update positions
                self._update_positions()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check if back button was clicked
                if self.back_button_rect.collidepoint(event.pos):
                    self.go_back = True
                    return False
        return True

    def _draw(self) -> None:
        """Draw the board scene."""
        self.screen.fill(BG_COLOR)
        self.board_renderer.draw(self.screen)

        # Draw the gray sidebar on the right
        pygame.draw.rect(self.screen, self.sidebar_color, self.sidebar_rect)

        # Draw the lighter gray horizontal box on top of the sidebar
        pygame.draw.rect(self.screen, self.horizontal_box_color, self.horizontal_box_rect)

        # Draw turn indicator text in the center of the horizontal box
        turn_text = self.human_turn_text if self.is_human_turn else self.computer_turn_text
        turn_text_rect = turn_text.get_rect(center=self.horizontal_box_rect.center)
        self.screen.blit(turn_text, turn_text_rect)

        # Draw the back button
        pygame.draw.rect(self.screen, self.current_back_button_color, self.back_button_rect, border_radius=8)
        # Draw button border
        pygame.draw.rect(self.screen, (255, 255, 255), self.back_button_rect, width=2, border_radius=8)
        # Draw button text
        self.screen.blit(self.back_button_text, self.back_button_text_rect)

        pygame.display.flip()

    def run(self) -> None:
        """Run the board scene game loop."""
        while self.running:
            self.running = self._handle_events()
            self._draw()
            self.clock.tick(FPS)

