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
        self.board_renderer = BoardRenderer(BOARD_CENTER, invert_colors=invert_colors, board_layout=board_layout)
        self.running = True
        self.go_back = False
        self._setup_back_button()

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

    def _update_positions(self) -> None:
        """Update positions based on current window size."""
        # Get current window dimensions
        window_w, window_h = self.screen.get_size()

        # Update board center position
        new_board_center = (window_w // 2, window_h // 2)
        self.board_renderer = BoardRenderer(new_board_center, invert_colors=self.invert_colors, board_layout=self.board_layout)

        # Back button stays in top-left corner, no need to update

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

