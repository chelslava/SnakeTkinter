#!/usr/bin/env python3
"""
PyAISnake CLI - Command-line interface for Snake game with AI.

Commands:
    play       Play the game manually
    ai         Let AI play the game
    train      Train AI models
    stats      View game statistics
"""

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .engine import Direction, GameConfig, GameState, SnakeGame
from .renderer import CLIRenderer

# Try imports for AI
try:
    from .ai import AStarAI, GeneticAI, NeuralAI

    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

try:
    import keyboard  # noqa: F401

    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False


console = Console()


def create_parser() -> argparse.ArgumentParser:
    """Create CLI argument parser"""
    parser = argparse.ArgumentParser(
        prog="pyaisnake",
        description="Modern Snake game with AI capabilities - CLI version",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Play command
    play_parser = subparsers.add_parser("play", help="Play the game manually")
    play_parser.add_argument(
        "--width",
        "-W",
        type=int,
        default=40,
        help="Game field width (default: 40)",
    )
    play_parser.add_argument(
        "--height",
        "-H",
        type=int,
        default=20,
        help="Game field height (default: 20)",
    )
    play_parser.add_argument(
        "--speed",
        "-s",
        type=int,
        default=100,
        help="Game speed in ms (default: 100, lower = faster)",
    )
    play_parser.add_argument(
        "--obstacles",
        "-o",
        type=int,
        default=0,
        help="Number of obstacles (default: 0)",
    )
    play_parser.add_argument(
        "--ascii",
        action="store_true",
        help="Use ASCII characters instead of Unicode",
    )

    # AI command
    ai_parser = subparsers.add_parser("ai", help="Let AI play the game")
    ai_parser.add_argument(
        "--algorithm",
        "-a",
        choices=["a_star", "neural", "genetic", "random"],
        default="a_star",
        help="AI algorithm to use (default: a_star)",
    )
    ai_parser.add_argument(
        "--visualize",
        "-V",
        action="store_true",
        help="Show visualization",
    )
    ai_parser.add_argument(
        "--games",
        "-g",
        type=int,
        default=1,
        help="Number of games to play (default: 1)",
    )
    ai_parser.add_argument(
        "--width",
        "-W",
        type=int,
        default=40,
    )
    ai_parser.add_argument(
        "--height",
        "-H",
        type=int,
        default=20,
    )
    ai_parser.add_argument(
        "--speed",
        "-s",
        type=int,
        default=50,
    )

    # Train command
    train_parser = subparsers.add_parser("train", help="Train AI models")
    train_parser.add_argument(
        "--algorithm",
        "-a",
        choices=["neural", "genetic"],
        required=True,
        help="Algorithm to train",
    )
    train_parser.add_argument(
        "--games",
        "-g",
        type=int,
        default=100,
        help="Number of training games (default: 100)",
    )
    train_parser.add_argument(
        "--save",
        type=str,
        help="Save model to file",
    )
    train_parser.add_argument(
        "--load",
        type=str,
        help="Load existing model to continue training",
    )

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="View game statistics")
    stats_parser.add_argument(
        "--top",
        "-t",
        type=int,
        default=10,
        help="Show top N scores (default: 10)",
    )
    stats_parser.add_argument(
        "--export",
        type=str,
        help="Export stats to JSON file",
    )

    return parser


def cmd_play(args: argparse.Namespace) -> int:
    """Run interactive play mode"""
    config = GameConfig(
        width=args.width,
        height=args.height,
        speed_ms=args.speed,
        initial_obstacles=args.obstacles,
    )

    game = SnakeGame(config)
    renderer = CLIRenderer(game, use_unicode=not args.ascii)

    console.print(
        Panel.fit(
            "[bold green]PyAISnake - Play Mode[/bold green]\n\n"
            "[cyan]Controls:[/cyan]\n"
            "  Arrow keys / WASD - Move\n"
            "  P / Space - Pause\n"
            "  R - Restart\n"
            "  Q / Esc - Quit\n\n"
            "[dim]Press any key to start...[/dim]",
            border_style="green",
        )
    )

    if KEYBOARD_AVAILABLE:
        return _play_keyboard(game, renderer, args.speed)
    else:
        return _play_fallback(game, renderer, args.speed)


