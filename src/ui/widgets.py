from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional, Tuple, List

import pygame

from src.constants import DARK, LIGHT, PANEL_BG, WHITE, GRAY


@dataclass
class Button:
    rect: pygame.Rect
    text: str
    on_click: Callable[[], None]
    enabled: bool = True

    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.enabled:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        color = LIGHT if self.enabled else (80, 80, 80)
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, DARK, self.rect, width=2, border_radius=10)

        label = font.render(self.text, True, (10, 10, 10))
        label_rect = label.get_rect(center=self.rect.center)
        screen.blit(label, label_rect)


@dataclass
class Dropdown:
    rect: pygame.Rect
    options: List[str]
    selected_index: int = 0
    is_open: bool = False
    on_change: Optional[Callable[[str], None]] = None

    def get_selected(self) -> str:
        return self.options[self.selected_index] if self.options else ""

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True if event was handled."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.is_open = not self.is_open
                return True
            elif self.is_open:
                # Check if clicking on dropdown options
                for i, option in enumerate(self.options):
                    option_rect = pygame.Rect(
                        self.rect.x,
                        self.rect.y + self.rect.height * (i + 1),
                        self.rect.width,
                        self.rect.height
                    )
                    if option_rect.collidepoint(event.pos):
                        self.selected_index = i
                        self.is_open = False
                        if self.on_change:
                            self.on_change(self.get_selected())
                        return True
                self.is_open = False
        return False

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        # Main dropdown box
        pygame.draw.rect(screen, WHITE, self.rect, border_radius=6)
        pygame.draw.rect(screen, DARK, self.rect, width=2, border_radius=6)

        # Selected text
        text = font.render(self.get_selected(), True, DARK)
        text_rect = text.get_rect(midleft=(self.rect.x + 8, self.rect.centery))
        screen.blit(text, text_rect)

        # Arrow
        arrow = "▼" if not self.is_open else "▲"
        arrow_surf = font.render(arrow, True, DARK)
        arrow_rect = arrow_surf.get_rect(midright=(self.rect.right - 8, self.rect.centery))
        screen.blit(arrow_surf, arrow_rect)

        # Draw options if open
        if self.is_open:
            for i, option in enumerate(self.options):
                option_rect = pygame.Rect(
                    self.rect.x,
                    self.rect.y + self.rect.height * (i + 1),
                    self.rect.width,
                    self.rect.height
                )
                color = LIGHT if i == self.selected_index else WHITE
                pygame.draw.rect(screen, color, option_rect)
                pygame.draw.rect(screen, DARK, option_rect, width=1)

                text = font.render(option, True, DARK)
                text_rect = text.get_rect(midleft=(option_rect.x + 8, option_rect.centery))
                screen.blit(text, text_rect)


@dataclass
class TextInput:
    rect: pygame.Rect
    value: str = ""
    placeholder: str = ""
    active: bool = False
    numeric_only: bool = False
    on_change: Optional[Callable[[str], None]] = None

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True if event was handled."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            was_active = self.active
            self.active = self.rect.collidepoint(event.pos)
            return was_active or self.active

        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.active = False
                if self.on_change:
                    self.on_change(self.value)
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.value = self.value[:-1]
                return True
            elif event.unicode:
                if self.numeric_only:
                    if event.unicode.isdigit() or (event.unicode == '.' and '.' not in self.value):
                        self.value += event.unicode
                        return True
                else:
                    self.value += event.unicode
                    return True
        return False

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        color = WHITE if self.active else LIGHT
        pygame.draw.rect(screen, color, self.rect, border_radius=6)
        border_color = (100, 150, 255) if self.active else DARK
        pygame.draw.rect(screen, border_color, self.rect, width=2, border_radius=6)

        display_text = self.value if self.value else self.placeholder
        text_color = DARK if self.value else GRAY
        text = font.render(display_text, True, text_color)
        text_rect = text.get_rect(midleft=(self.rect.x + 8, self.rect.centery))

        # Clip text to rect
        screen.set_clip(self.rect)
        screen.blit(text, text_rect)
        screen.set_clip(None)


@dataclass
class Checkbox:
    rect: pygame.Rect
    label: str
    checked: bool = False
    on_change: Optional[Callable[[bool], None]] = None

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True if event was handled."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Create larger clickable area including label
            click_rect = pygame.Rect(self.rect.x, self.rect.y, self.rect.width + 200, self.rect.height)
            if click_rect.collidepoint(event.pos):
                self.checked = not self.checked
                if self.on_change:
                    self.on_change(self.checked)
                return True
        return False

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        # Checkbox box
        box_size = 20
        box_rect = pygame.Rect(self.rect.x, self.rect.y, box_size, box_size)
        pygame.draw.rect(screen, WHITE, box_rect, border_radius=4)
        pygame.draw.rect(screen, DARK, box_rect, width=2, border_radius=4)

        # Checkmark
        if self.checked:
            pygame.draw.line(screen, DARK,
                           (box_rect.x + 4, box_rect.centery),
                           (box_rect.centerx, box_rect.bottom - 4), 3)
            pygame.draw.line(screen, DARK,
                           (box_rect.centerx, box_rect.bottom - 4),
                           (box_rect.right - 4, box_rect.y + 4), 3)

        # Label
        text = font.render(self.label, True, WHITE)
        text_rect = text.get_rect(midleft=(box_rect.right + 10, box_rect.centery))
        screen.blit(text, text_rect)


@dataclass
class Label:
    text: str
    x: int
    y: int
    color: Tuple[int, int, int] = WHITE
    bold: bool = False

    def draw(self, screen: pygame.Surface, font: pygame.font.Font) -> int:
        """Returns the y position after drawing."""
        text_surf = font.render(self.text, True, self.color)
        screen.blit(text_surf, (self.x, self.y))
        return self.y + text_surf.get_height() + 4


def draw_panel_bg(screen: pygame.Surface, rect: pygame.Rect) -> None:
    pygame.draw.rect(screen, PANEL_BG, rect, border_radius=14)
    pygame.draw.rect(screen, (60, 65, 80), rect, width=2, border_radius=14)


def draw_text(
    screen: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    x: int,
    y: int,
    color: Tuple[int, int, int] = WHITE,
) -> int:
    img = font.render(text, True, color)
    screen.blit(img, (x, y))
    return y + img.get_height() + 4
