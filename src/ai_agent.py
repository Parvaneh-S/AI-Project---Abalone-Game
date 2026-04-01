"""
AI Agent for Abalone Game.

Implements an iterative-deepening minimax search with alpha-beta pruning
and a multi-factor heuristic evaluation function for intelligent move
selection.  A configurable time budget ensures the agent always returns
a move before the clock expires.
"""
from __future__ import annotations

import math
import time
from typing import List, Optional, Tuple

from src.move_engine import (
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

# ---------------------------------------------------------------------------
# Heuristic weights – tuned for Abalone
# ---------------------------------------------------------------------------
_W_MARBLE_COUNT = 100      # Marble advantage (most important)
_W_CENTER_DIST  = -5       # Penalty per unit of Manhattan-distance from centre
_W_COHESION     = 3        # Reward per friendly-neighbour pair
_W_THREAT       = 8        # Bonus per opponent marble that can be pushed off
_W_EDGE_PENALTY = -4       # Penalty for own marbles sitting on the rim

# ---------------------------------------------------------------------------
# Endgame-awareness weights
# ---------------------------------------------------------------------------
_W_ENDGAME_SCORE_LEAD = 30   # Bonus per marble-diff unit when few moves remain
_W_TIME_ADVANTAGE     = 10   # Bonus when we have used less total time than opponent
_ENDGAME_MOVES_THRESHOLD = 8 # Remaining-moves count that activates endgame strategy

# ---------------------------------------------------------------------------
# Time-management constants
# ---------------------------------------------------------------------------
_OPENING_MARBLE_COUNT = 14        # Each side starts with 14 marbles
_OPENING_TIME_FRACTION = 0.25     # Use only 25% of time limit for opening moves
_FEW_MOVES_THRESHOLD = 10         # Positions with fewer moves are "simple"
_FEW_MOVES_TIME_FRACTION = 0.50   # Use 50% of time limit for simple positions
_DOMINANCE_THRESHOLD = 150        # Score gap to consider a move clearly dominant
_STABLE_DEPTH_COUNT = 3           # Consecutive depths with same best move → stop


def _is_opening_position(board: EngineBoard) -> bool:
    """Return True when no captures have occurred yet (both sides have 14).

    This covers the very first moves regardless of the starting layout
    (Standard, German Daisy, Belgian Daisy).
    """
    black = sum(1 for v in board.values() if v == 'b')
    white = sum(1 for v in board.values() if v == 'w')
    return black == _OPENING_MARBLE_COUNT and white == _OPENING_MARBLE_COUNT


def _manhattan_from_centre(cell: Cell) -> int:
    """Hex-grid Manhattan distance from the board centre (0, 0)."""
    q, r = cell
    return (abs(q) + abs(r) + abs(q + r)) // 2


def _is_edge_cell(cell: Cell) -> bool:
    """Return True if *cell* is on the outermost ring of the board."""
    return _manhattan_from_centre(cell) == 4  # RADIUS == 4


def _count_friendly_neighbours(board: EngineBoard, player: EnginePlayer) -> int:
    """Count the total number of adjacent same-colour pairs for *player*."""
    count = 0
    for cell, colour in board.items():
        if colour != player:
            continue
        for delta in DIRS.values():
            nb = cell_add(cell, delta)
            if board.get(nb) == player:
                count += 1
    # Each pair is counted twice (once from each end), but since we only
    # compare relative scores the factor-of-two cancels out.
    return count


def _count_threats(board: EngineBoard, player: EnginePlayer) -> int:
    """Estimate how many opponent marbles *player* can push off the board.

    A quick, cheap heuristic: look for 3-v-1 and 2-v-1 inline
    configurations where the opponent marble would be pushed off the edge.
    """
    opp = opponent(player)
    threats = 0
    for dnum, delta in DIRS.items():
        for cell, colour in board.items():
            if colour != player:
                continue
            # Check 2-v-1
            next1 = cell_add(cell, delta)
            if board.get(next1) != player:
                continue
            next2 = cell_add(next1, delta)
            if board.get(next2) == opp:
                beyond = cell_add(next2, delta)
                if beyond not in ALL_CELLS:
                    threats += 1
            # Check 3-v-1
            if board.get(next2) != player:
                continue
            next3 = cell_add(next2, delta)
            if board.get(next3) == opp:
                beyond3 = cell_add(next3, delta)
                if beyond3 not in ALL_CELLS:
                    threats += 1
    return threats


def evaluate(board: EngineBoard, player: EnginePlayer, *,
             remaining_moves: Optional[int] = None,
             opp_remaining_moves: Optional[int] = None,
             my_total_time_us: Optional[int] = None,
             opp_total_time_us: Optional[int] = None) -> float:
    """Return a heuristic score for *board* from *player*'s perspective.

    Higher is better for *player*.

    Optional endgame-context parameters
    ------------------------------------
    remaining_moves : moves left for *player* (None = unknown / unlimited).
    opp_remaining_moves : moves left for the opponent.
    my_total_time_us : cumulative µs *player* has spent on all moves so far.
    opp_total_time_us : cumulative µs the opponent has spent.

    When the game is close to ending (few remaining moves), the evaluation
    puts extra weight on the current marble-count lead (score advantage)
    and rewards having used less total time (tiebreaker advantage).
    """
    opp = opponent(player)

    my_cells = [c for c, v in board.items() if v == player]
    opp_cells = [c for c, v in board.items() if v == opp]

    # 1. Marble advantage (captures are reflected by count difference)
    marble_diff = len(my_cells) - len(opp_cells)

    # 2. Centrality – prefer positions closer to the centre
    my_centre = sum(_manhattan_from_centre(c) for c in my_cells)
    opp_centre = sum(_manhattan_from_centre(c) for c in opp_cells)
    centre_score = opp_centre - my_centre  # positive when we are more central

    # 3. Cohesion – reward tightly grouped marbles
    cohesion = (_count_friendly_neighbours(board, player)
                - _count_friendly_neighbours(board, opp))

    # 4. Threat – reward configurations that can push opponent off
    threat = _count_threats(board, player) - _count_threats(board, opp)

    # 5. Edge penalty – discourage own marbles sitting on the rim
    my_edge = sum(1 for c in my_cells if _is_edge_cell(c))
    opp_edge = sum(1 for c in opp_cells if _is_edge_cell(c))
    edge_score = opp_edge - my_edge  # positive when opponent has more edge marbles

    score = (
        _W_MARBLE_COUNT * marble_diff
        + 5 * centre_score
        + _W_COHESION * cohesion
        + _W_THREAT * threat
        + abs(_W_EDGE_PENALTY) * edge_score
    )

    # ── 6. Endgame awareness ─────────────────────────────────────────────
    # When the game is nearing its end (few remaining moves for either
    # player), prioritise holding or extending a score lead and having a
    # time advantage (the tiebreaker when scores are equal).
    min_remaining = None
    if remaining_moves is not None and opp_remaining_moves is not None:
        min_remaining = min(remaining_moves, opp_remaining_moves)
    elif remaining_moves is not None:
        min_remaining = remaining_moves
    elif opp_remaining_moves is not None:
        min_remaining = opp_remaining_moves

    if min_remaining is not None and min_remaining <= _ENDGAME_MOVES_THRESHOLD:
        # Urgency multiplier: as fewer moves remain the bonus grows.
        # Range: 1.0 (at threshold) → ~2.0 (at 1 move left).
        urgency = 1.0 + ((_ENDGAME_MOVES_THRESHOLD - min_remaining)
                         / max(_ENDGAME_MOVES_THRESHOLD, 1))

        # 6a. Amplify the score-lead bonus in the endgame.
        #     Positive marble_diff = we are ahead → reward.
        #     Negative marble_diff = we are behind → stronger threat/attack weight.
        score += _W_ENDGAME_SCORE_LEAD * marble_diff * urgency

        # 6b. Time-advantage bonus (tiebreaker: less time used is better).
        if my_total_time_us is not None and opp_total_time_us is not None:
            if opp_total_time_us > my_total_time_us:
                score += _W_TIME_ADVANTAGE * urgency
            elif my_total_time_us > opp_total_time_us:
                score -= _W_TIME_ADVANTAGE * urgency

    return score


# ---------------------------------------------------------------------------
# Move ordering heuristic (improves alpha-beta cutoffs)
# ---------------------------------------------------------------------------

def _move_sort_key(item: Tuple[Move, EngineBoard], player: EnginePlayer,
                   current_board: EngineBoard) -> float:
    """Return a key for sorting moves so promising ones come first.

    Pushes (sumito) and captures are examined first, then inline moves,
    then side-steps.  Within each category we use a quick evaluation.
    """
    move, new_board = item
    # Count marble difference – a capture will show up immediately
    my_old = sum(1 for v in current_board.values() if v == player)
    opp_old = sum(1 for v in current_board.values() if v != player)
    my_new = sum(1 for v in new_board.values() if v == player)
    opp_new = sum(1 for v in new_board.values() if v != player)
    capture = (opp_old - opp_new)  # >0 means we pushed one off

    # Higher capture priority first (negate for ascending sort)
    return -(capture * 1000 + (0 if move.kind == 'i' else -1))


class _SearchTimeout(Exception):
    """Raised inside the minimax search when the time budget is exhausted."""


class AIAgent:
    """AI agent that uses iterative-deepening minimax with alpha-beta pruning.

    The agent keeps deepening its search (depth 1, 2, 3, …) and always
    retains the best move found so far.  When the time budget is nearly
    exhausted the search is aborted and the best move from the deepest
    *completed* iteration is returned.

    Attributes
    ----------
    player : EnginePlayer
        'b' or 'w' – the colour this agent controls.
    max_depth : int
        Hard upper limit on search depth (safeguard).
    time_limit : float
        Maximum wall-clock seconds the agent may spend selecting a move.
    """

    def __init__(self, player: EnginePlayer, max_depth: int = 10,
                 time_limit: float = 4.5) -> None:
        """
        Args:
            player: The engine player character this agent controls ('b' or 'w').
            max_depth: Hard upper bound on search depth (default 10).
            time_limit: Wall-clock seconds the agent is allowed to think.
                        Defaults to 4.5 s (safe margin for a 5 s move clock).
        """
        self.player = player
        self.max_depth = max_depth
        self.time_limit = time_limit
        # Filled at the start of each select_move call
        self._deadline: float = 0.0

    # ------------------------------------------------------------------
    # Internal: time check
    # ------------------------------------------------------------------

    def _check_time(self) -> None:
        """Raise ``_SearchTimeout`` if the deadline has been reached."""
        if time.perf_counter() >= self._deadline:
            raise _SearchTimeout

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def select_move(
        self,
        board: EngineBoard,
        legal_moves: Optional[List[Tuple[Move, EngineBoard]]] = None,
        *,
        remaining_moves: Optional[int] = None,
        opp_remaining_moves: Optional[int] = None,
        my_total_time_us: Optional[int] = None,
        opp_total_time_us: Optional[int] = None,
    ) -> Optional[Tuple[Move, EngineBoard]]:
        """Pick the best move using iterative-deepening alpha-beta search.

        Optional endgame-context kwargs
        --------------------------------
        remaining_moves : How many moves this agent still has.
        opp_remaining_moves : How many moves the opponent still has.
        my_total_time_us : Cumulative µs this agent has spent so far.
        opp_total_time_us : Cumulative µs the opponent has spent so far.

        These values are forwarded to the evaluation function so that the
        AI plays more aggressively or conservatively near the endgame.

        The agent starts at depth 1 and progressively deepens.  It always
        keeps the best result from the last **fully completed** depth so
        that a move is available even when time is very short.

        **Time-saving heuristics** (tournament-oriented):
        * Opening positions (no captures yet) use a fraction of the budget.
        * Positions with few legal moves are searched with a reduced budget.
        * If one move is clearly dominant (large score gap over the runner-up),
          the search stops early.
        * If the same best move is selected for several consecutive depths,
          the search stops early (the choice is stable).

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

        # If there is exactly one legal move, play it immediately.
        if len(legal_moves) == 1:
            return legal_moves[0]

        # Store endgame context so that _minimax / evaluate can access it.
        self._remaining_moves = remaining_moves
        self._opp_remaining_moves = opp_remaining_moves
        self._my_total_time_us = my_total_time_us
        self._opp_total_time_us = opp_total_time_us

        # Order moves so alpha-beta prunes more aggressively
        legal_moves.sort(key=lambda m: _move_sort_key(m, self.player, board))

        # ── Adaptive time budget ──────────────────────────────────────────
        effective_limit = self.time_limit

        is_opening = _is_opening_position(board)
        if is_opening:
            effective_limit = self.time_limit * _OPENING_TIME_FRACTION
        elif len(legal_moves) < _FEW_MOVES_THRESHOLD:
            effective_limit = self.time_limit * _FEW_MOVES_TIME_FRACTION

        self._deadline = time.perf_counter() + effective_limit

        # Always have a fallback: the first move (best by move-ordering heuristic)
        best_move: Optional[Tuple[Move, EngineBoard]] = legal_moves[0]

        # Tracking for early-stop heuristics
        prev_best_notation: Optional[str] = None
        stable_count: int = 0

        for depth in range(1, self.max_depth + 1):
            try:
                candidate, best_score, second_best = self._search_root(
                    board, legal_moves, depth,
                )
                if candidate is not None:
                    best_move = candidate
            except _SearchTimeout:
                # Time ran out during this depth – use the result from the
                # previous (fully completed) depth.
                break

            # ── Early-stop: dominant move (large score gap) ───────────────
            if (second_best > -math.inf
                    and best_score - second_best >= _DOMINANCE_THRESHOLD
                    and depth >= 2):
                break

            # ── Early-stop: stable best move across depths ────────────────
            current_notation = best_move[0].notation() if best_move else None
            if current_notation == prev_best_notation:
                stable_count += 1
            else:
                stable_count = 1
            prev_best_notation = current_notation

            if stable_count >= _STABLE_DEPTH_COUNT and depth >= _STABLE_DEPTH_COUNT:
                break

            # If very little time is left, don't start another iteration
            if time.perf_counter() >= self._deadline - 0.05:
                break

        return best_move

    # ------------------------------------------------------------------
    # Root-level search (one full depth iteration)
    # ------------------------------------------------------------------

    def _search_root(
        self,
        board: EngineBoard,
        legal_moves: List[Tuple[Move, EngineBoard]],
        depth: int,
    ) -> Tuple[Optional[Tuple[Move, EngineBoard]], float, float]:
        """Run a fixed-depth alpha-beta search and return the best move.

        Returns
        -------
        (best_move, best_score, second_best_score)
            *best_move* is the chosen ``(Move, Board)`` pair (or *None*).
            *best_score* and *second_best_score* allow the caller to detect
            dominant moves (large gap ⇒ no need to search deeper).
        """
        best_score = -math.inf
        second_best_score = -math.inf
        best_move: Optional[Tuple[Move, EngineBoard]] = None

        alpha = -math.inf
        beta = math.inf

        for move, new_board in legal_moves:
            self._check_time()
            score = self._minimax(
                new_board,
                depth=depth - 1,
                alpha=alpha,
                beta=beta,
                is_maximising=False,
            )
            if score > best_score:
                second_best_score = best_score
                best_score = score
                best_move = (move, new_board)
            elif score > second_best_score:
                second_best_score = score
            alpha = max(alpha, score)

        return best_move, best_score, second_best_score

    # ------------------------------------------------------------------
    # Minimax with alpha-beta pruning
    # ------------------------------------------------------------------

    def _minimax(
        self,
        board: EngineBoard,
        depth: int,
        alpha: float,
        beta: float,
        is_maximising: bool,
    ) -> float:
        """Recursive minimax with alpha-beta pruning.

        Raises ``_SearchTimeout`` when the time budget is exhausted.
        """
        self._check_time()

        # Terminal / depth-limit check
        if depth == 0:
            return evaluate(
                board, self.player,
                remaining_moves=self._remaining_moves,
                opp_remaining_moves=self._opp_remaining_moves,
                my_total_time_us=self._my_total_time_us,
                opp_total_time_us=self._opp_total_time_us,
            )

        current_player = self.player if is_maximising else opponent(self.player)
        moves = generate_moves(current_player, board)

        if not moves:
            return -10_000 if is_maximising else 10_000

        # Order moves for better pruning
        moves.sort(key=lambda m: _move_sort_key(m, current_player, board))

        if is_maximising:
            max_eval = -math.inf
            for _, new_board in moves:
                eval_score = self._minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = math.inf
            for _, new_board in moves:
                eval_score = self._minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

