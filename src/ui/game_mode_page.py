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
        self.selected_mode = None  # Store which mode was selected

        self._load_background_color()
        self._setup_title_button()
        self._setup_game_mode_buttons()
        self._setup_back_button()
        self._update_positions()

    def _load_background_color(self) -> None:
        """Load the standard image and extract its background color."""
        try:
            standard_image = pygame.image.load("standard.png")
            # Extract background color from the top-left corner pixel
            self.bg_color = standard_image.get_at((0, 0))[:3]  # Get RGB, ignore alpha
        except (FileNotFoundError, pygame.error):
            # If image not found, keep the default LANDING_BG_COLOR
            pass

    def _setup_title_button(self) -> None:
        """Setup the 'Game Mode' title button at the top center of the page."""
        # Button properties
        button_width = 200
        button_height = 50

        # Position at the top center of the page
        button_x = (WINDOW_W - button_width) // 2  # Horizontally centered
        button_y = 30  # 30px from top

        # Create title button rectangle
        self.title_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

        # Button colors - matching the Start button from landing page
        self.title_button_color = (120, 140, 110)  # Darker sage green
        self.title_button_text_color = (255, 255, 255)  # White

        # Create button text
        font = pygame.font.Font(None, 36)
        self.title_button_text = font.render("Game Mode", True, self.title_button_text_color)
        self.title_button_text_rect = self.title_button_text.get_rect(center=self.title_button_rect.center)

    def _setup_game_mode_buttons(self) -> None:
        """Setup the three game mode option buttons in the center of the page."""
        # Button properties
        button_width = 600
        button_height = 60
        button_spacing = 30  # Space between buttons

        # Calculate starting Y position to center all three buttons vertically
        total_height = (button_height * 3) + (button_spacing * 2)
        start_y = (WINDOW_H - total_height) // 2

        # Button colors - matching the Start button from landing page
        self.button_color = (120, 140, 110)  # Darker sage green
        self.button_hover_color = (140, 160, 130)  # Lighter sage green for hover
        self.button_text_color = (255, 255, 255)  # White

        # Create three buttons
        self.mode_buttons = []
        button_labels = [
            "Human vs Computer: 40 moves per player",
            "Computer vs Computer: 40 moves per player",
            "Human vs Human: 50 moves per player"
        ]

        font = pygame.font.Font(None, 32)

        for i, label in enumerate(button_labels):
            button_x = (WINDOW_W - button_width) // 2
            button_y = start_y + (i * (button_height + button_spacing))

            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            button_text = font.render(label, True, self.button_text_color)
            button_text_rect = button_text.get_rect(center=button_rect.center)

            self.mode_buttons.append({
                'rect': button_rect,
                'text': button_text,
                'text_rect': button_text_rect,
                'label': label,
                'current_color': self.button_color,
                'mode': i  # 0, 1, or 2
            })

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

        # Update title button position
        if hasattr(self, 'title_button_rect'):
            button_x = (window_w - self.title_button_rect.width) // 2
            self.title_button_rect.x = button_x
            self.title_button_text_rect.center = self.title_button_rect.center

        # Update game mode buttons positions
        if hasattr(self, 'mode_buttons'):
            button_width = 600
            button_height = 60
            button_spacing = 30

            total_height = (button_height * 3) + (button_spacing * 2)
            start_y = (window_h - total_height) // 2

            for i, button in enumerate(self.mode_buttons):
                button_x = (window_w - button_width) // 2
                button_y = start_y + (i * (button_height + button_spacing))
                button['rect'].x = button_x
                button['rect'].y = button_y
                button['text_rect'].center = button['rect'].center

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
                else:
                    # Check if any game mode button was clicked
                    for button in self.mode_buttons:
                        if button['rect'].collidepoint(event.pos):
                            self.selected_mode = button['mode']
                            self.continue_requested = True
                            break
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

        # Update button hover states
        mouse_pos = pygame.mouse.get_pos()

        # Update hover state for each game mode button
        for button in self.mode_buttons:
            if button['rect'].collidepoint(mouse_pos):
                button['current_color'] = self.button_hover_color
            else:
                button['current_color'] = self.button_color

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

        # Draw the title "Game Mode" button at the top
        pygame.draw.rect(self.screen, self.title_button_color, self.title_button_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), self.title_button_rect, width=3, border_radius=10)
        self.screen.blit(self.title_button_text, self.title_button_text_rect)

        # Draw all game mode buttons
        for button in self.mode_buttons:
            # Draw button
            pygame.draw.rect(self.screen, button['current_color'], button['rect'], border_radius=10)
            # Draw button border
            pygame.draw.rect(self.screen, (255, 255, 255), button['rect'], width=3, border_radius=10)
            # Draw button text
            self.screen.blit(button['text'], button['text_rect'])

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

