"""
AI Agent for Abalone Game — Tournament-Strength Edition.

A highly optimised iterative-deepening alpha-beta agent with:
  • Zobrist-hashed transposition table
  • Principal Variation Search (PVS)
  • Killer move & history heuristic move ordering
  • Late Move Reductions (LMR)
  • Quiescence search for captures
  • Belgian-Daisy-aware multi-phase evaluation
  • Cluster detection via flood-fill (daisy formation tracking)
  • Advanced threat / danger analysis (2v1, 3v1, 3v2, near-threats)
  • Adaptive time management
"""
from __future__ import annotations

import math
import random
import time
from collections import defaultdict, deque
from typing import Dict, List, Optional, Set, Tuple

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

# ═══════════════════════════════════════════════════════════════════════════
#  PRE-COMPUTED LOOKUP TABLES (built once at import time)
# ═══════════════════════════════════════════════════════════════════════════

_CELL_LIST: List[Cell] = sorted(ALL_CELLS)
_CELL_INDEX: Dict[Cell, int] = {c: i for i, c in enumerate(_CELL_LIST)}
_NUM_CELLS = len(_CELL_LIST)  # 61

# Hex-ring distance from the centre (0,0)
_RING: Dict[Cell, int] = {}
for _c in ALL_CELLS:
    _q, _r = _c
    _RING[_c] = (abs(_q) + abs(_r) + abs(_q + _r)) // 2

# Ring-based positional value (centre = best, edge = worst)
_RING_VALUE: Dict[Cell, int] = {
    c: {0: 8, 1: 5, 2: 3, 3: 1, 4: -2}[_RING[c]] for c in ALL_CELLS
}

# Neighbour list for every cell
_NEIGHBOURS: Dict[Cell, List[Cell]] = {}
for _c in ALL_CELLS:
    _NEIGHBOURS[_c] = [cell_add(_c, d) for d in DIRS.values()
                        if cell_add(_c, d) in ALL_CELLS]

# Is-edge predicate
_IS_EDGE: Dict[Cell, bool] = {c: _RING[c] == 4 for c in ALL_CELLS}

# Near-edge (ring 3+)
_IS_NEAR_EDGE: Dict[Cell, bool] = {c: _RING[c] >= 3 for c in ALL_CELLS}

# ═══════════════════════════════════════════════════════════════════════════
#  ZOBRIST HASHING
# ═══════════════════════════════════════════════════════════════════════════

_RNG = random.Random(42)  # deterministic seed for reproducibility
_ZOBRIST: Dict[Tuple[Cell, str], int] = {}
for _c in ALL_CELLS:
    for _col in ('b', 'w'):
        _ZOBRIST[(_c, _col)] = _RNG.getrandbits(64)
_ZOBRIST_TURN: int = _RNG.getrandbits(64)  # XOR when it is black's turn


def _zobrist_hash(board: EngineBoard, is_maximising: bool) -> int:
    """Full Zobrist hash of *board* and side-to-move."""
    h = 0
    for cell, colour in board.items():
        h ^= _ZOBRIST[(cell, colour)]
    if is_maximising:
        h ^= _ZOBRIST_TURN
    return h


# ═══════════════════════════════════════════════════════════════════════════
#  TRANSPOSITION TABLE
# ═══════════════════════════════════════════════════════════════════════════

_TT_EXACT = 0
_TT_LOWER = 1  # score is a lower bound (failed high)
_TT_UPPER = 2  # score is an upper bound (failed low)

# Entry: (depth, flag, score, best_move_notation_or_None)
_TTEntry = Tuple[int, int, float, Optional[str]]


class _TranspositionTable:
    """Fixed-size hash table using Zobrist keys."""

    __slots__ = ('_table', '_mask')

    def __init__(self, size_bits: int = 20) -> None:
        self._mask = (1 << size_bits) - 1
        self._table: Dict[int, _TTEntry] = {}

    def probe(self, key: int) -> Optional[_TTEntry]:
        return self._table.get(key & self._mask)

    def store(self, key: int, depth: int, flag: int, score: float,
              best_move_notation: Optional[str]) -> None:
        idx = key & self._mask
        old = self._table.get(idx)
        # Always-replace if deeper or same depth
        if old is None or depth >= old[0]:
            self._table[idx] = (depth, flag, score, best_move_notation)

    def clear(self) -> None:
        self._table.clear()


