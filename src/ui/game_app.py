"""
Game application manager.
"""
from __future__ import annotations
import pygame

from src.ui.constants import WINDOW_W, WINDOW_H
from src.ui.landing_page import LandingPage
from src.ui.board_layout_page import GameModePage
from src.ui.board_scene import BoardScene


class GameApp:

    def __init__(self):
        pygame.init()

        self.screen = pygame.display.set_mode(
            (WINDOW_W, WINDOW_H),
            pygame.RESIZABLE
        )

        pygame.display.set_caption("Abalone - Marble Masters")
        self.clock = pygame.time.Clock()

        self._set_window_icon()

    def _set_window_icon(self) -> None:
        try:
            icon = pygame.image.load("images/icon.png")
            pygame.display.set_icon(icon)

        except (FileNotFoundError, pygame.error):
            try:
                icon = pygame.image.load("images/icon.jpg")
                pygame.display.set_icon(icon)

            except (FileNotFoundError, pygame.error):
                pass

    async def run(self) -> None:

        while True:

            # Landing page
            landing_page = LandingPage(
                self.screen,
                self.clock
            )

            if not await landing_page.run():
                self.quit()
                return

            while True:

                # Configuration page
                config_page = GameModePage(
                    self.screen,
                    self.clock
                )

                config_result = await config_page.run()

                if config_page.back_requested:
                    break

                if not config_result:
                    self.quit()
                    return

                board_layout = (
                    config_page.selected_board
                    if config_page.selected_board
                    else "standard"
                )

                invert_colors = (
                    config_page.selected_color == "white"
                )

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

                await board_scene.run()

                if not board_scene.go_back:
                    self.quit()
                    return

    def quit(self) -> None:
        pygame.quit()
