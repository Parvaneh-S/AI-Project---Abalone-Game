"""
Game application manager.
"""
import pygame
import math
from src.constants import WINDOW_W, WINDOW_H, BORDER_COLOR, BOARD_FILL
from src.ui.landing_page import LandingPage
from src.ui.game_mode_page import GameModePage
from src.ui.board_layout_page import GameModePage as BoardLayoutPage
from src.ui.board_scene import BoardScene

class GameApp:
    """
    Main game application that manages scenes and window.
    """

    def __init__(self):
        """Initialize the game application."""
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.RESIZABLE)
        pygame.display.set_caption("Abalone- Marble Masters")
        self.clock = pygame.time.Clock()

        self._set_window_icon()

    def _set_window_icon(self) -> None:
        """Set the window icon."""
        # Try to load icon from file, otherwise create programmatic one
        try:
            icon = pygame.image.load("icon.png")
            pygame.display.set_icon(icon)
        except (FileNotFoundError, pygame.error):
            try:
                icon = pygame.image.load("icon.jpg")
                pygame.display.set_icon(icon)
            except (FileNotFoundError, pygame.error):
                # Fall back to programmatic icon
                icon = self._create_icon()
                pygame.display.set_icon(icon)

    def _create_icon(self) -> pygame.Surface:
        """
        Create a simple hexagon icon for the window.

        Returns:
            Pygame surface containing the icon
        """
        icon_size = 32
        icon = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)

        # Create hexagon vertices for icon
        cx, cy = icon_size // 2, icon_size // 2
        radius = icon_size // 2 - 2

        cos30 = math.sqrt(3) / 2
        sin30 = 0.5

        hex_points = [
            (cx - radius * sin30, cy - radius * cos30),
            (cx + radius * sin30, cy - radius * cos30),
            (cx + radius, cy),
            (cx + radius * sin30, cy + radius * cos30),
            (cx - radius * sin30, cy + radius * cos30),
            (cx - radius, cy),
        ]

        # Draw brown hexagon border
        pygame.draw.polygon(icon, BORDER_COLOR, hex_points)
        # Draw smaller beige hexagon inside
        inner_points = [(cx + (p[0]-cx)*0.7, cy + (p[1]-cy)*0.7) for p in hex_points]
        pygame.draw.polygon(icon, BOARD_FILL, inner_points)

        return icon

    def run(self) -> None:
        """Run the game application."""
        # Main application loop to allow going back to landing page
        while True:
            # Show landing page first
            landing_page = LandingPage(self.screen, self.clock)
            if not landing_page.run():
                self.quit()
                return

            # Loop to allow going back from subsequent pages
            while True:
                # Show game mode page
                game_mode_page = GameModePage(self.screen, self.clock)
                game_mode_result = game_mode_page.run()

                # Check if user wants to go back to landing page
                if game_mode_page.back_requested:
                    break  # Break to outer loop to show landing page again

                if not game_mode_result:
                    self.quit()
                    return

                # Loop to allow going back from board scene to board layout page
                while True:
                    # Show board layout page
                    board_layout_page = BoardLayoutPage(self.screen, self.clock)
                    board_layout_result = board_layout_page.run()

                    # Check if user wants to go back to game mode page
                    if board_layout_page.back_requested:
                        break  # Break to show game mode page again

                    if not board_layout_result:
                        self.quit()
                        return

                    # Show board scene with inverted colors if white was selected
                    # For Belgian Daisy and German Daisy, color selection doesn't matter - always use black configuration
                    board_layout = board_layout_page.selected_board if board_layout_page.selected_board else 'standard'
                    if board_layout == 'standard':
                        invert_colors = board_layout_page.selected_color == 'white'
                    else:
                        # For Belgian Daisy and German Daisy, always use black configuration
                        invert_colors = False
                    board_scene = BoardScene(self.screen, self.clock, invert_colors=invert_colors, board_layout=board_layout)
                    board_scene.run()

                    # Check if user wants to go back
                    if not board_scene.go_back:
                        # User quit the application
                        self.quit()
                        return

    def quit(self) -> None:
        """Clean up and quit the application."""
        pygame.quit()

