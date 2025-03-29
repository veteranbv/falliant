"""
UI module for Falliant
Handles user input and game state control
"""

import curses
import json
import os
import time
from typing import Dict, List, Optional

from .constants import FRAMERATE, HIGH_SCORES_FILE
from .game import GameState
from .renderer import GameRenderer

# Game states
STATE_MENU = 0
STATE_GAME = 1
STATE_LEVEL_SELECT = 2
STATE_HIGH_SCORES = 3
STATE_CONFIRM_QUIT = 4
STATE_ENTER_INITIALS = 5  # New state for entering initials


class GameUI:
    """Handles user interface and input for the game"""

    def __init__(self, stdscr):
        """Initialize the UI with the curses screen"""
        self.stdscr = stdscr

        # Set up curses
        curses.curs_set(0)  # Hide cursor
        self.stdscr.nodelay(True)  # Non-blocking input
        self.stdscr.timeout(0)  # No delay

        # Enable keypad for special keys (like arrows)
        self.stdscr.keypad(True)

        # Initialize game state variables
        self.game_state: Optional[GameState] = None
        self.renderer = GameRenderer(stdscr)
        self.current_ui_state = STATE_MENU
        self.running = True
        self.selected_menu_option = 0
        self.selected_level = 1
        self.max_level = 10
        self.selected_high_score_index = 0
        self.confirm_quit_selected = 0
        self.high_scores = self._load_high_scores()

        # Variables for entering initials
        self.new_high_score = False
        self.current_initials = ["A", "A", "A"]  # Default initials
        self.initial_index = 0  # Current position in initials
        self.pending_score = 0
        self.pending_level = 0
        self.pending_lines = 0

        # Frame timing
        self.frame_time = 1.0 / FRAMERATE

        # Store special key codes for clearer handling
        self.KEY_SPACE = 32  # Space bar key code (ASCII)
        self.KEY_UP = curses.KEY_UP
        self.KEY_DOWN = curses.KEY_DOWN
        self.KEY_LEFT = curses.KEY_LEFT
        self.KEY_RIGHT = curses.KEY_RIGHT
        self.KEY_ENTER = 10  # Enter key code
        self.KEY_ESC = 27  # Escape key code

        # For debugging - last key pressed
        self.last_key = 0

        # Add a drop debounce flag to prevent multiple drops
        self.drop_debounce = False
        self.last_drop_time = 0

        # Show intro screen at startup
        self.show_intro_screen()

    def _load_high_scores(self) -> List[Dict]:
        """Load high scores from file"""
        if os.path.exists(HIGH_SCORES_FILE):
            try:
                with open(HIGH_SCORES_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass

        return []

    def _save_high_scores(self):
        """Save high scores to file"""
        try:
            with open(HIGH_SCORES_FILE, "w") as f:
                json.dump(self.high_scores, f)
        except IOError:
            pass  # Silently fail if can't write

    def _add_high_score(self, score: int, level: int, lines: int):
        """Check if score qualifies for high score and set up initials entry if it does"""
        # Check if score qualifies for top 10
        if len(self.high_scores) < 10 or score > self.high_scores[-1]["score"]:
            # Set up for entering initials
            self.pending_score = score
            self.pending_level = level
            self.pending_lines = lines
            self.current_initials = ["A", "A", "A"]
            self.initial_index = 0
            self.new_high_score = True
            self.current_ui_state = STATE_ENTER_INITIALS
            # Switch to blocking input for initials entry
            self.stdscr.nodelay(False)
            return True
        return False

    def _save_high_score(self):
        """Save the high score with initials to the list"""
        # Get the initials as a string
        initials = "".join(self.current_initials)

        # Add to list
        self.high_scores.append(
            {
                "initials": initials,
                "score": self.pending_score,
                "level": self.pending_level,
                "lines": self.pending_lines,
                "date": time.strftime("%Y-%m-%d %H:%M"),
            }
        )

        # Sort by score (descending)
        self.high_scores = sorted(
            self.high_scores, key=lambda x: x["score"], reverse=True
        )

        # Keep only top 10
        if len(self.high_scores) > 10:
            self.high_scores = self.high_scores[:10]

        # Save to file
        self._save_high_scores()

        # Reset
        self.new_high_score = False

    def _handle_initials_input(self):
        """Handle input when entering initials for high score"""
        key = self.stdscr.getch()

        if key != -1:
            self.last_key = key

        # Handle letter selection (up/down)
        if key == self.KEY_UP or key == ord("w") or key == ord("W"):
            # Move to next letter (A->B->C->...->Y->Z->A)
            current = ord(self.current_initials[self.initial_index])
            next_letter = chr(((current - ord("A") + 1) % 26) + ord("A"))
            self.current_initials[self.initial_index] = next_letter

        elif key == self.KEY_DOWN or key == ord("s") or key == ord("S"):
            # Move to previous letter (Z->Y->X->...->B->A->Z)
            current = ord(self.current_initials[self.initial_index])
            prev_letter = chr(((current - ord("A") - 1) % 26) + ord("A"))
            self.current_initials[self.initial_index] = prev_letter

        # Handle moving between positions (left/right)
        elif key == self.KEY_LEFT or key == ord("a") or key == ord("A"):
            self.initial_index = (self.initial_index - 1) % 3

        elif key == self.KEY_RIGHT or key == ord("d") or key == ord("D"):
            self.initial_index = (self.initial_index + 1) % 3

        # Confirm initials with Enter
        elif key == self.KEY_ENTER or key == ord("\n"):
            self._save_high_score()
            self.current_ui_state = STATE_HIGH_SCORES
            self.selected_high_score_index = 0
            # Restore non-blocking input
            self.stdscr.nodelay(True)

        # Cancel with Escape
        elif key == self.KEY_ESC:
            self.new_high_score = False
            self.current_ui_state = STATE_MENU
            # Restore non-blocking input
            self.stdscr.nodelay(True)

    def _handle_game_input(self):
        """Handle input during gameplay"""
        if self.game_state is None:
            return

        key = self.stdscr.getch()
        current_time = time.time()

        # Store last key for debugging
        if key != -1:
            self.last_key = key

        # If game is over, handle game over input
        if self.game_state.game_over:
            if key != -1:  # Any key pressed
                # If it's a high score, proceed to enter initials
                if self.new_high_score:
                    # We're already set to show initials screen
                    return
                # Otherwise return to menu
                self.current_ui_state = STATE_MENU
            return

        # Reset drop debounce if space is not being pressed and enough time has passed
        if (
            key != self.KEY_SPACE
            and key != ord(" ")
            and current_time - self.last_drop_time > 0.3
        ):
            self.drop_debounce = False

        # Handle special keys
        if key == self.KEY_LEFT:
            self.game_state.move_left()
        elif key == self.KEY_RIGHT:
            self.game_state.move_right()
        elif key == self.KEY_DOWN:
            self.game_state.move_down()
        elif key == self.KEY_UP:
            self.game_state.rotate()
        elif (key == self.KEY_SPACE or key == ord(" ")) and not self.drop_debounce:
            # Only drop if not currently in debounce period
            drop_result = self.game_state.drop_block()

            # Always activate debounce after drop, successful or not
            self.drop_debounce = True
            self.last_drop_time = current_time

            # Since drop immediately spawns a new piece, we need to clear pending input
            # to prevent the new piece from receiving the same input
            if drop_result:
                curses.flushinp()
        # Allow w key as alternative for rotate
        elif key == ord("w") or key == ord("W"):
            self.game_state.rotate()
        # Allow a/d as alternatives for left/right
        elif key == ord("a") or key == ord("A"):
            self.game_state.move_left()
        elif key == ord("d") or key == ord("D"):
            self.game_state.move_right()
        elif key == ord("s") or key == ord("S"):
            self.game_state.move_down()
        elif key == ord("c") or key == ord("C"):
            self.game_state.hold_block()
        elif key == ord("p") or key == ord("P"):
            self.game_state.toggle_pause()
        elif key == ord("q") or key == ord("Q"):
            self.current_ui_state = STATE_CONFIRM_QUIT
            self.confirm_quit_selected = 0

    def _handle_menu_input(self):
        """Handle input in the main menu"""
        key = self.stdscr.getch()

        if key != -1:
            self.last_key = key

        if key == self.KEY_UP or key == ord("w") or key == ord("W"):
            self.selected_menu_option = (self.selected_menu_option - 1) % 4
        elif key == self.KEY_DOWN or key == ord("s") or key == ord("S"):
            self.selected_menu_option = (self.selected_menu_option + 1) % 4
        elif key == self.KEY_ENTER or key == ord("\n"):  # Enter key
            if self.selected_menu_option == 0:  # Start Game
                self.game_state = GameState(self.selected_level)
                self.current_ui_state = STATE_GAME
            elif self.selected_menu_option == 1:  # Level Select
                self.current_ui_state = STATE_LEVEL_SELECT
            elif self.selected_menu_option == 2:  # High Scores
                self.current_ui_state = STATE_HIGH_SCORES
                self.selected_high_score_index = 0
            elif self.selected_menu_option == 3:  # Quit
                self.running = False

    def _handle_level_select_input(self):
        """Handle input in the level select screen"""
        key = self.stdscr.getch()

        if key != -1:
            self.last_key = key

        if key == self.KEY_UP or key == ord("w") or key == ord("W"):
            self.selected_level = max(1, self.selected_level - 5)
        elif key == self.KEY_DOWN or key == ord("s") or key == ord("S"):
            self.selected_level = min(self.max_level, self.selected_level + 5)
        elif key == self.KEY_LEFT or key == ord("a") or key == ord("A"):
            self.selected_level = max(1, self.selected_level - 1)
        elif key == self.KEY_RIGHT or key == ord("d") or key == ord("D"):
            self.selected_level = min(self.max_level, self.selected_level + 1)
        elif key == self.KEY_ENTER or key == ord("\n"):  # Enter key
            self.current_ui_state = STATE_MENU
        elif key == self.KEY_ESC:  # Escape key
            self.current_ui_state = STATE_MENU

    def _handle_high_scores_input(self):
        """Handle input in the high scores screen"""
        key = self.stdscr.getch()

        if key != -1:
            self.last_key = key

        if key == self.KEY_UP or key == ord("w") or key == ord("W"):
            self.selected_high_score_index = max(0, self.selected_high_score_index - 1)
        elif key == self.KEY_DOWN or key == ord("s") or key == ord("S"):
            max_index = min(10, len(self.high_scores)) - 1
            self.selected_high_score_index = min(
                max_index, self.selected_high_score_index + 1
            )
        elif key == self.KEY_ESC:  # Escape key
            self.current_ui_state = STATE_MENU

    def _handle_confirm_quit_input(self):
        """Handle input in the confirm quit dialog"""
        key = self.stdscr.getch()

        if key != -1:
            self.last_key = key

        if key == self.KEY_LEFT or key == ord("a") or key == ord("A"):
            self.confirm_quit_selected = 0  # No
        elif key == self.KEY_RIGHT or key == ord("d") or key == ord("D"):
            self.confirm_quit_selected = 1  # Yes
        elif key == self.KEY_ENTER or key == ord("\n"):  # Enter key
            if self.confirm_quit_selected == 1:  # Yes
                # We only add the score if the game is not already over
                # This prevents duplicate high score entries
                if (
                    self.game_state
                    and not self.game_state.game_over
                    and not self.new_high_score
                ):
                    self._add_high_score(
                        self.game_state.score,
                        self.game_state.level,
                        self.game_state.lines_cleared,
                    )
                self.current_ui_state = STATE_MENU
            else:  # No
                self.current_ui_state = STATE_GAME
        elif key == self.KEY_ESC:  # Escape key
            self.current_ui_state = STATE_GAME

    def _draw_debug_info(self):
        """Draw debug information on screen"""
        debug_info = f"Last key: {self.last_key}"
        self.renderer._safe_addstr(0, 0, debug_info)

    def show_intro_screen(self):
        """Show the intro screen with game information"""
        # Temporarily set nodelay to False for this screen
        self.stdscr.nodelay(False)

        # Clear any pending input
        curses.flushinp()

        # Show the intro screen
        self.renderer.draw_intro_screen()

        # Clear any pending input again after the intro screen
        curses.flushinp()

        # Reset nodelay to True for the main game
        self.stdscr.nodelay(True)

    def run(self):
        """Main game loop"""
        last_block_id = None

        while self.running:
            # Handle input based on current state
            if self.current_ui_state == STATE_GAME:
                self._handle_game_input()
            elif self.current_ui_state == STATE_MENU:
                self._handle_menu_input()
            elif self.current_ui_state == STATE_LEVEL_SELECT:
                self._handle_level_select_input()
            elif self.current_ui_state == STATE_HIGH_SCORES:
                self._handle_high_scores_input()
            elif self.current_ui_state == STATE_CONFIRM_QUIT:
                self._handle_confirm_quit_input()
            elif self.current_ui_state == STATE_ENTER_INITIALS:
                self._handle_initials_input()

            # Update game state
            if self.current_ui_state == STATE_GAME and self.game_state:
                # Check if the block has changed since last frame
                current_block_id = (
                    id(self.game_state.current_block)
                    if self.game_state.current_block
                    else None
                )

                if last_block_id is not None and current_block_id != last_block_id:
                    # A new block has spawned
                    curses.flushinp()  # Clear any pending input
                    # Activate debounce after a new block spawns
                    self.drop_debounce = True
                    self.last_drop_time = time.time()

                last_block_id = current_block_id

                # Update game state
                self.game_state.update()

                # Check if game is over
                if self.game_state.game_over and not self.new_high_score:
                    # Add to high scores if not already added
                    self._add_high_score(
                        self.game_state.score,
                        self.game_state.level,
                        self.game_state.lines_cleared,
                    )

            # Render current state
            if self.current_ui_state == STATE_GAME and self.game_state:
                if self.game_state.game_over:
                    self.renderer.draw_game_over(self.game_state)
                else:
                    self.renderer.draw_game_screen(self.game_state)
            elif self.current_ui_state == STATE_MENU:
                self.renderer.draw_menu(self.selected_menu_option, self.high_scores)
            elif self.current_ui_state == STATE_LEVEL_SELECT:
                self.renderer.draw_level_select(self.selected_level, self.max_level)
            elif self.current_ui_state == STATE_HIGH_SCORES:
                self.renderer.draw_high_scores(
                    self.high_scores, self.selected_high_score_index
                )
            elif self.current_ui_state == STATE_CONFIRM_QUIT:
                self.renderer.draw_confirm_quit(self.confirm_quit_selected)
            elif self.current_ui_state == STATE_ENTER_INITIALS:
                # Pass initial_index directly to the method instead of setting it on stdscr
                self.renderer.draw_enter_initials(
                    self.current_initials, self.initial_index
                )

            # Control frame rate
            time.sleep(self.frame_time)

            # Check for terminal resize
            if curses.is_term_resized(
                self.stdscr.getmaxyx()[0], self.stdscr.getmaxyx()[1]
            ):
                curses.resize_term(0, 0)
                self.renderer = GameRenderer(
                    self.stdscr
                )  # Recreate renderer with new dimensions
