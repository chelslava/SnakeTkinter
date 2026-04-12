"""Regression tests for TUI state refresh behavior."""

from __future__ import annotations

import asyncio
import importlib.util

import pytest


def _require_tui_dependencies() -> None:
    if importlib.util.find_spec("textual") is None:
        pytest.skip("textual is not installed in this environment")


def test_pause_refreshes_title_and_message_bar() -> None:
    """Pausing should immediately refresh both title and message bar."""
    _require_tui_dependencies()

    from textual.widgets import Static

    from pyaisnake.engine import GameState
    from pyaisnake.tui import GameScreen, PyAISnakeTUI, TitleBar

    async def run_test() -> None:
        app = PyAISnakeTUI()
        async with app.run_test() as pilot:
            app.push_screen(GameScreen())
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, GameScreen)

            screen.action_toggle_pause()

            assert screen.game is not None
            assert screen.game.state == GameState.PAUSED
            assert "PAUSED" in str(screen.query_one(TitleBar).render())
            assert "PAUSED" in str(screen.query_one("#message-bar", Static).render())

    asyncio.run(run_test())


def test_restart_refreshes_stats_and_clears_status_message() -> None:
    """Restarting should immediately reset visible state without waiting for a tick."""
    _require_tui_dependencies()

    from textual.widgets import Static

    from pyaisnake.tui import GameScreen, PyAISnakeTUI, StatsPanel, TitleBar

    async def run_test() -> None:
        app = PyAISnakeTUI()
        async with app.run_test() as pilot:
            app.push_screen(GameScreen())
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, GameScreen)
            assert screen.game is not None

            screen.game.stats.score = 5
            screen.action_toggle_pause()
            screen.action_restart()

            assert screen.game.stats.score == 0
            assert "PAUSED" not in str(screen.query_one(TitleBar).render())
            assert "GAME OVER" not in str(screen.query_one(TitleBar).render())
            assert "Score:[/cyan]     [bold bright_green]0" in str(screen.query_one(StatsPanel).render())
            assert str(screen.query_one("#message-bar", Static).render()) == ""

    asyncio.run(run_test())


def test_game_over_tick_refreshes_title_and_message() -> None:
    """A terminal transition during a tick should refresh visible game-over feedback."""
    _require_tui_dependencies()

    from textual.widgets import Static

    from pyaisnake.engine import Direction, GameState
    from pyaisnake.tui import GameScreen, PyAISnakeTUI, TitleBar

    async def run_test() -> None:
        app = PyAISnakeTUI()
        async with app.run_test() as pilot:
            app.push_screen(GameScreen())
            await pilot.pause()

            screen = app.screen
            assert isinstance(screen, GameScreen)
            assert screen.game is not None

            head = screen.game.snake[0]
            screen.game.snake[0] = (screen.game.config.width - 1, head[1])
            screen.game.direction = Direction.RIGHT

            screen.game_tick()

            assert screen.game.state == GameState.GAME_OVER
            assert "GAME OVER" in str(screen.query_one(TitleBar).render())
            assert "GAME OVER" in str(screen.query_one("#message-bar", Static).render())

    asyncio.run(run_test())
