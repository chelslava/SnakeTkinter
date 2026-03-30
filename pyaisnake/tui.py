"""
Textual TUI for PyAISnake - Modern terminal user interface.
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Center, Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, Static

from .engine import Direction, GameConfig, GameState, SnakeGame


class GameWidget(Static):
    """Widget that renders the snake game"""

    game: reactive[SnakeGame | None] = reactive(None, recompose=True)

    def __init__(self, game: SnakeGame, **kwargs) -> None:
        super().__init__(**kwargs)
        self.game = game

    def render(self) -> str:
        if not self.game:
            return "No game"

        lines = []
        config = self.game.config
        w, h = config.width, config.height

        border = "═" * w
        lines.append(f"╔{border}╗")

        snake_set = set(self.game.snake)
        head = self.game.snake[0] if self.game.snake else None
        food = self.game.food

        for y in range(h):
            row_parts = ["║"]
            for x in range(w):
                pos = (x, y)
                if pos == head:
                    row_parts.append("[bold bright_green]██[/bold bright_green]")
                elif pos in snake_set:
                    row_parts.append("[green]▓▓[/green]")
                elif pos == food:
                    row_parts.append("[bold bright_red]🍎[/bold bright_red]")
                elif pos in self.game.obstacles:
                    row_parts.append("[dim yellow]▒▒[/dim yellow]")
                else:
                    row_parts.append("  ")
            row_parts.append("║")
            lines.append("".join(row_parts))

        lines.append(f"╚{border}╝")

        status = ""
        if self.game.state == GameState.PAUSED:
            status = " [bold yellow]⏸ PAUSED[/bold yellow]"
        elif self.game.state == GameState.GAME_OVER:
            status = " [bold red]☠ GAME OVER[/bold red]"
        elif self.game.state == GameState.WIN:
            status = " [bold bright_green]🏆 WIN![/bold bright_green]"

        lines.append(f"Score: {self.game.stats.score} | Length: {len(self.game.snake)}{status}")

        return "\n".join(lines)


class StatsWidget(Static):
    """Widget that shows game statistics"""

    game: reactive[SnakeGame | None] = reactive(None, recompose=True)

    def __init__(self, game: SnakeGame, **kwargs) -> None:
        super().__init__(**kwargs)
        self.game = game

    def render(self) -> str:
        if not self.game:
            return ""

        stats = self.game.stats
        lines = [
            "[bold cyan]═══ Stats ═══[/bold cyan]",
            "",
            f"  [cyan]Score:[/cyan]     [bold]{stats.score}[/bold]",
            f"  [cyan]Length:[/cyan]    {len(self.game.snake)}",
            f"  [cyan]Time:[/cyan]      {stats.duration:.1f}s",
            f"  [cyan]Moves:[/cyan]     {stats.moves}",
            f"  [cyan]Food:[/cyan]      {stats.food_eaten}",
        ]

        if stats.moves > 0:
            lines.append(f"  [cyan]Efficiency:[/cyan] {stats.efficiency:.1%}")

        return "\n".join(lines)


class ControlsWidget(Static):
    """Widget that shows controls"""

    def render(self) -> str:
        return """
[bold cyan]═══ Controls ═══[/bold cyan]

  [cyan]↑↓←→ / WASD[/cyan]  Move
  [cyan]P / Space[/cyan]    Pause
  [cyan]R[/cyan]            Restart
  [cyan]Q / Esc[/cyan]      Back
"""


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

    def __init__(self, config: GameConfig | None = None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.config = config or GameConfig(width=30, height=15, speed_ms=150)
        self.game: SnakeGame | None = None
        self._running = False
        self._timer = None

    def compose(self) -> ComposeResult:
        self.game = SnakeGame(self.config)

        yield Header()
        with Container(classes="game-container"), Horizontal():
            with Vertical(classes="game-area"):
                yield Center(GameWidget(self.game, id="game"))
            with Vertical(classes="sidebar"):
                yield StatsWidget(self.game, id="stats")
                yield ControlsWidget()
        yield Footer()

    def on_mount(self) -> None:
        self._running = True
        self._timer = self.set_interval(self.config.speed_ms / 1000, self.game_tick)

    def on_unmount(self) -> None:
        if self._timer:
            self._timer.stop()

    def game_tick(self) -> None:
        if self.game and self.game.state == GameState.RUNNING and self._running:
            self.game.update()
            game_widget = self.query_one("#game", GameWidget)
            stats_widget = self.query_one("#stats", StatsWidget)
            game_widget.game = self.game
            stats_widget.game = self.game
            game_widget.refresh()
            stats_widget.refresh()

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
    Screen {
        align: center middle;
    }

    .menu-container {
        width: 60;
        height: auto;
        padding: 2;
    }

    .title {
        text-align: center;
        margin-bottom: 2;
    }

    .menu-button {
        width: 100%;
        margin: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Center(), Container(classes="menu-container"):
            yield Label("[bold bright_green]🐍 PyAISnake[/bold bright_green]", classes="title")
            yield Label("[dim]TUI Edition[/dim]", classes="title")
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

    .game-container {
        width: 100%;
        height: 100%;
        padding: 1;
    }

    .game-area {
        width: auto;
        height: auto;
    }

    .sidebar {
        width: 25;
        height: auto;
        padding: 1;
        margin-left: 2;
    }

    GameWidget, StatsWidget, ControlsWidget {
        height: auto;
        padding: 1;
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
