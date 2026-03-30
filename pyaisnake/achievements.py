"""
Achievement system for PyAISnake.
"""

import json
import sqlite3
import time
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum


class AchievementType(Enum):
    SCORE = "score"
    LENGTH = "length"
    TIME = "time"
    SPEED = "speed"
    POWER_UPS = "power_ups"
    SPECIAL = "special"


@dataclass
class Achievement:
    """Achievement definition"""

    id: str
    name: str
    description: str
    type: AchievementType
    threshold: int
    icon: str = "🏆"
    secret: bool = False


# All achievements
ACHIEVEMENTS = [
    # Score achievements
    Achievement(
        "first_food", "First Blood", "Eat your first apple", AchievementType.SCORE, 1, "🍎"
    ),
    Achievement(
        "score_10", "Getting Started", "Reach a score of 10", AchievementType.SCORE, 10, "⭐"
    ),
    Achievement("score_25", "Snake Master", "Reach a score of 25", AchievementType.SCORE, 25, "🌟"),
    Achievement(
        "score_50", "Legendary Snake", "Reach a score of 50", AchievementType.SCORE, 50, "👑"
    ),
    Achievement("score_100", "Snake God", "Reach a score of 100", AchievementType.SCORE, 100, "🏆"),
    # Length achievements
    Achievement("length_10", "Growing Up", "Reach length 10", AchievementType.LENGTH, 10, "📏"),
    Achievement("length_25", "Long Boi", "Reach length 25", AchievementType.LENGTH, 25, "🐍"),
    Achievement("length_50", "Anaconda", "Reach length 50", AchievementType.LENGTH, 50, "🦎"),
    # Time achievements
    Achievement(
        "survivor_1min", "Survivor I", "Survive for 1 minute", AchievementType.TIME, 60, "⏱️"
    ),
    Achievement(
        "survivor_3min", "Survivor II", "Survive for 3 minutes", AchievementType.TIME, 180, "⏱️"
    ),
    Achievement(
        "survivor_5min", "Survivor III", "Survive for 5 minutes", AchievementType.TIME, 300, "⏱️"
    ),
    Achievement("marathon", "Marathon", "Survive for 10 minutes", AchievementType.TIME, 600, "🏃"),
    # Speed achievements
    Achievement(
        "speed_demon",
        "Speed Demon",
        "Win puzzle mode in under 2 minutes",
        AchievementType.SPEED,
        120,
        "⚡",
    ),
    Achievement(
        "lightning", "Lightning Fast", "Get 10 food in 30 seconds", AchievementType.SPEED, 30, "⚡"
    ),
    # Power-up achievements
    Achievement(
        "power_collector",
        "Collector",
        "Collect 5 power-ups in one game",
        AchievementType.POWER_UPS,
        5,
        "💎",
    ),
    Achievement(
        "power_hunter",
        "Power Hunter",
        "Collect 25 power-ups total",
        AchievementType.POWER_UPS,
        25,
        "💎",
    ),
    # Special achievements
    Achievement(
        "perfect_game",
        "Perfectionist",
        "Score 50+ without dying",
        AchievementType.SPECIAL,
        50,
        "✨",
        secret=True,
    ),
    Achievement(
        "close_call",
        "Close Call",
        "Survive with only 1 safe move 10 times",
        AchievementType.SPECIAL,
        10,
        "😅",
        secret=True,
    ),
    Achievement(
        "survival_master",
        "Survival Master",
        "Survive 5 minutes in Survival mode",
        AchievementType.SPECIAL,
        300,
        "💪",
    ),
    Achievement(
        "puzzle_solver", "Puzzle Solver", "Complete Puzzle mode", AchievementType.SPECIAL, 20, "🧩"
    ),
    Achievement(
        "time_champion",
        "Time Champion",
        "Score 30+ in Time Attack",
        AchievementType.SPECIAL,
        30,
        "⏱️",
    ),
]


