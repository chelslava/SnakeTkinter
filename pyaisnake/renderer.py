"""
CLI Renderer - Rich-based terminal rendering for Snake game.
"""

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from .engine import Direction, GameState, SnakeGame


class CLIRenderer:
    """
    Rich-based CLI renderer for Snake game with smooth rendering.
    """

    # Unicode symbols - all double-width for consistent grid
    SYMBOLS = {
        "head": "██",
        "body": "▓▓",
        "food": "🍎",
        "obstacle": "▒▒",
        "empty": "  ",
        "border_h": "══",
        "border_v": "║",
        "border_tl": "╔",
        "border_tr": "╗",
        "border_bl": "╚",
        "border_br": "╝",
    }

    # ASCII fallback
    ASCII_SYMBOLS = {
        "head": "@@",
        "body": "oo",
        "food": "**",
        "obstacle": "##",
        "empty": "  ",
        "border_h": "--",
        "border_v": "|",
        "border_tl": "+",
        "border_tr": "+",
        "border_bl": "+",
        "border_br": "+",
    }

    # Colors
    COLORS = {
        "head": "bold bright_green",
        "body": "green",
        "food": "bold bright_red on red",
        "obstacle": "dim yellow",
        "border": "bright_white",
        "empty": "black",
    }

    def __init__(
        self,
        game: SnakeGame,
        console: Console | None = None,
        use_unicode: bool = True,
    ):
        self.game = game
        self.console = console or Console()
        self.use_unicode = use_unicode
        self.symbols = self.SYMBOLS if use_unicode else self.ASCII_SYMBOLS
        self._live: Live | None = None

    def start_live(self) -> None:
        """Start live display mode for smooth rendering"""
        self._live = Live(
            self._generate_frame(),
            console=self.console,
            refresh_per_second=30,
            screen=True,
        )
        self._live.start()

    def stop_live(self) -> None:
        """Stop live display"""
        if self._live:
            self._live.stop()
            self._live = None

    def update(self) -> None:
        """Update display without flickering"""
        if self._live:
            self._live.update(self._generate_frame())
        else:
            self.render()

    def render(self) -> None:
        """Render current game state to terminal (single frame)"""
        self.console.print(self._generate_frame())

    def _generate_frame(self) -> Panel:
        """Generate complete frame as Panel"""
        game_content = self._render_game_field()
        stats_content = self._render_stats()

        layout = Table(show_header=False, show_edge=False, expand=False)
        layout.add_column()
        layout.add_column()
        layout.add_row(game_content, stats_content)

        title = "[bold bright_green]PyAISnake[/bold bright_green]"

        if self.game.state == GameState.PAUSED:
            title += " [bold yellow]⏸ PAUSED[/bold yellow]"
        elif self.game.state == GameState.GAME_OVER:
            title += " [bold red]☠ GAME OVER[/bold red]"

        return Panel(
            layout,
            title=title,
            title_align="left",
            border_style="bright_green",
            padding=(0, 1),
        )

    def _render_game_field(self) -> str:
        """Render game field as string with consistent grid"""
        lines = []
        config = self.game.config

        # Top border - double width characters
        border = self.symbols["border_h"] * config.width
        lines.append(f"{self.symbols['border_tl']}{border}{self.symbols['border_tr']}")

        # Pre-compute for O(1) lookup
        snake_set = set(self.game.snake)
        head = self.game.snake[0] if self.game.snake else None
        food = self.game.food

        # Game field
        for y in range(config.height):
            row_parts = [self.symbols["border_v"]]

            for x in range(config.width):
                pos = (x, y)

                if pos == head:
                    row_parts.append(self._colorize(self.symbols["head"], "head"))
                elif pos in snake_set:
                    row_parts.append(self._colorize(self.symbols["body"], "body"))
                elif pos == food:
                    row_parts.append(self._colorize(self.symbols["food"], "food"))
                elif pos in self.game.obstacles:
                    row_parts.append(self._colorize(self.symbols["obstacle"], "obstacle"))
                else:
                    row_parts.append(self.symbols["empty"])

            row_parts.append(self.symbols["border_v"])
            lines.append("".join(row_parts))

        # Bottom border
        lines.append(f"{self.symbols['border_bl']}{border}{self.symbols['border_br']}")

        return "\n".join(lines)

    def _colorize(self, text: str, style: str) -> str:
        """Apply color style to text"""
        color = self.COLORS.get(style, "white")
        return f"[{color}]{text}[/{color}]"

    def _render_stats(self) -> Panel:
        """Render statistics panel"""
        stats = self.game.stats

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(justify="right", style="cyan", no_wrap=True)
        table.add_column(justify="left", style="bold white", no_wrap=True)

        table.add_row("Score", f"[bold bright_green]{stats.score}[/bold bright_green]")
        table.add_row("Length", str(len(self.game.snake)))
        table.add_row("Moves", str(stats.moves))
        table.add_row("Food", str(stats.food_eaten))
        table.add_row("Time", f"{stats.duration:.1f}s")

        if stats.moves > 0:
            table.add_row("Efficiency", f"{stats.efficiency:.1%}")

        dir_arrows = {
            Direction.UP: "↑",
            Direction.DOWN: "↓",
            Direction.LEFT: "←",
            Direction.RIGHT: "→",
        }
        arrow = dir_arrows.get(self.game.direction, "?")
        table.add_row("Direction", f"[bold]{arrow}[/bold]")

        safe = self.game.get_safe_directions()
        safe_colors = {0: "red", 1: "yellow", 2: "green", 3: "bright_green", 4: "bright_green"}
        safe_color = safe_colors.get(len(safe), "white")
        table.add_row("Safe moves", f"[{safe_color}]{len(safe)}[/{safe_color}]")

        return Panel(
            table,
            title="[bold cyan]Stats[/bold cyan]",
            border_style="dim cyan",
            padding=(1, 1),
        )

    def render_minimal(self) -> str:
        """Render minimal ASCII version for AI training."""
        return self.game.render_ascii()

    def render_ai_info(self, ai_data: dict) -> None:
        """Render AI decision information"""
        if not ai_data:
            return

        table = Table(title="[bold magenta]AI Info[/bold magenta]", show_header=False)
        table.add_column(style="magenta")
        table.add_column(style="white")

        for key, value in ai_data.items():
            table.add_row(str(key), str(value))

        self.console.print(table)