# ═══════════════════════════════════════════════════════════════════════════
#  CLUSTER DETECTION (Belgian Daisy formation analysis)
# ═══════════════════════════════════════════════════════════════════════════

def _flood_fill_clusters(cells: List[Cell]) -> List[List[Cell]]:
    """Return connected components of *cells* on the hex grid."""
    cell_set: Set[Cell] = set(cells)
    visited: Set[Cell] = set()
    clusters: List[List[Cell]] = []

    for start in cells:
        if start in visited:
            continue
        cluster: List[Cell] = []
        queue = deque([start])
        visited.add(start)
        while queue:
            c = queue.popleft()
            cluster.append(c)
            for nb in _NEIGHBOURS[c]:
                if nb in cell_set and nb not in visited:
                    visited.add(nb)
                    queue.append(nb)
        clusters.append(cluster)

    return clusters


def _centroid(cells: List[Cell]) -> Tuple[float, float]:
    """Return the (q, r) centroid of a list of cells."""
    n = len(cells)
    if n == 0:
        return (0.0, 0.0)
    sq = sum(c[0] for c in cells)
    sr = sum(c[1] for c in cells)
    return (sq / n, sr / n)


def _cluster_compactness(cells: List[Cell]) -> float:
    """Measure compactness: lower average distance to centroid is better.
    Returns negative value (penalty for spread) so that higher = more compact."""
    if len(cells) <= 1:
        return 0.0
    cq, cr = _centroid(cells)
    total_dist = 0.0
    for q, r in cells:
        dq = q - cq
        dr = r - cr
        total_dist += (abs(dq) + abs(dr) + abs(dq + dr)) / 2
    return -total_dist / len(cells)


# ═══════════════════════════════════════════════════════════════════════════
#  THREAT & DANGER ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════

def _count_threats_advanced(board: EngineBoard, player: EnginePlayer) -> Tuple[float, float]:
    """Compute (attack_threats, defensive_dangers) for *player*.

    attack_threats  — weighted count of opponent marbles *player* can push off.
    defensive_dangers — weighted count of *player*'s own marbles at risk.

    Covers 2v1, 3v1, 3v2 push-off and near-threat situations.
    """
    opp = opponent(player)
    attack = 0.0
    danger = 0.0

    for dnum, delta in DIRS.items():
        for cell, colour in board.items():
            # ── ATTACK threats (player pushing opponent off) ──────────
            if colour == player:
                n1 = cell_add(cell, delta)
                if board.get(n1) != player:
                    continue
                n2 = cell_add(n1, delta)

                # 2v1 push-off
                if board.get(n2) == opp:
                    beyond = cell_add(n2, delta)
                    if beyond not in ALL_CELLS:
                        attack += 4.0
                    elif board.get(beyond) is None:
                        # Near-threat: opponent 1 step from edge with our 2 inline
                        if _IS_NEAR_EDGE.get(n2, False):
                            attack += 1.0

                # 3v1 push-off
                if board.get(n2) == player:
                    n3 = cell_add(n2, delta)
                    if board.get(n3) == opp:
                        beyond3 = cell_add(n3, delta)
                        if beyond3 not in ALL_CELLS:
                            attack += 5.0
                        elif board.get(beyond3) is None:
                            if _IS_NEAR_EDGE.get(n3, False):
                                attack += 1.5

                    # 3v2 push-off
                    if board.get(n3) == opp:
                        n4 = cell_add(n3, delta)
                        if board.get(n4) == opp:
                            beyond4 = cell_add(n4, delta)
                            if beyond4 not in ALL_CELLS:
                                attack += 3.0
                            elif board.get(beyond4) is None:
                                if _IS_NEAR_EDGE.get(n4, False):
                                    attack += 0.8

            # ── DEFENSIVE dangers (opponent pushing player off) ───────
            if colour == opp:
                n1 = cell_add(cell, delta)
                if board.get(n1) != opp:
                    continue
                n2 = cell_add(n1, delta)

                # 2v1 danger to our marble
                if board.get(n2) == player:
                    beyond = cell_add(n2, delta)
                    if beyond not in ALL_CELLS:
                        danger += 4.0
                    elif board.get(beyond) is None and _IS_NEAR_EDGE.get(n2, False):
                        danger += 1.0

                # 3v1 danger
                if board.get(n2) == opp:
                    n3 = cell_add(n2, delta)
                    if board.get(n3) == player:
                        beyond3 = cell_add(n3, delta)
                        if beyond3 not in ALL_CELLS:
                            danger += 5.0
                        elif board.get(beyond3) is None and _IS_NEAR_EDGE.get(n3, False):
                            danger += 1.5

                    # 3v2 danger
                    if board.get(n3) == player:
                        n4 = cell_add(n3, delta)
                        if board.get(n4) == player:
                            beyond4 = cell_add(n4, delta)
                            if beyond4 not in ALL_CELLS:
                                danger += 3.0

    return attack, danger


