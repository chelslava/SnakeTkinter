"""
Textual TUI for PyAISnake - Modern terminal user interface.

Full-screen game with TUI-specific features.
"""

from __future__ import annotations

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, Static

from .engine import Direction, GameConfig, GameState, SnakeGame
from .renderer import Theme


class GameField(Static):
    """Widget that renders the snake game field"""

    game: reactive[SnakeGame | None] = reactive(None)
    theme: reactive[Theme] = reactive(Theme.DEFAULT)

    THEMES = {
        Theme.DEFAULT: {
            "head": ("██", "bold bright_green"),
            "body": ("▓▓", "green"),
            "food": ("🍎", "bold bright_red"),
            "empty": ("  ", None),
            "obstacle": ("▒▒", "dim yellow"),
        },
        Theme.NEON: {
            "head": ("◈◈", "bold bright_cyan"),
            "body": ("◇◇", "cyan"),
            "food": ("●●", "bold bright_magenta"),
            "empty": ("  ", None),
            "obstacle": ("▓▓", "dim magenta"),
        },
        Theme.RETRO: {
            "head": ("@@", "bold bright_green"),
            "body": ("oo", "green"),
            "food": ("**", "bold bright_red"),
            "empty": ("  ", None),
            "obstacle": ("%%", "dim yellow"),
        },
    }

    def __init__(self, game: SnakeGame, theme: Theme = Theme.DEFAULT, **kwargs) -> None:
        super().__init__(**kwargs)
        self.game = game
        self.theme = theme

    def render(self) -> str:
        if not self.game:
            return ""

        config = self.game.config
        w, h = config.width, config.height
        theme = self.THEMES.get(self.theme, self.THEMES[Theme.DEFAULT])

        lines = []
        border = "══" * w
        lines.append(f"╔{border}╗")

        snake_set = set(self.game.snake)
        head = self.game.snake[0] if self.game.snake else None
        food = self.game.food

        for y in range(h):
            row = "║"
            for x in range(w):
                pos = (x, y)
                if pos == head:
                    sym, color = theme["head"]
                    row += f"[{color}]{sym}[/{color}]" if color else sym
                elif pos in snake_set:
                    sym, color = theme["body"]
                    row += f"[{color}]{sym}[/{color}]" if color else sym
                elif pos == food:
                    sym, color = theme["food"]
                    row += f"[{color}]{sym}[/{color}]" if color else sym
                elif pos in self.game.obstacles:
                    sym, color = theme["obstacle"]
                    row += f"[{color}]{sym}[/{color}]" if color else sym
                else:
                    sym, _ = theme["empty"]
                    row += sym
            row += "║"
            lines.append(row)

        lines.append(f"╚{border}╝")
        return "\n".join(lines)


class StatsPanel(Static):
    """Widget that shows game statistics"""

    game: reactive[SnakeGame | None] = reactive(None)

    def __init__(self, game: SnakeGame, **kwargs) -> None:
        super().__init__(**kwargs)
        self.game = game

    def render(self) -> str:
        if not self.game:
            return ""

        stats = self.game.stats
        g = self.game

        lines = [
            "[bold bright_cyan]═══ STATS ═══[/bold bright_cyan]",
            "",
            f"  [cyan]Score:[/cyan]     [bold bright_green]{stats.score}[/bold bright_green]",
            f"  [cyan]Length:[/cyan]    {len(g.snake)}",
            f"  [cyan]Time:[/cyan]      {stats.duration:.1f}s",
            f"  [cyan]Moves:[/cyan]     {stats.moves}",
            f"  [cyan]Food:[/cyan]      {stats.food_eaten}",
        ]

        if stats.moves > 0:
            lines.append(f"  [cyan]Efficiency:[/cyan] {stats.efficiency:.1%}")

        if g.stats.power_ups_collected > 0:
            lines.append(
                f"  [cyan]Power-ups:[/cyan] [bright_magenta]{g.stats.power_ups_collected}[/bright_magenta]"
            )

        if g.active_effects:
            lines.append("")
            lines.append("[bold bright_yellow]═══ EFFECTS ═══[/bold bright_yellow]")
            for effect in g.active_effects:
                if effect.type.value == "star":
                    lines.append(
                        f"  [bright_yellow]⚡ Speed {effect.remaining:.0f}s[/bright_yellow]"
                    )
                elif effect.type.value == "diamond":
                    lines.append(
                        f"  [bright_magenta]×2 Score {effect.remaining:.0f}s[/bright_magenta]"
                    )
                elif effect.type.value == "freeze":
                    lines.append(f"  [bright_cyan]❄ Slow {effect.remaining:.0f}s[/bright_cyan]")

        lines.append("")
        lines.append("[bold bright_white]═══ CONTROLS ═══[/bold bright_white]")
        lines.append("")
        lines.append("  [white]↑↓←→ / WASD[/white]  Move")
        lines.append("  [white]P / Space[/white]    Pause")
        lines.append("  [white]R[/white]            Restart")
        lines.append("  [white]Q / Esc[/white]      Menu")

        lines.append("")
        dir_arrows = {
            Direction.UP: "↑",
            Direction.DOWN: "↓",
            Direction.LEFT: "←",
            Direction.RIGHT: "→",
        }
        arrow = dir_arrows.get(g.direction, "?")
        lines.append(f"  Direction: [bold bright_yellow]{arrow}[/bold bright_yellow]")

        safe = g.get_safe_directions()
        safe_color = {0: "red", 1: "yellow", 2: "green", 3: "bright_green"}.get(len(safe), "white")
        lines.append(f"  Safe: [{safe_color}]{len(safe)}[/{safe_color}]")

        return "\n".join(lines)


