"""
Game mode selection page for the Abalone game.
"""
import pygame
from typing import Optional
from src.constants import (
    WINDOW_W, WINDOW_H, FPS,
    LANDING_BG_COLOR
)


class GameModePage:
    """
    Game mode page that displays game mode options.
    """

    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock):
        """
        Initialize the game mode page.

        Args:
            screen: Pygame surface to draw on
            clock: Pygame clock for timing
        """
        self.screen = screen
        self.clock = clock
        self.bg_color = LANDING_BG_COLOR  # Default background color
        self.back_requested = False  # Flag to indicate back button was pressed
        self.continue_requested = False  # Flag to indicate continue to next page

        self._setup_game_mode_button()
        self._setup_back_button()
        self._update_positions()

    def _setup_game_mode_button(self) -> None:
        """Setup the 'Game Mode' button at the top of the page."""
        # Button properties
        button_width = 200
        button_height = 50

        # Position at the top center of the page
        button_x = (WINDOW_W - button_width) // 2  # Horizontally centered
        button_y = 30  # 30px from top

        # Create Game Mode button rectangle
        self.game_mode_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

        # Button colors - sage green matching the landing page
        self.button_color = (164, 182, 156)  # Sage green
        self.button_hover_color = (184, 202, 176)  # Lighter sage green
        self.button_text_color = (255, 255, 255)  # White
        self.current_game_mode_button_color = self.button_color

        # Create button text
        font = pygame.font.Font(None, 28)
        self.game_mode_button_text = font.render("Game Mode", True, self.button_text_color)
        self.game_mode_button_text_rect = self.game_mode_button_text.get_rect(center=self.game_mode_button_rect.center)

    def _setup_back_button(self) -> None:
        """Setup the 'Back' button at the top left of the page."""
        # Button properties
        button_width = 100
        button_height = 40

        # Position at the top left of the page
        button_x = 30  # 30px from left
        button_y = 30  # 30px from top

        # Create Back button rectangle
        self.back_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        self.current_back_button_color = self.button_color

        # Create button text
        font = pygame.font.Font(None, 28)
        self.back_button_text = font.render("Back", True, self.button_text_color)
        self.back_button_text_rect = self.back_button_text.get_rect(center=self.back_button_rect.center)

    def _update_positions(self) -> None:
        """Update positions based on current window size."""
        # Get current window dimensions
        window_w, window_h = self.screen.get_size()

        # Update Game Mode button position
        if hasattr(self, 'game_mode_button_rect'):
            button_x = (window_w - self.game_mode_button_rect.width) // 2
            button_y = 30  # 30px from top
            self.game_mode_button_rect.x = button_x
            self.game_mode_button_rect.y = button_y
            self.game_mode_button_text_rect.center = self.game_mode_button_rect.center

        # Back button position doesn't need to change (stays at top left)

    def _handle_events(self) -> Optional[bool]:
        """
        Handle user input events.

        Returns:
            True to continue to next scene, False to quit, None to keep waiting
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.VIDEORESIZE:
                # Window was resized, update positions
                self._update_positions()
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check if Back button was clicked
                if self.back_button_rect.collidepoint(event.pos):
                    self.back_requested = True
                # Check if Game Mode button was clicked
                elif self.game_mode_button_rect.collidepoint(event.pos):
                    self.continue_requested = True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

        # Update button hover states
        mouse_pos = pygame.mouse.get_pos()

        # Game Mode button hover
        if self.game_mode_button_rect.collidepoint(mouse_pos):
            self.current_game_mode_button_color = self.button_hover_color
        else:
            self.current_game_mode_button_color = self.button_color

        # Back button hover
        if self.back_button_rect.collidepoint(mouse_pos):
            self.current_back_button_color = self.button_hover_color
        else:
            self.current_back_button_color = self.button_color

        return None  # Continue waiting

    def _draw(self) -> None:
        """Draw the game mode page."""
        # Fill background with color
        self.screen.fill(self.bg_color)

        # Draw the Game Mode button
        pygame.draw.rect(self.screen, self.current_game_mode_button_color, self.game_mode_button_rect, border_radius=10)
        # Draw button border
        pygame.draw.rect(self.screen, (255, 255, 255), self.game_mode_button_rect, width=3, border_radius=10)
        # Draw button text
        self.screen.blit(self.game_mode_button_text, self.game_mode_button_text_rect)

        # Draw the Back button
        pygame.draw.rect(self.screen, self.current_back_button_color, self.back_button_rect, border_radius=10)
        # Draw button border
        pygame.draw.rect(self.screen, (255, 255, 255), self.back_button_rect, width=3, border_radius=10)
        # Draw button text
        self.screen.blit(self.back_button_text, self.back_button_text_rect)

        pygame.display.flip()

    def run(self) -> bool:
        """
        Run the game mode page.

        Returns:
            True if user wants to continue, False if quit
        """
        while True:
            result = self._handle_events()
            if result is not None:
                return result

            # Check if back button was pressed
            if self.back_requested:
                return False  # Go back to landing page

            # Check if continue was requested
            if self.continue_requested:
                return True  # Continue to next page

            self._draw()
            self.clock.tick(FPS)

