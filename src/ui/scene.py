from __future__ import annotations

import time
from typing import Optional, Tuple

import pygame

from src.ai.random_agent import RandomAgent
from src.constants import BG
from src.game.game_state import GameState
from src.game.history import HistoryManager, Snapshot
from src.game.layouts import get_layout_by_name
from src.game.rules import Move, RulesEngine
from src.game.timer import MoveTimer
from src.ui.board_renderer import BoardRenderer
from src.ui.panels import ConfigPanel, ControlsPanel, HudPanel


class GameScene:
    def __init__(self) -> None:
        self.rules = RulesEngine()
        self.board_renderer = BoardRenderer()

        self.history = HistoryManager()
        self.timer = MoveTimer()

        self.mode = "Human vs Computer"
        self.human_player = "BLACK"
        self.ai_player = "WHITE"
        self.ai = RandomAgent(self.rules)

        self.state = self._new_state()

        # UI Panels
        self.config_panel = ConfigPanel(on_config_change=self._on_config_change)
        self.controls = ControlsPanel(
            on_start=self.start,
            on_pause=self.pause_resume,
            on_reset=self.reset,
            on_undo=self.undo,
            on_stop=self.stop,
        )
        self.hud = HudPanel()

        # Interaction state
        self.selected: Tuple[int, int] | None = None
        self.hover: Tuple[int, int] | None = None
        self.dragging: Tuple[int, int] | None = None  # Cell being dragged
        self.drag_pos: Tuple[int, int] | None = None  # Current mouse position during drag

        self._ai_think_delay_until: float = 0.0  # small delay so UI feels responsive

    def _new_state(self) -> GameState:
        config = self.config_panel.get_config() if hasattr(self, 'config_panel') else {}
        return GameState(
            board=get_layout_by_name(config.get("layout", "Standard")),
            to_move="BLACK",
            status="STOPPED",
            score_black_off=0,
            score_white_off=0,
            moves_black=0,
            moves_white=0,
            next_ai_move_text="N/A",
            layout_name=config.get("layout", "Standard"),
            game_mode=config.get("mode", "Human vs Computer"),
            human_color=config.get("human_color", "BLACK"),
            move_limit_per_player=config.get("move_limit"),
            time_limit_black=config.get("time_limit_black"),
            time_limit_white=config.get("time_limit_white"),
        )

    def _on_config_change(self) -> None:
        """Handle configuration changes."""
        config = self.config_panel.get_config()

        # Update game mode and player colors
        self.mode = config.get("mode", "Human vs Computer")
        self.human_player = config.get("human_color", "BLACK")
        self.ai_player = "WHITE" if self.human_player == "BLACK" else "BLACK"

        # If game is stopped, update state with new config
        if self.state.status == "STOPPED":
            self.state = self._new_state()

    # -------- control actions --------
    def start(self) -> None:
        if self.state.status == "STOPPED":
            self.state.status = "RUNNING"
            self.timer.reset()
            self.history.clear()
            self.selected = None
            self.dragging = None
            self.state.next_ai_move_text = "N/A"

    def pause_resume(self) -> None:
        if self.state.status == "RUNNING":
            self.state.status = "PAUSED"
        elif self.state.status == "PAUSED":
            self.state.status = "RUNNING"

    def reset(self) -> None:
        self.state = self._new_state()
        self.timer.reset()
        self.history.clear()
        self.selected = None
        self.dragging = None

    def stop(self) -> None:
        self.state.status = "STOPPED"
        self.selected = None
        self.dragging = None

    def undo(self) -> None:
        snap = self.history.undo()
        if snap is None:
            return
        self.state = snap.state.clone()
        self.selected = None
        self.dragging = None

    # -------- input / update / draw --------
    def handle_event(self, event: pygame.event.Event) -> None:
        # Config panel gets first priority
        self.config_panel.handle_event(event)
        self.controls.handle_event(event)

        if event.type == pygame.MOUSEMOTION:
            self.hover = self.board_renderer.pixel_to_cell(event.pos, self.state.board)

            # Update drag position
            if self.dragging is not None:
                self.drag_pos = event.pos

        if self.state.status != "RUNNING":
            return

        # Only human can interact
        if self.mode == "Human vs Computer" and self.state.to_move != self.human_player:
            return

        # Handle drag and drop
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            cell = self.board_renderer.pixel_to_cell(event.pos, self.state.board)
            if cell is None:
                return

            piece = self.state.board.get(cell)
            want = "B" if self.state.to_move == "BLACK" else "W"

            if piece == want:
                # Start dragging
                self.dragging = cell
                self.selected = cell
                self.drag_pos = event.pos
                return

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.dragging is not None:
                # Try to complete the move
                dst_cell = self.board_renderer.pixel_to_cell(event.pos, self.state.board)
                if dst_cell is not None and dst_cell != self.dragging:
                    move = Move(src=self.dragging, dst=dst_cell)
                    before = self.state.clone()

                    if self.rules.apply_move_simple(self.state, move):
                        self.history.push(Snapshot(before, f"HUMAN {move.to_text()}", None))
                        self.selected = None
                        # schedule AI thinking soon
                        self._ai_think_delay_until = time.perf_counter() + 0.15

                # End dragging
                self.dragging = None
                self.drag_pos = None
                return

        # Original click-to-move support (if not dragging)
        if self.dragging is None and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            cell = self.board_renderer.pixel_to_cell(event.pos, self.state.board)
            if cell is None:
                return

            piece = self.state.board.get(cell)
            if self.selected is None:
                # select own marble
                want = "B" if self.state.to_move == "BLACK" else "W"
                if piece == want:
                    self.selected = cell
                return

            # second click: attempt move
            move = Move(src=self.selected, dst=cell)
            before = self.state.clone()
            if self.rules.apply_move_simple(self.state, move):
                self.history.push(Snapshot(before, f"HUMAN {move.to_text()}", None))
                self.selected = None
                # schedule AI thinking soon
                self._ai_think_delay_until = time.perf_counter() + 0.15
            else:
                # if click another own marble, switch selection
                want = "B" if before.to_move == "BLACK" else "W"
                if piece == want:
                    self.selected = cell
                else:
                    self.selected = None

    def update(self, dt: float) -> None:
        if self.state.status != "RUNNING":
            return

        # Check move limit
        if self.state.move_limit_per_player:
            if (self.state.moves_black >= self.state.move_limit_per_player or
                self.state.moves_white >= self.state.move_limit_per_player):
                self.state.status = "GAMEOVER"
                return

        # AI turn
        if self.mode == "Human vs Computer" and self.state.to_move == self.ai_player:
            now = time.perf_counter()
            if now < self._ai_think_delay_until:
                return

            # show a "next move" suggestion before applying
            time_limit = None
            if self.ai_player == "BLACK" and self.state.time_limit_black:
                time_limit = self.state.time_limit_black
            elif self.ai_player == "WHITE" and self.state.time_limit_white:
                time_limit = self.state.time_limit_white
            else:
                time_limit = 1.0

            suggested = self.ai.choose_move(self.state.clone(), time_limit_s=time_limit)
            self.state.next_ai_move_text = suggested.to_text() if suggested else "No legal moves"

            if suggested is None:
                self.state.status = "GAMEOVER"
                return

            before = self.state.clone()
            self.timer.start_turn(self.ai_player)
            applied = self.rules.apply_move_simple(self.state, suggested)
            elapsed = self.timer.stop_turn()

            if applied:
                self.timer.add_ai_entry(suggested.to_text(), elapsed)
                self.history.push(Snapshot(before, f"AI({self.ai.name}) {suggested.to_text()}", elapsed))
            else:
                # should not happen if move was legal; treat as game over
                self.state.status = "GAMEOVER"

    def draw(self, screen: pygame.Surface, font, title_font) -> None:
        screen.fill(BG)

        self.board_renderer.draw(
            screen,
            board=self.state.board,
            selected=self.selected,
            hover=self.hover,
            dragging=self.dragging,
            drag_pos=self.drag_pos,
        )

        self.config_panel.draw(screen, font, title_font)
        self.controls.draw(screen, font, title_font)
        self.hud.draw(screen, font, title_font, self.state, self.history, self.timer, self.mode)