class TitleBar(Static):
    """Title bar showing game state"""

    game: reactive[SnakeGame | None] = reactive(None)

    def __init__(self, game: SnakeGame, **kwargs) -> None:
        super().__init__(**kwargs)
        self.game = game

    def render(self) -> str:
        if not self.game:
            return ""

        title = "[bold bright_green]🐍 PyAISnake[/bold bright_green]"

        if self.game.state == GameState.PAUSED:
            title += "  [bold yellow]⏸ PAUSED[/bold yellow]"
        elif self.game.state == GameState.GAME_OVER:
            title += "  [bold red]☠ GAME OVER[/bold red]"
        elif self.game.state == GameState.WIN:
            title += "  [bold bright_green]🏆 WIN![/bold bright_green]"

        if self.game.shield_count > 0:
            title += f"  [bright_blue]🛡×{self.game.shield_count}[/bright_blue]"
        if self.game.score_multiplier > 1:
            title += f"  [bright_magenta]×{int(self.game.score_multiplier)}[/bright_magenta]"
        if self.game.speed_modifier < 1:
            title += "  [bright_yellow]⚡[/bright_yellow]"
        if self.game.speed_modifier > 1:
            title += "  [bright_cyan]❄[/bright_cyan]"

        return title


class GameScreen(Screen):
    """Full-screen game screen"""

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
        Binding("q", "quit_game", "Menu"),
        Binding("escape", "quit_game", "Menu", show=False),
    ]

    CSS = """
    GameScreen {
        layout: vertical;
    }

    .title-bar {
        height: 3;
        padding: 1 2;
        content-align: center middle;
    }

    .game-container {
        layout: horizontal;
        height: 1fr;
    }

    .game-field {
        width: 1fr;
        padding: 1 2;
        content-align: center middle;
    }

    .stats-panel {
        width: 28;
        padding: 1 2;
    }

    .message-bar {
        height: 3;
        padding: 1 2;
        content-align: center middle;
    }
    """

    def __init__(
        self, config: GameConfig | None = None, theme: Theme = Theme.DEFAULT, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.config = config or GameConfig(width=40, height=20, speed_ms=120)
        self.theme = theme
        self.game: SnakeGame | None = None
        self._running = False
        self._timer = None

    def compose(self) -> ComposeResult:
        self.game = SnakeGame(self.config)

        yield TitleBar(self.game, classes="title-bar")
        with Horizontal(classes="game-container"):
            yield GameField(self.game, self.theme, classes="game-field")
            yield StatsPanel(self.game, classes="stats-panel")
        yield Static("", id="message-bar", classes="message-bar")

    def on_mount(self) -> None:
        self._running = True
        self._timer = self.set_interval(self.config.speed_ms / 1000, self.game_tick)
        self._refresh_view("")

    def on_unmount(self) -> None:
        if self._timer:
            self._timer.stop()

    def _refresh_view(self, message: str | None = None) -> None:
        """Refresh all game widgets from the current game state."""
        if not self.game:
            return

        title_bar = self.query_one(TitleBar)
        game_field = self.query_one(GameField)
        stats_panel = self.query_one(StatsPanel)
        message_bar = self.query_one("#message-bar", Static)

        title_bar.game = self.game
        game_field.game = self.game
        stats_panel.game = self.game

        title_bar.refresh()
        game_field.refresh()
        stats_panel.refresh()

        if message is not None:
            message_bar.update(message)
            message_bar.refresh()

    def game_tick(self) -> None:
        if self.game and self.game.state == GameState.RUNNING and self._running:
            self.game.update()
            message = None

            if self.game.state == GameState.GAME_OVER:
                self._running = False
                message = "[bold red]☠ GAME OVER! Press R to restart or Q for menu[/bold red]"
            elif self.game.state == GameState.WIN:
                self._running = False
                message = (
                    "[bold bright_green]🏆 YOU WIN! Press R to restart or Q for menu[/bold bright_green]"
                )

            self._refresh_view(message)

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
            if self.game.state == GameState.PAUSED:
                self._refresh_view("[bold yellow]⏸ PAUSED - Press P to continue[/bold yellow]")
            else:
                self._refresh_view("")

    def action_restart(self) -> None:
        if self.game:
            self.game.reset()
            self._running = True
            self._refresh_view("")

    def action_quit_game(self) -> None:
        self.app.pop_screen()


class MainMenuScreen(Screen):
    """Main menu screen with options"""

    BINDINGS = [
        Binding("q,escape", "quit", "Quit"),
        Binding("1", "play_classic", "Classic"),
        Binding("2", "play_speed", "Speed"),
    ]

    CSS = """
    MainMenuScreen {
        align: center middle;
        background: $surface;
    }

    .menu-container {
        width: 60;
        padding: 2;
    }

    .menu-title {
        text-align: center;
        margin-bottom: 2;
    }

    .menu-subtitle {
        text-align: center;
        margin-bottom: 1;
    }

    .menu-button {
        width: 100%;
        margin: 1;
        min-height: 3;
    }

    .menu-section {
        margin-top: 2;
        text-align: center;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(classes="menu-container"):
            yield Label("[bold bright_green]🐍 PyAISnake[/bold bright_green]", classes="menu-title")
            yield Label("[dim]TUI Edition - Full Screen Mode[/dim]", classes="menu-subtitle")

            yield Label("[bold cyan]Game Modes[/bold cyan]", classes="menu-section")
            yield Button("🎮 Classic Mode", id="classic", variant="success", classes="menu-button")
            yield Button(
                "⚡ Speed Mode (Fast)", id="speed", variant="warning", classes="menu-button"
            )
            yield Button(
                "🎯 Challenge Mode", id="challenge", variant="primary", classes="menu-button"
            )

            yield Label("[bold cyan]Options[/bold cyan]", classes="menu-section")
            yield Button("🎨 Change Theme", id="theme", variant="default", classes="menu-button")

            yield Label("[bold cyan]Other[/bold cyan]", classes="menu-section")
            yield Button("❌ Quit", id="quit", variant="error", classes="menu-button")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id

        if button_id == "classic":
            config = GameConfig(width=40, height=20, speed_ms=120)
            self.app.push_screen(GameScreen(config))
        elif button_id == "speed":
            config = GameConfig(width=40, height=20, speed_ms=60)
            self.app.push_screen(GameScreen(config))
        elif button_id == "challenge":
            config = GameConfig(width=25, height=15, speed_ms=80)
            self.app.push_screen(GameScreen(config))
        elif button_id == "theme":
            self.app.next_theme()
        elif button_id == "quit":
            self.app.exit()

    def action_play_classic(self) -> None:
        config = GameConfig(width=40, height=20, speed_ms=120)
        self.app.push_screen(GameScreen(config))

    def action_play_speed(self) -> None:
        config = GameConfig(width=40, height=20, speed_ms=60)
        self.app.push_screen(GameScreen(config))


class PyAISnakeTUI(App):
    """PyAISnake TUI Application with full-screen game"""

    CSS = """
    App {
        background: $surface;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+t", "next_theme", "Theme", show=True),
    ]

    SCREENS = {
        "menu": MainMenuScreen,
        "game": GameScreen,
    }

    _themes = [Theme.DEFAULT, Theme.NEON, Theme.RETRO]
    _theme_index = 0

    def on_mount(self) -> None:
        self.push_screen("menu")

    def action_next_theme(self) -> None:
        self._theme_index = (self._theme_index + 1) % len(self._themes)
        theme_name = self._themes[self._theme_index].value
        self.notify(f"Theme: {theme_name}", title="Theme Changed")


def main() -> int:
    """Entry point for TUI"""
    app = PyAISnakeTUI()
    app.run()
    return 0


if __name__ == "__main__":
    main()
