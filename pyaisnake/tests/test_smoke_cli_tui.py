"""Smoke coverage for user-facing CLI and TUI entry points."""

from __future__ import annotations

import asyncio
import importlib.util

import pytest


def _require_cli_dependencies() -> None:
    if importlib.util.find_spec("rich") is None:
        pytest.skip("rich is not installed in this environment")


def _require_tui_dependencies() -> None:
    if importlib.util.find_spec("textual") is None:
        pytest.skip("textual is not installed in this environment")


def test_cli_help_lists_primary_user_commands() -> None:
    """The root parser should expose the main user-facing commands."""
    _require_cli_dependencies()

    from pyaisnake.cli import create_parser

    help_text = create_parser().format_help()

    for command in ("play", "ai", "train", "stats", "replay", "analyze"):
        assert command in help_text


def test_cli_parser_smoke_for_core_commands() -> None:
    """Primary CLI commands should parse with their documented core options."""
    _require_cli_dependencies()

    from pyaisnake.cli import create_parser

    parser = create_parser()

    play_args = parser.parse_args(["play", "--width", "50", "--speed", "80"])
    ai_args = parser.parse_args(["ai", "--algorithm", "random", "--games", "2"])
    stats_args = parser.parse_args(["stats", "--top", "5"])

    assert play_args.command == "play"
    assert play_args.width == 50
    assert play_args.speed == 80
    assert ai_args.command == "ai"
    assert ai_args.algorithm == "random"
    assert ai_args.games == 2
    assert stats_args.command == "stats"
    assert stats_args.top == 5


def test_tui_app_mounts_menu_screen() -> None:
    """The TUI app should boot into the main menu without crashing."""
    _require_tui_dependencies()

    from pyaisnake.tui import MainMenuScreen, PyAISnakeTUI

    async def run_smoke() -> None:
        app = PyAISnakeTUI()
        async with app.run_test():
            assert isinstance(app.screen, MainMenuScreen)

    asyncio.run(run_smoke())


def test_game_screen_uses_expected_default_dimensions() -> None:
    """GameScreen should preserve its documented default playfield size."""
    _require_tui_dependencies()

    from pyaisnake.tui import GameScreen

    screen = GameScreen()

    assert screen.config.width == 40
    assert screen.config.height == 20
    assert screen.config.speed_ms == 120
