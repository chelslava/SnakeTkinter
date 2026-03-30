"""
Multiplayer game engine - Two snakes competing on the same field.
"""

import random
import time
from dataclasses import dataclass, field
from enum import Enum

from .engine import Difficulty, Direction


class MultiplayerState(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    P1_WINS = "p1_wins"
    P2_WINS = "p2_wins"
    DRAW = "draw"


@dataclass
class PlayerStats:
    """Statistics for one player"""

    score: int = 0
    length: int = 3
    deaths: int = 0
    food_eaten: int = 0
    start_time: float = field(default_factory=time.time)

    @property
    def duration(self) -> float:
        return time.time() - self.start_time


@dataclass
class MultiplayerConfig:
    """Configuration for multiplayer game"""

    width: int = 40
    height: int = 20
    speed_ms: int = 100
    difficulty: Difficulty = Difficulty.NORMAL
    power_ups_enabled: bool = True
    time_limit: float | None = None  # None = no limit
    score_to_win: int | None = None  # None = no limit
    self_collision: bool = True
    wall_death: bool = True


class MultiplayerGame:
    """
    Multiplayer Snake game with two players on the same field.
    """

    OPPOSITE = {
        Direction.UP: Direction.DOWN,
        Direction.DOWN: Direction.UP,
        Direction.LEFT: Direction.RIGHT,
        Direction.RIGHT: Direction.LEFT,
    }

    def __init__(self, config: MultiplayerConfig | None = None):
        self.config = config or MultiplayerConfig()
        self.state = MultiplayerState.RUNNING

        self.snake1: list[tuple[int, int]] = []
        self.snake2: list[tuple[int, int]] = []
        self.direction1 = Direction.RIGHT
        self.direction2 = Direction.LEFT
        self.next_direction1: Direction | None = None
        self.next_direction2: Direction | None = None

        self.food: tuple[int, int] | None = None
        self.obstacles: set[tuple[int, int]] = set()

        self.stats1 = PlayerStats()
        self.stats2 = PlayerStats()

        self._start_time = time.time()
        self._init_game()

    def _init_game(self) -> None:
        """Initialize game state"""
        w = self.config.width
        h = self.config.height

        self.snake1 = [(5, h // 2), (4, h // 2), (3, h // 2)]
        self.snake2 = [(w - 6, h // 2), (w - 5, h // 2), (w - 4, h // 2)]

        self.direction1 = Direction.RIGHT
        self.direction2 = Direction.LEFT
        self.next_direction1 = None
        self.next_direction2 = None

        self.stats1 = PlayerStats()
        self.stats2 = PlayerStats()

        self._spawn_food()

    def _spawn_food(self) -> None:
        """Spawn food at random valid position"""
        all_positions = {
            (x, y) for x in range(self.config.width) for y in range(self.config.height)
        }

        occupied = set(self.snake1) | set(self.snake2) | self.obstacles
        available = list(all_positions - occupied)

        if available:
            self.food = random.choice(available)
        else:
            self.food = None

    def set_direction1(self, direction: Direction) -> bool:
        """Set direction for player 1"""
        if direction == self.OPPOSITE.get(self.direction1):
            return False
        self.next_direction1 = direction
        return True

    def set_direction2(self, direction: Direction) -> bool:
        """Set direction for player 2"""
        if direction == self.OPPOSITE.get(self.direction2):
            return False
        self.next_direction2 = direction
        return True

    def update(self) -> bool:
        """Update game state by one tick"""
        if self.state != MultiplayerState.RUNNING:
            return False

        if self.next_direction1:
            self.direction1 = self.next_direction1
            self.next_direction1 = None

        if self.next_direction2:
            self.direction2 = self.next_direction2
            self.next_direction2 = None

        head1 = self.snake1[0]
        head2 = self.snake2[0]

        new_head1 = self._move(head1, self.direction1)
        new_head2 = self._move(head2, self.direction2)

        p1_dead = self._check_collision(new_head1, is_player1=True)
        p2_dead = self._check_collision(new_head2, is_player1=False)

        head_on_collision = new_head1 == new_head2

        if head_on_collision:
            self.state = MultiplayerState.DRAW
            return False

        if p1_dead and p2_dead:
            self.state = MultiplayerState.DRAW
            return False

        if p1_dead:
            self.stats1.deaths += 1
            self.state = MultiplayerState.P2_WINS
            return False

        if p2_dead:
            self.stats2.deaths += 1
            self.state = MultiplayerState.P1_WINS
            return False

        self.snake1.insert(0, new_head1)
        self.snake2.insert(0, new_head2)

        if new_head1 == self.food:
            self.stats1.score += 1
            self.stats1.food_eaten += 1
            self.stats1.length = len(self.snake1)
            self._spawn_food()
        else:
            self.snake1.pop()

        if new_head2 == self.food:
            self.stats2.score += 1
            self.stats2.food_eaten += 1
            self.stats2.length = len(self.snake2)
            self._spawn_food()
        else:
            self.snake2.pop()

        self._check_win_conditions()
        return True

    def _move(self, pos: tuple[int, int], direction: Direction) -> tuple[int, int]:
        """Get next position after moving in direction"""
        x, y = pos
        if direction == Direction.UP:
            return (x, y - 1)
        elif direction == Direction.DOWN:
            return (x, y + 1)
        elif direction == Direction.LEFT:
            return (x - 1, y)
        else:
            return (x + 1, y)

    def _check_collision(self, pos: tuple[int, int], is_player1: bool) -> bool:
        """Check if position causes collision"""
        x, y = pos

        if self.config.wall_death and (
            x < 0 or x >= self.config.width or y < 0 or y >= self.config.height
        ):
            return True

        if pos in self.obstacles:
            return True

        if is_player1:
            if pos in set(self.snake1[1:]):
                return True
            if pos in set(self.snake2):
                return True
        else:
            if pos in set(self.snake2[1:]):
                return True
            if pos in set(self.snake1):
                return True

        return False

    def _check_win_conditions(self) -> None:
        """Check if any win condition is met"""
        if self.config.score_to_win:
            if self.stats1.score >= self.config.score_to_win:
                self.state = MultiplayerState.P1_WINS
            elif self.stats2.score >= self.config.score_to_win:
                self.state = MultiplayerState.P2_WINS

        if self.config.time_limit:
            elapsed = time.time() - self._start_time
            if elapsed >= self.config.time_limit:
                if self.stats1.score > self.stats2.score:
                    self.state = MultiplayerState.P1_WINS
                elif self.stats2.score > self.stats1.score:
                    self.state = MultiplayerState.P2_WINS
                else:
                    self.state = MultiplayerState.DRAW

    def reset(self) -> None:
        """Reset game"""
        self.state = MultiplayerState.RUNNING
        self._start_time = time.time()
        self._init_game()

    def pause(self) -> None:
        """Toggle pause"""
        if self.state == MultiplayerState.RUNNING:
            self.state = MultiplayerState.PAUSED
        elif self.state == MultiplayerState.PAUSED:
            self.state = MultiplayerState.RUNNING

    def get_safe_directions1(self) -> list[Direction]:
        """Get safe directions for player 1"""
        safe = []
        head = self.snake1[0]
        for direction in Direction:
            new_pos = self._move(head, direction)
            if not self._check_collision(
                new_pos, is_player1=True
            ) and direction != self.OPPOSITE.get(self.direction1):
                safe.append(direction)
        return safe

    def get_safe_directions2(self) -> list[Direction]:
        """Get safe directions for player 2"""
        safe = []
        head = self.snake2[0]
        for direction in Direction:
            new_pos = self._move(head, direction)
            if not self._check_collision(
                new_pos, is_player1=False
            ) and direction != self.OPPOSITE.get(self.direction2):
                safe.append(direction)
        return safe
