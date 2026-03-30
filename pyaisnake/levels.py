"""
Level system for PyAISnake - Custom levels with obstacles and objectives.
"""

import json
import random
from dataclasses import dataclass, field
from enum import Enum


class LevelObjective(Enum):
    REACH_SCORE = "reach_score"
    REACH_LENGTH = "reach_length"
    SURVIVE_TIME = "survive_time"
    COLLECT_ALL = "collect_all"


@dataclass
class LevelConfig:
    """Configuration for a custom level"""

    name: str = "Custom Level"
    description: str = ""
    width: int = 40
    height: int = 20
    speed_ms: int = 100

    obstacles: list[tuple[int, int]] = field(default_factory=list)
    power_up_positions: list[tuple[int, int, str]] = field(default_factory=list)

    start_position: tuple[int, int] | None = None
    start_direction: str = "right"
    start_length: int = 3

    objective: LevelObjective = LevelObjective.REACH_SCORE
    objective_value: int = 10

    time_limit: float | None = None

    walls_wrap: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "name": self.name,
            "description": self.description,
            "width": self.width,
            "height": self.height,
            "speed_ms": self.speed_ms,
            "obstacles": self.obstacles,
            "power_up_positions": self.power_up_positions,
            "start_position": self.start_position,
            "start_direction": self.start_direction,
            "start_length": self.start_length,
            "objective": self.objective.value,
            "objective_value": self.objective_value,
            "time_limit": self.time_limit,
            "walls_wrap": self.walls_wrap,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LevelConfig":
        """Create from dictionary"""
        return cls(
            name=data.get("name", "Custom Level"),
            description=data.get("description", ""),
            width=data.get("width", 40),
            height=data.get("height", 20),
            speed_ms=data.get("speed_ms", 100),
            obstacles=[tuple(o) for o in data.get("obstacles", [])],
            power_up_positions=[tuple(p) for p in data.get("power_up_positions", [])],
            start_position=tuple(data["start_position"]) if data.get("start_position") else None,
            start_direction=data.get("start_direction", "right"),
            start_length=data.get("start_length", 3),
            objective=LevelObjective(data.get("objective", "reach_score")),
            objective_value=data.get("objective_value", 10),
            time_limit=data.get("time_limit"),
            walls_wrap=data.get("walls_wrap", False),
        )

    def save(self, path: str) -> None:
        """Save level to JSON file"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "LevelConfig":
        """Load level from JSON file"""
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


BUILTIN_LEVELS: dict[str, LevelConfig] = {
    "classic": LevelConfig(
        name="Classic",
        description="Standard endless mode",
        width=40,
        height=20,
    ),
    "maze_small": LevelConfig(
        name="Small Maze",
        description="Navigate through a small maze",
        width=20,
        height=20,
        obstacles=[
            (5, 5),
            (5, 6),
            (5, 7),
            (5, 8),
            (5, 9),
            (5, 10),
            (5, 11),
            (5, 12),
            (5, 13),
            (5, 14),
            (14, 5),
            (14, 6),
            (14, 7),
            (14, 8),
            (14, 9),
            (14, 10),
            (14, 11),
            (14, 12),
            (14, 13),
            (14, 14),
        ],
        objective=LevelObjective.REACH_LENGTH,
        objective_value=15,
    ),
    "cross": LevelConfig(
        name="Crossroads",
        description="Cross-shaped obstacles",
        width=30,
        height=20,
        obstacles=[
            (14, 5),
            (14, 6),
            (14, 7),
            (14, 8),
            (14, 11),
            (14, 12),
            (14, 13),
            (14, 14),
            (8, 9),
            (9, 9),
            (10, 9),
            (11, 9),
            (17, 9),
            (18, 9),
            (19, 9),
            (20, 9),
            (8, 10),
            (9, 10),
            (10, 10),
            (11, 10),
            (17, 10),
            (18, 10),
            (19, 10),
            (20, 10),
        ],
        objective=LevelObjective.REACH_SCORE,
        objective_value=20,
    ),
    "speed_run": LevelConfig(
        name="Speed Run",
        description="Fast-paced challenge",
        width=30,
        height=15,
        speed_ms=50,
        objective=LevelObjective.SURVIVE_TIME,
        objective_value=60,
    ),
    "spiral": LevelConfig(
        name="Spiral",
        description="Spiral maze pattern",
        width=25,
        height=25,
        obstacles=[
            (5, 5),
            (6, 5),
            (7, 5),
            (8, 5),
            (9, 5),
            (10, 5),
            (11, 5),
            (12, 5),
            (13, 5),
            (14, 5),
            (15, 5),
            (16, 5),
            (17, 5),
            (18, 5),
            (19, 5),
            (19, 6),
            (19, 7),
            (19, 8),
            (19, 9),
            (19, 10),
            (19, 11),
            (19, 12),
            (19, 13),
            (19, 14),
            (19, 15),
            (19, 16),
            (19, 17),
            (19, 18),
            (19, 19),
            (18, 19),
            (17, 19),
            (16, 19),
            (15, 19),
            (14, 19),
            (13, 19),
            (12, 19),
            (11, 19),
            (10, 19),
            (9, 19),
            (8, 19),
            (7, 19),
            (6, 19),
            (5, 19),
            (5, 18),
            (5, 17),
            (5, 16),
            (5, 15),
            (5, 14),
            (5, 13),
            (5, 12),
            (5, 11),
            (5, 10),
            (5, 9),
            (5, 8),
            (5, 7),
            (5, 6),
            (8, 8),
            (9, 8),
            (10, 8),
            (11, 8),
            (12, 8),
            (13, 8),
            (14, 8),
            (15, 8),
            (16, 8),
            (16, 9),
            (16, 10),
            (16, 11),
            (16, 12),
            (16, 13),
            (16, 14),
            (16, 15),
            (16, 16),
            (15, 16),
            (14, 16),
            (13, 16),
            (12, 16),
            (11, 16),
            (10, 16),
            (9, 16),
            (8, 16),
            (8, 15),
            (8, 14),
            (8, 13),
            (8, 12),
            (8, 11),
            (8, 10),
            (8, 9),
        ],
        objective=LevelObjective.REACH_LENGTH,
        objective_value=30,
    ),
    "tiny": LevelConfig(
        name="Tiny Box",
        description="Very small field",
        width=10,
        height=10,
        speed_ms=80,
        objective=LevelObjective.REACH_LENGTH,
        objective_value=15,
    ),
    "wide": LevelConfig(
        name="Wide Open",
        description="Extra wide field",
        width=60,
        height=10,
        objective=LevelObjective.REACH_SCORE,
        objective_value=50,
    ),
    "survival_easy": LevelConfig(
        name="Survival Easy",
        description="Survive for 2 minutes",
        width=40,
        height=20,
        speed_ms=150,
        objective=LevelObjective.SURVIVE_TIME,
        objective_value=120,
    ),
}


def list_levels() -> list[str]:
    """List all available levels"""
    return list(BUILTIN_LEVELS.keys())


def get_level(name: str) -> LevelConfig | None:
    """Get a level by name"""
    return BUILTIN_LEVELS.get(name)


def generate_random_level(difficulty: str = "normal") -> LevelConfig:
    """Generate a random level"""
    if difficulty == "easy":
        width, height = 40, 20
        num_obstacles = 5
        speed = 120
    elif difficulty == "hard":
        width, height = 30, 15
        num_obstacles = 30
        speed = 70
    else:
        width, height = 35, 18
        num_obstacles = 15
        speed = 100

    obstacles = set()
    center_x, center_y = width // 2, height // 2

    safe_zone = set()
    for dx in range(-3, 4):
        for dy in range(-3, 4):
            safe_zone.add((center_x + dx, center_y + dy))

    all_positions = {(x, y) for x in range(width) for y in range(height)} - safe_zone

    for _ in range(num_obstacles):
        if all_positions:
            pos = random.choice(list(all_positions))
            obstacles.add(pos)
            all_positions.discard(pos)

    return LevelConfig(
        name=f"Random {difficulty.title()}",
        description=f"Randomly generated {difficulty} level",
        width=width,
        height=height,
        speed_ms=speed,
        obstacles=list(obstacles),
        objective=LevelObjective.REACH_SCORE,
        objective_value=20 if difficulty == "easy" else 15 if difficulty == "normal" else 10,
    )
