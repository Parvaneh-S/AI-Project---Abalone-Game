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
    Game mode selection page that displays game mode options.
    """

    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock):
        """
        Initialize the game mode selection page.

        Args:
            screen: Pygame surface to draw on
            clock: Pygame clock for timing
        """
        self.screen = screen
        self.clock = clock
        self.standard_image: Optional[pygame.Surface] = None
        self.scaled_image: Optional[pygame.Surface] = None
        self.german_daisy_image: Optional[pygame.Surface] = None
        self.scaled_german_daisy_image: Optional[pygame.Surface] = None
        self.belgian_daisy_image: Optional[pygame.Surface] = None
        self.scaled_belgian_daisy_image: Optional[pygame.Surface] = None
        self.image_x = 0
        self.image_y = 0
        self.image_width = 0
        self.image_height = 0
        self.german_daisy_x = 0
        self.german_daisy_y = 0
        self.belgian_daisy_x = 0
        self.belgian_daisy_y = 0
        self.bg_color = LANDING_BG_COLOR  # Default background color

        # Selection states
        self.selected_board = None  # Can be 'standard', 'german', or 'belgian'
        self.selected_color = None  # Can be 'black' or 'white'
        self.back_requested = False  # Flag to indicate back button was pressed
        self.next_requested = False  # Flag to indicate next button was pressed

        self._load_image()
        self._setup_button()
        self._setup_board_layout_button()
        self._setup_back_button()
        self._setup_next_button()
        self._update_positions()

    def _load_image(self) -> None:
        """Load the standard game mode image and extract its background color."""
        try:
            self.standard_image = pygame.image.load("standard.png")
            # Extract background color from the top-left corner pixel
            self.bg_color = self.standard_image.get_at((0, 0))[:3]  # Get RGB, ignore alpha
            self._scale_image()
        except (FileNotFoundError, pygame.error):
            # If image not found, we'll just show a placeholder
            pass

        try:
            self.german_daisy_image = pygame.image.load("GermanDaisy.png")
            self._scale_german_daisy_image()
        except (FileNotFoundError, pygame.error):
            # If image not found, we'll just show a placeholder
            pass

        try:
            self.belgian_daisy_image = pygame.image.load("BelgianDaisy.png")
            self._scale_belgian_daisy_image()
        except (FileNotFoundError, pygame.error):
            # If image not found, we'll just show a placeholder
            pass

    def _scale_image(self) -> None:
        """Scale the image to a consistent smaller size."""
        if not self.standard_image:
            return

        # Get image dimensions
        img_width, img_height = self.standard_image.get_size()

        # Scale to a smaller size (max 180x180) maintaining aspect ratio
        max_size = 180
        scale = min(max_size / img_width, max_size / img_height)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)

        self.scaled_image = pygame.transform.scale(
            self.standard_image,
            (new_width, new_height)
        )

        # Store image dimensions for dynamic positioning
        self.image_width = new_width
        self.image_height = new_height

    def _scale_german_daisy_image(self) -> None:
        """Scale the German Daisy image to match the standard image size."""
        if not self.german_daisy_image:
            return

        # Scale to the same size as the standard image
        self.scaled_german_daisy_image = pygame.transform.scale(
            self.german_daisy_image,
            (self.image_width, self.image_height)
        )

    def _scale_belgian_daisy_image(self) -> None:
        """Scale the Belgian Daisy image to match the standard image size."""
        if not self.belgian_daisy_image:
            return

        # Scale to the same size as the standard image
        self.scaled_belgian_daisy_image = pygame.transform.scale(
            self.belgian_daisy_image,
            (self.image_width, self.image_height)
        )

    def _update_positions(self) -> None:
        """Update positions based on current window size."""
        # Get current window dimensions
        window_w, window_h = self.screen.get_size()

        # Padding from edges for German Daisy image (increased to move it left and up)
        padding_right = 60  # Moved left from right edge
        padding_bottom = 120  # Moved up from bottom edge
        padding_left = 60  # Same padding for Belgian Daisy on the left

        # Position Standard image in the center of the page
        if self.scaled_image:
            self.image_x = (window_w - self.image_width) // 2
            self.image_y = (window_h - self.image_height) // 2 - 30  # Slight upward adjustment for button space

        # Position German Daisy image in the bottom right area (moved up and left)
        if self.scaled_german_daisy_image:
            self.german_daisy_x = window_w - self.scaled_german_daisy_image.get_width() - padding_right
            self.german_daisy_y = window_h - self.scaled_german_daisy_image.get_height() - padding_bottom

        # Position Belgian Daisy image in the bottom left area (mirror of German Daisy)
        if self.scaled_belgian_daisy_image:
            self.belgian_daisy_x = padding_left
            self.belgian_daisy_y = window_h - self.scaled_belgian_daisy_image.get_height() - padding_bottom

        # Update button positions - position them below their respective images
        if hasattr(self, 'button_rect'):
            # Standard button - centered below the standard image
            button_x = self.image_x + (self.image_width - self.button_rect.width) // 2
            button_y = self.image_y + self.image_height + 15  # 15px below the image
            self.button_rect.x = button_x
            self.button_rect.y = button_y
            self.button_text_rect.center = self.button_rect.center

            # Update "I Play As" text position at the bottom of the page
            if hasattr(self, 'i_play_as_text_rect'):
                window_w, window_h = self.screen.get_size()

                # Position circles near the bottom of the page
                circle_y = window_h - self.circle_radius - 40  # 40px from bottom

                # Position "I Play As" text above the circles
                self.i_play_as_text_rect.centerx = self.button_rect.centerx
                self.i_play_as_text_rect.bottom = circle_y - self.circle_radius - 15  # 15px above circles

                # Update circle positions
                if hasattr(self, 'black_circle_center'):
                    self.black_circle_center[0] = self.button_rect.centerx - self.circle_spacing // 2
                    self.black_circle_center[1] = circle_y
                if hasattr(self, 'white_circle_center'):
                    self.white_circle_center[0] = self.button_rect.centerx + self.circle_spacing // 2
                    self.white_circle_center[1] = circle_y

        if hasattr(self, 'german_daisy_button_rect'):
            # German Daisy button - centered below the German Daisy image
            if self.scaled_german_daisy_image:
                button_x = self.german_daisy_x + (self.scaled_german_daisy_image.get_width() - self.german_daisy_button_rect.width) // 2
                button_y = self.german_daisy_y + self.scaled_german_daisy_image.get_height() + 15  # 15px below the image
                self.german_daisy_button_rect.x = button_x
                self.german_daisy_button_rect.y = button_y
                self.german_daisy_button_text_rect.center = self.german_daisy_button_rect.center

        if hasattr(self, 'belgian_daisy_button_rect'):
            # Belgian Daisy button - centered below the Belgian Daisy image
            if self.scaled_belgian_daisy_image:
                button_x = self.belgian_daisy_x + (self.scaled_belgian_daisy_image.get_width() - self.belgian_daisy_button_rect.width) // 2
                button_y = self.belgian_daisy_y + self.scaled_belgian_daisy_image.get_height() + 15  # 15px below the image
                self.belgian_daisy_button_rect.x = button_x
                self.belgian_daisy_button_rect.y = button_y
                self.belgian_daisy_button_text_rect.center = self.belgian_daisy_button_rect.center

        if hasattr(self, 'board_layout_button_rect'):
            # Board Layout button - top center of the page
            window_w, window_h = self.screen.get_size()
            button_x = (window_w - self.board_layout_button_rect.width) // 2
            button_y = 30  # 30px from top
            self.board_layout_button_rect.x = button_x
            self.board_layout_button_rect.y = button_y
            self.board_layout_button_text_rect.center = self.board_layout_button_rect.center

        if hasattr(self, 'next_button_rect'):
            # Next button - top right of the page
            window_w, window_h = self.screen.get_size()
            button_x = window_w - self.next_button_rect.width - 30  # 30px from right
            button_y = 30  # 30px from top
            self.next_button_rect.x = button_x
            self.next_button_rect.y = button_y
            self.next_button_text_rect.center = self.next_button_rect.center

    def _setup_button(self) -> None:
        """Setup the 'Standard' and 'German Daisy' buttons below the images."""
        # Button properties - smaller size
        standard_button_width = 120
        german_daisy_button_width = 155  # Wider to fit "German Daisy" text comfortably
        belgian_daisy_button_width = 155  # Same width as German Daisy button
        button_height = 35

        # Position below the center (where the images will be)
        button_x = (WINDOW_W - standard_button_width) // 2  # Horizontally centered
        button_y = (WINDOW_H // 2) + 120  # Below the center, moved down

        # Create Standard button rectangle
        self.button_rect = pygame.Rect(button_x, button_y, standard_button_width, button_height)

        # Button colors - matching the Start button from landing page
        self.button_color = (120, 140, 110)  # Darker sage green
        self.button_hover_color = (140, 160, 130)  # Lighter sage green for hover
        self.button_text_color = (255, 255, 255)  # White
        self.current_button_color = self.button_color

        # Create button text with smaller font
        font = pygame.font.Font(None, 28)
        self.button_text = font.render("Standard", True, self.button_text_color)
        self.button_text_rect = self.button_text.get_rect(center=self.button_rect.center)

        # Create "I Play As" text below Standard button
        self.i_play_as_text = font.render("I Play As", True, (0, 0, 0))  # Black color
        # Position it below the Standard button (will be updated in _update_positions)
        self.i_play_as_text_rect = self.i_play_as_text.get_rect()
        self.i_play_as_text_rect.centerx = self.button_rect.centerx
        self.i_play_as_text_rect.top = self.button_rect.bottom + 20  # 20px below the button

        # Create circles below "I Play As" text
        self.circle_radius = 20  # Radius of the circles
        self.circle_spacing = 50  # Spacing between the two circles
        # Black circle (left)
        self.black_circle_center = [
            self.button_rect.centerx - self.circle_spacing // 2,
            self.i_play_as_text_rect.bottom + 30  # 30px below the text
        ]
        # White circle (right)
        self.white_circle_center = [
            self.button_rect.centerx + self.circle_spacing // 2,
            self.i_play_as_text_rect.bottom + 30  # 30px below the text
        ]

        # Create German Daisy button rectangle (wider than Standard)
        self.german_daisy_button_rect = pygame.Rect(button_x, button_y, german_daisy_button_width, button_height)
        self.current_german_daisy_button_color = self.button_color

        # Create German Daisy button text
        self.german_daisy_button_text = font.render("German Daisy", True, self.button_text_color)
        self.german_daisy_button_text_rect = self.german_daisy_button_text.get_rect(center=self.german_daisy_button_rect.center)

        # Create Belgian Daisy button rectangle (same width as German Daisy)
        self.belgian_daisy_button_rect = pygame.Rect(button_x, button_y, belgian_daisy_button_width, button_height)
        self.current_belgian_daisy_button_color = self.button_color

        # Create Belgian Daisy button text
        self.belgian_daisy_button_text = font.render("Belgian Daisy", True, self.button_text_color)
        self.belgian_daisy_button_text_rect = self.belgian_daisy_button_text.get_rect(center=self.belgian_daisy_button_rect.center)

    def _setup_board_layout_button(self) -> None:
        """Setup the 'Board Layout' button at the top of the page."""
        # Button properties
        button_width = 200
        button_height = 50

        # Position at the top center of the page
        button_x = (WINDOW_W - button_width) // 2  # Horizontally centered
        button_y = 30  # 30px from top

        # Create Board Layout button rectangle
        self.board_layout_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        self.current_board_layout_button_color = self.button_color

        # Create button text
        font = pygame.font.Font(None, 28)
        self.board_layout_button_text = font.render("Board Layout", True, self.button_text_color)
        self.board_layout_button_text_rect = self.board_layout_button_text.get_rect(center=self.board_layout_button_rect.center)

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

    def _setup_next_button(self) -> None:
        """Setup the 'Next' button at the top right of the page."""
        # Button properties
        button_width = 100
        button_height = 40

        # Position at the top right of the page
        button_x = WINDOW_W - button_width - 30  # 30px from right
        button_y = 30  # 30px from top

        # Create Next button rectangle
        self.next_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        self.current_next_button_color = self.button_color

        # Create button text
        font = pygame.font.Font(None, 28)
        self.next_button_text = font.render("Next", True, self.button_text_color)
        self.next_button_text_rect = self.next_button_text.get_rect(center=self.next_button_rect.center)

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
                # Check if Next button was clicked
                elif self.next_button_rect.collidepoint(event.pos):
                    # Only proceed if a board layout is selected and a color is chosen
                    if self.selected_board in ['standard', 'german', 'belgian'] and self.selected_color in ['black', 'white']:
                        self.next_requested = True
                # Check if Standard button was clicked
                elif self.button_rect.collidepoint(event.pos):
                    self.selected_board = 'standard'
                # Check if German Daisy button was clicked
                elif self.german_daisy_button_rect.collidepoint(event.pos):
                    self.selected_board = 'german'
                # Check if Belgian Daisy button was clicked
                elif self.belgian_daisy_button_rect.collidepoint(event.pos):
                    self.selected_board = 'belgian'
                # Check if black circle was clicked
                elif hasattr(self, 'black_circle_center'):
                    black_circle_rect = pygame.Rect(
                        self.black_circle_center[0] - self.circle_radius,
                        self.black_circle_center[1] - self.circle_radius,
                        self.circle_radius * 2,
                        self.circle_radius * 2
                    )
                    if black_circle_rect.collidepoint(event.pos):
                        # Check if click is actually within the circle
                        dx = event.pos[0] - self.black_circle_center[0]
                        dy = event.pos[1] - self.black_circle_center[1]
                        if dx*dx + dy*dy <= self.circle_radius * self.circle_radius:
                            self.selected_color = 'black'
                # Check if white circle was clicked
                if hasattr(self, 'white_circle_center'):
                    white_circle_rect = pygame.Rect(
                        self.white_circle_center[0] - self.circle_radius,
                        self.white_circle_center[1] - self.circle_radius,
                        self.circle_radius * 2,
                        self.circle_radius * 2
                    )
                    if white_circle_rect.collidepoint(event.pos):
                        # Check if click is actually within the circle
                        dx = event.pos[0] - self.white_circle_center[0]
                        dy = event.pos[1] - self.white_circle_center[1]
                        if dx*dx + dy*dy <= self.circle_radius * self.circle_radius:
                            self.selected_color = 'white'
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

        # Update button hover states
        mouse_pos = pygame.mouse.get_pos()

        # Standard button hover
        if self.button_rect.collidepoint(mouse_pos):
            self.current_button_color = self.button_hover_color
        else:
            self.current_button_color = self.button_color

        # German Daisy button hover
        if self.german_daisy_button_rect.collidepoint(mouse_pos):
            self.current_german_daisy_button_color = self.button_hover_color
        else:
            self.current_german_daisy_button_color = self.button_color

        # Belgian Daisy button hover
        if self.belgian_daisy_button_rect.collidepoint(mouse_pos):
            self.current_belgian_daisy_button_color = self.button_hover_color
        else:
            self.current_belgian_daisy_button_color = self.button_color

        # Board Layout button hover
        if self.board_layout_button_rect.collidepoint(mouse_pos):
            self.current_board_layout_button_color = self.button_hover_color
        else:
            self.current_board_layout_button_color = self.button_color

        # Back button hover
        if self.back_button_rect.collidepoint(mouse_pos):
            self.current_back_button_color = self.button_hover_color
        else:
            self.current_back_button_color = self.button_color

        # Next button hover
        if self.next_button_rect.collidepoint(mouse_pos):
            self.current_next_button_color = self.button_hover_color
        else:
            self.current_next_button_color = self.button_color

        return None  # Continue waiting

    def _draw(self) -> None:
        """Draw the game mode selection page."""
        # Fill background with color matching the standard.png image
        self.screen.fill(self.bg_color)

        # Draw the scaled standard image if available
        if self.scaled_image:
            self.screen.blit(self.scaled_image, (self.image_x, self.image_y))

        # Draw the scaled German Daisy image if available
        if self.scaled_german_daisy_image:
            self.screen.blit(self.scaled_german_daisy_image, (self.german_daisy_x, self.german_daisy_y))

        # Draw the scaled Belgian Daisy image if available
        if self.scaled_belgian_daisy_image:
            self.screen.blit(self.scaled_belgian_daisy_image, (self.belgian_daisy_x, self.belgian_daisy_y))

        # Draw the Standard button
        button_color = self.current_button_color
        button_border_width = 3
        button_border_color = (255, 255, 255)

        # Highlight if selected
        if self.selected_board == 'standard':
            button_border_width = 5
            button_border_color = (166, 112, 74)  # Brown color matching board rim

        pygame.draw.rect(self.screen, button_color, self.button_rect, border_radius=10)
        # Draw button border
        pygame.draw.rect(self.screen, button_border_color, self.button_rect, width=button_border_width, border_radius=10)
        # Draw button text
        self.screen.blit(self.button_text, self.button_text_rect)

        # Draw "I Play As" text below the Standard button
        if hasattr(self, 'i_play_as_text'):
            self.screen.blit(self.i_play_as_text, self.i_play_as_text_rect)

            # Draw the two circles below "I Play As" text
            if hasattr(self, 'black_circle_center'):
                # Draw black circle
                pygame.draw.circle(self.screen, (0, 0, 0), self.black_circle_center, self.circle_radius)
                # Draw border - highlight if selected
                border_color = (166, 112, 74) if self.selected_color == 'black' else (0, 0, 0)
                border_width = 4 if self.selected_color == 'black' else 2
                pygame.draw.circle(self.screen, border_color, self.black_circle_center, self.circle_radius, border_width)

            if hasattr(self, 'white_circle_center'):
                # Draw white circle
                pygame.draw.circle(self.screen, (255, 255, 255), self.white_circle_center, self.circle_radius)
                # Draw border - highlight if selected
                border_color = (166, 112, 74) if self.selected_color == 'white' else (0, 0, 0)
                border_width = 4 if self.selected_color == 'white' else 2
                pygame.draw.circle(self.screen, border_color, self.white_circle_center, self.circle_radius, border_width)

        # Draw the German Daisy button
        german_border_width = 3
        german_border_color = (255, 255, 255)

        # Highlight if selected
        if self.selected_board == 'german':
            german_border_width = 5
            german_border_color = (166, 112, 74)  # Brown color matching board rim

        pygame.draw.rect(self.screen, self.current_german_daisy_button_color, self.german_daisy_button_rect, border_radius=10)
        # Draw button border
        pygame.draw.rect(self.screen, german_border_color, self.german_daisy_button_rect, width=german_border_width, border_radius=10)
        # Draw button text
        self.screen.blit(self.german_daisy_button_text, self.german_daisy_button_text_rect)

        # Draw the Belgian Daisy button
        belgian_border_width = 3
        belgian_border_color = (255, 255, 255)

        # Highlight if selected
        if self.selected_board == 'belgian':
            belgian_border_width = 5
            belgian_border_color = (166, 112, 74)  # Brown color matching board rim

        pygame.draw.rect(self.screen, self.current_belgian_daisy_button_color, self.belgian_daisy_button_rect, border_radius=10)
        # Draw button border
        pygame.draw.rect(self.screen, belgian_border_color, self.belgian_daisy_button_rect, width=belgian_border_width, border_radius=10)
        # Draw button text
        self.screen.blit(self.belgian_daisy_button_text, self.belgian_daisy_button_text_rect)

        # Draw the Board Layout button
        pygame.draw.rect(self.screen, self.current_board_layout_button_color, self.board_layout_button_rect, border_radius=10)
        # Draw button border
        pygame.draw.rect(self.screen, (255, 255, 255), self.board_layout_button_rect, width=3, border_radius=10)
        # Draw button text
        self.screen.blit(self.board_layout_button_text, self.board_layout_button_text_rect)

        # Draw the Back button
        pygame.draw.rect(self.screen, self.current_back_button_color, self.back_button_rect, border_radius=10)
        # Draw button border
        pygame.draw.rect(self.screen, (255, 255, 255), self.back_button_rect, width=3, border_radius=10)
        # Draw button text
        self.screen.blit(self.back_button_text, self.back_button_text_rect)

        # Draw the Next button
        pygame.draw.rect(self.screen, self.current_next_button_color, self.next_button_rect, border_radius=10)
        # Draw button border
        pygame.draw.rect(self.screen, (255, 255, 255), self.next_button_rect, width=3, border_radius=10)
        # Draw button text
        self.screen.blit(self.next_button_text, self.next_button_text_rect)

        pygame.display.flip()

    def run(self) -> bool:
        """
        Run the game mode selection page.

        Returns:
            True if user wants to continue to the game, False if quit
        """
        while True:
            result = self._handle_events()
            if result is not None:
                return result

            # Check if back button was pressed
            if self.back_requested:
                return False  # Go back to game mode page

            # Check if next button was pressed with valid selections
            if self.next_requested:
                return True  # Proceed to board scene

            self._draw()
            self.clock.tick(FPS)

