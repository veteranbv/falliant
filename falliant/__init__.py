"""
Falliant - A terminal-based block stacking game
"""

__version__ = "0.1.0"

import curses
import sys

from .constants import GAME_NAME
from .ui import GameUI


def main():
    """Main entry point for the game"""
    try:
        # Use curses wrapper to handle initialization and cleanup
        curses.wrapper(run_game)
        return 0
    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        return 130
    except curses.error as e:
        print(f"Terminal error: {e}")
        print(f"Please ensure your terminal is large enough to play {GAME_NAME}.")
        print("Minimum recommended size: 80x24")
        return 1


def run_game(stdscr):
    """Run the game with the initialized curses screen"""
    # Create and run the UI
    ui = GameUI(stdscr)
    ui.run()


if __name__ == "__main__":
    sys.exit(main())
