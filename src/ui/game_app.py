"""
Game application manager.
"""
import pygame
from src.ui.constants import WINDOW_W, WINDOW_H
from src.ui.landing_page import LandingPage
from src.ui.board_layout_page import GameModePage
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

        try:
            icon = pygame.image.load("images/icon.png")
            pygame.display.set_icon(icon)
        except (FileNotFoundError, pygame.error):
            try:
                icon = pygame.image.load("images/icon.jpg")
                pygame.display.set_icon(icon)
            except (FileNotFoundError, pygame.error):
                pass  # No icon available


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
                # Show unified game configuration page (game mode + board layout + color selection)
                config_page = GameModePage(self.screen, self.clock)
                config_result = config_page.run()

                # Check if user wants to go back to landing page
                if config_page.back_requested:
                    break  # Break to outer loop to show landing page again

                if not config_result:
                    self.quit()
                    return

                # Show board scene with the selected configuration
                board_layout = config_page.selected_board if config_page.selected_board else 'standard'
                # Use the selected color for all board layouts
                invert_colors = config_page.selected_color == 'white'

                board_scene = BoardScene(
                    self.screen,
                    self.clock,
                    invert_colors=invert_colors,
                    board_layout=board_layout,
                    game_mode=config_page.selected_mode,
                    player1_time=config_page.player1_time,
                    player2_time=config_page.player2_time,
                    move_limit=config_page.move_limit
                )
                board_scene.run()

                # Check if user wants to go back
                if not board_scene.go_back:
                    # User quit the application
                    self.quit()
                    return

    def quit(self) -> None:
        """Clean up and quit the application."""
        pygame.quit()