def _play_keyboard(game: SnakeGame, renderer: CLIRenderer, speed: int) -> int:
    """Play with keyboard library using Live display"""
    import keyboard

    running = True

    def on_quit():
        nonlocal running
        running = False

    keyboard.add_hotkey("up", lambda: game.set_direction(Direction.UP))
    keyboard.add_hotkey("down", lambda: game.set_direction(Direction.DOWN))
    keyboard.add_hotkey("left", lambda: game.set_direction(Direction.LEFT))
    keyboard.add_hotkey("right", lambda: game.set_direction(Direction.RIGHT))
    keyboard.add_hotkey("w", lambda: game.set_direction(Direction.UP))
    keyboard.add_hotkey("s", lambda: game.set_direction(Direction.DOWN))
    keyboard.add_hotkey("a", lambda: game.set_direction(Direction.LEFT))
    keyboard.add_hotkey("d", lambda: game.set_direction(Direction.RIGHT))
    keyboard.add_hotkey("p", game.pause)
    keyboard.add_hotkey("space", game.pause)
    keyboard.add_hotkey("r", game.reset)
    keyboard.add_hotkey("q", on_quit)
    keyboard.add_hotkey("esc", on_quit)

    keyboard.read_event()  # Wait for first key

    try:
        # Start live display for smooth rendering
        renderer.start_live()

        while running:
            if game.state == GameState.RUNNING:
                game.update()
                renderer.update()
                time.sleep(speed / 1000)
            elif game.state == GameState.PAUSED:
                renderer.update()
                time.sleep(0.1)  # Slower update when paused
            elif game.state == GameState.GAME_OVER:
                renderer.update()
                # Wait for key press
                key = keyboard.read_event(timeout=None)
                if key and key.event_type == keyboard.KEY_DOWN:
                    if key.name == "r":
                        game.reset()
                    elif key.name in ("q", "esc"):
                        break

    finally:
        renderer.stop_live()
        keyboard.unhook_all()

    console.print(f"\n[cyan]Final score:[/cyan] [bold]{game.stats.score}[/bold]")
    return 0


def _play_fallback(game: SnakeGame, renderer: CLIRenderer, speed: int) -> int:
    """Play with fallback input using Live display"""
    console.print("[yellow]Note: keyboard library not available.[/yellow]")
    console.print("[yellow]Using demo mode - AI will play.[/yellow]")
    console.print("[dim]Press Ctrl+C to quit[/dim]\n")

    time.sleep(1)

    try:
        renderer.start_live()

        while True:
            if game.state == GameState.RUNNING:
                # Simple random AI for demo
                safe = game.get_safe_directions()
                if safe:
                    import random

                    game.set_direction(random.choice(safe))
                game.update()
                renderer.update()
                time.sleep(speed / 1000)
            elif game.state == GameState.GAME_OVER:
                renderer.update()
                time.sleep(2)
                game.reset()

    except KeyboardInterrupt:
        pass
    finally:
        renderer.stop_live()

    console.print(f"\n[cyan]Final score:[/cyan] [bold]{game.stats.score}[/bold]")
    return 0


def cmd_ai(args: argparse.Namespace) -> int:
    """Run AI play mode"""
    config = GameConfig(
        width=args.width,
        height=args.height,
        speed_ms=args.speed,
    )

    results = []

    for game_num in range(args.games):
        game = SnakeGame(config)
        renderer = CLIRenderer(game) if args.visualize else None

        ai = _create_ai(args.algorithm, game)

        if renderer and args.visualize:
            renderer.start_live()

        try:
            moves = 0
            while game.state == GameState.RUNNING:
                direction = ai.get_direction()
                if direction:
                    game.set_direction(direction)

                if game.update():
                    moves += 1

                if renderer:
                    renderer.update()
                    time.sleep(args.speed / 1000)

        finally:
            if renderer:
                renderer.stop_live()

        results.append(
            {
                "game": game_num + 1,
                "score": game.stats.score,
                "moves": moves,
                "duration": game.stats.duration,
            }
        )

        if not args.visualize:
            console.print(f"Game {game_num + 1}: Score={game.stats.score}, Moves={moves}")

    if args.games > 1:
        _show_ai_summary(results)

    return 0


def _create_ai(algorithm: str, game: SnakeGame):
    """Create AI instance"""
    if algorithm == "random":
        return RandomAI(game)
    elif algorithm == "a_star":
        return AStarAI(game)
    elif algorithm == "neural":
        return NeuralAI(game)
    elif algorithm == "genetic":
        return GeneticAI(game)
    else:
        return RandomAI(game)


