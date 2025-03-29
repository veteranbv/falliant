"""
Renderer module for Falliant
Handles drawing the game elements to the screen using curses
"""

import curses
from typing import Dict, List

from .block import Block
from .constants import BOARD_HEIGHT, BOARD_WIDTH, GAME_NAME
from .game import GameState


class GameRenderer:
    """Handles rendering the game to the terminal"""

    def __init__(self, stdscr):
        """Initialize the renderer with the curses screen"""
        self.stdscr = stdscr
        self.height, self.width = stdscr.getmaxyx()

        # Initialize colors
        self._init_colors()

    def _init_colors(self):
        """Initialize color pairs for blocks and UI elements"""
        curses.start_color()

        # Base colors
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)  # I-piece
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # O-piece
        curses.init_pair(3, curses.COLOR_MAGENTA, curses.COLOR_BLACK)  # T-piece
        curses.init_pair(4, curses.COLOR_BLUE, curses.COLOR_BLACK)  # J-piece
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_BLACK)  # L-piece
        curses.init_pair(6, curses.COLOR_GREEN, curses.COLOR_BLACK)  # S-piece
        curses.init_pair(7, curses.COLOR_RED, curses.COLOR_BLACK)  # Z-piece

        # UI colors
        curses.init_pair(8, curses.COLOR_BLACK, curses.COLOR_WHITE)  # Highlight
        curses.init_pair(9, curses.COLOR_WHITE, curses.COLOR_BLACK)  # Normal text
        curses.init_pair(10, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Title

    def _safe_addch(self, y: int, x: int, ch, attr=0):
        """Safely add a character to the screen, checking bounds"""
        if 0 <= y < self.height - 1 and 0 <= x < self.width - 1:  # Leave 1 cell margin
            try:
                self.stdscr.addch(y, x, ch, attr)
            except curses.error:
                pass  # Ignore errors (usually writing at bottom-right corner)

    def _safe_addstr(self, y: int, x: int, string: str, attr=0):
        """Safely add a string to the screen, checking bounds"""
        if 0 <= y < self.height - 1:  # Check vertical bounds
            # Handle horizontal bounds by truncating if needed
            max_len = self.width - x - 1 if x >= 0 else 0
            if max_len <= 0:
                return

            display_str = string[:max_len]
            try:
                self.stdscr.addstr(y, x, display_str, attr)
            except curses.error:
                pass  # Ignore errors

    def _draw_borders(
        self, start_y: int, start_x: int, board_height: int, board_width: int
    ):
        """Draw borders around the game board using Unicode box-drawing characters"""
        # Unicode box-drawing characters for better appearance
        HORIZONTAL = "═"
        VERTICAL = "║"
        TOP_LEFT = "╔"
        TOP_RIGHT = "╗"
        BOTTOM_LEFT = "╚"
        BOTTOM_RIGHT = "╝"

        # Draw horizontal borders
        for x in range(start_x + 1, start_x + board_width + 1):
            self._safe_addstr(start_y, x, HORIZONTAL)
            self._safe_addstr(start_y + board_height + 1, x, HORIZONTAL)

        # Draw vertical borders
        for y in range(start_y + 1, start_y + board_height + 1):
            self._safe_addstr(y, start_x, VERTICAL)
            self._safe_addstr(y, start_x + board_width + 1, VERTICAL)

        # Draw corners
        self._safe_addstr(start_y, start_x, TOP_LEFT)
        self._safe_addstr(start_y, start_x + board_width + 1, TOP_RIGHT)
        self._safe_addstr(start_y + board_height + 1, start_x, BOTTOM_LEFT)
        self._safe_addstr(
            start_y + board_height + 1, start_x + board_width + 1, BOTTOM_RIGHT
        )

    def _draw_block_cell(self, y: int, x: int, color_pair: int):
        """Draw a block cell with square brackets"""
        self._safe_addstr(y, x, "[]", curses.color_pair(color_pair))

    def _draw_block(
        self,
        block: Block,
        start_y: int,
        start_x: int,
        board_offset_y: int = 0,
        board_offset_x: int = 0,
    ):
        """Draw a block at the specified position"""
        if block is None:
            return

        shape = block.shape
        # Color pair is shape_index + 1 because color pairs start at 1
        color_pair = block.shape_index + 1

        for y, row in enumerate(shape):
            for x in range(len(row)):
                # Look for "[]" in each two characters
                if x + 1 < len(row) and row[x : x + 2] == "[]":
                    draw_y = start_y + y + board_offset_y
                    draw_x = start_x + x + board_offset_x

                    if 0 <= draw_y < self.height and 0 <= draw_x + 1 < self.width:
                        self._draw_block_cell(draw_y, draw_x, color_pair)

    def _draw_board(self, game_state: GameState, start_y: int, start_x: int):
        """Draw the game board and placed blocks"""
        # Draw border around the board
        self._draw_borders(start_y, start_x, BOARD_HEIGHT, BOARD_WIDTH * 2)

        # Draw placed blocks
        for y in range(BOARD_HEIGHT):
            for x in range(BOARD_WIDTH):
                color_pair = game_state.board[y][x]

                if color_pair != 0:
                    self._draw_block_cell(
                        start_y + y + 1, start_x + x * 2 + 1, color_pair
                    )

        # Draw current block
        if game_state.current_block and not game_state.game_over:
            shape = game_state.current_block.shape
            # Color pair is shape_index + 1 because color pairs start at 1
            color_pair = game_state.current_block.shape_index + 1

            # Special handling for I-piece horizontal (index 0, rotation 0)
            if (
                game_state.current_block.shape_index == 0
                and game_state.current_block.rotation == 0
            ):
                # Draw each cell carefully
                row = shape[0]
                for x in range(len(row)):
                    if x + 1 < len(row) and row[x : x + 2] == "[]":
                        # Calculate the proper position
                        board_x = game_state.current_block.x + (x // 2)
                        board_y = game_state.current_block.y

                        if 0 <= board_y < BOARD_HEIGHT and 0 <= board_x < BOARD_WIDTH:
                            self._draw_block_cell(
                                start_y + board_y + 1,
                                start_x + board_x * 2 + 1,
                                color_pair,
                            )
            else:
                # Draw other blocks normally
                for y, row in enumerate(shape):
                    for x in range(len(row)):
                        # Look for "[]" in each two characters
                        if x + 1 < len(row) and row[x : x + 2] == "[]":
                            board_y = game_state.current_block.y + y
                            board_x = game_state.current_block.x + (x // 2)

                            if (
                                0 <= board_y < BOARD_HEIGHT
                                and 0 <= board_x < BOARD_WIDTH
                            ):
                                self._draw_block_cell(
                                    start_y + board_y + 1,
                                    start_x + board_x * 2 + 1,
                                    color_pair,
                                )

    def _draw_sidebar(
        self, game_state: GameState, start_y: int, sidebar_x: int, sidebar_width: int
    ):
        """Draw the sidebar with game information"""
        # Draw game title
        title = GAME_NAME
        title_x = sidebar_x + (sidebar_width - len(title)) // 2
        self._safe_addstr(
            start_y, title_x, title, curses.color_pair(10) | curses.A_BOLD
        )

        # Calculate heights to make everything fit within board height
        section_height = BOARD_HEIGHT // 3

        # Draw score info section
        score_y = start_y + 2
        self._safe_addstr(score_y, sidebar_x, f"Score: {game_state.score}")
        self._safe_addstr(score_y + 1, sidebar_x, f"Level: {game_state.level}")
        self._safe_addstr(score_y + 2, sidebar_x, f"Lines: {game_state.lines_cleared}")

        # Draw next block preview
        next_label_y = score_y + section_height
        self._safe_addstr(next_label_y, sidebar_x, "Next:")

        if game_state.next_block:
            next_block_y = next_label_y + 1
            next_block_x = sidebar_x + 2
            # Color pair is shape_index + 1 because color pairs start at 1
            color_pair = game_state.next_block.shape_index + 1

            # Special handling for different block shapes
            shape = game_state.next_block.shape

            # For I-piece horizontal (rotation 0), display it properly
            if (
                game_state.next_block.shape_index == 0
                and game_state.next_block.rotation == 0
            ):
                # Draw it character by character to ensure it fits
                for x in range(min(len(shape[0]), 8)):
                    if x + 1 < len(shape[0]) and shape[0][x : x + 2] == "[]":
                        self._safe_addstr(
                            next_block_y,
                            next_block_x + x,
                            "[]",
                            curses.color_pair(color_pair),
                        )
            else:
                # Draw other blocks normally
                for y, row in enumerate(shape):
                    for x in range(min(len(row), sidebar_width - 4)):
                        # Look for "[]" in each two characters
                        if x + 1 < len(row) and row[x : x + 2] == "[]":
                            self._safe_addstr(
                                next_block_y + y,
                                next_block_x + x,
                                "[]",
                                curses.color_pair(color_pair),
                            )

        # Draw held block
        hold_label_y = next_label_y + section_height
        self._safe_addstr(hold_label_y, sidebar_x, "Hold:")

        if game_state.hold_block_index is not None:
            hold_y = hold_label_y + 1
            hold_x = sidebar_x + 2

            # Create a temporary block for display
            temp_block = Block(game_state.hold_block_index, 0, 0, 0)

            # Special handling for I-piece in hold
            if game_state.hold_block_index == 0:
                shape = temp_block.shape
                for x in range(min(len(shape[0]), 8)):
                    if x + 1 < len(shape[0]) and shape[0][x : x + 2] == "[]":
                        self._safe_addstr(
                            hold_y,
                            hold_x + x,
                            "[]",
                            curses.color_pair(game_state.hold_block_index + 1),
                        )
            else:
                # Draw the held block
                for y, row in enumerate(temp_block.shape):
                    for x in range(min(len(row), sidebar_width - 4)):
                        # Look for "[]" in each two characters
                        if x + 1 < len(row) and row[x : x + 2] == "[]":
                            self._safe_addstr(
                                hold_y + y,
                                hold_x + x,
                                "[]",
                                curses.color_pair(game_state.hold_block_index + 1),
                            )

        # Draw controls (compact version)
        controls_y = start_y + BOARD_HEIGHT - 7
        self._safe_addstr(controls_y, sidebar_x, "Controls:", curses.A_UNDERLINE)
        self._safe_addstr(controls_y + 1, sidebar_x, "←/→/A/D: Move")
        self._safe_addstr(controls_y + 2, sidebar_x, "↓/S: Down")
        self._safe_addstr(controls_y + 3, sidebar_x, "↑/W: Rotate")
        self._safe_addstr(controls_y + 4, sidebar_x, "Space: Drop")
        self._safe_addstr(controls_y + 5, sidebar_x, "C: Hold")
        self._safe_addstr(controls_y + 6, sidebar_x, "P: Pause Q: Quit")

    def draw_game_screen(self, game_state: GameState):
        """Draw the main game screen with board, next block, hold block, and controls"""
        self.stdscr.clear()

        # Calculate board dimensions
        board_display_width = BOARD_WIDTH * 2

        # Calculate positions for board and sidebar
        board_start_x = (self.width - board_display_width - 25) // 2
        board_start_y = (self.height - BOARD_HEIGHT) // 2
        sidebar_x = board_start_x + board_display_width + 5
        sidebar_width = 20

        # Draw board and UI elements
        self._draw_board(game_state, board_start_y, board_start_x)
        self._draw_sidebar(game_state, board_start_y, sidebar_x, sidebar_width)

        # Draw pause message if needed
        if game_state.paused:
            self._draw_paused(
                board_start_y, board_start_x, BOARD_HEIGHT, board_display_width
            )

        self.stdscr.refresh()

    def draw_game_over(self, game_state):
        """Draw the game over screen with final score"""
        # First draw the game screen as background
        self.draw_game_screen(game_state)

        # Calculate center position
        center_y = self.height // 2
        center_x = self.width // 2

        # Create a game over message box
        box_width = 40
        box_height = 7
        box_start_y = center_y - 3
        box_start_x = center_x - box_width // 2

        # Draw background for the message box (filled rectangle)
        for y in range(box_height):
            for x in range(box_width):
                self._safe_addstr(
                    box_start_y + y, box_start_x + x, " ", curses.A_REVERSE
                )

        # Draw border for the message box
        for x in range(box_width):
            self._safe_addstr(box_start_y, box_start_x + x, " ", curses.A_REVERSE)
            self._safe_addstr(
                box_start_y + box_height - 1, box_start_x + x, " ", curses.A_REVERSE
            )

        for y in range(box_height):
            self._safe_addstr(box_start_y + y, box_start_x, " ", curses.A_REVERSE)
            self._safe_addstr(
                box_start_y + y, box_start_x + box_width - 1, " ", curses.A_REVERSE
            )

        # Draw the title
        title = "GAME OVER"
        title_y = box_start_y + 1
        title_x = center_x - len(title) // 2
        self._safe_addstr(title_y, title_x, title, curses.A_BOLD | curses.color_pair(1))

        # Draw final score
        score_text = f"Final Score: {game_state.score}"
        score_x = center_x - len(score_text) // 2
        self._safe_addstr(box_start_y + 3, score_x, score_text, curses.A_BOLD)

        # Draw high score hint
        instructions = "Press ANY KEY to continue..."
        instructions_x = center_x - len(instructions) // 2
        self._safe_addstr(box_start_y + 5, instructions_x, instructions)

        self.stdscr.refresh()

    def _draw_paused(
        self, start_y: int, start_x: int, board_height: int, board_width: int
    ):
        """Draw the pause message"""
        message = "PAUSED"
        msg_y = start_y + board_height // 2
        msg_x = start_x + (board_width - len(message)) // 2

        self._safe_addstr(msg_y, msg_x, message, curses.A_BOLD)
        self._safe_addstr(msg_y + 1, msg_x - 6, "Press P to continue", curses.A_BOLD)

    def draw_menu(self, selected_option: int, high_scores: List[Dict]):
        """Draw the main menu"""
        self.stdscr.clear()

        # Calculate center position
        center_y = self.height // 2
        center_x = self.width // 2

        # Draw game title
        title = GAME_NAME
        title_y = center_y - 5
        title_x = center_x - len(title) // 2
        self._safe_addstr(
            title_y, title_x, title, curses.color_pair(10) | curses.A_BOLD
        )

        # Draw menu options
        menu_options = ["Start Game", "Level Select", "High Scores", "Quit"]

        for i, option in enumerate(menu_options):
            menu_y = center_y - 2 + i
            menu_x = center_x - len(option) // 2

            # Highlight selected option
            if i == selected_option:
                self._safe_addstr(menu_y, menu_x, option, curses.color_pair(8))
            else:
                self._safe_addstr(menu_y, menu_x, option)

        # Draw highest score if available
        if high_scores and len(high_scores) > 0:
            high_score = max(score["score"] for score in high_scores)
            score_text = f"High Score: {high_score}"
            score_y = center_y + 3
            score_x = center_x - len(score_text) // 2
            self._safe_addstr(score_y, score_x, score_text)

        # Draw controls
        controls_text = "↑/↓: Select | Enter: Confirm"
        controls_y = self.height - 2
        controls_x = center_x - len(controls_text) // 2
        self._safe_addstr(controls_y, controls_x, controls_text)

        self.stdscr.refresh()

    def draw_level_select(self, selected_level: int, max_level: int):
        """Draw the level select screen"""
        self.stdscr.clear()

        # Calculate center position
        center_y = self.height // 2
        center_x = self.width // 2

        # Draw title
        title = "Select Starting Level"
        title_y = center_y - 5
        title_x = center_x - len(title) // 2
        self._safe_addstr(
            title_y, title_x, title, curses.color_pair(10) | curses.A_BOLD
        )

        # Draw level options
        levels_per_row = 5
        levels_row_start = center_y - 2

        for level in range(1, max_level + 1):
            row = (level - 1) // levels_per_row
            col = (level - 1) % levels_per_row

            level_y = levels_row_start + row
            level_x = center_x - levels_per_row * 3 + col * 6

            # Highlight selected level
            if level == selected_level:
                self._safe_addstr(level_y, level_x, f"{level:2d}", curses.color_pair(8))
            else:
                self._safe_addstr(level_y, level_x, f"{level:2d}")

        # Draw controls
        controls_text = "←/→/↑/↓: Select | Enter: Confirm | Esc: Back"
        controls_y = self.height - 2
        controls_x = center_x - len(controls_text) // 2
        self._safe_addstr(controls_y, controls_x, controls_text)

        self.stdscr.refresh()

    def draw_enter_initials(self, current_initials, initial_index=0):
        """Draw the screen for entering initials for a new high score"""
        # Clear screen
        self.stdscr.clear()

        # Calculate center positions
        center_y = self.height // 2 - 4
        center_x = self.width // 2

        # Draw title
        title = "NEW HIGH SCORE!"
        title_x = center_x - len(title) // 2
        self._safe_addstr(
            center_y, title_x, title, curses.A_BOLD | curses.color_pair(10)
        )

        # Draw instruction
        instruction = "Enter your initials:"
        instruction_x = center_x - len(instruction) // 2
        self._safe_addstr(center_y + 2, instruction_x, instruction)

        # Draw initials boxes
        initials_y = center_y + 4
        box_width = 3
        spacing = 2
        total_width = (box_width + spacing) * 3 - spacing
        start_x = center_x - total_width // 2

        for i in range(3):
            box_x = start_x + i * (box_width + spacing)

            # Draw box outline
            is_selected = i == initial_index
            box_attrs = curses.A_BOLD if is_selected else 0

            # Top of box
            self._safe_addstr(initials_y, box_x, "+", box_attrs)
            self._safe_addstr(initials_y, box_x + 1, "-", box_attrs)
            self._safe_addstr(initials_y, box_x + 2, "-", box_attrs)
            self._safe_addstr(initials_y, box_x + 3, "-", box_attrs)
            self._safe_addstr(initials_y, box_x + 4, "+", box_attrs)

            # Sides of box
            self._safe_addstr(initials_y + 1, box_x, "|", box_attrs)
            self._safe_addstr(initials_y + 1, box_x + 4, "|", box_attrs)

            # Bottom of box
            self._safe_addstr(initials_y + 2, box_x, "+", box_attrs)
            self._safe_addstr(initials_y + 2, box_x + 1, "-", box_attrs)
            self._safe_addstr(initials_y + 2, box_x + 2, "-", box_attrs)
            self._safe_addstr(initials_y + 2, box_x + 3, "-", box_attrs)
            self._safe_addstr(initials_y + 2, box_x + 4, "+", box_attrs)

            # Draw the initial letter
            letter_x = box_x + 2
            letter_attr = curses.A_BOLD
            if is_selected:
                letter_attr |= curses.A_REVERSE
            self._safe_addstr(
                initials_y + 1, letter_x, current_initials[i], letter_attr
            )

        # Draw controls
        controls_y = initials_y + 5
        controls = [
            "↑/W: Previous Letter",
            "↓/S: Next Letter",
            "←/A: Previous Position",
            "→/D: Next Position",
            "Enter: Confirm",
            "Esc: Cancel",
        ]

        for i, control in enumerate(controls):
            control_x = center_x - len(control) // 2
            self._safe_addstr(controls_y + i, control_x, control)

        self.stdscr.refresh()

    def draw_high_scores(self, high_scores, selected_index):
        """Draw the high scores screen"""
        self.stdscr.clear()

        # Draw title
        title = "HIGH SCORES"
        title_x = (self.width - len(title)) // 2
        self._safe_addstr(2, title_x, title, curses.A_BOLD | curses.color_pair(10))

        # Draw table headers
        header_y = 5
        header_x = self.width // 2 - 25
        self._safe_addstr(header_y, header_x, "RANK", curses.A_UNDERLINE)
        self._safe_addstr(header_y, header_x + 8, "INITIALS", curses.A_UNDERLINE)
        self._safe_addstr(header_y, header_x + 20, "SCORE", curses.A_UNDERLINE)
        self._safe_addstr(header_y, header_x + 30, "LEVEL", curses.A_UNDERLINE)
        self._safe_addstr(header_y, header_x + 40, "LINES", curses.A_UNDERLINE)
        self._safe_addstr(header_y, header_x + 50, "DATE", curses.A_UNDERLINE)

        # Draw high scores
        if high_scores:
            for i, score in enumerate(high_scores):
                score_y = header_y + i + 2
                rank = f"{i + 1:2d}."

                # Get initials (handle old high scores without initials)
                initials = score.get("initials", "---")

                # Get date (handle old high scores without date)
                date = score.get("date", "")

                # Highlight selected score
                attr = curses.A_BOLD if i == selected_index else 0
                self._safe_addstr(score_y, header_x, rank, attr)
                self._safe_addstr(score_y, header_x + 8, initials, attr)
                self._safe_addstr(score_y, header_x + 20, f"{score['score']:6d}", attr)
                self._safe_addstr(score_y, header_x + 30, f"{score['level']:2d}", attr)
                self._safe_addstr(score_y, header_x + 40, f"{score['lines']:3d}", attr)
                if date:
                    self._safe_addstr(score_y, header_x + 50, date, attr)
        else:
            self._safe_addstr(
                header_y + 2, (self.width - 20) // 2, "No high scores yet!"
            )

        # Draw instructions
        instructions = "ESC: Back to Menu"
        self._safe_addstr(
            self.height - 3, (self.width - len(instructions)) // 2, instructions
        )

        self.stdscr.refresh()

    def draw_confirm_quit(self, selected_option: int):
        """Draw confirmation dialog for quitting the game"""
        self.stdscr.clear()

        # Calculate center position
        center_y = self.height // 2
        center_x = self.width // 2

        # Draw dialog
        dialog_width = 40
        dialog_height = 5
        dialog_start_y = center_y - dialog_height // 2
        dialog_start_x = center_x - dialog_width // 2

        # Draw borders
        self._draw_borders(dialog_start_y, dialog_start_x, dialog_height, dialog_width)

        # Draw message
        message = "Are you sure you want to quit?"
        message_y = dialog_start_y + 1
        message_x = center_x - len(message) // 2
        self._safe_addstr(message_y, message_x, message)

        # Draw options
        options = ["No", "Yes"]
        options_y = message_y + 2

        for i, option in enumerate(options):
            option_x = center_x - 5 + i * 10

            # Highlight selected option
            if i == selected_option:
                self._safe_addstr(options_y, option_x, option, curses.color_pair(8))
            else:
                self._safe_addstr(options_y, option_x, option)

        self.stdscr.refresh()

    def draw_font_recommendation(self):
        """Display a message recommending a monospace font for best experience"""
        # Clear screen first
        self.stdscr.clear()

        # Calculate center of screen
        center_y = self.height // 2

        # Draw game title
        title = GAME_NAME
        title_x = (self.width - len(title)) // 2
        self._safe_addstr(
            center_y - 5, title_x, title, curses.color_pair(10) | curses.A_BOLD
        )

        # Draw recommendation
        message = "For the best experience, please use a monospaced font."
        message_x = (self.width - len(message)) // 2
        self._safe_addstr(center_y - 2, message_x, message)

        # Add examples of good fonts
        fonts = "Recommended: Fira Code, JetBrains Mono, Hack, or IBM Plex Mono"
        fonts_x = (self.width - len(fonts)) // 2
        self._safe_addstr(center_y, fonts_x, fonts)

        # Add press key message
        continue_msg = "Press any key to continue..."
        continue_x = (self.width - len(continue_msg)) // 2
        self._safe_addstr(center_y + 3, continue_x, continue_msg)

        # Refresh and wait for key
        self.stdscr.refresh()
        self.stdscr.getch()

    def draw_intro_screen(self):
        """Display a proper intro screen with game information and tetromino graphic"""
        # Clear screen first
        self.stdscr.clear()

        # Calculate center positions
        center_y = 4
        center_x = self.width // 2

        # Draw ASCII art title
        title_art = [
            "    _________    __    __    _______    _   ________",
            "   / ____/   |  / /   / /   /  _/   |  / | / /_  __/",
            "  / /_  / /| | / /   / /    / // /| | /  |/ / / /   ",
            " / __/ / ___ |/ /___/ /____/ // ___ |/ /|  / / /    ",
            "/_/   /_/  |_/_____/_____/___/_/  |_/_/ |_/ /_/     ",
        ]

        # Find the longest line to calculate proper centering
        max_width = max(len(line) for line in title_art)
        title_x = center_x - max_width // 2

        for i, line in enumerate(title_art):
            self._safe_addstr(
                center_y + i, title_x, line, curses.color_pair(10) | curses.A_BOLD
            )

        # Draw game description
        desc_y = center_y + 7
        description = [
            "A Terminal-based Block Stacking Game",
            "",
            "Stack blocks to complete lines and score points!",
            "As you clear more lines, the game gets faster.",
        ]

        for i, line in enumerate(description):
            desc_x = center_x - len(line) // 2
            self._safe_addstr(desc_y + i, desc_x, line)

        # Draw tetromino pieces with better layout
        blocks_y = desc_y + 6

        # I-piece (Cyan)
        i_piece_x = center_x - 12
        self._safe_addstr(blocks_y, i_piece_x, "[][][][]", curses.color_pair(1))

        # O-piece (Yellow)
        o_piece_x = center_x - 12
        self._safe_addstr(blocks_y + 2, o_piece_x, "[][]", curses.color_pair(2))
        self._safe_addstr(blocks_y + 3, o_piece_x, "[][]", curses.color_pair(2))

        # T-piece (Magenta)
        t_piece_x = center_x
        self._safe_addstr(blocks_y, t_piece_x, "  []  ", curses.color_pair(3))
        self._safe_addstr(blocks_y + 1, t_piece_x, "[][][]", curses.color_pair(3))

        # J-piece (Blue)
        j_piece_x = center_x + 10
        self._safe_addstr(blocks_y + 2, j_piece_x, "[]", curses.color_pair(4))
        self._safe_addstr(blocks_y + 3, j_piece_x, "[][][]", curses.color_pair(4))

        # L-piece (White)
        l_piece_x = center_x - 12
        self._safe_addstr(blocks_y + 5, l_piece_x, "    []", curses.color_pair(5))
        self._safe_addstr(blocks_y + 6, l_piece_x, "[][][]", curses.color_pair(5))

        # S-piece (Green)
        s_piece_x = center_x
        self._safe_addstr(blocks_y + 5, s_piece_x, "  [][]", curses.color_pair(6))
        self._safe_addstr(blocks_y + 6, s_piece_x, "[][]  ", curses.color_pair(6))

        # Z-piece (Red)
        z_piece_x = center_x + 10
        self._safe_addstr(blocks_y + 5, z_piece_x, "[][]  ", curses.color_pair(7))
        self._safe_addstr(blocks_y + 6, z_piece_x, "  [][]", curses.color_pair(7))

        # Draw controls
        controls_y = blocks_y + 8
        controls_x = center_x - 20
        controls = [
            "Controls:",
            "←/→/A/D: Move Left/Right",
            "↓/S: Move Down",
            "↑/W: Rotate",
            "Space: Drop",
            "C: Hold piece",
            "P: Pause",
        ]

        for i, line in enumerate(controls):
            self._safe_addstr(controls_y + i, controls_x, line)

        # Draw press key to start message
        start_y = controls_y + len(controls) + 2
        start_text = "Press any key to start..."
        start_x = center_x - len(start_text) // 2
        self._safe_addstr(start_y, start_x, start_text, curses.A_BLINK)

        # Display font recommendation
        font_y = start_y + 2
        font_text = "For best experience, use a monospaced font like Fira Code or JetBrains Mono"
        font_x = center_x - len(font_text) // 2
        self._safe_addstr(font_y, font_x, font_text, curses.color_pair(9))

        self.stdscr.refresh()

        # Wait for keypress
        self.stdscr.getch()
