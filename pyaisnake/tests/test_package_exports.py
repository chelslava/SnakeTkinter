"""Tests for package-level exports and optional import boundaries."""

from __future__ import annotations

import importlib.util

import pytest

import pyaisnake


def test_core_exports_do_not_eagerly_import_renderer() -> None:
    """Core package import should not eagerly load the optional renderer."""
    assert pyaisnake.SnakeGame.__name__ == "SnakeGame"
    assert pyaisnake.Direction.RIGHT.value == "Right"
    assert "CLIRenderer" not in pyaisnake.__dict__


def test_renderer_export_is_lazily_available_when_rich_is_installed() -> None:
    """The renderer export should still work when optional deps are available."""
    if importlib.util.find_spec("rich") is None:
        pytest.skip("rich is not installed in this environment")

    renderer_class = pyaisnake.CLIRenderer
    assert renderer_class.__name__ == "CLIRenderer"
