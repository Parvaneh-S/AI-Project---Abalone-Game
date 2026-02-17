from __future__ import annotations

from typing import List, Callable, Optional

import pygame

from src.constants import MARGIN, PANEL_W, SCREEN_H, SCREEN_W, WHITE
from src.game.history import HistoryManager
from src.game.timer import MoveTimer
from src.ui.widgets import Button, Dropdown, TextInput, Checkbox, draw_panel_bg, draw_text


class ConfigPanel:
    """Configuration panel for game settings."""

    def __init__(self, on_config_change: Optional[Callable] = None) -> None:
        self.rect = pygame.Rect(MARGIN, MARGIN, PANEL_W, 480)
        self.on_config_change = on_config_change

        x = self.rect.x + 16
        y = self.rect.y + 40
        w = self.rect.width - 32
        h = 32
        gap = 8

        # Board Layout Selection
        self.layout_dropdown = Dropdown(
            rect=pygame.Rect(x, y, w, h),
            options=["Standard", "German Daisy", "Belgian Daisy"],
            selected_index=0,
            on_change=self._notify_change
        )
        y += h + gap + 20

        # Game Mode Selection
        self.mode_dropdown = Dropdown(
            rect=pygame.Rect(x, y, w, h),
            options=["Human vs Computer", "Human vs Human", "Computer vs Computer"],
            selected_index=0,
            on_change=self._notify_change
        )
        y += h + gap + 20

        # Player Color Selection
        self.color_dropdown = Dropdown(
            rect=pygame.Rect(x, y, w, h),
            options=["BLACK", "WHITE"],
            selected_index=0,
            on_change=self._notify_change
        )
        y += h + gap + 20

        # Move Limit
        self.move_limit_enabled = Checkbox(
            rect=pygame.Rect(x, y, 20, 20),
            label="Enable Move Limit",
            checked=False,
            on_change=self._notify_change
        )
        y += 28 + gap

        self.move_limit_input = TextInput(
            rect=pygame.Rect(x, y, w // 2, h),
            value="50",
            placeholder="e.g., 50",
            numeric_only=True,
            on_change=self._notify_change
        )
        y += h + gap + 20

        # Time Limit Black
        self.time_limit_black_enabled = Checkbox(
            rect=pygame.Rect(x, y, 20, 20),
            label="BLACK Time Limit (s)",
            checked=False,
            on_change=self._notify_change
        )
        y += 28 + gap

        self.time_limit_black_input = TextInput(
            rect=pygame.Rect(x, y, w // 2, h),
            value="30.0",
            placeholder="e.g., 30.0",
            numeric_only=True,
            on_change=self._notify_change
        )
        y += h + gap + 20

        # Time Limit White
        self.time_limit_white_enabled = Checkbox(
            rect=pygame.Rect(x, y, 20, 20),
            label="WHITE Time Limit (s)",
            checked=False,
            on_change=self._notify_change
        )
        y += 28 + gap

        self.time_limit_white_input = TextInput(
            rect=pygame.Rect(x, y, w // 2, h),
            value="30.0",
            placeholder="e.g., 30.0",
            numeric_only=True,
            on_change=self._notify_change
        )

    def _notify_change(self, _=None) -> None:
        """Notify parent of configuration change."""
        if self.on_config_change:
            self.on_config_change()

    def get_config(self) -> dict:
        """Get current configuration as dictionary."""
        return {
            "layout": self.layout_dropdown.get_selected(),
            "mode": self.mode_dropdown.get_selected(),
            "human_color": self.color_dropdown.get_selected(),
            "move_limit": int(self.move_limit_input.value) if self.move_limit_enabled.checked and self.move_limit_input.value else None,
            "time_limit_black": float(self.time_limit_black_input.value) if self.time_limit_black_enabled.checked and self.time_limit_black_input.value else None,
            "time_limit_white": float(self.time_limit_white_input.value) if self.time_limit_white_enabled.checked and self.time_limit_white_input.value else None,
        }

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle events for all config widgets."""
        # Handle dropdowns first (they need priority for closing)
        if self.layout_dropdown.handle_event(event):
            return
        if self.mode_dropdown.handle_event(event):
            return
        if self.color_dropdown.handle_event(event):
            return

        # Handle other widgets
        self.move_limit_enabled.handle_event(event)
        self.move_limit_input.handle_event(event)
        self.time_limit_black_enabled.handle_event(event)
        self.time_limit_black_input.handle_event(event)
        self.time_limit_white_enabled.handle_event(event)
        self.time_limit_white_input.handle_event(event)

    def draw(self, screen: pygame.Surface, font: pygame.font.Font, title_font: pygame.font.Font) -> None:
        draw_panel_bg(screen, self.rect)

        x = self.rect.x + 16
        y = self.rect.y + 12

        y = draw_text(screen, title_font, "Configuration", x, y, WHITE)
        y += 4

        y = draw_text(screen, font, "Board Layout:", x, y)
        self.layout_dropdown.draw(screen, font)
        y = self.layout_dropdown.rect.bottom + 12

        y = draw_text(screen, font, "Game Mode:", x, y)
        self.mode_dropdown.draw(screen, font)
        y = self.mode_dropdown.rect.bottom + 12

        y = draw_text(screen, font, "Human Player Color:", x, y)
        self.color_dropdown.draw(screen, font)
        y = self.color_dropdown.rect.bottom + 12

        y = draw_text(screen, font, "Move Limit:", x, y)
        self.move_limit_enabled.draw(screen, font)
        self.move_limit_input.draw(screen, font)
        y = self.move_limit_input.rect.bottom + 12

        y = draw_text(screen, font, "Time Limits:", x, y)
        self.time_limit_black_enabled.draw(screen, font)
        self.time_limit_black_input.draw(screen, font)
        y = self.time_limit_black_input.rect.bottom + 8

        self.time_limit_white_enabled.draw(screen, font)
        self.time_limit_white_input.draw(screen, font)


class ControlsPanel:
    def __init__(self, on_start, on_pause, on_reset, on_undo, on_stop) -> None:
        self.rect = pygame.Rect(MARGIN, 520, PANEL_W, 220)
        self.buttons: List[Button] = []

        x = self.rect.x + 16
        y = self.rect.y + 40
        w = self.rect.width - 32
        h = 38
        gap = 10

        self.buttons.append(Button(pygame.Rect(x, y, w, h), "Start", on_start))
        y += h + gap
        self.buttons.append(Button(pygame.Rect(x, y, w, h), "Pause / Resume", on_pause))
        y += h + gap
        self.buttons.append(Button(pygame.Rect(x, y, w, h), "Reset", on_reset))
        y += h + gap
        self.buttons.append(Button(pygame.Rect(x, y, w, h), "Undo", on_undo))
        y += h + gap
        self.buttons.append(Button(pygame.Rect(x, y, w, h), "Stop", on_stop))

    def handle_event(self, event: pygame.event.Event) -> None:
        for b in self.buttons:
            b.handle_event(event)

    def draw(self, screen: pygame.Surface, font: pygame.font.Font, title_font: pygame.font.Font) -> None:
        draw_panel_bg(screen, self.rect)
        draw_text(screen, title_font, "Controls", self.rect.x + 16, self.rect.y + 12, WHITE)
        for b in self.buttons:
            b.draw(screen, font)


class HudPanel:
    def __init__(self) -> None:
        self.rect = pygame.Rect(SCREEN_W - PANEL_W - MARGIN, MARGIN, PANEL_W, SCREEN_H - MARGIN * 2)

    def draw(
        self,
        screen: pygame.Surface,
        font: pygame.font.Font,
        title_font: pygame.font.Font,
        state,
        history: HistoryManager,
        timer: MoveTimer,
        mode_text: str,
    ) -> None:
        draw_panel_bg(screen, self.rect)
        y = self.rect.y + 12
        x = self.rect.x + 16

        y = draw_text(screen, title_font, "Game Information", x, y, WHITE)
        y = draw_text(screen, font, f"Status: {state.status}", x, y)
        y = draw_text(screen, font, f"Mode: {mode_text}", x, y)
        y = draw_text(screen, font, f"Layout: {state.layout_name}", x, y)
        y = draw_text(screen, font, f"To move: {state.to_move}", x, y)

        y += 8
        y = draw_text(screen, title_font, "Score", x, y, WHITE)
        y = draw_text(screen, font, f"Black off-board: {state.score_black_off}", x, y)
        y = draw_text(screen, font, f"White off-board: {state.score_white_off}", x, y)

        y += 8
        y = draw_text(screen, title_font, "Moves Taken", x, y, WHITE)
        y = draw_text(screen, font, f"Black: {state.moves_black}", x, y)
        y = draw_text(screen, font, f"White: {state.moves_white}", x, y)

        # Show move limits if set
        if state.move_limit_per_player:
            y = draw_text(screen, font, f"Limit: {state.move_limit_per_player} per player", x, y)

        y += 8
        y = draw_text(screen, title_font, "Time Per Move (Agent)", x, y, WHITE)
        y = draw_text(screen, font, f"Total BLACK: {timer.total_time('BLACK'):.3f}s", x, y)
        y = draw_text(screen, font, f"Total WHITE: {timer.total_time('WHITE'):.3f}s", x, y)

        # Show time limits if set
        if state.time_limit_black:
            y = draw_text(screen, font, f"BLACK limit: {state.time_limit_black}s/move", x, y)
        if state.time_limit_white:
            y = draw_text(screen, font, f"WHITE limit: {state.time_limit_white}s/move", x, y)

        y = draw_text(screen, font, "Recent AI Moves:", x, y)
        for entry in timer.ai_history()[-5:][::-1]:
            y = draw_text(screen, font, f"  {entry.elapsed_s:.3f}s - {entry.move_text}", x, y)

        y += 8
        y = draw_text(screen, title_font, "Next AI Move", x, y, WHITE)
        y = draw_text(screen, font, state.next_ai_move_text, x, y)

        y += 8
        y = draw_text(screen, title_font, "Move History", x, y, WHITE)
        snaps = history.snapshots()[-10:][::-1]
        for s in snaps:
            time_str = f"({s.ai_time_s:.3f}s)" if s.ai_time_s else ""
            y = draw_text(screen, font, f"{s.move_text} {time_str}", x, y)
