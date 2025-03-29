"""
Game state management for Falliant
"""

import random
from typing import Optional

from .block import Block
from .constants import (
    BASE_FALL_DELAY,
    BLOCK_SHAPES,
    BOARD_HEIGHT,
    BOARD_WIDTH,
    DIRECTION_DOWN,
    DIRECTION_LEFT,
    DIRECTION_RIGHT,
    SCORING,
)


class GameState:
    """Manages the game state"""

    def __init__(self, starting_level: int = 1):
        self.board = [[0 for _ in range(BOARD_WIDTH)] for _ in range(BOARD_HEIGHT)]
        self.current_block: Optional[Block] = None
        self.next_block: Optional[Block] = None
        self.score = 0
        self.lines_cleared = 0
        self.level = starting_level
        self.game_over = False
        self.hold_block_index = None
        self.can_hold = True
        self.fall_delay = max(1, BASE_FALL_DELAY - (self.level - 1) * 2)
        self.fall_counter = 0
        self.paused = False

        # Initialize first blocks
        self._spawn_next_block()
        self._spawn_current_block()

    def _spawn_next_block(self):
        """Create the next block to fall"""
        # Randomly select a block type (shape index)
        shape_index = random.randint(0, len(BLOCK_SHAPES) - 1)
        # Always start with the first rotation (rotation 0)
        self.next_block = Block(shape_index, 0, 0, 0)

    def _spawn_current_block(self):
        """Move next block to current and create new next block"""
        if self.next_block is None:
            self._spawn_next_block()

        if self.next_block:  # Type check to satisfy linter
            self.current_block = self.next_block

            # Center the block horizontally
            if self.current_block:  # Type check to satisfy linter
                self.current_block.x = (BOARD_WIDTH - self.current_block.width) // 2
                self.current_block.y = 0

            # Check if the new block overlaps with existing blocks (game over)
            if self._check_collision():
                self.game_over = True

            self._spawn_next_block()
            self.can_hold = True

    def hold_block(self):
        """Hold the current block and swap with previously held block"""
        if not self.can_hold or self.current_block is None:
            return

        if self.hold_block_index is None:
            # No block in hold, so store current and get next
            self.hold_block_index = self.current_block.shape_index
            self._spawn_current_block()
        else:
            # Swap current block with held block
            temp_index = self.current_block.shape_index

            # Create new block from hold
            self.current_block = Block(self.hold_block_index, 0, 0, 0)

            # Center the block horizontally
            self.current_block.x = (BOARD_WIDTH - self.current_block.width) // 2
            self.current_block.y = 0

            # Store previous current
            self.hold_block_index = temp_index

        self.can_hold = False

    def _check_collision(self) -> bool:
        """Check if current block collides with board boundaries or other blocks"""
        if self.current_block is None:
            return False

        shape = self.current_block.shape
        for y, row in enumerate(shape):
            for x in range(len(row)):
                # Look for "[]" in each two characters
                if x + 1 < len(row) and row[x : x + 2] == "[]":
                    # Calculate board coordinates (x is divided by 2 since each block cell is two characters)
                    board_x = self.current_block.x + (x // 2)
                    board_y = self.current_block.y + y

                    # Check boundaries
                    if (
                        board_x < 0
                        or board_x >= BOARD_WIDTH
                        or board_y < 0
                        or board_y >= BOARD_HEIGHT
                    ):
                        return True

                    # Check collision with placed blocks
                    if board_y >= 0 and self.board[board_y][board_x] != 0:
                        return True

        return False

    def _rotate_block(self):
        """Rotate the current block"""
        if self.current_block is None:
            return

        # Save current position and rotation
        original_rotation = self.current_block.rotation
        original_x = self.current_block.x
        shape_index = self.current_block.shape_index

        # Skip rotation for O-piece (square), as it only has one rotation
        if shape_index == 1:  # O-piece
            return

        # Calculate next rotation
        max_rotation = len(BLOCK_SHAPES[shape_index]) - 1
        next_rotation = (original_rotation + 1) % (max_rotation + 1)
        self.current_block.rotation = next_rotation

        # Wall kick - try to adjust position if rotation causes collision
        if self._check_collision():
            # Try moving left
            self.current_block.x -= 1
            if self._check_collision():
                # Try moving right
                self.current_block.x = original_x + 1
                if self._check_collision():
                    # Try moving right more (for I piece)
                    self.current_block.x = original_x + 2
                    if self._check_collision():
                        # Revert to original position and rotation
                        self.current_block.x = original_x
                        self.current_block.rotation = original_rotation
                        return

    def _move_block(self, direction: int) -> bool:
        """Move the current block in the specified direction"""
        if self.current_block is None:
            return False

        # Save current position
        original_x = self.current_block.x
        original_y = self.current_block.y

        # Move block based on direction
        if direction == DIRECTION_LEFT:
            self.current_block.x -= 1
        elif direction == DIRECTION_RIGHT:
            self.current_block.x += 1
        elif direction == DIRECTION_DOWN:
            self.current_block.y += 1

        # Check for collision, revert if needed
        if self._check_collision():
            self.current_block.x = original_x
            self.current_block.y = original_y

            # If moving down caused collision, place block
            if direction == DIRECTION_DOWN:
                self._place_block()
                return True  # Block was placed

            return False  # Movement was blocked

        return True  # Movement succeeded

    def _place_block(self):
        """Place the current block onto the board"""
        if self.current_block is None:
            return

        # Store the current block for reference before it's replaced
        placed_block = self.current_block

        # Transfer block to board
        shape = placed_block.shape
        # Color pair is shape_index + 1 because color pairs start at 1
        color_pair = placed_block.shape_index + 1

        for y, row in enumerate(shape):
            for x in range(len(row)):
                # Look for "[]" in each two characters
                if x + 1 < len(row) and row[x : x + 2] == "[]":
                    # Calculate board coordinates (x is divided by 2 since each block cell is two characters)
                    board_x = placed_block.x + (x // 2)
                    board_y = placed_block.y + y

                    if 0 <= board_y < BOARD_HEIGHT and 0 <= board_x < BOARD_WIDTH:
                        self.board[board_y][board_x] = color_pair

        # Check for completed lines and spawn new block
        self._check_lines()
        self._spawn_current_block()

    def _check_lines(self):
        """Check for completed lines and remove them"""
        lines_cleared = 0
        y = BOARD_HEIGHT - 1

        while y >= 0:
            is_line_complete = True

            # Check if line is complete
            for x in range(BOARD_WIDTH):
                if self.board[y][x] == 0:
                    is_line_complete = False
                    break

            if is_line_complete:
                # Move all lines above this one down
                for y2 in range(y, 0, -1):
                    for x in range(BOARD_WIDTH):
                        self.board[y2][x] = self.board[y2 - 1][x]

                # Clear top line
                for x in range(BOARD_WIDTH):
                    self.board[0][x] = 0

                lines_cleared += 1
            else:
                y -= 1

        # Update score and level
        if lines_cleared > 0:
            # Score based on number of lines cleared
            if lines_cleared in SCORING:
                self.score += SCORING[lines_cleared] * self.level

            self.lines_cleared += lines_cleared

            # Level up every 10 lines
            new_level = self.lines_cleared // 10 + 1
            if new_level > self.level:
                self.level = new_level
                self.fall_delay = max(1, BASE_FALL_DELAY - (self.level - 1) * 2)

    def drop_block(self):
        """Drop the block to the bottom"""
        if self.current_block is None or self.paused or self.game_over:
            return False  # Drop failed

        # Remember starting position
        start_y = self.current_block.y

        # Keep moving down until one position before collision
        drop_count = 0
        last_valid_y = self.current_block.y

        while True:
            # Try moving down one more position
            self.current_block.y += 1

            # Check if this position is valid
            if self._check_collision():
                # If collision, go back to the last valid position
                self.current_block.y = last_valid_y
                break
            else:
                # No collision, update last valid position
                last_valid_y = self.current_block.y

            drop_count += 1
            # Limit the maximum drops to prevent infinite loops
            if drop_count > BOARD_HEIGHT * 2:
                break

        # Return whether the block moved at all
        moved = last_valid_y > start_y

        # If the block moved, trigger automatic placement
        if moved:
            # We need to place the block manually here
            self._place_block()

        return moved

    def update(self):
        """Update game state for one frame"""
        if self.paused or self.game_over or self.current_block is None:
            return

        self.fall_counter += 1
        if self.fall_counter >= self.fall_delay:
            self.fall_counter = 0
            self._move_block(DIRECTION_DOWN)

    def move_left(self):
        """Move the current block left"""
        if not self.paused and not self.game_over:
            self._move_block(DIRECTION_LEFT)

    def move_right(self):
        """Move the current block right"""
        if not self.paused and not self.game_over:
            self._move_block(DIRECTION_RIGHT)

    def move_down(self):
        """Move the current block down"""
        if not self.paused and not self.game_over:
            self._move_block(DIRECTION_DOWN)

    def rotate(self):
        """Rotate the current block"""
        if not self.paused and not self.game_over:
            self._rotate_block()

    def toggle_pause(self):
        """Toggle game pause state"""
        self.paused = not self.paused
