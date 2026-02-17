import math
import sys
import pygame

# ----------------------------
# Window
# ----------------------------
WINDOW_W, WINDOW_H = 900, 750
FPS = 60

# ----------------------------
# Colors
# ----------------------------
BORDER_COLOR = (166, 112, 74)     # brown
BOARD_FILL = (239, 225, 196)      # beige
BG_COLOR = (255, 255, 255)        # outside

EMPTY_COLOR = (145, 145, 145)     # gray
WHITE_COLOR = (245, 245, 245)
BLACK_COLOR = (15, 15, 15)

# ----------------------------
# Abalone layout (61 cells)
# ----------------------------
ROW_COUNTS = [5, 6, 7, 8, 9, 8, 7, 6, 5]

# ----------------------------
# Cell geometry
# ----------------------------
CELL_RADIUS = 22
CELL_GAP = 10

DX = 2 * CELL_RADIUS + CELL_GAP
DY = int((math.sqrt(3) / 2) * DX)

BOARD_CENTER = (WINDOW_W // 2, WINDOW_H // 2 + 10)

# ----------------------------
# Rim / padding controls
# ----------------------------
RIM_WIDTH = 42        # <-- make rim wider by increasing this
CELL_MARGIN = 8       # space between outermost circles and inner hex edge


def compute_cell_centers(center_xy: tuple[int, int]) -> list[list[tuple[int, int]]]:
    """Return cell centers laid out in rows: 5-6-7-8-9-8-7-6-5."""
    cx, cy = center_xy
    rows: list[list[tuple[int, int]]] = []

    total_rows = len(ROW_COUNTS)
    top_y = cy - (total_rows - 1) * DY // 2

    for r, count in enumerate(ROW_COUNTS):
        y = top_y + r * DY
        row_width = (count - 1) * DX
        start_x = cx - row_width // 2
        rows.append([(start_x + c * DX, y) for c in range(count)])

    return rows


def hex_polygon_around_cells(rows: list[list[tuple[int, int]]], extra: int) -> list[tuple[int, int]]:
    """
    Build a hexagon polygon around all circles.
    `extra` expands past the outermost circle boundary.

    For a regular hexagon with flat top/bottom, each vertex needs to be offset
    along the perpendicular bisector of the two adjacent edges (120° angle at each vertex).
    The offset direction at each vertex is 60° from the edges.
    """
    padding = CELL_RADIUS + extra

    # Get base positions from key cells
    top_left_base = rows[0][0]
    top_right_base = rows[0][-1]
    mid_right_base = rows[4][-1]
    bottom_right_base = rows[8][-1]
    bottom_left_base = rows[8][0]
    mid_left_base = rows[4][0]

    # For a regular hexagon, to offset parallel, we scale outward from center
    # OR offset each vertex perpendicular to its edges
    # The perpendicular offset at each 120° vertex corner is at the angle bisector (60° from each edge)

    # For a pointy-side hexagon (flat top), the 6 vertices are at angles:
    # from center: 30°, 90°, 150°, 210°, 270°, 330°
    # But our hexagon has flat sides on left/right, so vertices are at:
    # Top-left: 120°, Top-right: 60°, Right: 0°, Bottom-right: 300°, Bottom-left: 240°, Left: 180°

    # Offset each vertex perpendicular to the hexagon surface
    # For our flat-left-right hexagon orientation:
    cos30 = math.sqrt(3) / 2  # ≈ 0.866
    sin30 = 0.5

    # Top-left vertex (120° from center): offset at angle 120° outward
    top_left_x = top_left_base[0] - padding * sin30
    top_left_y = top_left_base[1] - padding * cos30

    # Top-right vertex (60° from center): offset at angle 60° outward
    top_right_x = top_right_base[0] + padding * sin30
    top_right_y = top_right_base[1] - padding * cos30

    # Middle-right vertex (0° from center): offset purely right
    mid_right_x = mid_right_base[0] + padding
    mid_right_y = mid_right_base[1]

    # Bottom-right vertex (300° from center): offset at angle 300° outward
    bottom_right_x = bottom_right_base[0] + padding * sin30
    bottom_right_y = bottom_right_base[1] + padding * cos30

    # Bottom-left vertex (240° from center): offset at angle 240° outward
    bottom_left_x = bottom_left_base[0] - padding * sin30
    bottom_left_y = bottom_left_base[1] + padding * cos30

    # Middle-left vertex (180° from center): offset purely left
    mid_left_x = mid_left_base[0] - padding
    mid_left_y = mid_left_base[1]

    return [
        (int(top_left_x), int(top_left_y)),
        (int(top_right_x), int(top_right_y)),
        (int(mid_right_x), int(mid_right_y)),
        (int(bottom_right_x), int(bottom_right_y)),
        (int(bottom_left_x), int(bottom_left_y)),
        (int(mid_left_x), int(mid_left_y)),
    ]


def example_marbles() -> dict[tuple[int, int], tuple[int, int, int]]:
    """Just to match the screenshot vibe. Remove if you want all gray."""
    colors: dict[tuple[int, int], tuple[int, int, int]] = {}

    # Top whites
    for c in range(ROW_COUNTS[0]):
        colors[(0, c)] = WHITE_COLOR
    for c in range(ROW_COUNTS[1]):
        colors[(1, c)] = WHITE_COLOR
    for c in range(2, 5):  # middle whites on row 2
        colors[(2, c)] = WHITE_COLOR

    # Bottom blacks
    last = len(ROW_COUNTS) - 1
    for c in range(ROW_COUNTS[last]):
        colors[(last, c)] = BLACK_COLOR
    for c in range(ROW_COUNTS[last - 1]):
        colors[(last - 1, c)] = BLACK_COLOR
    for c in range(2, 5):  # middle blacks on row 6
        colors[(6, c)] = BLACK_COLOR

    return colors


def draw_board(screen: pygame.Surface, rows: list[list[tuple[int, int]]]) -> None:
    # Inner hex should fully contain all circles (radius + margin)
    inner_hex = hex_polygon_around_cells(rows, extra=CELL_MARGIN)

    # Outer hex is inner hex expanded by rim width
    outer_hex = hex_polygon_around_cells(rows, extra=CELL_MARGIN + RIM_WIDTH)

    # Draw rim and inner fill
    pygame.draw.polygon(screen, BORDER_COLOR, outer_hex)
    pygame.draw.polygon(screen, BOARD_FILL, inner_hex)

    # Draw circles (all will sit inside inner_hex now)
    marble_map = example_marbles()
    for r, row in enumerate(rows):
        for c, (x, y) in enumerate(row):
            color = marble_map.get((r, c), EMPTY_COLOR)
            pygame.draw.circle(screen, (120, 120, 120), (x, y), CELL_RADIUS + 1)
            pygame.draw.circle(screen, color, (x, y), CELL_RADIUS)


def create_icon() -> pygame.Surface:
    """Create a simple hexagon icon for the window."""
    icon_size = 32
    icon = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)

    # Create hexagon vertices for icon
    cx, cy = icon_size // 2, icon_size // 2
    radius = icon_size // 2 - 2

    cos30 = math.sqrt(3) / 2
    sin30 = 0.5

    hex_points = [
        (cx - radius * sin30, cy - radius * cos30),
        (cx + radius * sin30, cy - radius * cos30),
        (cx + radius, cy),
        (cx + radius * sin30, cy + radius * cos30),
        (cx - radius * sin30, cy + radius * cos30),
        (cx - radius, cy),
    ]

    # Draw brown hexagon border
    pygame.draw.polygon(icon, BORDER_COLOR, hex_points)
    # Draw smaller beige hexagon inside
    inner_points = [(cx + (p[0]-cx)*0.7, cy + (p[1]-cy)*0.7) for p in hex_points]
    pygame.draw.polygon(icon, BOARD_FILL, inner_points)

    return icon


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Abalone- Marble Masters")

    # Set custom window icon
    # Try to load icon from file, otherwise create programmatic one
    try:
        icon = pygame.image.load("icon.png")
        pygame.display.set_icon(icon)
    except (FileNotFoundError, pygame.error):
        try:
            icon = pygame.image.load("icon.jpg")
            pygame.display.set_icon(icon)
        except (FileNotFoundError, pygame.error):
            # Fall back to programmatic icon
            icon = create_icon()
            pygame.display.set_icon(icon)

    clock = pygame.time.Clock()

    rows = compute_cell_centers(BOARD_CENTER)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        screen.fill(BG_COLOR)
        draw_board(screen, rows)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
