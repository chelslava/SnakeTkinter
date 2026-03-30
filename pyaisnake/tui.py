"""
Textual TUI for PyAISnake - Modern terminal user interface.

Uses the same rendering as CLI for consistent look.
"""

from __future__ import annotations

from rich.panel import Panel
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Center, Container
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, Static

from .engine import Direction, GameConfig, GameState, SnakeGame
from .renderer import CLIRenderer, Theme


class GameWidget(Static):
    """Widget that renders the snake game"""

    game: reactive[SnakeGame | None] = reactive(None)
    theme: reactive[Theme] = reactive(Theme.DEFAULT)

    def __init__(self, game: SnakeGame, theme: Theme = Theme.DEFAULT, **kwargs) -> None:
        super().__init__(**kwargs)
        self.game = game
        self.theme = theme
        self._renderer = CLIRenderer(game, theme=theme)

    def render(self) -> Panel:
        if not self.game:
            return Panel("No game")

        self._renderer.game = self.game
        return self._renderer._generate_frame()


class GameScreen(Screen):
    """Main game screen"""

    BINDINGS = [
        Binding("up", "move_up", "Up", show=False),
        Binding("down", "move_down", "Down", show=False),
        Binding("left", "move_left", "Left", show=False),
        Binding("right", "move_right", "Right", show=False),
        Binding("w", "move_up", "Up", show=False),
        Binding("s", "move_down", "Down", show=False),
        Binding("a", "move_left", "Left", show=False),
        Binding("d", "move_right", "Right", show=False),
        Binding("p", "toggle_pause", "Pause"),
        Binding("space", "toggle_pause", "Pause", show=False),
        Binding("r", "restart", "Restart"),
        Binding("q", "quit_game", "Back"),
        Binding("escape", "quit_game", "Back", show=False),
    ]

    def __init__(
        self, config: GameConfig | None = None, theme: Theme = Theme.DEFAULT, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.config = config or GameConfig(width=30, height=15, speed_ms=150)
        self.theme = theme
        self.game: SnakeGame | None = None
        self._running = False
        self._timer = None

    def compose(self) -> ComposeResult:
        self.game = SnakeGame(self.config)
        yield GameWidget(self.game, self.theme)

    def on_mount(self) -> None:
        self._running = True
        self._timer = self.set_interval(self.config.speed_ms / 1000, self.game_tick)

    def on_unmount(self) -> None:
        if self._timer:
            self._timer.stop()

    def game_tick(self) -> None:
        if self.game and self.game.state == GameState.RUNNING and self._running:
            self.game.update()
            game_widget = self.query_one(GameWidget)
            game_widget.game = self.game
            game_widget.refresh()

            if self.game.state == GameState.GAME_OVER:
                self._running = False

    def action_move_up(self) -> None:
        if self.game:
            self.game.set_direction(Direction.UP)

    def action_move_down(self) -> None:
        if self.game:
            self.game.set_direction(Direction.DOWN)

    def action_move_left(self) -> None:
        if self.game:
            self.game.set_direction(Direction.LEFT)

    def action_move_right(self) -> None:
        if self.game:
            self.game.set_direction(Direction.RIGHT)

    def action_toggle_pause(self) -> None:
        if self.game:
            self.game.pause()

    def action_restart(self) -> None:
        if self.game:
            self.game.reset()
            self._running = True

    def action_quit_game(self) -> None:
        self.app.pop_screen()


class MainMenuScreen(Screen):
    """Main menu screen"""

    BINDINGS = [
        Binding("q,escape", "quit", "Quit"),
    ]

    CSS = """
    MainMenuScreen {
        align: center middle;
    }

    .menu-container {
        width: auto;
        height: auto;
        padding: 1;
    }

    .title {
        text-align: center;
        margin-bottom: 1;
    }

    .menu-button {
        width: 30;
        margin: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Center(), Container(classes="menu-container"):
            yield Label("[bold bright_green]🐍 PyAISnake[/bold bright_green]", classes="title")
            yield Label("[dim]Terminal UI Edition[/dim]", classes="title")
            yield Button("▶ Play", id="play", variant="success", classes="menu-button")
            yield Button("❌ Quit", id="quit", variant="error", classes="menu-button")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "play":
            self.app.push_screen(GameScreen())
        elif button_id == "quit":
            self.app.exit()


class PyAISnakeTUI(App):
    """PyAISnake TUI Application"""

    CSS = """
    Screen {
        background: $surface;
    }

    GameWidget {
        height: auto;
        width: auto;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
    ]

    SCREENS = {
        "menu": MainMenuScreen,
        "game": GameScreen,
    }

    def on_mount(self) -> None:
        self.push_screen("menu")


def main() -> int:
    """Entry point for TUI"""
    app = PyAISnakeTUI()
    app.run()
    return 0


if __name__ == "__main__":
    main()
