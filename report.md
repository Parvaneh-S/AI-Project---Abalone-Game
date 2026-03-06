# Abalone State Space Generator — Technical Report

---

## Table of Contents

1. [State Representation, Actions, and Transition Model](#1-state-representation-actions-and-transition-model)
2. [Design and Architecture of the State Space Generator](#2-design-and-architecture-of-the-state-space-generator)
3. [Move Notation](#3-move-notation)

---

## 1. State Representation, Actions, and Transition Model

### 1.1 State Representation

A **state** in this program is a complete snapshot of the Abalone board at a single point in time. It is represented as a pair:

```
(player, board)
```

| Component | Type | Description |
|-----------|------|-------------|
| `player` | `str` — `'b'` or `'w'` | The colour whose turn it is to move |
| `board` | `Dict[Cell, Player]` | A dictionary mapping each occupied cell to its marble colour |

#### The Board Grid

The Abalone board is a hexagonal grid with 61 cells. This program uses **axial coordinates** `(q, r)` to represent cell positions, where:

- `q` is the column axis
- `r` is the row axis
- All valid cells satisfy: `|q| ≤ 4`, `|r| ≤ 4`, and `|q + r| ≤ 4`

This constraint produces exactly 61 cells, matching the standard Abalone board. The full set is pre-computed at module load time and stored in the constant `CELLS`.

```
CELLS = {
    (q, r)
    for q in range(-4, 5)
    for r in range(-4, 5)
    if abs(q) <= 4 and abs(r) <= 4 and abs(q + r) <= 4
}
```

Axial coordinates are converted to and from the human-readable **board notation** (`<Row><Col>`, e.g. `E5`) using `notation_to_axial()` and `axial_to_notation()`. Rows are labelled `A` (bottom, `r = +4`) through `I` (top, `r = −4`).

#### State Encoding

The `board` dictionary only stores **occupied** cells — empty cells are simply absent from the mapping. This keeps the state compact and makes membership tests efficient (`O(1)` average).

```python
Board = Dict[Cell, Player]   # e.g. {(0, 0): 'b', (1, -1): 'w', ...}
```

A state is **immutable in spirit**: every function that applies a move returns a **new** dictionary rather than mutating the existing one, which is essential for safe state-space exploration.

---

### 1.2 Actions

An **action** is a legal move available to the current player from the current state. All actions are instances of the frozen dataclass `Move`:

```python
@dataclass(frozen=True)
class Move:
    kind: str          # 'i' (inline) or 's' (side-step)
    a:    str          # trailing marble / first extremity (board notation)
    b:    Optional[str]  # leading marble / second extremity (None for single-marble inline)
    d:    int          # direction number ∈ {1, 3, 5, 7, 9, 11}
```

There are two broad categories of action:

#### Inline Moves (`kind = 'i'`)

A group of 1–3 same-colour marbles that are **collinear along the movement direction** all shift one step forward together.

- **Single marble** (`size = 1`): the marble moves into the adjacent empty cell in direction `d`.
- **Group of 2** (`size = 2`): two adjacent friendly marbles shift together.
- **Group of 3** (`size = 3`): three adjacent friendly marbles shift together.
- **Sumito**: when the cell ahead is occupied by the opponent, the group may push a smaller opponent chain (strictly fewer opponent marbles than friendly marbles). The pushed marbles move one step in the same direction; any marble pushed off the board is permanently removed.

#### Side-step Moves (`kind = 's'`)

A group of 2–3 same-colour marbles that are collinear along some axis shift **perpendicular** to that axis. All marbles in the group must move to empty cells. Side-stepping can never push opponent marbles.

#### Direction Set

Six directions are supported, numbered by convention:

| Number | Axial delta `(Δq, Δr)` | Named direction |
|--------|------------------------|-----------------|
| 1  | `(+1, −1)` | NE — up-right   |
| 3  | `(+1,  0)` | E  — right      |
| 5  | `( 0, +1)` | SE — down-right |
| 7  | `(−1, +1)` | SW — down-left  |
| 9  | `(−1,  0)` | W  — left       |
| 11 | `( 0, −1)` | NW — up-left    |

Each direction has a unique **opposite**: `OPPOSITE = {1:7, 3:9, 5:11, 7:1, 9:3, 11:5}`.

---

### 1.3 Transition Model

The **transition model** is the function that maps a `(state, action)` pair to the resulting successor state. It is implemented by two functions:

#### `apply_inline(board, player, trailing, size, dnum) → Optional[Board]`

1. Builds the group of `size` cells starting at `trailing` along direction `dnum`.
2. Verifies every cell in the group belongs to `player`.
3. Checks the cell immediately ahead of the group (`ahead`):
   - **Empty** → calls `_shift_group()` to produce the new board.
   - **Opponent marble** → counts the consecutive opponent chain; if the chain is strictly smaller than `size` and the cell beyond it is empty or off-board, removes both groups and places them shifted one step forward.
   - **Friendly marble or off-board** → returns `None` (illegal move).

#### `apply_sidestep(board, player, trailing, size, line_dnum, move_dnum) → Optional[Board]`

1. Builds the group of `size` cells along the line direction `line_dnum`.
2. Computes each marble's destination by applying the perpendicular move direction `move_dnum`.
3. If any destination is outside `CELLS` or already occupied, returns `None`.
4. Otherwise removes the group and places each marble at its destination.

Both functions return `None` to signal an illegal move, keeping the caller clean. The new board is always a **shallow copy** (`dict(board)`) so the original state is never modified.

---

## 2. Design and Architecture of the State Space Generator

### 2.1 High-Level Overview

The generator is implemented as a single self-contained Python module (`move_engine.py`) with no third-party dependencies. Its responsibility is to:

1. Read one board state from an input file.
2. Enumerate every legal move available to the current player.
3. Apply each move to obtain the successor board.
4. Write all moves and successor boards to output files.

The code is organised into five clearly separated layers:

```
┌─────────────────────────────────────────────┐
│                  Entry Point                │  main()
├─────────────────────────────────────────────┤
│               I/O Layer                     │  parse_input_file(), write_outputs()
├─────────────────────────────────────────────┤
│            Move Generation Layer            │  generate_moves(),
│                                             │  _collect_inline_moves(),
│                                             │  _collect_sidestep_moves()
├─────────────────────────────────────────────┤
│          Transition Model Layer             │  apply_inline(), apply_sidestep(),
│                                             │  _shift_group()
├─────────────────────────────────────────────┤
│        Board / Coordinate Utilities         │  cell_add(), cell_scale(),
│                                             │  notation_to_axial(), axial_to_notation(),
│                                             │  player_cells(), group_cells(), opponent()
└─────────────────────────────────────────────┘
```

### 2.2 Module-Level Constants

All fixed data is declared at module scope so it is computed once and shared:

| Constant | Purpose |
|----------|---------|
| `RADIUS = 4` | Half-width of the board in axial coordinates |
| `DIRS` | Maps each direction number to its `(Δq, Δr)` vector |
| `DIR_LIST` | Ordered list of all six direction numbers |
| `OPPOSITE` | Maps each direction to its 180° opposite |
| `CANONICAL_DIRS` | The three unique line orientations `{1, 3, 11}` used to enumerate side-step groups without duplication |
| `ROW_START`, `ROW_LEN` | Column bounds for each row letter `A`–`I` |
| `CELLS` | Pre-computed frozenset of all 61 valid board cells |
| `_MARBLE_RE` | Compiled regular expression for parsing marble tokens |

### 2.3 Coordinate System

The axial `(q, r)` system is chosen because:

- Adjacency is simply adding a direction vector: `cell_add(c, DIRS[d])`.
- Multi-step groups are generated with `cell_scale`: `cell_add(origin, cell_scale(d, i))`.
- Boundary checks reduce to three absolute-value inequalities.
- The mapping to/from the standard `<Row><Col>` notation is a linear arithmetic transformation (`notation_to_axial` / `axial_to_notation`), with no special-casing per row.

### 2.4 Move Generation Pipeline

`generate_moves(player, board)` orchestrates two sub-generators and deduplicates their output:

```
generate_moves(player, board)
│
├── _collect_inline_moves(board, player, seen)
│     For each friendly cell (origin):
│       For each direction d in DIR_LIST:
│         For each group size k ∈ {1, 2, 3}:
│           Build group → validate → apply_inline → record Move
│
└── _collect_sidestep_moves(board, player, seen)
      For each friendly cell (origin):
        For each canonical line direction ld ∈ {1, 3, 11}:
          For each group size k ∈ {2, 3}:
            Build group → validate →
              For each perpendicular move direction md:
                apply_sidestep → normalise endpoints → record Move
```

A shared `seen: Set[str]` of move notation strings is passed into both helpers. Any move whose notation is already present is silently discarded, preventing duplicates that would arise from iterating over overlapping groups. The final list is sorted lexicographically by notation string for deterministic, reproducible output.

#### Why Canonical Directions for Side-steps?

Using all six directions for the line axis would enumerate every group twice (once from each end). Restricting to only `{1, 3, 11}` (the three non-opposite pairs) ensures each group is visited exactly once. The `seen` set acts as a safety net for any edge cases.

### 2.5 Key Data Structures

| Structure | Type | Role |
|-----------|------|------|
| `board` | `Dict[Cell, Player]` | Current board state — absent keys are empty cells |
| `Move` | frozen `dataclass` | Immutable, hashable action representation |
| `seen` | `Set[str]` | Deduplication of move notations during generation |
| `results` | `List[Tuple[Move, Board]]` | Paired list of (move, successor board) |
| `CELLS` | `Set[Cell]` | Fast `O(1)` board-boundary check |

### 2.6 I/O Layer

`parse_input_file(path)` reads the two-line input format and builds the initial `(player, board)` state, validating every marble token against `_MARBLE_RE` and the coordinate bounds.

`write_outputs(input_path, moves)` derives the output filenames from the input filename stem and writes both files in a single pass, keeping move and board lines aligned by index.

### 2.7 Error Handling

All invalid inputs (bad row letter, out-of-range column, duplicate marble, unknown player) raise `ValueError` with a descriptive message. Move functions return `None` rather than raising exceptions, which keeps the generation loop simple.

---

## 3. Move Notation

### 3.1 Format

Every move is expressed as a hyphen-separated string. There are three forms:

| Move type | Format | Fields |
|-----------|--------|--------|
| Inline — single marble | `i-An-D` | `An` = marble position |
| Inline — group of 2 or 3 | `i-An-Bm-D` | `An` = trailing marble, `Bm` = leading marble |
| Side-step — group of 2 or 3 | `s-An-Bm-D` | `An`, `Bm` = group extremities (sorted) |

- `i` / `s` — move type (inline or side-step)
- `An`, `Bm` — marble positions in `<Row><Col>` notation (e.g. `E5`, `D4`)
- `D` — direction number from the set `{1, 3, 5, 7, 9, 11}`

### 3.2 Field Definitions

#### Move type

| Character | Meaning |
|-----------|---------|
| `i` | **Inline** — the group moves along its own axis |
| `s` | **Side-step** — the group moves perpendicular to its axis |

#### Marble positions

Positions use the standard Abalone board notation:
- **Row** — a letter `A`–`I`, where `A` is the bottom row and `I` is the top row
- **Col** — an integer; valid range varies by row (see the column table in the README)

For **inline moves**, `An` is the **trailing** marble (furthest from the direction of movement) and `Bm` is the **leading** marble (closest to the direction of movement).

For **side-step moves**, `An` and `Bm` are the two **extremities** of the group, normalised so that `An` always sorts before `Bm` (row letter first, then column number). This ensures each side-step move has exactly one canonical notation regardless of which end is chosen as the starting point during enumeration.

#### Direction number

| D  | Direction       | Axial delta `(Δq, Δr)` |
|----|-----------------|------------------------|
| 1  | NE (up-right)   | `(+1, −1)` |
| 3  | E  (right)      | `(+1,  0)` |
| 5  | SE (down-right) | `( 0, +1)` |
| 7  | SW (down-left)  | `(−1, +1)` |
| 9  | W  (left)       | `(−1,  0)` |
| 11 | NW (up-left)    | `( 0, −1)` |

### 3.3 Examples

| Notation | Interpretation |
|----------|---------------|
| `i-E5-3` | Move the single black/white marble at E5 one step to the right (East) |
| `i-D4-E5-1` | Move the inline group from trailing marble D4 to leading marble E5 in direction NE |
| `i-C3-E5-1` | Move a three-marble inline group (C3–D4–E5) forward in direction NE (2-1 Sumito possible) |
| `s-D4-D6-5` | Side-step the group with extremities D4 and D6 one step in direction SE |
| `s-C5-E5-7` | Side-step the group with extremities C5 and E5 one step in direction SW |

### 3.4 Notation Construction in Code

The `Move.notation()` method assembles the string from its fields:

```python
def notation(self) -> str:
    parts = [self.kind, self.a]
    if self.b is not None:
        parts.append(self.b)
    parts.append(str(self.d))
    return "-".join(parts)
```

For side-step moves, the extremities are normalised before the `Move` object is created:

```python
if notation_sort_key(a) > notation_sort_key(b):
    a, b = b, a
```

This guarantees that the same physical group side-stepping in the same direction always produces an identical notation string, which is also the key used for deduplication in the `seen` set.

