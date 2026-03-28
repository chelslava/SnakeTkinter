"""
CLI Renderer - Rich-based terminal rendering for Snake game.
"""

from enum import Enum

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.table import Table

from .engine import Direction, GameMode, GameState, PowerUpType, SnakeGame


class Theme(Enum):
    DEFAULT = "default"
    NEON = "neon"
    RETRO = "retro"
    MINIMAL = "minimal"
    HACKER = "hacker"


# Theme configurations
THEMES = {
    Theme.DEFAULT: {
        "symbols": {
            "head": "██",
            "body": "▓▓",
            "food": "🍎",
            "star": "⭐",
            "shield": "🛡️",
            "diamond": "💎",
            "freeze": "❄️",
            "mushroom": "🍄",
            "obstacle": "▒▒",
            "empty": "  ",
            "border_h": "══",
            "border_v": "║",
            "border_tl": "╔",
            "border_tr": "╗",
            "border_bl": "╚",
            "border_br": "╝",
        },
        "colors": {
            "head": "bold bright_green",
            "body": "green",
            "food": "bold bright_red",
            "star": "bold bright_yellow",
            "shield": "bold bright_blue",
            "diamond": "bold bright_magenta",
            "freeze": "bold bright_cyan",
            "mushroom": "bold magenta",
            "obstacle": "dim yellow",
            "border": "bright_white",
            "empty": "black",
        },
    },
    Theme.NEON: {
        "symbols": {
            "head": "◈◈",
            "body": "◇◇",
            "food": "●●",
            "star": "★★",
            "shield": "◆◆",
            "diamond": "◇◇",
            "freeze": "❄❄",
            "mushroom": "◎◎",
            "obstacle": "▓▓",
            "empty": "  ",
            "border_h": "━━",
            "border_v": "┃",
            "border_tl": "┏",
            "border_tr": "┓",
            "border_bl": "┗",
            "border_br": "┛",
        },
        "colors": {
            "head": "bold bright_cyan",
            "body": "cyan",
            "food": "bold bright_magenta",
            "star": "bold bright_yellow",
            "shield": "bold bright_blue",
            "diamond": "bold bright_magenta",
            "freeze": "bold bright_cyan",
            "mushroom": "bold magenta",
            "obstacle": "dim yellow",
            "border": "bright_magenta",
            "empty": "black",
        },
    },
    Theme.RETRO: {
        "symbols": {
            "head": "@@",
            "body": "oo",
            "food": "**",
            "star": "++",
            "shield": "##",
            "diamond": "$$",
            "freeze": "~~",
            "mushroom": "&&",
            "obstacle": "%%",
            "empty": "  ",
            "border_h": "--",
            "border_v": "|",
            "border_tl": "+",
            "border_tr": "+",
            "border_bl": "+",
            "border_br": "+",
        },
        "colors": {
            "head": "bold bright_green",
            "body": "green",
            "food": "bold bright_red",
            "star": "bold bright_yellow",
            "shield": "bold bright_blue",
            "diamond": "bold bright_magenta",
            "freeze": "bold bright_cyan",
            "mushroom": "bold magenta",
            "obstacle": "dim yellow",
            "border": "bright_white",
            "empty": "black",
        },
    },
    Theme.MINIMAL: {
        "symbols": {
            "head": "■■",
            "body": "□□",
            "food": "●●",
            "star": "◆◆",
            "shield": "◈◈",
            "diamond": "◇◇",
            "freeze": "○○",
            "mushroom": "◎◎",
            "obstacle": "██",
            "empty": "  ",
            "border_h": "──",
            "border_v": "│",
            "border_tl": "┌",
            "border_tr": "┐",
            "border_bl": "└",
            "border_br": "┘",
        },
        "colors": {
            "head": "bold white",
            "body": "dim white",
            "food": "bold white",
            "star": "bold white",
            "shield": "bold white",
            "diamond": "bold white",
            "freeze": "bold white",
            "mushroom": "bold white",
            "obstacle": "dim white",
            "border": "dim white",
            "empty": "black",
        },
    },
    Theme.HACKER: {
        "symbols": {
            "head": "01",
            "body": "10",
            "food": "00",
            "star": "11",
            "shield": "01",
            "diamond": "10",
            "freeze": "00",
            "mushroom": "11",
            "obstacle": "##",
            "empty": "  ",
            "border_h": "==",
            "border_v": "||",
            "border_tl": "++",
            "border_tr": "++",
            "border_bl": "++",
            "border_br": "++",
        },
        "colors": {
            "head": "bold bright_green",
            "body": "green",
            "food": "bold bright_green",
            "star": "bold bright_green",
            "shield": "bold bright_green",
            "diamond": "bold bright_green",
            "freeze": "bold bright_green",
            "mushroom": "bold bright_green",
            "obstacle": "dim green",
            "border": "bright_green",
            "empty": "black",
        },
    },
}


