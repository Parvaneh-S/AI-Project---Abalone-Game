"""
Game configuration page for the Abalone game - combines game mode and board layout selection.
"""
import pygame
from typing import Optional
from src.ui.constants import (
    WINDOW_W, WINDOW_H, FPS,
    LANDING_BG_COLOR
)


class GameModePage:
    """
    Unified game configuration page that displays game mode, board layout, and color selection.
    """

    def __init__(self, screen: pygame.Surface, clock: pygame.time.Clock):
        """
        Initialize the game configuration page.

        Args:
            screen: Pygame surface to draw on
            clock: Pygame clock for timing
        """
        self.screen = screen
        self.clock = clock
        self.bg_color = LANDING_BG_COLOR

        # Selection states
        self.selected_mode = None  # 0, 1, or 2 for game modes
        self.selected_board = None  # 'standard', 'german', or 'belgian'
        self.selected_color = None  # 'black' or 'white'

        # Player 1 settings
        self.player1_time = None  # 5, 10, or 15 seconds
        self.player1_move_limit = None  # 30, 40, or 50 moves

        # Player 2 settings
        self.player2_time = None  # 5, 10, or 15 seconds
        self.player2_move_limit = None  # 30, 40, or 50 moves

        self.back_requested = False
        self.next_requested = False

        # Dropdown menu states
        self.time_options = [5, 10, 15]
        self.move_limit_options = [30, 40, 50]

        # Load images
        self.standard_image: Optional[pygame.Surface] = None
        self.scaled_image: Optional[pygame.Surface] = None
        self.german_daisy_image: Optional[pygame.Surface] = None
        self.scaled_german_daisy_image: Optional[pygame.Surface] = None
        self.belgian_daisy_image: Optional[pygame.Surface] = None
        self.scaled_belgian_daisy_image: Optional[pygame.Surface] = None

        self._load_images()
        self._setup_title_button()
        self._setup_game_mode_buttons()
        self._setup_dropdown_menus()
        self._setup_board_buttons()
        self._setup_player_color_circles()
        self._setup_back_button()
        self._setup_next_button()
        self._update_positions()

    def _load_images(self) -> None:
        """Load board layout images."""
        try:
            self.standard_image = pygame.image.load("images/standard.png")
            self.bg_color = self.standard_image.get_at((0, 0))[:3]
            self._scale_image()
        except (FileNotFoundError, pygame.error):
            pass

        try:
            self.german_daisy_image = pygame.image.load("images/GermanDaisy.png")
            self._scale_german_daisy_image()
        except (FileNotFoundError, pygame.error):
            pass

        try:
            self.belgian_daisy_image = pygame.image.load("images/BelgianDaisy.png")
            self._scale_belgian_daisy_image()
        except (FileNotFoundError, pygame.error):
            pass

    def _scale_image(self) -> None:
        """Scale the standard board image for carousel display."""
        if not self.standard_image:
            return
        img_width, img_height = self.standard_image.get_size()
        # Scale to larger size for center display
        max_size = 200
        scale = min(max_size / img_width, max_size / img_height)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        self.scaled_image = pygame.transform.scale(self.standard_image, (new_width, new_height))
        self.image_width = new_width
        self.image_height = new_height

    def _scale_german_daisy_image(self) -> None:
        """Scale the German Daisy image."""
        if not self.german_daisy_image or not hasattr(self, 'image_width'):
            return
        self.scaled_german_daisy_image = pygame.transform.scale(
            self.german_daisy_image,
            (self.image_width, self.image_height)
        )

    def _scale_belgian_daisy_image(self) -> None:
        """Scale the Belgian Daisy image."""
        if not self.belgian_daisy_image or not hasattr(self, 'image_width'):
            return
        self.scaled_belgian_daisy_image = pygame.transform.scale(
            self.belgian_daisy_image,
            (self.image_width, self.image_height)
        )

    def _setup_title_button(self) -> None:
        """Setup the title button at the top."""
        button_width = 300
        button_height = 50
        button_x = (WINDOW_W - button_width) // 2
        button_y = 15

        self.title_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        self.title_button_color = (120, 140, 110)
        self.title_button_text_color = (255, 255, 255)

        font = pygame.font.Font(None, 36)
        self.title_button_text = font.render("Game Configuration", True, self.title_button_text_color)
        self.title_button_text_rect = self.title_button_text.get_rect(center=self.title_button_rect.center)

    def _setup_game_mode_buttons(self) -> None:
        """Setup the three game mode buttons."""
        button_width = 450
        button_height = 45
        button_spacing = 15

        total_height = (button_height * 3) + (button_spacing * 2)
        start_y = 90

        self.button_color = (120, 140, 110)
        self.button_hover_color = (140, 160, 130)
        self.button_text_color = (255, 255, 255)

        self.mode_buttons = []
        labels = [
            "Human vs AI",
            "AI vs AI",
            "Human vs Human"
        ]

        font = pygame.font.Font(None, 26)

        for i, label in enumerate(labels):
            button_x = (WINDOW_W - button_width) // 2
            button_y = start_y + (i * (button_height + button_spacing))

            button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
            button_text = font.render(label, True, self.button_text_color)
            button_text_rect = button_text.get_rect(center=button_rect.center)

            self.mode_buttons.append({
                'rect': button_rect,
                'text': button_text,
                'text_rect': button_text_rect,
                'current_color': self.button_color,
                'mode': i
            })

    def _setup_dropdown_menus(self) -> None:
        """Setup dropdown menus for time and move limit selection for both players."""
        # Dropdown dimensions
        self.dropdown_width = 120
        self.dropdown_height = 35
        self.dropdown_item_height = 35

        # Player labels
        font_large = pygame.font.Font(None, 28)
        self.player1_label = font_large.render("Player 1", True, (255, 255, 255))
        self.player2_label = font_large.render("Player 2", True, (255, 255, 255))

        # Player 1 dropdowns
        self.p1_time_dropdown_rect = pygame.Rect(0, 0, self.dropdown_width, self.dropdown_height)
        self.p1_move_limit_dropdown_rect = pygame.Rect(0, 0, self.dropdown_width, self.dropdown_height)
        self.p1_time_items = []
        self.p1_move_limit_items = []

        # Player 2 dropdowns
        self.p2_time_dropdown_rect = pygame.Rect(0, 0, self.dropdown_width, self.dropdown_height)
        self.p2_move_limit_dropdown_rect = pygame.Rect(0, 0, self.dropdown_width, self.dropdown_height)
        self.p2_time_items = []
        self.p2_move_limit_items = []

        # Font for dropdown items
        font_small = pygame.font.Font(None, 18)

        # Create Player 1 time dropdown items
        for time in self.time_options:
            item_rect = pygame.Rect(0, 0, self.dropdown_width, self.dropdown_item_height)
            item_text = font_small.render(f"{time}s", True, (255, 255, 255))
            self.p1_time_items.append({
                'rect': item_rect,
                'text': item_text,
                'value': time,
                'color': self.button_color
            })

        # Create Player 1 move limit dropdown items
        for limit in self.move_limit_options:
            item_rect = pygame.Rect(0, 0, self.dropdown_width, self.dropdown_item_height)
            item_text = font_small.render(f"{limit}", True, (255, 255, 255))
            self.p1_move_limit_items.append({
                'rect': item_rect,
                'text': item_text,
                'value': limit,
                'color': self.button_color
            })

        # Create Player 2 time dropdown items
        for time in self.time_options:
            item_rect = pygame.Rect(0, 0, self.dropdown_width, self.dropdown_item_height)
            item_text = font_small.render(f"{time}s", True, (255, 255, 255))
            self.p2_time_items.append({
                'rect': item_rect,
                'text': item_text,
                'value': time,
                'color': self.button_color
            })

        # Create Player 2 move limit dropdown items
        for limit in self.move_limit_options:
            item_rect = pygame.Rect(0, 0, self.dropdown_width, self.dropdown_item_height)
            item_text = font_small.render(f"{limit}", True, (255, 255, 255))
            self.p2_move_limit_items.append({
                'rect': item_rect,
                'text': item_text,
                'value': limit,
                'color': self.button_color
            })

    def _setup_board_buttons(self) -> None:
        """Setup the board layout selection with carousel display."""
        # Larger board display area in center
        self.board_display_width = 200
        self.board_display_height = 200
        self.board_display_y = 470

        # Board selection order: Standard (center), Belgian (left), German (right)
        self.board_order = ['standard', 'belgian', 'german']
        self.current_board_index = 0

        # Create rectangles for each board
        self.standard_button_rect = pygame.Rect(0, self.board_display_y, self.board_display_width, self.board_display_height)
        self.belgian_daisy_button_rect = pygame.Rect(0, self.board_display_y, self.board_display_width, self.board_display_height)
        self.german_daisy_button_rect = pygame.Rect(0, self.board_display_y, self.board_display_width, self.board_display_height)

        # Navigation arrows
        arrow_size = 40
        self.left_arrow_rect = pygame.Rect(20, self.board_display_y + self.board_display_height // 2 - arrow_size // 2,
                                          arrow_size, arrow_size)
        self.right_arrow_rect = pygame.Rect(WINDOW_W - arrow_size - 20,
                                           self.board_display_y + self.board_display_height // 2 - arrow_size // 2,
                                           arrow_size, arrow_size)

        # Selection buttons underneath the board display
        button_spacing = 30
        button_width = 140
        button_height = 45

        total_button_width = (button_width * 3) + (button_spacing * 2)
        button_start_x = (WINDOW_W - total_button_width) // 2
        button_y = self.board_display_y + self.board_display_height + 17

        self.board_buttons = [
            {
                'rect': pygame.Rect(button_start_x, button_y, button_width, button_height),
                'board': 'standard',
                'label': 'Standard',
                'current_color': self.button_color
            },
            {
                'rect': pygame.Rect(button_start_x + button_width + button_spacing, button_y, button_width, button_height),
                'board': 'belgian',
                'label': 'Belgian Daisy',
                'current_color': self.button_color
            },
            {
                'rect': pygame.Rect(button_start_x + (button_width + button_spacing) * 2, button_y, button_width, button_height),
                'board': 'german',
                'label': 'German Daisy',
                'current_color': self.button_color
            }
        ]

        # Label font
        font = pygame.font.Font(None, 24)
        self.button_labels = {}
        for button in self.board_buttons:
            self.button_labels[button['board']] = font.render(button['label'], True, (255, 255, 255))

    def _setup_player_color_circles(self) -> None:
        """Setup the player color selection circles."""
        self.circle_radius = 25
        self.circle_spacing = 80

        # Position below board buttons
        circle_y = 690
        center_x = WINDOW_W // 2

        self.black_circle_center = [center_x - self.circle_spacing // 2, circle_y]
        self.white_circle_center = [center_x + self.circle_spacing // 2, circle_y]

        # Label
        font = pygame.font.Font(None, 24)
        self.color_label_text = font.render("Your Color:", True, (0, 0, 0))
        self.color_label_rect = self.color_label_text.get_rect(
            center=(center_x, circle_y - 50)
        )

    def _setup_back_button(self) -> None:
        """Setup the Back button."""
        button_width = 100
        button_height = 40
        button_x = 30
        button_y = 30

        self.back_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        self.current_back_button_color = self.button_color

        font = pygame.font.Font(None, 28)
        self.back_button_text = font.render("Back", True, self.button_text_color)
        self.back_button_text_rect = self.back_button_text.get_rect(center=self.back_button_rect.center)

    def _setup_next_button(self) -> None:
        """Setup the Next button."""
        button_width = 100
        button_height = 40
        button_x = WINDOW_W - button_width - 30
        button_y = 30

        self.next_button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        self.current_next_button_color = self.button_color

        font = pygame.font.Font(None, 28)
        self.next_button_text = font.render("Next", True, self.button_text_color)
        self.next_button_text_rect = self.next_button_text.get_rect(center=self.next_button_rect.center)

    def _update_positions(self) -> None:
        """Update positions based on current window size."""
        # Get current window size
        window_w, window_h = self.screen.get_size()

        # Title position
        if hasattr(self, 'title_button_rect'):
            self.title_button_rect.centerx = window_w // 2
            self.title_button_text_rect.center = self.title_button_rect.center

        # Back and Next buttons
        self.back_button_rect.x = 30
        self.back_button_rect.y = 30
        self.back_button_text_rect.center = self.back_button_rect.center

        self.next_button_rect.x = window_w - self.next_button_rect.width - 30
        self.next_button_rect.y = 30
        self.next_button_text_rect.center = self.next_button_rect.center

        # Game mode buttons
        if hasattr(self, 'mode_buttons'):
            button_width = 450
            button_height = 45
            button_spacing = 15
            start_y = 90

            for i, button in enumerate(self.mode_buttons):
                button_x = (window_w - button_width) // 2
                button_y = start_y + (i * (button_height + button_spacing))
                button['rect'].x = button_x
                button['rect'].y = button_y
                button['text_rect'].center = button['rect'].center

        # Update dropdown menus position (appear below game mode buttons when selected)
        if self.selected_mode is not None and hasattr(self, 'p1_time_dropdown_rect'):
            # Position dropdown menus with simple, stable positioning
            dropdown_y = 280

            # Player 1 dropdowns - left side (side by side)
            p1_time_x = 80
            p1_move_limit_x = p1_time_x + self.dropdown_width + 20
            p1_dropdown_y = dropdown_y

            self.p1_time_dropdown_rect.x = p1_time_x
            self.p1_time_dropdown_rect.y = p1_dropdown_y

            self.p1_move_limit_dropdown_rect.x = p1_move_limit_x
            self.p1_move_limit_dropdown_rect.y = p1_dropdown_y

            # Update Player 1 dropdown item positions
            for i, item in enumerate(self.p1_time_items):
                item['rect'].x = self.p1_time_dropdown_rect.x
                item['rect'].y = self.p1_time_dropdown_rect.y + ((i + 1) * self.dropdown_item_height)

            for i, item in enumerate(self.p1_move_limit_items):
                item['rect'].x = self.p1_move_limit_dropdown_rect.x
                item['rect'].y = self.p1_move_limit_dropdown_rect.y + ((i + 1) * self.dropdown_item_height)

            # Player 2 dropdowns - right side (side by side)
            p2_move_limit_x = window_w - self.dropdown_width - 80
            p2_time_x = p2_move_limit_x - self.dropdown_width - 20
            p2_dropdown_y = dropdown_y

            self.p2_time_dropdown_rect.x = p2_time_x
            self.p2_time_dropdown_rect.y = p2_dropdown_y

            self.p2_move_limit_dropdown_rect.x = p2_move_limit_x
            self.p2_move_limit_dropdown_rect.y = p2_dropdown_y

            # Update Player 2 dropdown item positions
            for i, item in enumerate(self.p2_time_items):
                item['rect'].x = self.p2_time_dropdown_rect.x
                item['rect'].y = self.p2_time_dropdown_rect.y + ((i + 1) * self.dropdown_item_height)

            for i, item in enumerate(self.p2_move_limit_items):
                item['rect'].x = self.p2_move_limit_dropdown_rect.x
                item['rect'].y = self.p2_move_limit_dropdown_rect.y + ((i + 1) * self.dropdown_item_height)

        # Board images - centered in display area with larger size
        if hasattr(self, 'image_width'):
            board_center_x = window_w // 2
            board_center_y = 470

            # All three boards centered in same position (carousel style)
            self.standard_button_rect.centerx = board_center_x
            self.standard_button_rect.centery = board_center_y
            self.standard_button_rect.width = self.image_width
            self.standard_button_rect.height = self.image_height

            self.belgian_daisy_button_rect.centerx = board_center_x
            self.belgian_daisy_button_rect.centery = board_center_y
            self.belgian_daisy_button_rect.width = self.image_width
            self.belgian_daisy_button_rect.height = self.image_height

            self.german_daisy_button_rect.centerx = board_center_x
            self.german_daisy_button_rect.centery = board_center_y
            self.german_daisy_button_rect.width = self.image_width
            self.german_daisy_button_rect.height = self.image_height

            # Update arrow positions
            arrow_size = 40
            self.left_arrow_rect.centery = board_center_y
            self.left_arrow_rect.left = 20
            self.right_arrow_rect.centery = board_center_y
            self.right_arrow_rect.right = window_w - 20

            # Update button positions
            if hasattr(self, 'board_buttons'):
                button_spacing = 30
                button_width = 140
                button_height = 45
                total_button_width = (button_width * 3) + (button_spacing * 2)
                button_start_x = (window_w - total_button_width) // 2
                button_y = board_center_y + self.image_height // 2 + 17

                for i, button in enumerate(self.board_buttons):
                    button['rect'].x = button_start_x + (i * (button_width + button_spacing))
                    button['rect'].y = button_y

        # Color circles
        if hasattr(self, 'black_circle_center'):
            center_x = window_w // 2
            circle_y = 690
            self.black_circle_center[0] = center_x - self.circle_spacing // 2
            self.black_circle_center[1] = circle_y
            self.white_circle_center[0] = center_x + self.circle_spacing // 2
            self.white_circle_center[1] = circle_y
            self.color_label_rect.center = (center_x, circle_y - 50)

    def _handle_events(self) -> Optional[bool]:
        """Handle user input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.VIDEORESIZE:
                self._update_positions()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.back_button_rect.collidepoint(event.pos):
                    self.back_requested = True
                elif self.next_button_rect.collidepoint(event.pos):
                    if (self.selected_mode is not None and
                        self.player1_time is not None and
                        self.player1_move_limit is not None and
                        self.player2_time is not None and
                        self.player2_move_limit is not None and
                        self.selected_board in ['standard', 'german', 'belgian'] and
                        self.selected_color in ['black', 'white']):
                        self.next_requested = True
                # Check left arrow for carousel navigation (previous board)
                elif self.left_arrow_rect.collidepoint(event.pos):
                    if self.selected_board is None:
                        self.selected_board = 'german'
                    elif self.selected_board == 'standard':
                        self.selected_board = 'german'
                    elif self.selected_board == 'german':
                        self.selected_board = 'belgian'
                    elif self.selected_board == 'belgian':
                        self.selected_board = 'standard'
                # Check right arrow for carousel navigation (next board)
                elif self.right_arrow_rect.collidepoint(event.pos):
                    if self.selected_board is None:
                        self.selected_board = 'belgian'
                    elif self.selected_board == 'standard':
                        self.selected_board = 'belgian'
                    elif self.selected_board == 'belgian':
                        self.selected_board = 'german'
                    elif self.selected_board == 'german':
                        self.selected_board = 'standard'
                else:
                    # Check game mode buttons
                    for button in self.mode_buttons:
                        if button['rect'].collidepoint(event.pos):
                            self.selected_mode = button['mode']
                            break

                    # Check Player 1 dropdown items
                    if self.selected_mode is not None:
                        for item in self.p1_time_items:
                            if item['rect'].collidepoint(event.pos):
                                self.player1_time = item['value']
                                break

                        for item in self.p1_move_limit_items:
                            if item['rect'].collidepoint(event.pos):
                                self.player1_move_limit = item['value']
                                break

                        # Check Player 2 dropdown items
                        for item in self.p2_time_items:
                            if item['rect'].collidepoint(event.pos):
                                self.player2_time = item['value']
                                break

                        for item in self.p2_move_limit_items:
                            if item['rect'].collidepoint(event.pos):
                                self.player2_move_limit = item['value']
                                break

                    # Check board buttons (underneath the board display)
                    for button in self.board_buttons:
                        if button['rect'].collidepoint(event.pos):
                            self.selected_board = button['board']
                            break

                    # Check color circles
                    dx = event.pos[0] - self.black_circle_center[0]
                    dy = event.pos[1] - self.black_circle_center[1]
                    if dx*dx + dy*dy <= self.circle_radius * self.circle_radius:
                        self.selected_color = 'black'

                    dx = event.pos[0] - self.white_circle_center[0]
                    dy = event.pos[1] - self.white_circle_center[1]
                    if dx*dx + dy*dy <= self.circle_radius * self.circle_radius:
                        self.selected_color = 'white'

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False

        # Update hover states
        mouse_pos = pygame.mouse.get_pos()

        for button in self.mode_buttons:
            button['current_color'] = (
                self.button_hover_color if button['rect'].collidepoint(mouse_pos)
                else ((166, 112, 74) if self.selected_mode == button['mode'] else self.button_color)
            )

        for button in self.board_buttons:
            button['current_color'] = (
                self.button_hover_color if button['rect'].collidepoint(mouse_pos)
                else ((166, 112, 74) if self.selected_board == button['board'] else self.button_color)
            )

        self.current_back_button_color = (
            self.button_hover_color if self.back_button_rect.collidepoint(mouse_pos)
            else self.button_color
        )

        self.current_next_button_color = (
            self.button_hover_color if self.next_button_rect.collidepoint(mouse_pos)
            else self.button_color
        )

        return None

    def _draw(self) -> None:
        """Draw the game configuration page."""
        self.screen.fill(self.bg_color)

        # Draw title
        pygame.draw.rect(self.screen, self.title_button_color, self.title_button_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), self.title_button_rect, width=3, border_radius=10)
        self.screen.blit(self.title_button_text, self.title_button_text_rect)

        # Draw game mode buttons
        for button in self.mode_buttons:
            pygame.draw.rect(self.screen, button['current_color'], button['rect'], border_radius=10)
            pygame.draw.rect(self.screen, (255, 255, 255), button['rect'], width=3, border_radius=10)
            self.screen.blit(button['text'], button['text_rect'])

        # Draw dropdown menus if game mode is selected
        if self.selected_mode is not None:
            label_font = pygame.font.Font(None, 24)
            dropdown_label_font = pygame.font.Font(None, 16)

            # Determine player labels based on game mode
            if self.selected_mode == 0:  # Human vs AI
                player1_text = "Human"
                player2_text = "AI"
            elif self.selected_mode == 1:  # AI vs AI
                player1_text = "AI 1"
                player2_text = "AI 2"
            else:  # Human vs Human
                player1_text = "Human 1"
                player2_text = "Human 2"

            # ===== PLAYER 1 - LEFT SIDE =====
            # Player 1 label (dynamic based on game mode)
            p1_label = label_font.render(player1_text, True, (255, 255, 255))
            self.screen.blit(p1_label, (40, 250))

            # Player 1 Time dropdown
            pygame.draw.rect(self.screen, self.button_color, self.p1_time_dropdown_rect, border_radius=8)
            pygame.draw.rect(self.screen, (255, 255, 255), self.p1_time_dropdown_rect, width=2, border_radius=8)
            time_label = dropdown_label_font.render("Time", True, (255, 255, 255))
            self.screen.blit(time_label, (self.p1_time_dropdown_rect.centerx - time_label.get_width() // 2,
                                          self.p1_time_dropdown_rect.centery - time_label.get_height() // 2))

            # Player 1 Time items
            for item in self.p1_time_items:
                item_color = (166, 112, 74) if self.player1_time == item['value'] else self.button_color
                pygame.draw.rect(self.screen, item_color, item['rect'], border_radius=5)
                pygame.draw.rect(self.screen, (255, 255, 255), item['rect'], width=1, border_radius=5)
                self.screen.blit(item['text'], (item['rect'].centerx - item['text'].get_width() // 2,
                                               item['rect'].centery - item['text'].get_height() // 2))

            # Player 1 Move Limit dropdown
            pygame.draw.rect(self.screen, self.button_color, self.p1_move_limit_dropdown_rect, border_radius=8)
            pygame.draw.rect(self.screen, (255, 255, 255), self.p1_move_limit_dropdown_rect, width=2, border_radius=8)
            moves_label = dropdown_label_font.render("Moves", True, (255, 255, 255))
            self.screen.blit(moves_label, (self.p1_move_limit_dropdown_rect.centerx - moves_label.get_width() // 2,
                                           self.p1_move_limit_dropdown_rect.centery - moves_label.get_height() // 2))

            # Player 1 Move Limit items
            for item in self.p1_move_limit_items:
                item_color = (166, 112, 74) if self.player1_move_limit == item['value'] else self.button_color
                pygame.draw.rect(self.screen, item_color, item['rect'], border_radius=5)
                pygame.draw.rect(self.screen, (255, 255, 255), item['rect'], width=1, border_radius=5)
                self.screen.blit(item['text'], (item['rect'].centerx - item['text'].get_width() // 2,
                                               item['rect'].centery - item['text'].get_height() // 2))

            # ===== PLAYER 2 - RIGHT SIDE =====
            # Player 2 label (dynamic based on game mode)
            p2_label = label_font.render(player2_text, True, (255, 255, 255))
            self.screen.blit(p2_label, (self.screen.get_width() - 160, 250))

            # Player 2 Time dropdown
            pygame.draw.rect(self.screen, self.button_color, self.p2_time_dropdown_rect, border_radius=8)
            pygame.draw.rect(self.screen, (255, 255, 255), self.p2_time_dropdown_rect, width=2, border_radius=8)
            self.screen.blit(time_label, (self.p2_time_dropdown_rect.centerx - time_label.get_width() // 2,
                                          self.p2_time_dropdown_rect.centery - time_label.get_height() // 2))

            # Player 2 Time items
            for item in self.p2_time_items:
                item_color = (166, 112, 74) if self.player2_time == item['value'] else self.button_color
                pygame.draw.rect(self.screen, item_color, item['rect'], border_radius=5)
                pygame.draw.rect(self.screen, (255, 255, 255), item['rect'], width=1, border_radius=5)
                self.screen.blit(item['text'], (item['rect'].centerx - item['text'].get_width() // 2,
                                               item['rect'].centery - item['text'].get_height() // 2))

            # Player 2 Move Limit dropdown
            pygame.draw.rect(self.screen, self.button_color, self.p2_move_limit_dropdown_rect, border_radius=8)
            pygame.draw.rect(self.screen, (255, 255, 255), self.p2_move_limit_dropdown_rect, width=2, border_radius=8)
            self.screen.blit(moves_label, (self.p2_move_limit_dropdown_rect.centerx - moves_label.get_width() // 2,
                                           self.p2_move_limit_dropdown_rect.centery - moves_label.get_height() // 2))

            # Player 2 Move Limit items
            for item in self.p2_move_limit_items:
                item_color = (166, 112, 74) if self.player2_move_limit == item['value'] else self.button_color
                pygame.draw.rect(self.screen, item_color, item['rect'], border_radius=5)
                pygame.draw.rect(self.screen, (255, 255, 255), item['rect'], width=1, border_radius=5)
                self.screen.blit(item['text'], (item['rect'].centerx - item['text'].get_width() // 2,
                                               item['rect'].centery - item['text'].get_height() // 2))

        # Draw navigation arrows
        # Left arrow
        pygame.draw.rect(self.screen, (200, 200, 200), self.left_arrow_rect, border_radius=5)
        self.screen.blit(self._render_left_arrow(), (self.left_arrow_rect.x + 8, self.left_arrow_rect.y + 8))

        # Right arrow
        pygame.draw.rect(self.screen, (200, 200, 200), self.right_arrow_rect, border_radius=5)
        self.screen.blit(self._render_right_arrow(), (self.right_arrow_rect.x + 8, self.right_arrow_rect.y + 8))

        # Draw center board image (carousel style - only show one at a time, centered)
        if self.selected_board == 'standard' or self.selected_board is None:
            if self.scaled_image:
                self.screen.blit(self.scaled_image, (self.standard_button_rect.x, self.standard_button_rect.y))
            border_color = (166, 112, 74)
            pygame.draw.rect(self.screen, border_color, self.standard_button_rect, width=5, border_radius=10)
        elif self.selected_board == 'belgian':
            if self.scaled_belgian_daisy_image:
                self.screen.blit(self.scaled_belgian_daisy_image, (self.belgian_daisy_button_rect.x, self.belgian_daisy_button_rect.y))
            border_color = (166, 112, 74)
            pygame.draw.rect(self.screen, border_color, self.belgian_daisy_button_rect, width=5, border_radius=10)
        elif self.selected_board == 'german':
            if self.scaled_german_daisy_image:
                self.screen.blit(self.scaled_german_daisy_image, (self.german_daisy_button_rect.x, self.german_daisy_button_rect.y))
            border_color = (166, 112, 74)
            pygame.draw.rect(self.screen, border_color, self.german_daisy_button_rect, width=5, border_radius=10)

        # Draw selection buttons underneath
        for button in self.board_buttons:
            pygame.draw.rect(self.screen, button['current_color'], button['rect'], border_radius=8)
            pygame.draw.rect(self.screen, (255, 255, 255), button['rect'], width=2, border_radius=8)
            self.screen.blit(self.button_labels[button['board']],
                           (button['rect'].centerx - self.button_labels[button['board']].get_width() // 2,
                            button['rect'].centery - self.button_labels[button['board']].get_height() // 2))

        # Draw color label
        self.screen.blit(self.color_label_text, self.color_label_rect)

        # Draw color circles
        pygame.draw.circle(self.screen, (0, 0, 0), self.black_circle_center, self.circle_radius)
        border_color = (166, 112, 74) if self.selected_color == 'black' else (0, 0, 0)
        border_width = 4 if self.selected_color == 'black' else 2
        pygame.draw.circle(self.screen, border_color, self.black_circle_center, self.circle_radius, border_width)

        pygame.draw.circle(self.screen, (255, 255, 255), self.white_circle_center, self.circle_radius)
        border_color = (166, 112, 74) if self.selected_color == 'white' else (0, 0, 0)
        border_width = 4 if self.selected_color == 'white' else 2
        pygame.draw.circle(self.screen, border_color, self.white_circle_center, self.circle_radius, border_width)

        # Draw Back button
        pygame.draw.rect(self.screen, self.current_back_button_color, self.back_button_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), self.back_button_rect, width=3, border_radius=10)
        self.screen.blit(self.back_button_text, self.back_button_text_rect)

        # Draw Next button
        pygame.draw.rect(self.screen, self.current_next_button_color, self.next_button_rect, border_radius=10)
        pygame.draw.rect(self.screen, (255, 255, 255), self.next_button_rect, width=3, border_radius=10)
        self.screen.blit(self.next_button_text, self.next_button_text_rect)

        pygame.display.flip()

    def _render_left_arrow(self) -> pygame.Surface:
        """Render a left arrow symbol."""
        arrow = pygame.Surface((24, 24), pygame.SRCALPHA)
        arrow.fill((0, 0, 0, 0))
        pygame.draw.polygon(arrow, (50, 50, 50), [(18, 6), (6, 12), (18, 18)])
        return arrow

    def _render_right_arrow(self) -> pygame.Surface:
        """Render a right arrow symbol."""
        arrow = pygame.Surface((24, 24), pygame.SRCALPHA)
        arrow.fill((0, 0, 0, 0))
        pygame.draw.polygon(arrow, (50, 50, 50), [(6, 6), (18, 12), (6, 18)])
        return arrow

    def run(self) -> bool:
        """Run the game configuration page."""
        while True:
            result = self._handle_events()
            if result is not None:
                return result

            if self.back_requested:
                return False

            if self.next_requested:
                return True

            # Update positions every frame to make the page responsive
            self._update_positions()
            self._draw()
            self.clock.tick(FPS)

