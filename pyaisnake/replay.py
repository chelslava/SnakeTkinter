"""
Replay system for PyAISnake - Record, playback, and analyze games.
"""

import json
import time
from dataclasses import dataclass, field


@dataclass
class ReplayFrame:
    """Single frame of replay data"""

    tick: int
    snake: list[tuple[int, int]]
    direction: str
    food: tuple[int, int] | None
    score: int
    state: str


@dataclass
class ReplayRecording:
    """Complete replay recording"""

    version: str = "1.0"
    game_mode: str = "classic"
    width: int = 40
    height: int = 20
    speed_ms: int = 100
    seed: int | None = None
    recorded_at: float = field(default_factory=time.time)

    frames: list[ReplayFrame] = field(default_factory=list)

    final_score: int = 0
    final_length: int = 3
    duration: float = 0.0

    def add_frame(self, frame: ReplayFrame) -> None:
        """Add a frame to the recording"""
        self.frames.append(frame)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "version": self.version,
            "game_mode": self.game_mode,
            "width": self.width,
            "height": self.height,
            "speed_ms": self.speed_ms,
            "seed": self.seed,
            "recorded_at": self.recorded_at,
            "final_score": self.final_score,
            "final_length": self.final_length,
            "duration": self.duration,
            "frame_count": len(self.frames),
            "frames": [
                {
                    "tick": f.tick,
                    "snake": f.snake,
                    "direction": f.direction,
                    "food": f.food,
                    "score": f.score,
                    "state": f.state,
                }
                for f in self.frames
            ],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ReplayRecording":
        """Create from dictionary"""
        recording = cls(
            version=data.get("version", "1.0"),
            game_mode=data.get("game_mode", "classic"),
            width=data.get("width", 40),
            height=data.get("height", 20),
            speed_ms=data.get("speed_ms", 100),
            seed=data.get("seed"),
            recorded_at=data.get("recorded_at", time.time()),
            final_score=data.get("final_score", 0),
            final_length=data.get("final_length", 3),
            duration=data.get("duration", 0.0),
        )

        for frame_data in data.get("frames", []):
            recording.frames.append(
                ReplayFrame(
                    tick=frame_data["tick"],
                    snake=[tuple(p) for p in frame_data["snake"]],
                    direction=frame_data["direction"],
                    food=tuple(frame_data["food"]) if frame_data.get("food") else None,
                    score=frame_data["score"],
                    state=frame_data["state"],
                )
            )

        return recording

    def save(self, path: str) -> None:
        """Save replay to JSON file"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "ReplayRecording":
        """Load replay from JSON file"""
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))


class ReplayRecorder:
    """Records game sessions for later playback"""

    def __init__(
        self,
        game_mode: str = "classic",
        width: int = 40,
        height: int = 20,
        speed_ms: int = 100,
        seed: int | None = None,
    ):
        self.recording = ReplayRecording(
            game_mode=game_mode,
            width=width,
            height=height,
            speed_ms=speed_ms,
            seed=seed,
        )
        self._tick = 0

    def record_frame(
        self,
        snake: list[tuple[int, int]],
        direction: str,
        food: tuple[int, int] | None,
        score: int,
        state: str,
    ) -> None:
        """Record a single game frame"""
        frame = ReplayFrame(
            tick=self._tick,
            snake=list(snake),
            direction=direction,
            food=food,
            score=score,
            state=state,
        )
        self.recording.add_frame(frame)
        self._tick += 1

    def finalize(self, final_score: int, final_length: int, duration: float) -> None:
        """Finalize the recording with final stats"""
        self.recording.final_score = final_score
        self.recording.final_length = final_length
        self.recording.duration = duration

    def save(self, path: str) -> None:
        """Save recording to file"""
        self.recording.save(path)


class ReplayPlayer:
    """Plays back recorded games"""

    def __init__(self, recording: ReplayRecording):
        self.recording = recording
        self.current_frame = 0
        self.speed_multiplier = 1.0
        self.paused = False

    @classmethod
    def load(cls, path: str) -> "ReplayPlayer":
        """Load a replay from file"""
        recording = ReplayRecording.load(path)
        return cls(recording)

    @property
    def total_frames(self) -> int:
        return len(self.recording.frames)

    @property
    def is_finished(self) -> bool:
        return self.current_frame >= self.total_frames

    def get_frame(self) -> ReplayFrame | None:
        """Get current frame"""
        if self.current_frame < self.total_frames:
            return self.recording.frames[self.current_frame]
        return None

    def next_frame(self) -> ReplayFrame | None:
        """Advance to next frame"""
        if not self.paused and self.current_frame < self.total_frames:
            self.current_frame += 1
        return self.get_frame()

    def seek(self, frame: int) -> None:
        """Seek to specific frame"""
        self.current_frame = max(0, min(frame, self.total_frames - 1))

    def seek_percent(self, percent: float) -> None:
        """Seek to percentage of replay"""
        frame = int(percent * self.total_frames / 100)
        self.seek(frame)

    def restart(self) -> None:
        """Restart from beginning"""
        self.current_frame = 0


class ReplayAnalyzer:
    """Analyzes recorded games"""

    def __init__(self, recording: ReplayRecording):
        self.recording = recording

    @classmethod
    def load(cls, path: str) -> "ReplayAnalyzer":
        """Load and analyze a replay"""
        recording = ReplayRecording.load(path)
        return cls(recording)

    def get_statistics(self) -> dict:
        """Get replay statistics"""
        if not self.recording.frames:
            return {}

        scores = [f.score for f in self.recording.frames]
        lengths = [len(f.snake) for f in self.recording.frames]

        score_changes = []
        for i in range(1, len(self.recording.frames)):
            diff = self.recording.frames[i].score - self.recording.frames[i - 1].score
            if diff > 0:
                score_changes.append((i, diff))

        directions = {}
        for f in self.recording.frames:
            directions[f.direction] = directions.get(f.direction, 0) + 1

        total_frames = len(self.recording.frames)
        avg_speed = total_frames / self.recording.duration if self.recording.duration > 0 else 0

        return {
            "total_frames": total_frames,
            "duration": self.recording.duration,
            "final_score": self.recording.final_score,
            "final_length": self.recording.final_length,
            "max_score": max(scores) if scores else 0,
            "max_length": max(lengths) if lengths else 0,
            "food_collected": self.recording.final_score,
            "avg_fps": round(avg_speed, 2),
            "direction_distribution": directions,
            "score_events": score_changes[:10],
            "efficiency": round(self.recording.final_score / total_frames, 3)
            if total_frames > 0
            else 0,
        }

    def get_heatmap_data(self) -> dict[tuple[int, int], int]:
        """Get snake position frequency for heatmap"""
        heatmap: dict[tuple[int, int], int] = {}
        for frame in self.recording.frames:
            for x, y in frame.snake:
                key = (x, y)
                heatmap[key] = heatmap.get(key, 0) + 1
        return heatmap

    def find_key_moments(self) -> list[dict]:
        """Find interesting moments in the replay"""
        moments = []

        for i, frame in enumerate(self.recording.frames):
            if i == 0:
                continue

            prev = self.recording.frames[i - 1]

            if frame.score > prev.score:
                moments.append(
                    {
                        "frame": i,
                        "type": "food_eaten",
                        "score": frame.score,
                        "length": len(frame.snake),
                    }
                )

            if frame.state == "game_over":
                moments.append(
                    {
                        "frame": i,
                        "type": "death",
                        "score": frame.score,
                        "length": len(frame.snake),
                    }
                )

            if len(frame.snake) < len(prev.snake):
                moments.append(
                    {
                        "frame": i,
                        "type": "shrink",
                        "from_length": len(prev.snake),
                        "to_length": len(frame.snake),
                    }
                )

        return moments
