"""
Constants for the Falliant game
"""

import curses

# Game name
GAME_NAME = "Falliant"

# Game constants
BOARD_WIDTH = 10
BOARD_HEIGHT = 20
FRAMERATE = 60  # Frames per second
BASE_FALL_DELAY = 20  # Frames between block falls at level 1

# Block shapes - using [ ] for each cell, with consistent spacing
BLOCK_SHAPES = [
    # I-piece (Cyan) - Index 0
    [
        ["[][][][]"],  # Rotation 1 - horizontal
        [
            "[]",
            "[]",
            "[]",
            "[]",
        ],  # Rotation 2 - vertical
    ],
    # O-piece (Yellow) - Index 1
    [["[][]", "[][]"]],  # Only rotation
    # T-piece (Purple/Magenta) - Index 2
    [
        ["  []  ", "[][][]"],  # Rotation 1 - pointing up
        ["[]    ", "[][]  ", "[]    "],  # Rotation 2 - pointing right
        ["[][][]", "  []  "],  # Rotation 3 - pointing down
        ["  []  ", "[][]  ", "  []  "],  # Rotation 4 - pointing left
    ],
    # J-piece (Blue) - Index 3
    [
        ["[]    ", "[][][]"],  # Rotation 1
        ["[][]  ", "[]    ", "[]    "],  # Rotation 2
        ["[][][]", "    []"],  # Rotation 3
        ["  []  ", "  []  ", "[][]  "],  # Rotation 4
    ],
    # L-piece (Orange) - Index 4
    [
        ["    []", "[][][]"],  # Rotation 1
        ["[]    ", "[]    ", "[][]  "],  # Rotation 2
        ["[][][]", "[]    "],  # Rotation 3
        ["[][]  ", "  []  ", "  []  "],  # Rotation 4
    ],
    # S-piece (Green) - Index 5
    [
        ["  [][]", "[][]  "],  # Rotation 1
        ["[]    ", "[][]  ", "  []  "],  # Rotation 2
    ],
    # Z-piece (Red) - Index 6
    [
        ["[][]  ", "  [][]"],  # Rotation 1
        ["  []  ", "[][]  ", "[]    "],  # Rotation 2
    ],
]

# Block colors using curses constants
BLOCK_COLORS = [
    curses.COLOR_CYAN,  # I-piece
    curses.COLOR_YELLOW,  # O-piece
    curses.COLOR_MAGENTA,  # T-piece
    curses.COLOR_BLUE,  # J-piece
    curses.COLOR_WHITE,  # L-piece - Using WHITE to distinguish from Z-piece
    curses.COLOR_GREEN,  # S-piece
    curses.COLOR_RED,  # Z-piece
]

# Direction constants
DIRECTION_DOWN = 0
DIRECTION_RIGHT = 1
DIRECTION_LEFT = 2

# File to store high scores
HIGH_SCORES_FILE = "falliant_high_scores.json"

# Scoring constants
SCORING = {
    1: 40,  # 1 line: 40 × level
    2: 100,  # 2 lines: 100 × level
    3: 300,  # 3 lines: 300 × level
    4: 1200,  # 4 lines: 1200 × level (Falliant!)
}
