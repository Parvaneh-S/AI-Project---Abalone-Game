"""
AI Agent for Abalone Game.

Currently implements a simple random move selection strategy.
This module is designed to be easily extended with more sophisticated
search strategies and heuristic functions later.
"""
from __future__ import annotations

import random
from typing import List, Optional, Tuple

from src.move_engine import (
    Board as EngineBoard,
    Player as EnginePlayer,
    Move,
    generate_moves,
)


class AIAgent:
    """AI agent that selects a legal move for the given board state.

    The default strategy is purely random.  Replace or subclass the
    ``select_move`` method to plug in minimax / alpha-beta / etc.
    """

    def __init__(self, player: EnginePlayer) -> None:
        """
        Args:
            player: The engine player character this agent controls ('b' or 'w').
        """
        self.player = player

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def select_move(
        self,
        board: EngineBoard,
        legal_moves: Optional[List[Tuple[Move, EngineBoard]]] = None,
    ) -> Optional[Tuple[Move, EngineBoard]]:
        """Pick a move to play.

        Args:
            board: Current board state (axial-coord dict).
            legal_moves: Pre-computed legal moves.  If *None* the agent
                         will generate them itself via ``generate_moves``.

        Returns:
            A ``(Move, new_board)`` tuple, or *None* when no legal move
            exists (should not happen in a normal game).
        """
        if legal_moves is None:
            legal_moves = generate_moves(self.player, board)

        if not legal_moves:
            return None

        # --- Strategy: pick a random legal move ---
        return random.choice(legal_moves)