class AchievementSystem:
    """Manage achievements"""

    def __init__(self, db_path: str = "snake_stats.db"):
        self.db_path = db_path
        self._init_db()

        # Callback for when achievement is unlocked
        self.on_unlock: Callable[[Achievement], None] | None = None

        # Track progress during game
        self._session_stats = {
            "close_calls": 0,
            "power_ups": 0,
            "start_time": time.time(),
            "max_score": 0,
            "max_length": 0,
        }

    def _init_db(self) -> None:
        """Initialize database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS achievements (
                id TEXT PRIMARY KEY,
                unlocked_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        try:
            cursor.execute("SELECT id FROM achievements LIMIT 1")
        except sqlite3.OperationalError:
            cursor.execute("DROP TABLE IF EXISTS achievements")
            cursor.execute("""
                CREATE TABLE achievements (
                    id TEXT PRIMARY KEY,
                    unlocked_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

        conn.commit()
        conn.close()

    def start_session(self) -> None:
        """Reset session stats for new game"""
        self._session_stats = {
            "close_calls": 0,
            "power_ups": 0,
            "start_time": time.time(),
            "max_score": 0,
            "max_length": 0,
        }

    def record_close_call(self) -> None:
        """Record a close call (1 safe move)"""
        self._session_stats["close_calls"] += 1
        self._check_special_achievement("close_call", self._session_stats["close_calls"])

    def record_power_up(self) -> None:
        """Record power-up collection"""
        self._session_stats["power_ups"] += 1
        self._check_achievement("power_collector", self._session_stats["power_ups"])

    def check_achievements(
        self,
        score: int,
        length: int,
        duration: float,
        game_mode: str | None = None,
        power_ups: int = 0,
    ) -> list[Achievement]:
        """Check and unlock achievements based on game state"""
        unlocked = []

        self._session_stats["max_score"] = max(self._session_stats["max_score"], score)
        self._session_stats["max_length"] = max(self._session_stats["max_length"], length)

        for achievement in ACHIEVEMENTS:
            should_check = (
                (achievement.type == AchievementType.SCORE and score >= achievement.threshold)
                or (achievement.type == AchievementType.LENGTH and length >= achievement.threshold)
                or (achievement.type == AchievementType.TIME and duration >= achievement.threshold)
                or (
                    achievement.type == AchievementType.POWER_UPS
                    and power_ups >= achievement.threshold
                )
            )
            if should_check and self._unlock(achievement):
                unlocked.append(achievement)

        if score >= 50 and duration > 0:
            self._check_special_achievement("perfect_game", 1)

        if game_mode == "survival" and duration >= 300:
            self._check_special_achievement("survival_master", int(duration))

        if game_mode == "puzzle" and length >= 20:
            self._check_special_achievement("puzzle_solver", length)

        if game_mode == "time_attack" and score >= 30:
            self._check_special_achievement("time_champion", score)

        return unlocked

    def _check_achievement(self, achievement_id: str, value: int) -> None:
        """Check if achievement should be unlocked"""
        achievement = next((a for a in ACHIEVEMENTS if a.id == achievement_id), None)
        if achievement and value >= achievement.threshold:
            self._unlock(achievement)

    def _check_special_achievement(self, achievement_id: str, value: int) -> None:
        """Check special achievement"""
        achievement = next((a for a in ACHIEVEMENTS if a.id == achievement_id), None)
        if achievement and value >= achievement.threshold:
            self._unlock(achievement)

    def _unlock(self, achievement: Achievement) -> bool:
        """Unlock an achievement. Returns True if newly unlocked."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Check if already unlocked
        cursor.execute("SELECT id FROM achievements WHERE id = ?", (achievement.id,))
        if cursor.fetchone():
            conn.close()
            return False

        # Unlock
        cursor.execute("INSERT INTO achievements (id) VALUES (?)", (achievement.id,))
        conn.commit()
        conn.close()

        # Notify callback
        if self.on_unlock:
            self.on_unlock(achievement)

        return True

    def is_unlocked(self, achievement_id: str) -> bool:
        """Check if achievement is unlocked"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM achievements WHERE id = ?", (achievement_id,))
        result = cursor.fetchone() is not None

        conn.close()
        return result

    def get_unlocked(self) -> list[Achievement]:
        """Get all unlocked achievements"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("SELECT id FROM achievements")
        unlocked_ids = {row[0] for row in cursor.fetchall()}

        conn.close()

        return [a for a in ACHIEVEMENTS if a.id in unlocked_ids]

    def get_locked(self) -> list[Achievement]:
        """Get all locked achievements (excluding secret)"""
        unlocked_ids = {a.id for a in self.get_unlocked()}
        return [a for a in ACHIEVEMENTS if a.id not in unlocked_ids and not a.secret]

    def get_progress(self) -> dict:
        """Get overall achievement progress"""
        unlocked = self.get_unlocked()
        total = len(ACHIEVEMENTS)

        by_type: dict[str, dict] = {}
        for achievement in ACHIEVEMENTS:
            type_name = achievement.type.value
            if type_name not in by_type:
                by_type[type_name] = {"total": 0, "unlocked": 0}

            by_type[type_name]["total"] += 1
            if achievement in unlocked:
                by_type[type_name]["unlocked"] += 1

        return {
            "total": total,
            "unlocked": len(unlocked),
            "percentage": round(len(unlocked) / total * 100, 1) if total > 0 else 0,
            "by_type": by_type,
        }

    def export_to_json(self, path: str) -> None:
        """Export achievements to JSON"""
        unlocked = self.get_unlocked()

        data = {
            "achievements": [
                {
                    "id": a.id,
                    "name": a.name,
                    "description": a.description,
                    "type": a.type.value,
                    "icon": a.icon,
                }
                for a in unlocked
            ],
            "progress": self.get_progress(),
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
