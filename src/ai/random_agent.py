from __future__ import annotations

import random

from src.ai.agent_base import AgentBase
from src.game.game_state import GameState
from src.game.rules import Move, RulesEngine


class RandomAgent(AgentBase):
    def __init__(self, rules: RulesEngine) -> None:
        self._rules = rules

    @property
    def name(self) -> str:
        return "RandomAgent"

    def choose_move(self, state: GameState, time_limit_s: float) -> Move | None:
        moves = self._rules.legal_moves_simple(state)
        if not moves:
            return None
        return random.choice(moves)
