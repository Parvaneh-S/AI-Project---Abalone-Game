from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .game_state import GameState


@dataclass
class Snapshot:
    state: GameState
    move_text: str
    ai_time_s: float | None


class HistoryManager:
    def __init__(self) -> None:
        self._stack: List[Snapshot] = []

    def push(self, snapshot: Snapshot) -> None:
        self._stack.append(snapshot)

    def can_undo(self) -> bool:
        return len(self._stack) > 0

    def undo(self) -> Snapshot | None:
        if not self._stack:
            return None
        return self._stack.pop()

    def clear(self) -> None:
        self._stack.clear()

    def snapshots(self) -> List[Snapshot]:
        return list(self._stack)
