from __future__ import annotations
import math
import time
from typing import List, Optional, Tuple, Dict
from src.logic.move_engine import (
    Board as EngineBoard,
    Player as EnginePlayer,
    Cell,
    Move,
    CELLS as ALL_CELLS,
    DIRS,
    cell_add,
    opponent,
    generate_moves,
)
# TT Constants
TT_EXACT = 0
TT_LOWER = 1
TT_UPPER = 2
class TranspositionTable:
    def __init__(self):
        self.table: Dict[int, Tuple[int, float, int, Optional[Move]]] = {}
    def store(self, key: int, depth: int, score: float, bound: int, best_move: Optional[Move]):
        self.table[key] = (depth, score, bound, best_move)
    def lookup(self, key: int) -> Optional[Tuple[int, float, int, Optional[Move]]]:
        return self.table.get(key)
    def clear(self):
        self.table.clear()
def get_board_hash(board: EngineBoard, player: EnginePlayer) -> int:
    return hash(frozenset(board.items())) ^ hash(player)
def _manhattan_from_centre(cell: Cell) -> int:
    q, r = cell
    return (abs(q) + abs(r) + abs(q + r)) // 2
def _is_edge_cell(cell: Cell) -> bool:
    return _manhattan_from_centre(cell) == 4
def count_marbles(board: EngineBoard, player: EnginePlayer) -> int:
    return sum(1 for v in board.values() if v == player)
def detect_phase(my_marbles: int, opp_marbles: int) -> str:
    total = my_marbles + opp_marbles
    if total >= 26:
        return "opening"
    if total <= 18 or my_marbles <= 10 or opp_marbles <= 10:
        return "endgame"
    return "middlegame"
def calculate_cohesion_and_center(board: EngineBoard, player: EnginePlayer) -> Tuple[int, int]:
    cohesion = 0
    center_dist = 0
    for cell, colour in board.items():
        if colour == player:
            center_dist += _manhattan_from_centre(cell)
            for delta in DIRS.values():
                nb = cell_add(cell, delta)
                if board.get(nb) == player:
                    cohesion += 1
    return cohesion, center_dist
def count_threats_and_exposure(board: EngineBoard, player: EnginePlayer) -> Tuple[int, int]:
    opp = opponent(player)
    threats = 0
    exposure = 0
    for dnum, delta in DIRS.items():
        for cell, colour in board.items():
            if colour != player:
                continue
            next1 = cell_add(cell, delta)
            if board.get(next1) != player:
                continue
            next2 = cell_add(next1, delta)
            if board.get(next2) == opp:
                beyond = cell_add(next2, delta)
                if beyond not in ALL_CELLS:
                    threats += 1
            if board.get(next2) != player:
                continue
            next3 = cell_add(next2, delta)
            if board.get(next3) == opp:
                beyond3 = cell_add(next3, delta)
                if beyond3 not in ALL_CELLS:
                    threats += 1
    # Edge exposure: penalize pieces strictly on the outer rim
    for cell, colour in board.items():
        if colour == player and _is_edge_cell(cell):
            exposure += 1
    return threats, exposure
def evaluate(board: EngineBoard, player: EnginePlayer) -> float:
    opp = opponent(player)
    my_marbles = count_marbles(board, player)
    opp_marbles = count_marbles(board, opp)
    phase = detect_phase(my_marbles, opp_marbles)
    my_cohesion, my_center_dist = calculate_cohesion_and_center(board, player)
    opp_cohesion, opp_center_dist = calculate_cohesion_and_center(board, opp)
    my_threats, my_exposure = count_threats_and_exposure(board, player)
    opp_threats, opp_exposure = count_threats_and_exposure(board, opp)
    marble_diff = my_marbles - opp_marbles
    center_score = opp_center_dist - my_center_dist       # Positive means we are closer to center
    cohesion_score = my_cohesion - opp_cohesion           # Positive means we have better clusters
    threat_score = my_threats - opp_threats               # Positive means we have more push-off threats
    exposure_score = opp_exposure - my_exposure           # Positive means opponent has more exposed edge pieces
    # Phase-dependent weights
    if phase == "opening":
        w_marble = 1000
        w_center = 8
        w_cohesion = 5
        w_threat = 5
        w_exposure = 3
    elif phase == "middlegame":
        w_marble = 1000
        w_center = 5
        w_cohesion = 4
        w_threat = 15
        w_exposure = 8
    else: # endgame
        w_marble = 1500
        w_center = 2
        w_cohesion = 2
        w_threat = 20
        w_exposure = 15
    score = (
        w_marble * marble_diff +
        w_center * center_score +
        w_cohesion * cohesion_score +
        w_threat * threat_score +
        w_exposure * exposure_score
    )
    return score
class _SearchTimeout(Exception):
    pass
