from __future__ import annotations

import pygame

from src.constants import FPS, SCREEN_H, SCREEN_W
from src.ui.scene import GameScene


class App:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("Abalone - Marble Masters")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("consolas", 18)
        self.title_font = pygame.font.SysFont("consolas", 22, bold=True)

        self.scene = GameScene()
        self.running = True

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break
                self.scene.handle_event(event)

            self.scene.update(dt)
            self.scene.draw(self.screen, self.font, self.title_font)
            pygame.display.flip()

        pygame.quit()