def _show_ai_summary(results: list) -> None:
    """Show AI performance summary"""
    table = Table(title="[bold cyan]AI Performance Summary[/bold cyan]")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold white")

    scores = [r["score"] for r in results]
    table.add_row("Games Played", str(len(results)))
    table.add_row("Average Score", f"{sum(scores) / len(scores):.1f}")
    table.add_row("Best Score", str(max(scores)))
    table.add_row("Worst Score", str(min(scores)))

    console.print(table)


def cmd_train(args: argparse.Namespace) -> int:
    """Train AI models"""
    console.print(f"[bold cyan]Training {args.algorithm} AI...[/bold cyan]")
    console.print(f"Games: {args.games}")

    # Training implementation depends on AI module
    console.print("[yellow]Training mode is under development.[/yellow]")
    console.print("[dim]Use 'play' and 'ai' modes for now.[/dim]")

    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    """Show game statistics"""
    db_path = Path("snake_stats.db")

    if not db_path.exists():
        console.print("[yellow]No statistics database found.[/yellow]")
        console.print("[dim]Play some games to generate statistics.[/dim]")
        return 0

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Get top scores
        cursor.execute(
            """
            SELECT score, length, duration, timestamp
            FROM games
            ORDER BY score DESC
            LIMIT ?
        """,
            (args.top,),
        )

        rows = cursor.fetchall()

        if not rows:
            console.print("[yellow]No games recorded yet.[/yellow]")
            return 0

        table = Table(title=f"[bold cyan]Top {args.top} Scores[/bold cyan]")
        table.add_column("#", style="dim", width=3)
        table.add_column("Score", style="bold green")
        table.add_column("Length", style="cyan")
        table.add_column("Duration", style="yellow")
        table.add_column("Date", style="dim")

        for i, (score, length, duration, timestamp) in enumerate(rows, 1):
            table.add_row(
                str(i),
                str(score),
                str(length),
                f"{duration:.1f}s",
                timestamp[:10] if timestamp else "N/A",
            )

        console.print(table)

        # Export if requested
        if args.export:
            data = {
                "top_scores": [
                    {
                        "rank": i,
                        "score": score,
                        "length": length,
                        "duration": duration,
                        "date": timestamp,
                    }
                    for i, (score, length, duration, timestamp) in enumerate(rows, 1)
                ]
            }

            with open(args.export, "w") as f:
                json.dump(data, f, indent=2)

            console.print(f"\n[green]Exported to {args.export}[/green]")

        conn.close()

    except Exception as e:
        console.print(f"[red]Error reading database: {e}[/red]")
        return 1

    return 0


# Simple AI implementations for demo
class RandomAI:
    """Simple random AI"""

    def __init__(self, game: SnakeGame):
        self.game = game

    def get_direction(self) -> Direction | None:
        import random

        safe = self.game.get_safe_directions()
        return random.choice(safe) if safe else None


class AStarAI:
    """A* pathfinding AI"""

    def __init__(self, game: SnakeGame):
        self.game = game

    def get_direction(self) -> Direction | None:
        if not self.game.food:
            return None

        head = self.game.snake[0]
        food = self.game.food

        # Simple greedy: move towards food
        dx = food[0] - head[0]
        dy = food[1] - head[1]

        # Try preferred direction first, then alternatives
        if abs(dx) > abs(dy):
            preferred = Direction.RIGHT if dx > 0 else Direction.LEFT
        else:
            preferred = Direction.DOWN if dy > 0 else Direction.UP

        safe = self.game.get_safe_directions()

        if preferred in safe:
            return preferred
        elif safe:
            return safe[0]

        return None


class NeuralAI:
    """Neural network AI placeholder"""

    def __init__(self, game: SnakeGame):
        self.game = game

    def get_direction(self) -> Direction | None:
        # Fallback to A*
        return AStarAI(self.game).get_direction()


class GeneticAI:
    """Genetic algorithm AI placeholder"""

    def __init__(self, game: SnakeGame):
        self.game = game

    def get_direction(self) -> Direction | None:
        # Fallback to A*
        return AStarAI(self.game).get_direction()


def main() -> int:
    """Main entry point"""
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "play":
        return cmd_play(args)
    elif args.command == "ai":
        return cmd_ai(args)
    elif args.command == "train":
        return cmd_train(args)
    elif args.command == "stats":
        return cmd_stats(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
