from __future__ import annotations

from abc import ABC, abstractmethod

from src.game.game_state import GameState
from src.game.rules import Move


class AgentBase(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def choose_move(self, state: GameState, time_limit_s: float) -> Move | None:
        raise NotImplementedError
