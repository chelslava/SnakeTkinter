"""
CLI Renderer - Rich-based terminal rendering for Snake game.
"""


from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .engine import Direction, GameState, SnakeGame


class CLIRenderer:
    """
    Rich-based CLI renderer for Snake game.

    Usage:
        renderer = CLIRenderer(game)
        renderer.render()
    """

    # Unicode symbols
    SYMBOLS = {
        "head": "🐍",
        "body": "▓",
        "food": "🍎",
        "obstacle": "🧱",
        "empty": " ",
        "border_h": "─",
        "border_v": "│",
        "border_tl": "┌",
        "border_tr": "┐",
        "border_bl": "└",
        "border_br": "┘",
    }

    # ASCII fallback
    ASCII_SYMBOLS = {
        "head": "@",
        "body": "o",
        "food": "*",
        "obstacle": "#",
        "empty": " ",
        "border_h": "-",
        "border_v": "|",
        "border_tl": "+",
        "border_tr": "+",
        "border_bl": "+",
        "border_br": "+",
    }

    # Colors
    COLORS = {
        "head": "bold green",
        "body": "green",
        "food": "bold red",
        "obstacle": "dim yellow",
        "border": "dim white",
        "stats": "cyan",
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

        self._last_frame = ""

    def render(self) -> None:
        """Render current game state to terminal"""
        self.console.clear()

        # Create main layout
        layout = Table(show_header=False, show_edge=False)
        layout.add_column(ratio=3)
        layout.add_column(ratio=1)

        # Game field
        game_panel = self._render_game_field()

        # Stats panel
        stats_panel = self._render_stats()

        layout.add_row(game_panel, stats_panel)

        self.console.print(layout)

        # State messages
        if self.game.state == GameState.GAME_OVER:
            self._render_game_over()
        elif self.game.state == GameState.PAUSED:
            self._render_paused()

    def _render_game_field(self) -> Panel:
        """Render game field as panel"""
        lines = []

        config = self.game.config

        # Top border
        border = self.symbols["border_h"] * config.width
        top = f"{self.symbols['border_tl']}{border}{self.symbols['border_tr']}"
        lines.append(self._colorize(top, "border"))

        # Game field
        for y in range(config.height):
            row_chars = [self._colorize(self.symbols["border_v"], "border")]

            for x in range(config.width):
                pos = (x, y)
                char = self._get_cell_char(pos)
                row_chars.append(char)

            row_chars.append(self._colorize(self.symbols["border_v"], "border"))
            lines.append("".join(row_chars))

        # Bottom border
        bottom = f"{self.symbols['border_bl']}{border}{self.symbols['border_br']}"
        lines.append(self._colorize(bottom, "border"))

        content = "\n".join(lines)

        return Panel(
            content,
            title="[bold green]PyAISnake[/bold green]",
            title_align="left",
            border_style="dim green",
        )

    def _get_cell_char(self, pos: tuple[int, int]) -> str:
        """Get character for a cell position"""
        if pos == self.game.snake[0]:
            return self._colorize(self.symbols["head"], "head")
        elif pos in self.game.snake:
            return self._colorize(self.symbols["body"], "body")
        elif pos == self.game.food:
            return self._colorize(self.symbols["food"], "food")
        elif pos in self.game.obstacles:
            return self._colorize(self.symbols["obstacle"], "obstacle")
        else:
            return self.symbols["empty"]

    def _colorize(self, text: str, style: str) -> str:
        """Apply color style to text"""
        color = self.COLORS.get(style, "white")
        return f"[{color}]{text}[/{color}]"

    def _render_stats(self) -> Panel:
        """Render statistics panel"""
        stats = self.game.stats

        table = Table(show_header=False, box=None, padding=1)
        table.add_column(justify="right", style="cyan")
        table.add_column(justify="left", style="bold white")

        table.add_row("Score:", str(stats.score))
        table.add_row("Length:", str(len(self.game.snake)))
        table.add_row("Moves:", str(stats.moves))
        table.add_row("Food:", str(stats.food_eaten))
        table.add_row("Time:", f"{stats.duration:.1f}s")

        if stats.moves > 0:
            table.add_row("Efficiency:", f"{stats.efficiency:.2%}")

        # Direction indicator
        dir_arrows = {
            Direction.UP: "⬆",
            Direction.DOWN: "⬇",
            Direction.LEFT: "⬅",
            Direction.RIGHT: "➡",
        }
        arrow = dir_arrows.get(self.game.direction, "?")
        table.add_row("Direction:", arrow)

        # Safe moves
        safe = self.game.get_safe_directions()
        table.add_row("Safe moves:", str(len(safe)))

        return Panel(
            table,
            title="[bold cyan]Statistics[/bold cyan]",
            border_style="dim cyan",
        )

    def _render_game_over(self) -> None:
        """Render game over overlay"""
        stats = self.game.stats

        content = Table(show_header=False, box=None)
        content.add_column(justify="center")

        content.add_row("")
        content.add_row("[bold red]GAME OVER[/bold red]")
        content.add_row("")
        content.add_row(f"[cyan]Score:[/cyan] [bold]{stats.score}[/bold]")
        content.add_row(f"[cyan]Time:[/cyan] {stats.duration:.1f}s")
        content.add_row("")
        content.add_row("[dim]Press R to restart or Q to quit[/dim]")

        panel = Panel(
            Align.center(content),
            border_style="red",
        )

        self.console.print(panel)

    def _render_paused(self) -> None:
        """Render paused overlay"""
        content = Text()
        content.append("\n")
        content.append("PAUSED\n", style="bold yellow")
        content.append("\n")
        content.append("Press P to continue\n", style="dim")
        content.append("Press Q to quit\n", style="dim")

        panel = Panel(
            Align.center(content),
            border_style="yellow",
        )

        self.console.print(panel)

    def render_minimal(self) -> str:
        """
        Render minimal ASCII version for AI training or headless mode.
        Returns string instead of printing.
        """
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
