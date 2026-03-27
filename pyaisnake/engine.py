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


class Difficulty(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    EXTREME = "extreme"


class PowerUpType(Enum):
    APPLE = "apple"  # Normal food (+1 score)
    STAR = "star"  # Speed boost for 5 seconds
    SHIELD = "shield"  # Pass through walls once
    DIAMOND = "diamond"  # Double points for 10 seconds
    FREEZE = "freeze"  # Slow down game temporarily
    MUSHROOM = "mushroom"  # Snake shrinks by 3 segments


@dataclass
class PowerUp:
    """Active power-up effect"""

    type: PowerUpType
    position: tuple[int, int]
    spawn_time: float = field(default_factory=time.time)

    # Duration in seconds (0 = instant)
    DURATIONS = {
        PowerUpType.APPLE: 0,
        PowerUpType.STAR: 5,
        PowerUpType.SHIELD: 0,  # One-time use
        PowerUpType.DIAMOND: 10,
        PowerUpType.FREEZE: 5,
        PowerUpType.MUSHROOM: 0,  # Instant
    }

    @property
    def duration(self) -> float:
        return self.DURATIONS.get(self.type, 0)

    @property
    def is_expired(self) -> bool:
        if self.duration == 0:
            return False
        return time.time() - self.spawn_time > self.duration


@dataclass
class ActiveEffect:
    """Currently active power-up effect on player"""

    type: PowerUpType
    start_time: float
    duration: float

    @property
    def remaining(self) -> float:
        return max(0, self.duration - (time.time() - self.start_time))

    @property
    def is_active(self) -> bool:
        return self.remaining > 0


@dataclass
class GameConfig:
    """Game configuration"""

    width: int = 40
    height: int = 40
    initial_obstacles: int = 0
    speed_ms: int = 100
    wrap_around: bool = False
    difficulty: Difficulty = Difficulty.NORMAL
    power_ups_enabled: bool = True


@dataclass
class GameStats:
    """Game statistics"""

    score: int = 0
    moves: int = 0
    food_eaten: int = 0
    power_ups_collected: int = 0
    start_time: float = field(default_factory=time.time)

    @property
    def duration(self) -> float:
        return time.time() - self.start_time

    @property
    def efficiency(self) -> float:
        if self.moves == 0:
            return 0.0
        return self.food_eaten / self.moves


# Difficulty presets
DIFFICULTY_CONFIG = {
    Difficulty.EASY: {
        "speed_ms": 150,
        "obstacles": 0,
        "power_ups_enabled": True,
        "power_up_frequency": 0.3,  # 30% chance
    },
    Difficulty.NORMAL: {
        "speed_ms": 100,
        "obstacles": 0,
        "power_ups_enabled": True,
        "power_up_frequency": 0.2,
    },
    Difficulty.HARD: {
        "speed_ms": 70,
        "obstacles": 5,
        "power_ups_enabled": True,
        "power_up_frequency": 0.15,
    },
    Difficulty.EXTREME: {
        "speed_ms": 50,
        "obstacles": 15,
        "power_ups_enabled": False,
        "power_up_frequency": 0,
    },
}


class SnakeGame:
    """
    Pure game engine without GUI dependencies.
    """

    OPPOSITE = {
        Direction.UP: Direction.DOWN,
        Direction.DOWN: Direction.UP,
        Direction.LEFT: Direction.RIGHT,
        Direction.RIGHT: Direction.LEFT,
    }

    # Power-up spawn weights
    POWER_UP_WEIGHTS = {
        PowerUpType.APPLE: 70,  # Most common
        PowerUpType.STAR: 8,
        PowerUpType.SHIELD: 5,
        PowerUpType.DIAMOND: 5,
        PowerUpType.FREEZE: 7,
        PowerUpType.MUSHROOM: 5,
    }

    def __init__(self, config: GameConfig | None = None):
        self.config = config or GameConfig()
        self._apply_difficulty_config()
        self.state = GameState.RUNNING
        self.stats = GameStats()

        # Game objects
        self.snake: list[tuple[int, int]] = []
        self.food: tuple[int, int] | None = None
        self.obstacles: set[tuple[int, int]] = set()
        self.direction = Direction.RIGHT
        self.next_direction: Direction | None = None

        # Power-ups
        self.current_power_up: PowerUp | None = None
        self.active_effects: list[ActiveEffect] = []
        self.shield_count: int = 0
        self.score_multiplier: float = 1.0
        self.speed_modifier: float = 1.0

        # Callbacks
        self.on_food_eaten: Callable[[], None] | None = None
        self.on_collision: Callable[[], None] | None = None
        self.on_move: Callable[[tuple[int, int]], None] | None = None
        self.on_power_up: Callable[[PowerUpType], None] | None = None

        self._init_game()

    def _apply_difficulty_config(self) -> None:
        """Apply difficulty-based configuration"""
        diff_config = DIFFICULTY_CONFIG.get(self.config.difficulty, {})

        if self.config.speed_ms == 100:  # Default, override with difficulty
            self.config.speed_ms = diff_config.get("speed_ms", 100)

        if self.config.initial_obstacles == 0:
            self.config.initial_obstacles = diff_config.get("obstacles", 0)

        self.config.power_ups_enabled = diff_config.get("power_ups_enabled", True)
        self._power_up_frequency = diff_config.get("power_up_frequency", 0.2)

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
        self.active_effects = []
        self.shield_count = 0
        self.score_multiplier = 1.0
        self.speed_modifier = 1.0
        self._spawn_food()

        if self.config.initial_obstacles > 0:
            self._create_obstacles(self.config.initial_obstacles)

    def _spawn_food(self) -> None:
        """Spawn food or power-up at random valid position"""
        all_positions = {
            (x, y) for x in range(self.config.width) for y in range(self.config.height)
        }

        occupied = set(self.snake) | self.obstacles
        available = list(all_positions - occupied)

        if not available:
            self.food = None
            self.current_power_up = None
            self.state = GameState.WIN
            return

        position = random.choice(available)

        # Decide if spawning power-up or regular food
        if self.config.power_ups_enabled and random.random() < self._power_up_frequency:
            # Choose power-up type based on weights
            power_up_type = random.choices(
                list(self.POWER_UP_WEIGHTS.keys()), weights=list(self.POWER_UP_WEIGHTS.values())
            )[0]

            self.current_power_up = PowerUp(type=power_up_type, position=position)
            self.food = position
        else:
            self.current_power_up = PowerUp(type=PowerUpType.APPLE, position=position)
            self.food = position

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
        """Set movement direction."""
        if direction == self.OPPOSITE.get(self.direction):
            return False

        self.next_direction = direction
        return True

    def update(self) -> bool:
        """Update game state by one tick."""
        if self.state != GameState.RUNNING:
            return False

        # Update active effects
        self._update_effects()

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

        # Check wall collision with shield
        if not self._is_valid_position(new_head):
            if self.shield_count > 0:
                self.shield_count -= 1
                # Wrap around or move anyway
                if self.config.wrap_around:
                    x = new_head[0] % self.config.width
                    y = new_head[1] % self.config.height
                    new_head = (x, y)
                else:
                    # Bounce back - don't move
                    return True
            else:
                self.state = GameState.GAME_OVER
                if self.on_collision:
                    self.on_collision()
                return False

        self.snake.insert(0, new_head)
        self.stats.moves += 1

        if self.on_move:
            self.on_move(new_head)

        if new_head == self.food:
            self._collect_power_up()
            self._spawn_food()
        else:
            self.snake.pop()

        return True

    def _collect_power_up(self) -> None:
        """Collect and apply power-up effect"""
        if not self.current_power_up:
            return

        power_type = self.current_power_up.type
        self.stats.power_ups_collected += 1

        # Apply effect
        if power_type == PowerUpType.APPLE:
            self.stats.score += int(1 * self.score_multiplier)
            self.stats.food_eaten += 1

        elif power_type == PowerUpType.STAR:
            self.stats.score += int(1 * self.score_multiplier)
            self.stats.food_eaten += 1
            self.speed_modifier = 0.5  # Speed boost (lower delay)
            self.active_effects.append(
                ActiveEffect(type=power_type, start_time=time.time(), duration=5.0)
            )

        elif power_type == PowerUpType.SHIELD:
            self.stats.score += int(1 * self.score_multiplier)
            self.stats.food_eaten += 1
            self.shield_count += 1

        elif power_type == PowerUpType.DIAMOND:
            self.stats.score += int(1 * self.score_multiplier)
            self.stats.food_eaten += 1
            self.score_multiplier = 2.0
            self.active_effects.append(
                ActiveEffect(type=power_type, start_time=time.time(), duration=10.0)
            )

        elif power_type == PowerUpType.FREEZE:
            self.stats.score += int(1 * self.score_multiplier)
            self.stats.food_eaten += 1
            self.speed_modifier = 2.0  # Slow down (higher delay)
            self.active_effects.append(
                ActiveEffect(type=power_type, start_time=time.time(), duration=5.0)
            )

        elif power_type == PowerUpType.MUSHROOM:
            self.stats.score += int(1 * self.score_multiplier)
            self.stats.food_eaten += 1
            # Shrink snake by 3 segments (minimum length 3)
            while len(self.snake) > 3 and len(self.snake) > len(self.snake) - 3:
                if len(self.snake) > 3:
                    self.snake.pop()

        if self.on_food_eaten:
            self.on_food_eaten()

        if self.on_power_up:
            self.on_power_up(power_type)

    def _update_effects(self) -> None:
        """Update active power-up effects"""
        # Remove expired effects
        self.active_effects = [e for e in self.active_effects if e.is_active]

        # Check for active effects
        has_star = any(e.type == PowerUpType.STAR for e in self.active_effects)
        has_freeze = any(e.type == PowerUpType.FREEZE for e in self.active_effects)
        has_diamond = any(e.type == PowerUpType.DIAMOND for e in self.active_effects)

        self.speed_modifier = 1.0
        self.score_multiplier = 1.0

        if has_star:
            self.speed_modifier = 0.5
        if has_freeze:
            self.speed_modifier = 2.0
        if has_diamond:
            self.score_multiplier = 2.0

    @property
    def effective_speed(self) -> int:
        """Get effective game speed with modifiers"""
        return int(self.config.speed_ms * self.speed_modifier)

    def _is_valid_position(self, pos: tuple[int, int]) -> bool:
        """Check if position is valid for movement"""
        x, y = pos

        if self.config.wrap_around:
            x = x % self.config.width
            y = y % self.config.height
        else:
            if x < 0 or x >= self.config.width:
                return False
            if y < 0 or y >= self.config.height:
                return False

        if pos in self.snake:
            return False

        return pos not in self.obstacles

    def reset(self) -> None:
        """Reset game to initial state"""
        self.state = GameState.RUNNING
        self.stats = GameStats()
        self.direction = Direction.RIGHT
        self.next_direction = None
        self.active_effects = []
        self.shield_count = 0
        self.score_multiplier = 1.0
        self.speed_modifier = 1.0
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
            "power_up": self.current_power_up.type.value if self.current_power_up else None,
            "active_effects": [e.type.value for e in self.active_effects],
            "shield_count": self.shield_count,
            "score_multiplier": self.score_multiplier,
        }

    def render_ascii(self) -> str:
        """Render game as ASCII art (for testing/debugging)"""
        lines = []

        for y in range(self.config.height):
            row = []
            for x in range(self.config.width):
                pos = (x, y)

                if pos == self.snake[0]:
                    char = "@" if self.shield_count > 0 else "H"
                elif pos in self.snake:
                    char = "o"
                elif pos == self.food:
                    char = self._get_power_up_char()
                elif pos in self.obstacles:
                    char = "#"
                else:
                    char = "."

                row.append(char)
            lines.append("".join(row))

        return "\n".join(lines)

    def _get_power_up_char(self) -> str:
        """Get ASCII character for current power-up"""
        if not self.current_power_up:
            return "*"

        chars = {
            PowerUpType.APPLE: "*",
            PowerUpType.STAR: "S",
            PowerUpType.SHIELD: "D",
            PowerUpType.DIAMOND: "$",
            PowerUpType.FREEZE: "F",
            PowerUpType.MUSHROOM: "M",
        }
        return chars.get(self.current_power_up.type, "*")

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
