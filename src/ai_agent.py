"""
AI Agent for Abalone Game.

Implements a minimax search with alpha-beta pruning and a multi-factor
heuristic evaluation function for intelligent move selection.
"""
from __future__ import annotations

import math
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


def evaluate(board: EngineBoard, player: EnginePlayer) -> float:
    """Return a heuristic score for *board* from *player*'s perspective.

    Higher is better for *player*.
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


class AIAgent:
    """AI agent that uses minimax with alpha-beta pruning to select moves.

    Attributes
    ----------
    player : EnginePlayer
        'b' or 'w' – the colour this agent controls.
    max_depth : int
        Maximum search depth for the minimax tree.
    """

    def __init__(self, player: EnginePlayer, max_depth: int = 3) -> None:
        """
        Args:
            player: The engine player character this agent controls ('b' or 'w').
            max_depth: How many plies deep to search (default 3).
        """
        self.player = player
        self.max_depth = max_depth

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def select_move(
        self,
        board: EngineBoard,
        legal_moves: Optional[List[Tuple[Move, EngineBoard]]] = None,
    ) -> Optional[Tuple[Move, EngineBoard]]:
        """Pick the best move using minimax with alpha-beta pruning.

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

        # Order moves so alpha-beta prunes more aggressively
        legal_moves.sort(key=lambda m: _move_sort_key(m, self.player, board))

        best_score = -math.inf
        best_move: Optional[Tuple[Move, EngineBoard]] = None

        alpha = -math.inf
        beta = math.inf

        for move, new_board in legal_moves:
            # After our move it's the opponent's turn → minimising layer
            score = self._minimax(
                new_board,
                depth=self.max_depth - 1,
                alpha=alpha,
                beta=beta,
                is_maximising=False,
            )
            if score > best_score:
                best_score = score
                best_move = (move, new_board)
            alpha = max(alpha, score)

        return best_move

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

        *is_maximising* is True when it is **this agent's** turn (we want
        to maximise), False on the opponent's turn (we minimise).
        """
        # Terminal / depth-limit check
        if depth == 0:
            return evaluate(board, self.player)

        current_player = self.player if is_maximising else opponent(self.player)
        moves = generate_moves(current_player, board)

        if not moves:
            # No legal moves – treat as a very bad / very good outcome
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
                    break  # β cut-off
            return max_eval
        else:
            min_eval = math.inf
            for _, new_board in moves:
                eval_score = self._minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # α cut-off
            return min_eval