# ═══════════════════════════════════════════════════════════════════════════
#  GAME-PHASE DETECTION
# ═══════════════════════════════════════════════════════════════════════════

_OPENING_MARBLE_COUNT = 14

# Phase constants
_PHASE_OPENING = 0
_PHASE_MIDGAME = 1
_PHASE_ENDGAME = 2


def _detect_phase(board: EngineBoard, player: EnginePlayer,
                  remaining_moves: Optional[int] = None) -> int:
    """Determine the game phase: opening, midgame, or endgame."""
    my_count = sum(1 for v in board.values() if v == player)
    opp_count = sum(1 for v in board.values() if v == opponent(player))

    # Endgame: either side lost ≥3 marbles, or few moves remain
    if (my_count <= 11 or opp_count <= 11 or
            (remaining_moves is not None and remaining_moves <= 10)):
        return _PHASE_ENDGAME

    # Opening: no captures at all
    if my_count == _OPENING_MARBLE_COUNT and opp_count == _OPENING_MARBLE_COUNT:
        return _PHASE_OPENING

    return _PHASE_MIDGAME


# ═══════════════════════════════════════════════════════════════════════════
#  PHASE-DEPENDENT WEIGHT PROFILES (tuned for Belgian Daisy)
# ═══════════════════════════════════════════════════════════════════════════

# Keys: marble_count, ring_position, cohesion, attack_threat, danger,
#       edge_penalty, formation, cluster_merge, center_of_mass,
#       endgame_lead, time_advantage, breakaway
_WEIGHTS = {
    _PHASE_OPENING: {
        'marble_count':   80,
        'ring_position':  4,
        'cohesion':       5,
        'attack_threat':  3,
        'danger':         -4,
        'edge_penalty':   5,
        'formation':      8,       # Keep daisy formations tight
        'cluster_merge':  12,      # Strong incentive to merge two daisies
        'center_of_mass': 6,
        'endgame_lead':   0,
        'time_advantage': 0,
        'breakaway':      -6,      # Penalise isolated marbles leaving cluster
    },
    _PHASE_MIDGAME: {
        'marble_count':   120,
        'ring_position':  5,
        'cohesion':       4,
        'attack_threat':  10,
        'danger':         -8,
        'edge_penalty':   6,
        'formation':      4,
        'cluster_merge':  4,
        'center_of_mass': 5,
        'endgame_lead':   15,
        'time_advantage': 5,
        'breakaway':      -3,
    },
    _PHASE_ENDGAME: {
        'marble_count':   200,
        'ring_position':  3,
        'cohesion':       3,
        'attack_threat':  14,
        'danger':         -12,
        'edge_penalty':   8,
        'formation':      2,
        'cluster_merge':  0,
        'center_of_mass': 3,
        'endgame_lead':   40,
        'time_advantage': 12,
        'breakaway':      -2,
    },
}

