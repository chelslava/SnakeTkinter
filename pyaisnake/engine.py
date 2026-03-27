"""
Game Engine - Pure game logic without GUI dependencies.
"""

import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum


class Direction(Enum):
    UP = "Up"
    DOWN = "Down"
    LEFT = "Left"
    RIGHT = "Right"


class GameState(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    GAME_OVER = "game_over"
    WIN = "win"


@dataclass
class GameConfig:
    """Game configuration"""

    width: int = 40
    height: int = 40
    initial_obstacles: int = 0
    speed_ms: int = 100
    wrap_around: bool = False


@dataclass
class GameStats:
    """Game statistics"""

    score: int = 0
    moves: int = 0
    food_eaten: int = 0
    start_time: float = field(default_factory=time.time)

    @property
    def duration(self) -> float:
        return time.time() - self.start_time

    @property
    def efficiency(self) -> float:
        if self.moves == 0:
            return 0.0
        return self.food_eaten / self.moves


class SnakeGame:
    """
    Pure game engine without GUI dependencies.

    Usage:
        game = SnakeGame()
        game.on_food_eaten = lambda: print("Yummy!")

        while game.state == GameState.RUNNING:
            game.update()
            print(game.render_ascii())
            time.sleep(0.1)
    """

    OPPOSITE = {
        Direction.UP: Direction.DOWN,
        Direction.DOWN: Direction.UP,
        Direction.LEFT: Direction.RIGHT,
        Direction.RIGHT: Direction.LEFT,
    }

    def __init__(self, config: GameConfig | None = None):
        self.config = config or GameConfig()
        self.state = GameState.RUNNING
        self.stats = GameStats()

        # Game objects
        self.snake: list[tuple[int, int]] = []
        self.food: tuple[int, int] | None = None
        self.obstacles: set[tuple[int, int]] = set()
        self.direction = Direction.RIGHT
        self.next_direction: Direction | None = None

        # Callbacks
        self.on_food_eaten: Callable[[], None] | None = None
        self.on_collision: Callable[[], None] | None = None
        self.on_move: Callable[[tuple[int, int]], None] | None = None

        self._init_game()

    def _init_game(self) -> None:
        """Initialize game state"""
        center_x = self.config.width // 2
        center_y = self.config.height // 2

        self.snake = [
            (center_x, center_y),
            (center_x - 1, center_y),
            (center_x - 2, center_y),
        ]

        self.obstacles = set()
        self._spawn_food()

        if self.config.initial_obstacles > 0:
            self._create_obstacles(self.config.initial_obstacles)

    def _spawn_food(self) -> None:
        """Spawn food at random valid position"""
        all_positions = {
            (x, y) for x in range(self.config.width) for y in range(self.config.height)
        }

        occupied = set(self.snake) | self.obstacles
        available = list(all_positions - occupied)

        if available:
            self.food = random.choice(available)
        else:
            self.food = None
            self.state = GameState.WIN

    def _create_obstacles(self, count: int) -> None:
        """Create random obstacles"""
        all_positions = {
            (x, y) for x in range(self.config.width) for y in range(self.config.height)
        }

        occupied = set(self.snake) | {self.food} if self.food else set(self.snake)

        safe_zone = set()
        head = self.snake[0]
        for dx in range(-3, 4):
            for dy in range(-3, 4):
                safe_zone.add((head[0] + dx, head[1] + dy))

        available = list(all_positions - occupied - safe_zone)
        count = min(count, len(available))

        self.obstacles = set(random.sample(available, count))

    def set_direction(self, direction: Direction) -> bool:
        """
        Set movement direction.
        Returns False if direction is opposite to current (invalid move).
        """
        if direction == self.OPPOSITE.get(self.direction):
            return False

        self.next_direction = direction
        return True

    def update(self) -> bool:
        """
        Update game state by one tick.
        Returns True if game is still running, False if game over.
        """
        if self.state != GameState.RUNNING:
            return False

        if self.next_direction:
            self.direction = self.next_direction
            self.next_direction = None

        head = self.snake[0]

        if self.direction == Direction.UP:
            new_head = (head[0], head[1] - 1)
        elif self.direction == Direction.DOWN:
            new_head = (head[0], head[1] + 1)
        elif self.direction == Direction.LEFT:
            new_head = (head[0] - 1, head[1])
        else:  # RIGHT
            new_head = (head[0] + 1, head[1])

        if not self._is_valid_position(new_head):
            self.state = GameState.GAME_OVER
            if self.on_collision:
                self.on_collision()
            return False

        self.snake.insert(0, new_head)
        self.stats.moves += 1

        if self.on_move:
            self.on_move(new_head)

        if new_head == self.food:
            self.stats.score += 1
            self.stats.food_eaten += 1
            self._spawn_food()
            if self.on_food_eaten:
                self.on_food_eaten()
        else:
            self.snake.pop()

        return True

    def _is_valid_position(self, pos: tuple[int, int]) -> bool:
        """Check if position is valid for movement"""
        x, y = pos

        # Check boundaries
        if self.config.wrap_around:
            x = x % self.config.width
            y = y % self.config.height
        else:
            if x < 0 or x >= self.config.width:
                return False
            if y < 0 or y >= self.config.height:
                return False

        # Check collision with snake body
        if pos in self.snake:
            return False

        # Check collision with obstacles
        return pos not in self.obstacles

    def reset(self) -> None:
        """Reset game to initial state"""
        self.state = GameState.RUNNING
        self.stats = GameStats()
        self.direction = Direction.RIGHT
        self.next_direction = None
        self._init_game()

    def pause(self) -> None:
        """Toggle pause state"""
        if self.state == GameState.RUNNING:
            self.state = GameState.PAUSED
        elif self.state == GameState.PAUSED:
            self.state = GameState.RUNNING

    def get_state_dict(self) -> dict:
        """Get game state as dictionary for AI/serialization"""
        return {
            "snake": list(self.snake),
            "food": self.food,
            "obstacles": list(self.obstacles),
            "direction": self.direction.value,
            "score": self.stats.score,
            "moves": self.stats.moves,
            "state": self.state.value,
        }

    def render_ascii(self) -> str:
        """Render game as ASCII art (for testing/debugging)"""
        lines = []

        for y in range(self.config.height):
            row = []
            for x in range(self.config.width):
                pos = (x, y)

                if pos == self.snake[0]:
                    char = "@"
                elif pos in self.snake:
                    char = "o"
                elif pos == self.food:
                    char = "*"
                elif pos in self.obstacles:
                    char = "#"
                else:
                    char = "."

                row.append(char)
            lines.append("".join(row))

        return "\n".join(lines)

    def get_safe_directions(self) -> list[Direction]:
        """Get list of safe movement directions"""
        safe = []
        head = self.snake[0]

        for direction in Direction:
            if direction == self.OPPOSITE.get(self.direction):
                continue

            new_pos = self._get_next_position(head, direction)
            if self._is_valid_position(new_pos):
                safe.append(direction)

        return safe

    def _get_next_position(self, pos: tuple[int, int], direction: Direction) -> tuple[int, int]:
        """Get next position for a direction"""
        x, y = pos

        if direction == Direction.UP:
            return (x, y - 1)
        elif direction == Direction.DOWN:
            return (x, y + 1)
        elif direction == Direction.LEFT:
            return (x - 1, y)
        else:  # RIGHT
            return (x + 1, y)
