from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Tuple

Player = Literal["BLACK", "WHITE"]
Piece = Literal["B", "W"]
Coord = Tuple[int, int]  # axial (q, r)


@dataclass
class GameState:
    board: Dict[Coord, Piece | None]
    to_move: Player
    status: Literal["STOPPED", "RUNNING", "PAUSED", "GAMEOVER"]
    score_black_off: int
    score_white_off: int
    moves_black: int
    moves_white: int
    next_ai_move_text: str = "N/A"

    # Configuration
    layout_name: str = "Standard"
    game_mode: str = "Human vs Computer"
    human_color: str = "BLACK"
    move_limit_per_player: int | None = None  # None = unlimited
    time_limit_black: float | None = None  # seconds per move, None = unlimited
    time_limit_white: float | None = None  # seconds per move, None = unlimited

    def clone(self) -> "GameState":
        return GameState(
            board=dict(self.board),
            to_move=self.to_move,
            status=self.status,
            score_black_off=self.score_black_off,
            score_white_off=self.score_white_off,
            moves_black=self.moves_black,
            moves_white=self.moves_white,
            next_ai_move_text=self.next_ai_move_text,
            layout_name=self.layout_name,
            game_mode=self.game_mode,
            human_color=self.human_color,
            move_limit_per_player=self.move_limit_per_player,
            time_limit_black=self.time_limit_black,
            time_limit_white=self.time_limit_white,
        )

    def switch_player(self) -> None:
        self.to_move = "WHITE" if self.to_move == "BLACK" else "BLACK"

    def bump_move_count(self) -> None:
        if self.to_move == "BLACK":
            self.moves_black += 1
        else:
            self.moves_white += 1