# ═══════════════════════════════════════════════════════════════════════════
#  EVALUATION FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def evaluate(board: EngineBoard, player: EnginePlayer, *,
             remaining_moves: Optional[int] = None,
             opp_remaining_moves: Optional[int] = None,
             my_total_time_us: Optional[int] = None,
             opp_total_time_us: Optional[int] = None) -> float:
    """Multi-factor heuristic evaluation, Belgian Daisy optimised.

    Higher is better for *player*.
    """
    opp = opponent(player)

    my_cells = [c for c, v in board.items() if v == player]
    opp_cells = [c for c, v in board.items() if v == opp]
    my_count = len(my_cells)
    opp_count = len(opp_cells)

    phase = _detect_phase(board, player, remaining_moves)
    W = _WEIGHTS[phase]

    # ── 1. Marble advantage ──────────────────────────────────────────────
    marble_diff = my_count - opp_count

    # ── 2. Ring-based positional score ───────────────────────────────────
    my_ring = sum(_RING_VALUE[c] for c in my_cells)
    opp_ring = sum(_RING_VALUE[c] for c in opp_cells)
    ring_score = my_ring - opp_ring

    # ── 3. Cohesion (friendly-neighbour pairs) ───────────────────────────
    my_cohesion = 0
    for c in my_cells:
        for nb in _NEIGHBOURS[c]:
            if board.get(nb) == player:
                my_cohesion += 1
    opp_cohesion = 0
    for c in opp_cells:
        for nb in _NEIGHBOURS[c]:
            if board.get(nb) == opp:
                opp_cohesion += 1
    cohesion_diff = my_cohesion - opp_cohesion

    # ── 4. Threat & danger analysis ──────────────────────────────────────
    my_attack, my_danger = _count_threats_advanced(board, player)
    opp_attack, opp_danger = _count_threats_advanced(board, opp)
    threat_score = my_attack - opp_attack
    danger_score = my_danger - opp_danger  # positive = we are more in danger

    # ── 5. Edge penalty differential ─────────────────────────────────────
    my_edge = sum(1 for c in my_cells if _IS_EDGE[c])
    opp_edge = sum(1 for c in opp_cells if _IS_EDGE[c])
    edge_diff = opp_edge - my_edge  # positive when opponent has more edge marbles

    # ── 6. Formation / cluster analysis (Belgian Daisy aware) ────────────
    formation_score = 0.0
    cluster_merge_score = 0.0
    breakaway_score = 0.0

    my_clusters = _flood_fill_clusters(my_cells)

    # Formation compactness: reward tight clusters
    for cluster in my_clusters:
        formation_score += _cluster_compactness(cluster) * len(cluster)

    # Opponent formation (penalise if opponent is well-formed)
    opp_clusters = _flood_fill_clusters(opp_cells)
    for cluster in opp_clusters:
        formation_score -= _cluster_compactness(cluster) * len(cluster) * 0.5

    # Cluster merge incentive (Belgian Daisy: ideally merge 2 daisies into 1)
    if len(my_clusters) >= 2:
        # Compute distances between the two largest clusters' centroids
        my_clusters.sort(key=len, reverse=True)
        c1 = _centroid(my_clusters[0])
        c2 = _centroid(my_clusters[1])
        dq = c1[0] - c2[0]
        dr = c1[1] - c2[1]
        inter_dist = (abs(dq) + abs(dr) + abs(dq + dr)) / 2
        # Reward smaller distance (closer to merging)
        cluster_merge_score = -inter_dist
    elif len(my_clusters) == 1:
        # Already merged — bonus
        cluster_merge_score = 5.0

    # Breakaway penalty: count marbles with zero friendly neighbours
    for c in my_cells:
        if not any(board.get(nb) == player for nb in _NEIGHBOURS[c]):
            breakaway_score += 1.0

    # ── 7. Centre-of-mass ────────────────────────────────────────────────
    my_com = _centroid(my_cells) if my_cells else (0.0, 0.0)
    opp_com = _centroid(opp_cells) if opp_cells else (0.0, 0.0)
    my_com_dist = (abs(my_com[0]) + abs(my_com[1]) + abs(my_com[0] + my_com[1])) / 2
    opp_com_dist = (abs(opp_com[0]) + abs(opp_com[1]) + abs(opp_com[0] + opp_com[1])) / 2
    com_diff = opp_com_dist - my_com_dist  # positive when we are more central

    # ── Assemble score ───────────────────────────────────────────────────
    score = (
        W['marble_count']   * marble_diff
        + W['ring_position']  * ring_score
        + W['cohesion']       * cohesion_diff
        + W['attack_threat']  * threat_score
        + W['danger']         * danger_score
        + W['edge_penalty']   * edge_diff
        + W['formation']      * formation_score
        + W['cluster_merge']  * cluster_merge_score
        + W['center_of_mass'] * com_diff
        + W['breakaway']      * breakaway_score
    )

    # ── 8. Endgame / move-limit awareness ────────────────────────────────
    min_remaining = None
    if remaining_moves is not None and opp_remaining_moves is not None:
        min_remaining = min(remaining_moves, opp_remaining_moves)
    elif remaining_moves is not None:
        min_remaining = remaining_moves
    elif opp_remaining_moves is not None:
        min_remaining = opp_remaining_moves

    if min_remaining is not None and min_remaining <= 12:
        urgency = 1.0 + (12 - min_remaining) / 12.0
        score += W['endgame_lead'] * marble_diff * urgency

        if my_total_time_us is not None and opp_total_time_us is not None:
            if opp_total_time_us > my_total_time_us:
                score += W['time_advantage'] * urgency
            elif my_total_time_us > opp_total_time_us:
                score -= W['time_advantage'] * urgency

    # ── 9. Win/loss terminal bonuses ─────────────────────────────────────
    if opp_count <= 8:  # opponent has lost ≥6 marbles → we win
        score += 50_000
    if my_count <= 8:   # we have lost ≥6 marbles → we lose
        score -= 50_000

    return score


