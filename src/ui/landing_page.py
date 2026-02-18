"""
Landing page scene for the Abalone game.
"""
import pygame
from typing import Optional
from src.constants import (
    WINDOW_W, WINDOW_H, FPS,
    LANDING_PAGE_IMAGES,
    LANDING_BG_COLOR
)


class LandingPage:
    """
    Landing page scene that displays the game logo and waits for user input.
    """

    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock):
        """
        Initialize the landing page.

        Args:
            screen: Pygame surface to draw on
            clock: Pygame clock for timing
        """
        self.screen = screen
        self.clock = clock
        self.landing_image: Optional[pygame.Surface] = None
        self.scaled_image: Optional[pygame.Surface] = None
        self.image_x = 0
        self.image_y = 0

        self._load_image()
        self._setup_text()

    def _load_image(self) -> None:
        """Load the landing page image from available files."""
        for img_file in LANDING_PAGE_IMAGES:
            try:
                self.landing_image = pygame.image.load(img_file)
                break
            except (FileNotFoundError, pygame.error):
                continue

        if self.landing_image:
            self._scale_image()

    def _scale_image(self) -> None:
        """Keep the image at original size and center it."""
        if not self.landing_image:
            return

        # Get current window dimensions
        window_w, window_h = self.screen.get_size()

        # Keep the image at its original size (no scaling)
        self.scaled_image = self.landing_image

        # Get image dimensions
        img_width, img_height = self.landing_image.get_size()

        # Center the image
        self.image_x = (window_w - img_width) // 2
        self.image_y = (window_h - img_height) // 2

    def _setup_text(self) -> None:
        """Setup the 'Start' button in the middle right part of the screen."""
        # Button properties
        button_width = 200
        button_height = 60

        # Position in middle right (right side, vertically centered)
        button_x = WINDOW_W - button_width - 30  # 30px from right edge (moved more to the right)
        button_y = (WINDOW_H - button_height) // 2  # Vertically centered

        # Create button rectangle
        self.button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

        # Button colors - darker colors for contrast against cream background
        self.button_color = (120, 140, 110)  # Darker sage green
        self.button_hover_color = (140, 160, 130)  # Lighter sage green for hover
        self.button_text_color = (255, 255, 255)  # White
        self.current_button_color = self.button_color

        # Create button text
        font = pygame.font.Font(None, 48)
        self.button_text = font.render("Start", True, self.button_text_color)
        self.button_text_rect = self.button_text.get_rect(center=self.button_rect.center)

    def _update_positions(self) -> None:
        """Update positions based on current window size."""
        # Get current window dimensions
        window_w, window_h = self.screen.get_size()

        # Update image if it exists
        if self.landing_image:
            self._scale_image()

        # Update button position
        button_x = window_w - self.button_rect.width - 30  # 30px from right edge
        button_y = (window_h - self.button_rect.height) // 2  # Vertically centered
        self.button_rect.x = button_x
        self.button_rect.y = button_y
        self.button_text_rect.center = self.button_rect.center

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
                # Check if button was clicked
                if self.button_rect.collidepoint(event.pos):
                    return True
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                else:
                    return True

        # Update button hover state
        mouse_pos = pygame.mouse.get_pos()
        if self.button_rect.collidepoint(mouse_pos):
            self.current_button_color = self.button_hover_color
        else:
            self.current_button_color = self.button_color

        return None  # Continue waiting

    def _draw(self) -> None:
        """Draw the landing page."""
        # Fill background with dark color
        self.screen.fill(LANDING_BG_COLOR)

        # Draw the scaled image if available
        if self.scaled_image:
            self.screen.blit(self.scaled_image, (self.image_x, self.image_y))

        # Draw the button
        pygame.draw.rect(self.screen, self.current_button_color, self.button_rect, border_radius=10)
        # Draw button border
        pygame.draw.rect(self.screen, (255, 255, 255), self.button_rect, width=3, border_radius=10)
        # Draw button text
        self.screen.blit(self.button_text, self.button_text_rect)

        pygame.display.flip()

    def run(self) -> bool:
        """
        Run the landing page scene.

        Returns:
            True if user wants to continue to the game, False if quit
        """
        while True:
            result = self._handle_events()
            if result is not None:
                return result

            self._draw()
            self.clock.tick(FPS)

