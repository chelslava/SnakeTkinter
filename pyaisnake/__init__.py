"""
PyAISnake - Modern Snake game with AI capabilities.

Usage:
    # As CLI
    pyaisnake play
    pyaisnake ai --visualize

    # As module
    python -m pyaisnake play

    # As library
    from pyaisnake import SnakeGame, Direction
    game = SnakeGame()
    while game.state == GameState.RUNNING:
        game.update()
        print(game.render_ascii())
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .controller import CLIController
from .engine import Direction, GameConfig, GameState, SnakeGame

if TYPE_CHECKING:
    from .renderer import CLIRenderer

__version__ = "2.9.0"
__all__ = [
    "Direction",
    "GameConfig",
    "GameState",
    "SnakeGame",
    "CLIRenderer",
    "CLIController",
]


def __getattr__(name: str) -> Any:
    """Lazily resolve optional UI exports."""
    if name == "CLIRenderer":
        from .renderer import CLIRenderer as renderer_class

        return renderer_class
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
