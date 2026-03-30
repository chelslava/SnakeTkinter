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

from .controller import CLIController
from .engine import Direction, GameConfig, GameState, SnakeGame
from .renderer import CLIRenderer

__version__ = "2.6.0"
__all__ = [
    "Direction",
    "GameConfig",
    "GameState",
    "SnakeGame",
    "CLIRenderer",
    "CLIController",
]
