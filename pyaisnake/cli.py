#!/usr/bin/env python3
"""
PyAISnake CLI - Command-line interface for Snake game with AI.

Commands:
    play       Play the game manually
    ai         Let AI play the game
    train      Train AI models
    stats      View game statistics
    tournament Run AI tournament
    achievements View achievements
"""

import argparse
import json
import random
import sqlite3
import sys
import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from . import __version__
from .achievements import Achievement, AchievementSystem
from .engine import Difficulty, Direction, GameConfig, GameMode, GameState, SnakeGame
from .renderer import CLIRenderer, Theme

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
        help="Number of obstacles (default: based on difficulty)",
    )
    play_parser.add_argument(
        "--difficulty",
        "-d",
        choices=["easy", "normal", "hard", "extreme"],
        default="normal",
        help="Difficulty level (default: normal)",
    )
    play_parser.add_argument(
        "--theme",
        "-t",
        choices=["default", "neon", "retro", "minimal", "hacker"],
        default="default",
        help="Color theme (default: default)",
    )
    play_parser.add_argument(
        "--no-power-ups",
        action="store_true",
        help="Disable power-ups",
    )
    play_parser.add_argument(
        "--mode",
        "-m",
        choices=["classic", "time_attack", "survival", "puzzle"],
        default="classic",
        help="Game mode (default: classic)",
    )

    # AI command
    ai_parser = subparsers.add_parser("ai", help="Let AI play the game")
    ai_parser.add_argument(
        "--algorithm",
        "-a",
        choices=["a_star", "neural", "genetic", "random", "dqn"],
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
        help="Number of games (default: 1)",
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
    ai_parser.add_argument(
        "--difficulty",
        "-d",
        choices=["easy", "normal", "hard", "extreme"],
        default="normal",
    )
    ai_parser.add_argument(
        "--theme",
        "-t",
        choices=["default", "neon", "retro", "minimal", "hacker"],
        default="default",
    )

    # Train command
    train_parser = subparsers.add_parser("train", help="Train AI models")
    train_parser.add_argument(
        "--algorithm",
        "-a",
        choices=["neural", "genetic", "dqn"],
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

    # Tournament command
    tournament_parser = subparsers.add_parser("tournament", help="Run AI tournament")
    tournament_parser.add_argument(
        "--algorithms",
        type=str,
        default="a_star,neural,genetic,random",
        help="Comma-separated list of algorithms (default: all)",
    )
    tournament_parser.add_argument(
        "--games",
        "-g",
        type=int,
        default=10,
        help="Games per algorithm (default: 10)",
    )
    tournament_parser.add_argument(
        "--width",
        "-W",
        type=int,
        default=40,
    )
    tournament_parser.add_argument(
        "--height",
        "-H",
        type=int,
        default=20,
    )

    # Achievements command
    achievements_parser = subparsers.add_parser("achievements", help="View achievements")
    achievements_parser.add_argument(
        "--export",
        type=str,
        help="Export achievements to JSON",
    )

    # Multiplayer command
    mp_parser = subparsers.add_parser("multiplayer", help="Play local multiplayer")
    mp_parser.add_argument(
        "--width",
        "-W",
        type=int,
        default=40,
        help="Game field width (default: 40)",
    )
    mp_parser.add_argument(
        "--height",
        "-H",
        type=int,
        default=20,
        help="Game field height (default: 20)",
    )
    mp_parser.add_argument(
        "--speed",
        "-s",
        type=int,
        default=100,
        help="Game speed in ms (default: 100)",
    )
    mp_parser.add_argument(
        "--score",
        type=int,
        default=None,
        help="Score to win (default: no limit)",
    )
    mp_parser.add_argument(
        "--time",
        type=float,
        default=None,
        help="Time limit in seconds (default: no limit)",
    )

    return parser


def _get_difficulty(value: str) -> Difficulty:
    """Convert string to Difficulty enum"""
    return {
        "easy": Difficulty.EASY,
        "normal": Difficulty.NORMAL,
        "hard": Difficulty.HARD,
        "extreme": Difficulty.EXTREME,
    }.get(value, Difficulty.NORMAL)


def _get_theme(value: str) -> Theme:
    """Convert string to Theme enum"""
    return {
        "default": Theme.DEFAULT,
        "neon": Theme.NEON,
        "retro": Theme.RETRO,
        "minimal": Theme.MINIMAL,
        "hacker": Theme.HACKER,
    }.get(value, Theme.DEFAULT)


def _get_game_mode(value: str) -> GameMode:
    """Convert string to GameMode enum"""
    return {
        "classic": GameMode.CLASSIC,
        "time_attack": GameMode.TIME_ATTACK,
        "survival": GameMode.SURVIVAL,
        "puzzle": GameMode.PUZZLE,
    }.get(value, GameMode.CLASSIC)


def cmd_play(args: argparse.Namespace) -> int:
    """Run interactive play mode"""
    difficulty = _get_difficulty(args.difficulty)
    theme = _get_theme(args.theme)
    game_mode = _get_game_mode(args.mode)

    config = GameConfig(
        width=args.width,
        height=args.height,
        speed_ms=args.speed,
        initial_obstacles=args.obstacles,
        difficulty=difficulty,
        power_ups_enabled=not args.no_power_ups,
        game_mode=game_mode,
    )

    game = SnakeGame(config)
    renderer = CLIRenderer(game, theme=theme)

    difficulty_names = {
        Difficulty.EASY: "🟢 Easy",
        Difficulty.NORMAL: "🟡 Normal",
        Difficulty.HARD: "🟠 Hard",
        Difficulty.EXTREME: "🔴 Extreme",
    }

    mode_names = {
        GameMode.CLASSIC: "🎮 Classic",
        GameMode.TIME_ATTACK: "⏱️ Time Attack (2 min)",
        GameMode.SURVIVAL: "💪 Survival",
        GameMode.PUZZLE: "🧩 Puzzle (length 20)",
    }

    mode_info = ""
    if game_mode == GameMode.TIME_ATTACK:
        mode_info = "\n[cyan]Goal:[/cyan] Maximize score in 2 minutes!"
    elif game_mode == GameMode.SURVIVAL:
        mode_info = "\n[cyan]Goal:[/cyan] Survive as long as possible (speed increases!)"
    elif game_mode == GameMode.PUZZLE:
        mode_info = "\n[cyan]Goal:[/cyan] Reach length 20 to win!"

    console.print(
        Panel.fit(
            f"[bold green]PyAISnake v{__version__} - Play Mode[/bold green]\n\n"
            f"[cyan]Mode:[/cyan] {mode_names.get(game_mode, 'Classic')}\n"
            f"[cyan]Difficulty:[/cyan] {difficulty_names.get(difficulty, 'Normal')}\n"
            f"[cyan]Theme:[/cyan] {theme.value}\n"
            f"[cyan]Power-ups:[/cyan] {'Enabled' if config.power_ups_enabled else 'Disabled'}"
            f"{mode_info}\n\n"
            "[cyan]Controls:[/cyan]\n"
            "  Arrow keys / WASD - Move\n"
            "  P / Space - Pause\n"
            "  R - Restart\n"
            "  Q / Esc - Quit\n\n"
            "[cyan]Power-ups:[/cyan]\n"
            "  🍎 Apple   - Normal food (+1)\n"
            "  ⭐ Star    - Speed boost (5s)\n"
            "  🛡️ Shield  - Pass through walls\n"
            "  💎 Diamond - Double points (10s)\n"
            "  ❄️ Freeze  - Slow game (5s)\n"
            "  🍄 Mushroom- Shrink (-3)\n\n"
            "[dim]Press any key to start...[/dim]",
            border_style="green",
        )
    )

    if KEYBOARD_AVAILABLE:
        return _play_keyboard(game, renderer, config)
    else:
        return _play_fallback(game, renderer, config)


def _play_keyboard(game: SnakeGame, renderer: CLIRenderer, config: GameConfig) -> int:
    """Play with keyboard library using Live display"""
    import keyboard

    running = True
    achievement_system = AchievementSystem()
    achievement_system.start_session()
    unlocked_queue: list[Achievement] = []

    def on_achievement_unlock(achievement: Achievement) -> None:
        unlocked_queue.append(achievement)

    achievement_system.on_unlock = on_achievement_unlock

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

    keyboard.read_event()

    try:
        renderer.start_live()

        while running:
            if game.state == GameState.RUNNING:
                game.update()

                safe = game.get_safe_directions()
                if len(safe) == 1:
                    achievement_system.record_close_call()

                mode_name = config.game_mode.value if config.game_mode else "classic"
                newly_unlocked = achievement_system.check_achievements(
                    score=game.stats.score,
                    length=len(game.snake),
                    duration=game.stats.duration,
                    game_mode=mode_name,
                    power_ups=game.stats.power_ups_collected,
                )

                for a in newly_unlocked:
                    console.print(
                        f"\n[bold yellow]🏆 Achievement Unlocked: {a.icon} {a.name}[/bold yellow]"
                    )

                renderer.update()
                time.sleep(game.effective_speed / 1000)
            elif game.state == GameState.PAUSED:
                renderer.update()
                time.sleep(0.1)
            elif game.state == GameState.GAME_OVER:
                renderer.update()
                key = keyboard.read_event()
                if key and key.event_type == keyboard.KEY_DOWN:
                    if key.name == "r":
                        game.reset()
                        achievement_system.start_session()
                    elif key.name in ("q", "esc"):
                        break

    finally:
        renderer.stop_live()
        keyboard.unhook_all()

    console.print(f"\n[cyan]Final score:[/cyan] [bold]{game.stats.score}[/bold]")
    console.print(f"[cyan]Power-ups collected:[/cyan] {game.stats.power_ups_collected}")
    return 0


def _play_fallback(game: SnakeGame, renderer: CLIRenderer, config: GameConfig) -> int:
    """Play with fallback input using Live display"""
    console.print("[yellow]Note: keyboard library not available.[/yellow]")
    console.print("[yellow]Using demo mode - AI will play.[/yellow]")
    console.print("[dim]Press Ctrl+C to quit[/dim]\n")

    achievement_system = AchievementSystem()
    achievement_system.start_session()

    time.sleep(1)

    try:
        renderer.start_live()

        while True:
            if game.state == GameState.RUNNING:
                safe_dirs = game.get_safe_directions()
                if safe_dirs:
                    game.set_direction(random.choice(safe_dirs))
                game.update()

                safe = game.get_safe_directions()
                if len(safe) == 1:
                    achievement_system.record_close_call()

                mode_name = config.game_mode.value if config.game_mode else "classic"
                newly_unlocked = achievement_system.check_achievements(
                    score=game.stats.score,
                    length=len(game.snake),
                    duration=game.stats.duration,
                    game_mode=mode_name,
                    power_ups=game.stats.power_ups_collected,
                )

                for a in newly_unlocked:
                    console.print(
                        f"\n[bold yellow]🏆 Achievement Unlocked: {a.icon} {a.name}[/bold yellow]"
                    )

                renderer.update()
                time.sleep(game.effective_speed / 1000)
            elif game.state == GameState.GAME_OVER:
                renderer.update()
                time.sleep(2)
                game.reset()
                achievement_system.start_session()

    except KeyboardInterrupt:
        pass
    finally:
        renderer.stop_live()

    console.print(f"\n[cyan]Final score:[/cyan] [bold]{game.stats.score}[/bold]")
    return 0


def cmd_ai(args: argparse.Namespace) -> int:
    """Run AI play mode"""
    difficulty = _get_difficulty(args.difficulty)
    theme = _get_theme(args.theme)

    config = GameConfig(
        width=args.width,
        height=args.height,
        speed_ms=args.speed,
        difficulty=difficulty,
    )

    results = []

    for game_num in range(args.games):
        game = SnakeGame(config)
        renderer = CLIRenderer(game, theme=theme) if args.visualize else None

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
                    time.sleep(game.effective_speed / 1000)

        finally:
            if renderer:
                renderer.stop_live()

        results.append(
            {
                "game": game_num + 1,
                "score": game.stats.score,
                "moves": moves,
                "duration": game.stats.duration,
                "power_ups": game.stats.power_ups_collected,
            }
        )

        if not args.visualize:
            console.print(
                f"Game {game_num + 1}: Score={game.stats.score}, "
                f"Moves={moves}, Power-ups={game.stats.power_ups_collected}"
            )

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
    elif algorithm == "dqn":
        from .ai.dqn import DQNAI

        ai = DQNAI(game)
        model_path = Path("dqn_model.pkl")
        if model_path.exists():
            ai.load_model(str(model_path))
        return ai
    else:
        return RandomAI(game)


def _show_ai_summary(results: list) -> None:
    """Show AI performance summary"""
    table = Table(title="[bold cyan]AI Performance Summary[/bold cyan]")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold white")

    scores = [r["score"] for r in results]
    power_ups = [r["power_ups"] for r in results]

    table.add_row("Games Played", str(len(results)))
    table.add_row("Average Score", f"{sum(scores) / len(scores):.1f}")
    table.add_row("Best Score", str(max(scores)))
    table.add_row("Worst Score", str(min(scores)))
    table.add_row("Total Power-ups", str(sum(power_ups)))

    console.print(table)


def cmd_train(args: argparse.Namespace) -> int:
    """Train AI models"""
    if args.algorithm not in ("neural", "dqn"):
        console.print(f"[red]Training not supported for {args.algorithm}[/red]")
        return 1

    from .ai.dqn import DQNAI

    console.print("[bold cyan]Training DQN AI...[/bold cyan]")
    console.print(f"Games: {args.games}")

    config = GameConfig(width=20, height=20, speed_ms=0)

    dqn_path = Path("dqn_model.pkl")
    scores_history: list[int] = []
    best_score = 0

    game = SnakeGame(config)
    ai = DQNAI(game, epsilon_start=1.0, epsilon_end=0.01, epsilon_decay=0.995)
    ai.start_training()

    if dqn_path.exists():
        ai.load_model(str(dqn_path))

    for episode in range(args.games):
        game = SnakeGame(config)
        ai.game = game

        steps = 0
        while game.state == GameState.RUNNING and steps < 1000:
            direction = ai.get_direction()
            if direction:
                game.set_direction(direction)
            game.update()
            steps += 1

        scores_history.append(game.stats.score)

        if game.stats.score > best_score:
            best_score = game.stats.score

        if (episode + 1) % 10 == 0:
            avg_score = sum(scores_history[-10:]) / 10
            console.print(
                f"Episode {episode + 1}/{args.games} | "
                f"Score: {game.stats.score} | "
                f"Avg(10): {avg_score:.1f} | "
                f"Best: {best_score} | "
                f"Epsilon: {ai.epsilon:.3f}"
            )

        if args.save:
            ai.save_model(args.save)
        else:
            ai.save_model(str(dqn_path))

    ai.stop_training()

    console.print("\n[bold green]Training complete![/bold green]")
    console.print(f"Best score: {best_score}")
    console.print(f"Final epsilon: {ai.epsilon:.3f}")

    if args.save:
        console.print(f"Model saved to: {args.save}")
    else:
        console.print("Model saved to: dqn_model.pkl")

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


def cmd_tournament(args: argparse.Namespace) -> int:
    """Run AI tournament between algorithms"""
    algorithms = [a.strip() for a in args.algorithms.split(",")]

    console.print("[bold cyan]🎮 AI Tournament[/bold cyan]")
    console.print(f"Algorithms: {', '.join(algorithms)}")
    console.print(f"Games per algorithm: {args.games}\n")

    config = GameConfig(
        width=args.width,
        height=args.height,
        difficulty=Difficulty.NORMAL,
    )

    results = {}

    for algorithm in algorithms:
        console.print(f"[yellow]Running {algorithm}...[/yellow]")
        scores = []

        for _ in range(args.games):
            game = SnakeGame(config)
            ai = _create_ai(algorithm, game)

            while game.state == GameState.RUNNING:
                direction = ai.get_direction()
                if direction:
                    game.set_direction(direction)
                game.update()

            scores.append(game.stats.score)

        results[algorithm] = {
            "scores": scores,
            "avg": sum(scores) / len(scores),
            "max": max(scores),
            "min": min(scores),
        }

    # Display results
    table = Table(title="[bold cyan]🏆 Tournament Results[/bold cyan]")
    table.add_column("Algorithm", style="cyan")
    table.add_column("Avg Score", style="bold white")
    table.add_column("Best", style="green")
    table.add_column("Worst", style="red")
    table.add_column("Rank", style="bold yellow")

    # Sort by average score
    sorted_results = sorted(results.items(), key=lambda x: x[1]["avg"], reverse=True)

    for rank, (algo, data) in enumerate(sorted_results, 1):
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else "  "
        table.add_row(
            algo,
            f"{data['avg']:.1f}",
            str(data["max"]),
            str(data["min"]),
            f"{medal} #{rank}",
        )

    console.print(table)

    winner = sorted_results[0][0]
    console.print(f"\n[bold green]🏆 Winner: {winner}[/bold green]")

    return 0


# Simple AI implementations
class RandomAI:
    """Simple random AI"""

    def __init__(self, game: SnakeGame):
        self.game = game

    def get_direction(self) -> Direction | None:
        safe = self.game.get_safe_directions()
        return random.choice(safe) if safe else None


class AStarAI:
    """A* pathfinding AI with trap avoidance"""

    def __init__(self, game: SnakeGame):
        self.game = game
        self._path: list[tuple[int, int]] = []
        self._last_food: tuple[int, int] | None = None

    def get_direction(self) -> Direction | None:
        if not self.game.food:
            return self._get_safe_direction()

        head = self.game.snake[0]
        food = self.game.food

        if food != self._last_food or not self._path:
            self._path = self._find_path(head, food)
            self._last_food = food

        if self._path:
            next_pos = self._path[0]
            self._path = self._path[1:]
            return self._pos_to_direction(head, next_pos)

        return self._get_safe_direction()

    def _find_path(self, start: tuple[int, int], goal: tuple[int, int]) -> list[tuple[int, int]]:
        import heapq

        snake_set = set(self.game.snake)
        obstacles = self.game.obstacles
        width = self.game.config.width
        height = self.game.config.height

        open_set: list[tuple[int, tuple[int, int]]] = [(0, start)]
        came_from: dict[tuple[int, int], tuple[int, int]] = {}
        g_score: dict[tuple[int, int], int] = {start: 0}

        while open_set:
            _, current = heapq.heappop(open_set)

            if current == goal:
                return self._reconstruct_path(came_from, current)

            for dx, dy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                neighbor = (current[0] + dx, current[1] + dy)

                if not (0 <= neighbor[0] < width and 0 <= neighbor[1] < height):
                    continue

                if neighbor in snake_set and neighbor != self.game.snake[-1]:
                    continue

                if neighbor in obstacles:
                    continue

                tentative_g = g_score[current] + 1

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score = tentative_g + abs(neighbor[0] - goal[0]) + abs(neighbor[1] - goal[1])
                    heapq.heappush(open_set, (f_score, neighbor))

        return []

    def _reconstruct_path(
        self, came_from: dict[tuple[int, int], tuple[int, int]], current: tuple[int, int]
    ) -> list[tuple[int, int]]:
        path = []
        while current in came_from:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path

    def _pos_to_direction(self, head: tuple[int, int], next_pos: tuple[int, int]) -> Direction:
        dx = next_pos[0] - head[0]
        dy = next_pos[1] - head[1]

        if dy < 0:
            return Direction.UP
        elif dy > 0:
            return Direction.DOWN
        elif dx < 0:
            return Direction.LEFT
        else:
            return Direction.RIGHT

    def _get_safe_direction(self) -> Direction | None:
        safe = self.game.get_safe_directions()
        if not safe:
            return None

        best_dir = None
        best_space = -1

        for direction in safe:
            space = self._count_accessible_space(direction)
            if space > best_space:
                best_space = space
                best_dir = direction

        return best_dir

    def _count_accessible_space(self, direction: Direction) -> int:
        head = self.game.snake[0]
        dx, dy = {
            Direction.UP: (0, -1),
            Direction.DOWN: (0, 1),
            Direction.LEFT: (-1, 0),
            Direction.RIGHT: (1, 0),
        }[direction]

        new_head = (head[0] + dx, head[1] + dy)

        visited = {new_head}
        queue = [new_head]
        snake_set = set(self.game.snake)
        obstacles = self.game.obstacles

        while queue:
            pos = queue.pop(0)
            for ddx, ddy in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
                npos = (pos[0] + ddx, pos[1] + ddy)
                if (
                    0 <= npos[0] < self.game.config.width
                    and 0 <= npos[1] < self.game.config.height
                    and npos not in visited
                    and npos not in snake_set
                    and npos not in obstacles
                ):
                    visited.add(npos)
                    queue.append(npos)

        return len(visited)


class NeuralAI:
    """Neural network AI placeholder"""

    def __init__(self, game: SnakeGame):
        self.game = game

    def get_direction(self) -> Direction | None:
        return AStarAI(self.game).get_direction()


class GeneticAI:
    """Genetic algorithm AI placeholder"""

    def __init__(self, game: SnakeGame):
        self.game = game

    def get_direction(self) -> Direction | None:
        return AStarAI(self.game).get_direction()


def cmd_achievements(args: argparse.Namespace) -> int:
    """Show achievements"""
    system = AchievementSystem()

    progress = system.get_progress()
    unlocked = system.get_unlocked()
    locked = system.get_locked()

    # Progress header
    console.print(
        Panel.fit(
            f"[bold bright_green]🏆 Achievements[/bold bright_green]\n\n"
            f"[cyan]Progress:[/cyan] {progress['unlocked']}/{progress['total']} ({progress['percentage']}%)",
            border_style="bright_green",
        )
    )

    # Unlocked achievements
    if unlocked:
        console.print("\n[bold green]✅ Unlocked[/bold green]")
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="dim")
        table.add_column(style="bold white")
        table.add_column(style="cyan")

        for a in sorted(unlocked, key=lambda x: x.type.value):
            table.add_row(a.icon, a.name, a.description)

        console.print(table)

    # Locked achievements (non-secret)
    if locked:
        console.print("\n[bold yellow]🔒 Locked[/bold yellow]")
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column(style="dim")
        table.add_column(style="white")
        table.add_column(style="dim")

        for a in sorted(locked, key=lambda x: (x.type.value, x.threshold)):
            table.add_row("❓", a.name, a.description)

        console.print(table)

    # Export if requested
    if args.export:
        system.export_to_json(args.export)
        console.print(f"\n[green]Exported to {args.export}[/green]")

    return 0


def cmd_multiplayer(args: argparse.Namespace) -> int:
    """Run local multiplayer game"""
    from .multiplayer import MultiplayerConfig, MultiplayerGame, MultiplayerState
    from .renderer import MultiplayerRenderer

    config = MultiplayerConfig(
        width=args.width,
        height=args.height,
        speed_ms=args.speed,
        score_to_win=args.score,
        time_limit=args.time,
    )

    game = MultiplayerGame(config)
    renderer = MultiplayerRenderer(game)

    console.print(
        Panel.fit(
            f"[bold green]PyAISnake v{__version__} - Multiplayer Mode[/bold green]\n\n"
            f"[cyan]Field:[/cyan] {args.width}x{args.height}\n"
            f"[cyan]Speed:[/cyan] {args.speed}ms\n"
            f"[cyan]Score to win:[/cyan] {args.score or 'No limit'}\n"
            f"[cyan]Time limit:[/cyan] {args.time or 'No limit'}s\n\n"
            "[bright_cyan]Player 1 (Cyan):[/bright_cyan] WASD\n"
            "[bright_magenta]Player 2 (Magenta):[/bright_magenta] Arrow Keys\n\n"
            "[cyan]Controls:[/cyan]\n"
            "  P / Space - Pause\n"
            "  R - Restart\n"
            "  Q / Esc - Quit\n\n"
            "[dim]Press any key to start...[/dim]",
            border_style="green",
        )
    )

    if not KEYBOARD_AVAILABLE:
        console.print("[red]Error: keyboard library required for multiplayer[/red]")
        console.print("[dim]Install with: pip install keyboard[/dim]")
        return 1

    import keyboard

    running = True

    def on_quit():
        nonlocal running
        running = False

    keyboard.add_hotkey("w", lambda: game.set_direction1(Direction.UP))
    keyboard.add_hotkey("s", lambda: game.set_direction1(Direction.DOWN))
    keyboard.add_hotkey("a", lambda: game.set_direction1(Direction.LEFT))
    keyboard.add_hotkey("d", lambda: game.set_direction1(Direction.RIGHT))
    keyboard.add_hotkey("up", lambda: game.set_direction2(Direction.UP))
    keyboard.add_hotkey("down", lambda: game.set_direction2(Direction.DOWN))
    keyboard.add_hotkey("left", lambda: game.set_direction2(Direction.LEFT))
    keyboard.add_hotkey("right", lambda: game.set_direction2(Direction.RIGHT))
    keyboard.add_hotkey("p", game.pause)
    keyboard.add_hotkey("space", game.pause)
    keyboard.add_hotkey("r", game.reset)
    keyboard.add_hotkey("q", on_quit)
    keyboard.add_hotkey("esc", on_quit)

    keyboard.read_event()

    try:
        renderer.start_live()

        while running:
            if game.state == MultiplayerState.RUNNING:
                game.update()
                renderer.update()
                time.sleep(config.speed_ms / 1000)
            elif game.state == MultiplayerState.PAUSED:
                renderer.update()
                time.sleep(0.1)
            else:
                renderer.update()
                key = keyboard.read_event()
                if key and key.event_type == keyboard.KEY_DOWN:
                    if key.name == "r":
                        game.reset()
                    elif key.name in ("q", "esc"):
                        break

    finally:
        renderer.stop_live()
        keyboard.unhook_all()

    console.print(f"\n[bright_cyan]Player 1 Score:[/bright_cyan] [bold]{game.stats1.score}[/bold]")
    console.print(
        f"[bright_magenta]Player 2 Score:[/bright_magenta] [bold]{game.stats2.score}[/bold]"
    )
    return 0


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
    elif args.command == "tournament":
        return cmd_tournament(args)
    elif args.command == "achievements":
        return cmd_achievements(args)
    elif args.command == "multiplayer":
        return cmd_multiplayer(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())