class CLIRenderer:
    """Rich-based CLI renderer for Snake game with smooth rendering."""

    POWER_UP_SYMBOLS = {
        PowerUpType.APPLE: "food",
        PowerUpType.STAR: "star",
        PowerUpType.SHIELD: "shield",
        PowerUpType.DIAMOND: "diamond",
        PowerUpType.FREEZE: "freeze",
        PowerUpType.MUSHROOM: "mushroom",
    }

    def __init__(
        self,
        game: SnakeGame,
        console: Console | None = None,
        theme: Theme = Theme.DEFAULT,
    ):
        self.game = game
        self.console = console or Console()
        self.theme = theme
        self._load_theme()
        self._live: Live | None = None

    def _load_theme(self) -> None:
        """Load theme configuration"""
        config = THEMES.get(self.theme, THEMES[Theme.DEFAULT])
        self.symbols = config["symbols"]
        self.colors = config["colors"]

    def set_theme(self, theme: Theme) -> None:
        """Change theme"""
        self.theme = theme
        self._load_theme()

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

        # Add game mode to title
        mode_names = {
            GameMode.CLASSIC: "",
            GameMode.TIME_ATTACK: " [cyan]⏱️ Time Attack[/cyan]",
            GameMode.SURVIVAL: " [orange]💪 Survival[/orange]",
            GameMode.PUZZLE: " [magenta]🧩 Puzzle[/magenta]",
        }
        title += mode_names.get(self.game.config.game_mode, "")

        if self.game.state == GameState.PAUSED:
            title += " [bold yellow]⏸ PAUSED[/bold yellow]"
        elif self.game.state == GameState.GAME_OVER:
            title += " [bold red]☠ GAME OVER[/bold red]"
        elif self.game.state == GameState.WIN:
            title += " [bold bright_green]🏆 WIN![/bold bright_green]"

        # Add active effects to title
        effects = []
        if self.game.shield_count > 0:
            effects.append(f"[bright_blue]🛡×{self.game.shield_count}[/bright_blue]")
        if self.game.score_multiplier > 1:
            effects.append(f"[bright_magenta]×{int(self.game.score_multiplier)}[/bright_magenta]")
        if self.game.speed_modifier < 1:
            effects.append("[bright_yellow]⚡[/bright_yellow]")
        if self.game.speed_modifier > 1:
            effects.append("[bright_cyan]❄[/bright_cyan]")

        if effects:
            title += " " + " ".join(effects)

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

        # Top border
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
                elif pos == food and self.game.current_power_up:
                    symbol_key = self.POWER_UP_SYMBOLS.get(self.game.current_power_up.type, "food")
                    row_parts.append(self._colorize(self.symbols[symbol_key], symbol_key))
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
        color = self.colors.get(style, "white")
        return f"[{color}]{text}[/{color}]"

    def _render_stats(self) -> Panel:
        """Render statistics panel"""
        stats = self.game.stats

        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(justify="right", style="cyan", no_wrap=True)
        table.add_column(justify="left", style="bold white", no_wrap=True)

        table.add_row("Score", f"[bold bright_green]{stats.score}[/bold bright_green]")
        table.add_row("Length", str(len(self.game.snake)))

        # Mode-specific stats
        if (
            self.game.config.game_mode == GameMode.TIME_ATTACK
            and stats.mode_time_remaining is not None
        ):
            time_val = stats.mode_time_remaining
            time_color = (
                "bright_red" if time_val < 30 else "bright_yellow" if time_val < 60 else "cyan"
            )
            table.add_row("Time Left", f"[{time_color}]{time_val:.1f}s[/{time_color}]")
        else:
            table.add_row("Time", f"{stats.duration:.1f}s")

        if self.game.config.game_mode == GameMode.PUZZLE:
            target = 20
            current = len(self.game.snake)
            progress = min(100, int(current / target * 100))
            table.add_row(
                "Progress", f"[bright_magenta]{current}/{target} ({progress}%)[/bright_magenta]"
            )

        table.add_row("Moves", str(stats.moves))
        table.add_row("Food", str(stats.food_eaten))

        if stats.moves > 0:
            table.add_row("Efficiency", f"{stats.efficiency:.1%}")

        # Power-ups collected
        if stats.power_ups_collected > 0:
            table.add_row(
                "Power-ups", f"[bright_magenta]{stats.power_ups_collected}[/bright_magenta]"
            )

        # Active effects
        if self.game.active_effects:
            effect_names = []
            for effect in self.game.active_effects:
                if effect.type == PowerUpType.STAR:
                    effect_names.append(f"[bright_yellow]⚡{effect.remaining:.0f}s[/bright_yellow]")
                elif effect.type == PowerUpType.DIAMOND:
                    effect_names.append(
                        f"[bright_magenta]×2 {effect.remaining:.0f}s[/bright_magenta]"
                    )
                elif effect.type == PowerUpType.FREEZE:
                    effect_names.append(f"[bright_cyan]❄{effect.remaining:.0f}s[/bright_cyan]")
            if effect_names:
                table.add_row("Effects", " ".join(effect_names))

        # Direction indicator
        dir_arrows = {
            Direction.UP: "↑",
            Direction.DOWN: "↓",
            Direction.LEFT: "←",
            Direction.RIGHT: "→",
        }
        arrow = dir_arrows.get(self.game.direction, "?")
        table.add_row("Direction", f"[bold]{arrow}[/bold]")

        # Safe moves
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