class AIAgent:
    def __init__(self, player: EnginePlayer, max_depth: int = 20, time_limit: float = 9.5) -> None:
        self.player = player
        self.max_depth = max_depth
        self.time_limit = time_limit
        self._deadline: float = 0.0
        self.tt = TranspositionTable()
        self.history_heuristic: Dict[Tuple[Move, int], float] = {}
    def _check_time(self) -> None:
        if time.perf_counter() >= self._deadline:
            raise _SearchTimeout
    def _move_sort_key(self, move: Move, new_board: EngineBoard, player: EnginePlayer, current_board: EngineBoard, tt_best_move: Optional[Move]) -> float:
        score = 0.0
        # 1. PV Move (Transposition Table best move)
        if tt_best_move and move == tt_best_move:
            score += 100000.0 
        # 2. Capture evaluation
        opp_old = count_marbles(current_board, opponent(player))
        opp_new = count_marbles(new_board, opponent(player))
        capture = opp_old - opp_new
        if capture > 0:
            score += 10000.0 * capture
        # 3. History Heuristic (moves that caused beta cutoffs in the past)
        hh_val = self.history_heuristic.get((move, 1 if player == self.player else -1), 0.0)
        score += hh_val / 100.0
        # 4. Inline/Push preference vs Side-step
        if move.kind == "i":
            score += 10.0
        return -score  # Return negative because we sort ascending
    def select_move(
        self,
        board: EngineBoard,
        legal_moves: Optional[List[Tuple[Move, EngineBoard]]] = None,
        **kwargs
    ) -> Optional[Tuple[Move, EngineBoard]]:
        if legal_moves is None:
            legal_moves = generate_moves(self.player, board)
        if not legal_moves:
            return None
        if len(legal_moves) == 1:
            return legal_moves[0]
        # Phase-based adaptive time budget
        my_marbles = count_marbles(board, self.player)
        opp_marbles = count_marbles(board, opponent(self.player))
        phase = detect_phase(my_marbles, opp_marbles)
        start_time = time.perf_counter()
        # Adaptive time budgeting
        if phase == "opening":
            self._deadline = start_time + min(3.0, self.time_limit)
        elif len(legal_moves) < 15: # Simple positions with reduced mobility
            self._deadline = start_time + min(4.0, self.time_limit)
        else:
            self._deadline = start_time + min(self.time_limit, 9.2)
        best_move = legal_moves[0]
        self.tt.clear() # Clear table per move to manage memory
        # Iterative Deepening
        for depth in range(1, self.max_depth + 1):
            try:
                candidate = self._search_root(board, legal_moves, depth)
                if candidate is not None:
                    best_move = candidate
            except _SearchTimeout:
                # Time limit exceeded, return best move from the *previous fully completed* depth.
                break
            # If we're really close to the deadline, do not even risk starting a new depth
            if time.perf_counter() >= self._deadline - 0.5:
                break
        return best_move
    def _search_root(
        self,
        board: EngineBoard,
        legal_moves: List[Tuple[Move, EngineBoard]],
        depth: int,
    ) -> Optional[Tuple[Move, EngineBoard]]:
        best_score = -math.inf
        best_move: Optional[Tuple[Move, EngineBoard]] = None
        alpha = -math.inf
        beta = math.inf
        h = get_board_hash(board, self.player)
        tt_entry = self.tt.lookup(h)
        tt_best_move = tt_entry[3] if tt_entry else None
        # Custom Move Ordering
        legal_moves.sort(key=lambda m: self._move_sort_key(m[0], m[1], self.player, board, tt_best_move))
        for move, new_board in legal_moves:
            self._check_time()
            score = self._minimax(new_board, depth - 1, alpha, beta, False)
            if score > best_score:
                best_score = score
                best_move = (move, new_board)
            alpha = max(alpha, score)
        if best_move:
            self.tt.store(h, depth, best_score, TT_EXACT, best_move[0])
        return best_move
    def _minimax(
        self,
        board: EngineBoard,
        depth: int,
        alpha: float,
        beta: float,
        is_maximising: bool,
    ) -> float:
        self._check_time()
        current_player = self.player if is_maximising else opponent(self.player)
        h = get_board_hash(board, current_player)
        tt_entry = self.tt.lookup(h)
        tt_best_move = None
        if tt_entry:
            tt_depth, tt_score, tt_bound, tt_best_move = tt_entry
            if tt_depth >= depth:
                if tt_bound == TT_EXACT: return tt_score
                elif tt_bound == TT_LOWER and tt_score > alpha: alpha = tt_score
                elif tt_bound == TT_UPPER and tt_score < beta: beta = tt_score
                if alpha >= beta: return tt_score
        if depth == 0:
            return evaluate(board, self.player)
        moves = generate_moves(current_player, board)
        if not moves: # Terminal state check
            return -100000.0 if is_maximising else 100000.0
        moves.sort(key=lambda m: self._move_sort_key(m[0], m[1], current_player, board, tt_best_move))
        orig_alpha = alpha
        best_move_obj = None
        if is_maximising:
            max_eval = -math.inf
            for move, new_board in moves:
                score = self._minimax(new_board, depth - 1, alpha, beta, False)
                if score > max_eval:
                    max_eval = score
                    best_move_obj = move
                alpha = max(alpha, score)
                if beta <= alpha: # Beta cutoff
                    hh_key = (move, 1)
                    self.history_heuristic[hh_key] = self.history_heuristic.get(hh_key, 0.0) + float(depth * depth)
                    break
            bound = TT_EXACT
            if max_eval <= orig_alpha: bound = TT_UPPER
            elif max_eval >= beta: bound = TT_LOWER
            self.tt.store(h, depth, max_eval, bound, best_move_obj)
            return max_eval
        else: # Minimising
            min_eval = math.inf
            for move, new_board in moves:
                score = self._minimax(new_board, depth - 1, alpha, beta, True)
                if score < min_eval:
                    min_eval = score
                    best_move_obj = move
                beta = min(beta, score)
                if beta <= alpha: # Alpha cutoff
                    hh_key = (move, -1)
                    self.history_heuristic[hh_key] = self.history_heuristic.get(hh_key, 0.0) + float(depth * depth)
                    break
            bound = TT_EXACT
            if min_eval <= orig_alpha: bound = TT_UPPER
            elif min_eval >= beta: bound = TT_LOWER
            self.tt.store(h, depth, min_eval, bound, best_move_obj)
            return min_eval
