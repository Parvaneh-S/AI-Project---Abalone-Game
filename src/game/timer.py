from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Literal

Player = Literal["BLACK", "WHITE"]


@dataclass
class AiTimingEntry:
    move_text: str
    elapsed_s: float


class MoveTimer:
    def __init__(self) -> None:
        self._turn_start: float | None = None
        self._current_player: Player | None = None
        self._total: Dict[Player, float] = {"BLACK": 0.0, "WHITE": 0.0}
        self._ai_history: List[AiTimingEntry] = []

    def start_turn(self, player: Player) -> None:
        self._current_player = player
        self._turn_start = time.perf_counter()

    def stop_turn(self) -> float:
        if self._turn_start is None or self._current_player is None:
            return 0.0
        elapsed = time.perf_counter() - self._turn_start
        self._total[self._current_player] += elapsed
        self._turn_start = None
        self._current_player = None
        return elapsed

    def total_time(self, player: Player) -> float:
        return self._total[player]

    def add_ai_entry(self, move_text: str, elapsed_s: float) -> None:
        self._ai_history.append(AiTimingEntry(move_text=move_text, elapsed_s=elapsed_s))

    def ai_history(self) -> List[AiTimingEntry]:
        return list(self._ai_history)

    def reset(self) -> None:
        self._turn_start = None
        self._current_player = None
        self._total = {"BLACK": 0.0, "WHITE": 0.0}
        self._ai_history.clear()
