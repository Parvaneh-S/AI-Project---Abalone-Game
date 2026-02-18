"""
Constants for the Abalone game application.
"""
import math

# ----------------------------
# Window
# ----------------------------
WINDOW_W = 900
WINDOW_H = 750
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
CELL_RADIUS = 20  # Increased for bigger board
CELL_GAP = 9      # Proportionally increased

DX = 2 * CELL_RADIUS + CELL_GAP
DY = int((math.sqrt(3) / 2) * DX)

BOARD_CENTER = (WINDOW_W // 2, WINDOW_H // 2)  # Perfectly centered

# ----------------------------
# Rim / padding controls
# ----------------------------
RIM_WIDTH = 38        # Proportionally increased for bigger board
CELL_MARGIN = 8       # Proportionally increased

# ----------------------------
# Landing Page
# ----------------------------
LANDING_PAGE_IMAGES = ["landing_page_icon.png", "landing_logo.png", "icon.png", "icon.jpg"]
LANDING_TEXT_COLOR = (255, 255, 255)
LANDING_BG_COLOR = (245, 235, 220)  # Cream color matching the landing page icon background
LANDING_TEXT_BG_COLOR = (0, 0, 0, 180)

