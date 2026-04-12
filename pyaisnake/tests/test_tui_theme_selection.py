"""Regression tests for TUI theme selection behavior."""

from __future__ import annotations

import asyncio
import importlib.util

import pytest


def _require_tui_dependencies() -> None:
    if importlib.util.find_spec("textual") is None:
        pytest.skip("textual is not installed in this environment")


def test_menu_theme_selection_applies_to_new_game_screens() -> None:
    """Changing theme in the menu should affect the next started game."""
    _require_tui_dependencies()

    from pyaisnake.renderer import Theme
    from pyaisnake.tui import GameScreen, MainMenuScreen, PyAISnakeTUI

    async def run_test() -> None:
        app = PyAISnakeTUI()
        async with app.run_test() as pilot:
            assert isinstance(app.screen, MainMenuScreen)

            app.action_next_theme()
            await pilot.pause()
            app.screen.action_play_classic()
            await pilot.pause()

            assert isinstance(app.screen, GameScreen)
            assert app.current_theme == Theme.NEON
            assert app.screen.theme == Theme.NEON

    asyncio.run(run_test())


def test_global_theme_switch_updates_active_game_screen() -> None:
    """The global theme hotkey should update an already-open game screen."""
    _require_tui_dependencies()

    from pyaisnake.renderer import Theme
    from pyaisnake.tui import GameField, GameScreen, PyAISnakeTUI

    async def run_test() -> None:
        app = PyAISnakeTUI()
        async with app.run_test() as pilot:
            app.push_screen(GameScreen())
            await pilot.pause()

            assert isinstance(app.screen, GameScreen)
            assert app.screen.theme == Theme.DEFAULT

            app.action_next_theme()
            await pilot.pause()

            assert app.current_theme == Theme.NEON
            assert app.screen.theme == Theme.NEON
            assert app.screen.query_one(GameField).theme == Theme.NEON

    asyncio.run(run_test())