# ═══════════════════════════════════════════════════════════════════════════
#  MOVE ORDERING HELPERS
# ═══════════════════════════════════════════════════════════════════════════

def _quick_move_score(move: Move, new_board: EngineBoard,
                      current_board: EngineBoard,
                      player: EnginePlayer) -> int:
    """Fast heuristic for move ordering (higher = try first)."""
    # Capture detection
    opp = opponent(player)
    opp_old = sum(1 for v in current_board.values() if v == opp)
    opp_new = sum(1 for v in new_board.values() if v == opp)
    capture = opp_old - opp_new

    score = capture * 10_000

    # Prefer inline over side-step when no capture
    if move.kind == 'i':
        score += 100

    return score


# ═══════════════════════════════════════════════════════════════════════════
#  TIME-MANAGEMENT CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════

_OPENING_TIME_FRACTION = 0.30
_FEW_MOVES_THRESHOLD = 10
_FEW_MOVES_TIME_FRACTION = 0.50
_DOMINANCE_THRESHOLD = 150
_STABLE_DEPTH_COUNT = 3
_TIME_CHECK_INTERVAL = 512  # check clock every N nodes


# ═══════════════════════════════════════════════════════════════════════════
#  SEARCH ENGINE
# ═══════════════════════════════════════════════════════════════════════════

class _SearchTimeout(Exception):
    """Raised inside the search when the time budget is exhausted."""


