from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple, Literal, Optional

from .game_state import GameState, Player, Coord

Piece = Literal["B", "W"]


@dataclass(frozen=True)
class Move:
    src: Coord
    dst: Coord

    def to_text(self) -> str:
        return f"{self.src} -> {self.dst}"


class RulesEngine:
    # 6 axial directions
    DIRS: list[Coord] = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]

    def is_adjacent(self, a: Coord, b: Coord) -> bool:
        dq = b[0] - a[0]
        dr = b[1] - a[1]
        return (dq, dr) in self.DIRS

    def piece_for_player(self, player: Player) -> Piece:
        return "B" if player == "BLACK" else "W"

    def legal_moves_simple(self, state: GameState) -> List[Move]:
        """Deliverable-1 placeholder: single-step moves only (no pushing)."""
        moves: list[Move] = []
        piece = self.piece_for_player(state.to_move)

        for src, p in state.board.items():
            if p != piece:
                continue
            for dq, dr in self.DIRS:
                dst = (src[0] + dq, src[1] + dr)
                if dst in state.board and state.board[dst] is None:
                    moves.append(Move(src=src, dst=dst))
        return moves

    def apply_move_simple(self, state: GameState, move: Move) -> bool:
        """Returns True if move applied."""
        if move.src not in state.board or move.dst not in state.board:
            return False
        if state.board[move.dst] is not None:
            return False
        piece = self.piece_for_player(state.to_move)
        if state.board[move.src] != piece:
            return False
        if not self.is_adjacent(move.src, move.dst):
            return False

        state.board[move.src] = None
        state.board[move.dst] = piece
        state.bump_move_count()
        state.switch_player()
        return True
