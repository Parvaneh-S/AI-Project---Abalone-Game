from __future__ import annotations
import math
import time
import random
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

# Zobrist Hashing Setup
random.seed(42)
ZOBRIST = {}
for q in range(-4, 5):
    for r in range(-4, 5):
        if abs(q) <= 4 and abs(r) <= 4 and abs(q + r) <= 4:
            cell = (q, r)
            ZOBRIST[(cell, 'b')] = random.getrandbits(64)
            ZOBRIST[(cell, 'w')] = random.getrandbits(64)
ZOBRIST_PLAYER_W = random.getrandbits(64)

def get_board_hash(board: EngineBoard, player: EnginePlayer) -> int:
    h = 0
    for cell, color in board.items():
        h ^= ZOBRIST[(cell, color)]
    if player == 'w':
        h ^= ZOBRIST_PLAYER_W
    return h

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

    my_marbles = 0
    opp_marbles = 0
    my_center_dist = 0
    opp_center_dist = 0
    my_cohesion = 0
    opp_cohesion = 0
    my_exposure = 0
    opp_exposure = 0
    my_threats = 0
    opp_threats = 0

    # Pre-cache ALL_CELLS for faster lookup
    all_cells = ALL_CELLS

    # Single pass over the board
    for cell, colour in board.items():
        is_my = (colour == player)
        if is_my:
            my_marbles += 1
            my_center_dist += _manhattan_from_centre(cell)
            if _is_edge_cell(cell):
                my_exposure += 1
        else:
            opp_marbles += 1
            opp_center_dist += _manhattan_from_centre(cell)
            if _is_edge_cell(cell):
                opp_exposure += 1

        # Cohesion & Threats in the same pass
        for dnum, delta in DIRS.items():
            next1 = cell_add(cell, delta)
            next1_color = board.get(next1)

            # Cohesion
            if next1_color == colour:
                if is_my:
                    my_cohesion += 1
                else:
                    opp_cohesion += 1

            # Threats (only check if we are pushing opponent)
            if is_my and next1_color == opp:
                next2 = cell_add(next1, delta)
                if board.get(next2) == opp:
                    beyond = cell_add(next2, delta)
                    if beyond not in all_cells:
                        my_threats += 1
                elif board.get(next2) == colour:
                    pass # Not a straightforward push
            elif not is_my and next1_color == player:
                next2 = cell_add(next1, delta)
                if board.get(next2) == player:
                    beyond = cell_add(next2, delta)
                    if beyond not in all_cells:
                        opp_threats += 1

    phase = detect_phase(my_marbles, opp_marbles)

    marble_diff = my_marbles - opp_marbles
    center_score = opp_center_dist - my_center_dist
    cohesion_score = my_cohesion - opp_cohesion
    threat_score = my_threats - opp_threats
    exposure_score = opp_exposure - my_exposure

    # Phase-dependent weights
    if phase == "opening":
        w_marble, w_center, w_cohesion, w_threat, w_exposure = 1000, 8, 5, 5, 3
    elif phase == "middlegame":
        w_marble, w_center, w_cohesion, w_threat, w_exposure = 1000, 5, 4, 15, 8
    else: # endgame
        w_marble, w_center, w_cohesion, w_threat, w_exposure = 1500, 2, 2, 20, 15

    if my_marbles <= 8:
        return -99999.0
    if opp_marbles <= 8:
        return 99999.0

    return float(
        w_marble * marble_diff +
        w_center * center_score +
        w_cohesion * cohesion_score +
        w_threat * threat_score +
        w_exposure * exposure_score
    )

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
        self.killer_moves: Dict[int, List[Move]] = {}

    def _check_time(self) -> None:
        if time.perf_counter() >= self._deadline:
            raise _SearchTimeout
    def _move_sort_key(self, move: Move, new_board: EngineBoard, player: EnginePlayer, current_board: EngineBoard, tt_best_move: Optional[Move], depth: int) -> float:
        score = 0.0
        # 1. PV Move (Transposition Table best move)
        if tt_best_move and move == tt_best_move:
            score += 100000.0 

        # 2. Capture evaluation
        opp_old = sum(1 for v in current_board.values() if v == opponent(player))
        opp_new = sum(1 for v in new_board.values() if v == opponent(player))
        capture = opp_old - opp_new
        if capture > 0:
            score += 10000.0 * capture

        # 3. Killer Moves
        killers = self.killer_moves.get(depth, [])
        if move in killers:
            score += 5000.0

        # 4. History Heuristic
        hh_val = self.history_heuristic.get((move, 1 if player == self.player else -1), 0.0)
        score += hh_val / 100.0

        # 5. Inline preference
        if move.kind == "i":
            score += 10.0
        return -score
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
        self.killer_moves.clear()

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
        legal_moves.sort(key=lambda m: self._move_sort_key(m[0], m[1], self.player, board, tt_best_move, depth))

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
        if not moves:
            return -100000.0 if is_maximising else 100000.0

        moves.sort(key=lambda m: self._move_sort_key(m[0], m[1], current_player, board, tt_best_move, depth))

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
                if beta <= alpha:
                    # Beta cutoff - store killer move
                    if depth not in self.killer_moves: self.killer_moves[depth] = []
                    if move not in self.killer_moves[depth]:
                        self.killer_moves[depth].insert(0, move)
                        if len(self.killer_moves[depth]) > 2:
                            self.killer_moves[depth].pop()

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
                if beta <= alpha:
                    # Alpha cutoff - store killer move
                    if depth not in self.killer_moves: self.killer_moves[depth] = []
                    if move not in self.killer_moves[depth]:
                        self.killer_moves[depth].insert(0, move)
                        if len(self.killer_moves[depth]) > 2:
                            self.killer_moves[depth].pop()

                    hh_key = (move, -1)
                    self.history_heuristic[hh_key] = self.history_heuristic.get(hh_key, 0.0) + float(depth * depth)
                    break
            bound = TT_EXACT
            if min_eval <= orig_alpha: bound = TT_UPPER
            elif min_eval >= beta: bound = TT_LOWER
            self.tt.store(h, depth, min_eval, bound, best_move_obj)
            return min_eval