class AIAgent:
    """Tournament-strength Abalone AI with advanced search & evaluation.

    Features
    --------
    * Iterative deepening with aspiration windows
    * Principal Variation Search (PVS) with alpha-beta pruning
    * Zobrist-hashed transposition table
    * Killer moves (2 slots per depth)
    * History heuristic for quiet-move ordering
    * Late Move Reductions (LMR)
    * Quiescence search on capture moves
    * Multi-phase evaluation tuned for Belgian Daisy
    """

    def __init__(self, player: EnginePlayer, max_depth: int = 40,
                 time_limit: float = 4.5) -> None:
        self.player = player
        self.max_depth = max_depth
        self.time_limit = time_limit

        # Transposition table (persists across moves for the same game)
        self._tt = _TranspositionTable(size_bits=20)

        # Killer moves: 2 slots per depth
        self._killers: Dict[int, List[Optional[str]]] = defaultdict(lambda: [None, None])

        # History heuristic counters:  player -> move_notation -> score
        self._history: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        # Node counter for infrequent time checks
        self._nodes: int = 0

        # Filled at the start of each select_move call
        self._deadline: float = 0.0

        # Endgame context (set per-move)
        self._remaining_moves: Optional[int] = None
        self._opp_remaining_moves: Optional[int] = None
        self._my_total_time_us: Optional[int] = None
        self._opp_total_time_us: Optional[int] = None

    # ------------------------------------------------------------------
    # Time management
    # ------------------------------------------------------------------

    def _check_time(self) -> None:
        """Raise ``_SearchTimeout`` every *_TIME_CHECK_INTERVAL* nodes."""
        self._nodes += 1
        if self._nodes & (_TIME_CHECK_INTERVAL - 1) == 0:
            if time.perf_counter() >= self._deadline:
                raise _SearchTimeout

    # ------------------------------------------------------------------
    # Move ordering
    # ------------------------------------------------------------------

    def _order_moves(
        self,
        moves: List[Tuple[Move, EngineBoard]],
        board: EngineBoard,
        player: EnginePlayer,
        depth: int,
        pv_notation: Optional[str] = None,
    ) -> List[Tuple[Move, EngineBoard]]:
        """Sort *moves* with PV-first, captures, killers, then history."""

        def _key(item: Tuple[Move, EngineBoard]) -> Tuple[int, int, int]:
            move, new_board = item
            notation = move.notation()

            # Priority bucket (lower = tried first)
            if notation == pv_notation:
                bucket = 0
            else:
                cap = _quick_move_score(move, new_board, board, player)
                if cap > 0:
                    bucket = 1
                elif (notation == self._killers[depth][0] or
                      notation == self._killers[depth][1]):
                    bucket = 2
                else:
                    bucket = 3

            hist = self._history[player].get(notation, 0)
            quick = _quick_move_score(move, new_board, board, player)
            # Sort: ascending bucket, descending quick + history
            return (bucket, -quick, -hist)

        moves.sort(key=_key)
        return moves

    def _store_killer(self, depth: int, notation: str) -> None:
        """Store a killer move (non-capture beta-cutoff move)."""
        k = self._killers[depth]
        if k[0] != notation:
            k[1] = k[0]
            k[0] = notation

    def _update_history(self, player: EnginePlayer, notation: str, depth: int) -> None:
        """Increment the history counter for a cutoff move."""
        self._history[player][notation] += depth * depth

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
        """Pick the best move using iterative-deepening PVS.

        Returns a ``(Move, new_board)`` tuple, or *None* if no move exists.
        """
        if legal_moves is None:
            legal_moves = generate_moves(self.player, board)

        if not legal_moves:
            return None

        if len(legal_moves) == 1:
            return legal_moves[0]

        # Store endgame context
        self._remaining_moves = remaining_moves
        self._opp_remaining_moves = opp_remaining_moves
        self._my_total_time_us = my_total_time_us
        self._opp_total_time_us = opp_total_time_us
        self._nodes = 0

        # ── Adaptive time budget ──────────────────────────────────────
        effective_limit = self.time_limit

        my_count = sum(1 for v in board.values() if v == self.player)
        opp_count = sum(1 for v in board.values() if v == opponent(self.player))
        is_opening = (my_count == _OPENING_MARBLE_COUNT and
                      opp_count == _OPENING_MARBLE_COUNT)

        if is_opening:
            effective_limit = self.time_limit * _OPENING_TIME_FRACTION
        elif len(legal_moves) < _FEW_MOVES_THRESHOLD:
            effective_limit = self.time_limit * _FEW_MOVES_TIME_FRACTION

        self._deadline = time.perf_counter() + effective_limit

        # Initial move ordering
        legal_moves = self._order_moves(legal_moves, board, self.player, 0)

        best_move: Optional[Tuple[Move, EngineBoard]] = legal_moves[0]
        prev_score: float = 0.0

        # Tracking for early-stop heuristics
        prev_best_notation: Optional[str] = None
        stable_count: int = 0

        for depth in range(1, self.max_depth + 1):
            # ── Aspiration window ─────────────────────────────────────
            if depth >= 4:
                asp_alpha = prev_score - 50
                asp_beta = prev_score + 50
            else:
                asp_alpha = -math.inf
                asp_beta = math.inf

            try:
                candidate, best_score, second_best = self._search_root(
                    board, legal_moves, depth, asp_alpha, asp_beta,
                )

                # If aspiration window failed, re-search with full window
                if best_score <= asp_alpha or best_score >= asp_beta:
                    candidate, best_score, second_best = self._search_root(
                        board, legal_moves, depth, -math.inf, math.inf,
                    )

                if candidate is not None:
                    best_move = candidate
                    prev_score = best_score

                    # Reorder moves: put the best move first for next iteration
                    best_notation = best_move[0].notation()
                    legal_moves = self._order_moves(
                        legal_moves, board, self.player, 0,
                        pv_notation=best_notation,
                    )

            except _SearchTimeout:
                break

            # ── Early-stop: dominant move ─────────────────────────────
            if (second_best > -math.inf
                    and best_score - second_best >= _DOMINANCE_THRESHOLD
                    and depth >= 2):
                break

            # ── Early-stop: stable best move ──────────────────────────
            current_notation = best_move[0].notation() if best_move else None
            if current_notation == prev_best_notation:
                stable_count += 1
            else:
                stable_count = 1
            prev_best_notation = current_notation

            if stable_count >= _STABLE_DEPTH_COUNT and depth >= _STABLE_DEPTH_COUNT:
                break

            if time.perf_counter() >= self._deadline - 0.05:
                break

        return best_move

    # ------------------------------------------------------------------
    # Root-level search
    # ------------------------------------------------------------------

    def _search_root(
        self,
        board: EngineBoard,
        legal_moves: List[Tuple[Move, EngineBoard]],
        depth: int,
        alpha: float,
        beta: float,
    ) -> Tuple[Optional[Tuple[Move, EngineBoard]], float, float]:
        """PVS at the root level."""
        best_score = -math.inf
        second_best_score = -math.inf
        best_move: Optional[Tuple[Move, EngineBoard]] = None
        first = True

        for move, new_board in legal_moves:
            self._check_time()

            if first:
                score = -self._pvs(
                    new_board, depth - 1, -beta, -alpha,
                    is_maximising=False,
                )
                first = False
            else:
                # Zero-window search
                score = -self._pvs(
                    new_board, depth - 1, -alpha - 1, -alpha,
                    is_maximising=False,
                )
                if alpha < score < beta:
                    # Re-search with full window
                    score = -self._pvs(
                        new_board, depth - 1, -beta, -score,
                        is_maximising=False,
                    )

            if score > best_score:
                second_best_score = best_score
                best_score = score
                best_move = (move, new_board)
            elif score > second_best_score:
                second_best_score = score

            if score > alpha:
                alpha = score
            if alpha >= beta:
                break

        # Store best move in TT
        if best_move is not None:
            zhash = _zobrist_hash(board, True)
            flag = _TT_EXACT
            if best_score <= alpha:
                flag = _TT_UPPER
            elif best_score >= beta:
                flag = _TT_LOWER
            self._tt.store(zhash, depth, flag, best_score,
                           best_move[0].notation())

        return best_move, best_score, second_best_score

    # ------------------------------------------------------------------
    # Principal Variation Search with TT, killers, history, LMR
    # ------------------------------------------------------------------

    def _pvs(
        self,
        board: EngineBoard,
        depth: int,
        alpha: float,
        beta: float,
        is_maximising: bool,
    ) -> float:
        """Negamax-style PVS with alpha-beta pruning.

        Returns the score from the perspective of the side to move.
        """
        self._check_time()

        # ── Transposition table probe ─────────────────────────────────
        zhash = _zobrist_hash(board, is_maximising)
        tt_entry = self._tt.probe(zhash)
        tt_best_notation: Optional[str] = None

        if tt_entry is not None:
            tt_depth, tt_flag, tt_score, tt_best_notation = tt_entry
            if tt_depth >= depth:
                if tt_flag == _TT_EXACT:
                    return tt_score
                elif tt_flag == _TT_LOWER and tt_score >= beta:
                    return tt_score
                elif tt_flag == _TT_UPPER and tt_score <= alpha:
                    return tt_score

        # ── Leaf / quiescence ─────────────────────────────────────────
        current_player = self.player if is_maximising else opponent(self.player)

        if depth <= 0:
            return self._quiescence(board, alpha, beta, current_player, 3)

        moves = generate_moves(current_player, board)

        if not moves:
            # No legal moves — effectively a loss for current player
            return -50_000

        # ── Move ordering ─────────────────────────────────────────────
        moves = self._order_moves(moves, board, current_player, depth,
                                  pv_notation=tt_best_notation)

        best_score = -math.inf
        best_notation: Optional[str] = None
        first = True
        move_index = 0

        original_alpha = alpha

        for move, new_board in moves:
            self._check_time()
            notation = move.notation()

            # ── Late Move Reductions (LMR) ────────────────────────────
            reduction = 0
            if (not first and depth >= 3 and move_index >= 4):
                # Check if this is a quiet move (no capture)
                opp = opponent(current_player)
                opp_old = sum(1 for v in board.values() if v == opp)
                opp_new = sum(1 for v in new_board.values() if v == opp)
                is_capture = (opp_old - opp_new) > 0
                is_killer = (notation == self._killers[depth][0] or
                             notation == self._killers[depth][1])
                if not is_capture and not is_killer:
                    reduction = 1

            if first:
                score = -self._pvs(
                    new_board, depth - 1 - reduction, -beta, -alpha,
                    not is_maximising,
                )
                # Re-search if LMR reduced and score is interesting
                if reduction > 0 and score > alpha:
                    score = -self._pvs(
                        new_board, depth - 1, -beta, -alpha,
                        not is_maximising,
                    )
                first = False
            else:
                # Zero-window scout
                score = -self._pvs(
                    new_board, depth - 1 - reduction, -alpha - 1, -alpha,
                    not is_maximising,
                )
                # Re-search if LMR reduced
                if reduction > 0 and score > alpha:
                    score = -self._pvs(
                        new_board, depth - 1, -alpha - 1, -alpha,
                        not is_maximising,
                    )
                # Full re-search if scout found something
                if alpha < score < beta:
                    score = -self._pvs(
                        new_board, depth - 1, -beta, -score,
                        not is_maximising,
                    )

            if score > best_score:
                best_score = score
                best_notation = notation

            if score > alpha:
                alpha = score

            if alpha >= beta:
                # Beta cutoff — update killers & history
                opp = opponent(current_player)
                opp_old = sum(1 for v in board.values() if v == opp)
                opp_new = sum(1 for v in new_board.values() if v == opp)
                is_capture = (opp_old - opp_new) > 0
                if not is_capture:
                    self._store_killer(depth, notation)
                self._update_history(current_player, notation, depth)
                break

            move_index += 1

        # ── Store in TT ───────────────────────────────────────────────
        if best_score <= original_alpha:
            flag = _TT_UPPER
        elif best_score >= beta:
            flag = _TT_LOWER
        else:
            flag = _TT_EXACT
        self._tt.store(zhash, depth, flag, best_score, best_notation)

        return best_score

    # ------------------------------------------------------------------
    # Quiescence search (captures only)
    # ------------------------------------------------------------------

    def _quiescence(
        self,
        board: EngineBoard,
        alpha: float,
        beta: float,
        player: EnginePlayer,
        max_ply: int,
    ) -> float:
        """Search only capture moves to avoid the horizon effect.

        Uses negamax convention: score is from *player*'s perspective.
        """
        self._check_time()

        # Standing pat: evaluate the position
        # We need score from player's perspective (who is "self.player")
        if player == self.player:
            stand_pat = evaluate(
                board, self.player,
                remaining_moves=self._remaining_moves,
                opp_remaining_moves=self._opp_remaining_moves,
                my_total_time_us=self._my_total_time_us,
                opp_total_time_us=self._opp_total_time_us,
            )
        else:
            stand_pat = -evaluate(
                board, self.player,
                remaining_moves=self._remaining_moves,
                opp_remaining_moves=self._opp_remaining_moves,
                my_total_time_us=self._my_total_time_us,
                opp_total_time_us=self._opp_total_time_us,
            )

        if max_ply <= 0:
            return stand_pat

        if stand_pat >= beta:
            return stand_pat
        if stand_pat > alpha:
            alpha = stand_pat

        # Generate only capture moves
        opp = opponent(player)
        opp_count = sum(1 for v in board.values() if v == opp)
        all_moves = generate_moves(player, board)

        capture_moves = []
        for move, new_board in all_moves:
            new_opp_count = sum(1 for v in new_board.values() if v == opp)
            if new_opp_count < opp_count:
                capture_moves.append((move, new_board))

        if not capture_moves:
            return stand_pat

        # Order captures by value
        capture_moves.sort(
            key=lambda item: -_quick_move_score(item[0], item[1], board, player)
        )

        for move, new_board in capture_moves:
            score = -self._quiescence(new_board, -beta, -alpha,
                                       opp, max_ply - 1)
            if score >= beta:
                return score
            if score > alpha:
                alpha = score

        return alpha
