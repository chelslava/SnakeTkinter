# 🐍 PyAISnake - CLI Snake Game with AI

Modern Snake game with AI capabilities - now fully in terminal!

## 🚀 Quick Start

```bash
# Install
uv sync

# Play the game
uv run pyaisnake play

# Watch AI play
uv run pyaisnake ai --visualize

# View statistics
uv run pyaisnake stats
```

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/chelslava/SnakeTkinter.git
cd SnakeTkinter

# Install dependencies with uv
uv sync
```

## 🎮 Commands

### `play` - Manual Play

Play Snake manually in the terminal:

```bash
uv run pyaisnake play [OPTIONS]

Options:
  --width, -W     Field width (default: 40)
  --height, -H    Field height (default: 20)
  --speed, -s     Game speed in ms (default: 100, lower = faster)
  --obstacles, -o Number of obstacles (default: 0)
  --ascii         Use ASCII instead of Unicode
```

**Controls:**
- `↑↓←→` or `WASD` - Move
- `P` or `Space` - Pause
- `R` - Restart
- `Q` or `Esc` - Quit

### `ai` - AI Play

Let AI play the game:

```bash
uv run pyaisnake ai [OPTIONS]

Options:
  --algorithm, -a  AI algorithm: a_star, neural, genetic, random (default: a_star)
  --visualize, -V  Show visualization
  --games, -g      Number of games (default: 1)
```

**Examples:**
```bash
# Watch A* AI play
uv run pyaisnake ai --visualize

# Run 10 AI games without visualization
uv run pyaisnake ai --algorithm a_star --games 10

# Fast AI game
uv run pyaisnake ai --speed 20
```

### `train` - Train AI

Train AI models:

```bash
uv run pyaisnake train [OPTIONS]

Options:
  --algorithm, -a  Algorithm to train: neural, genetic (required)
  --games, -g      Training games (default: 100)
  --save           Save model to file
  --load           Load existing model
```

**Examples:**
```bash
# Train neural network
uv run pyaisnake train --algorithm neural --games 1000 --save neural_model.pkl

# Continue training
uv run pyaisnake train --algorithm neural --load neural_model.pkl --games 500
```

### `stats` - Statistics

View game statistics:

```bash
uv run pyaisnake stats [OPTIONS]

Options:
  --top, -t   Show top N scores (default: 10)
  --export    Export stats to JSON
```

**Examples:**
```bash
# Show top 10 scores
uv run pyaisnake stats

# Show top 20 and export
uv run pyaisnake stats --top 20 --export stats.json
```

## 🧠 AI Algorithms

| Algorithm | Description | Best For |
|-----------|-------------|----------|
| **A\*** | Optimal pathfinding | High scores |
| **Neural** | Neural network (MLPRegressor) | Learning from games |
| **Genetic** | Evolutionary algorithm | Long-term optimization |
| **Random** | Random safe moves | Baseline comparison |

## 📁 Project Structure

```
pyaisnake/
├── __init__.py      # Package init
├── __main__.py      # python -m pyaisnake
├── cli.py           # CLI entry point
├── engine.py        # Game logic (pure Python)
├── renderer.py      # Rich-based CLI renderer
├── controller.py    # Keyboard input handler
├── ai/              # AI algorithms
│   ├── base.py      # A* pathfinding
│   ├── neural.py    # Neural network
│   └── genetic.py   # Genetic algorithm
├── modes.py         # Game modes
├── analytics.py     # Game analytics
└── logger.py        # Logging system
```

## 🎯 Game Modes

| Mode | Description |
|------|-------------|
| **Classic** | Standard Snake game |
| **Time Attack** | 2 minutes to max score |
| **Survival** | Increasing difficulty |
| **Puzzle** | Level-based challenges |
| **Speed Run** | Speed challenges |

## ⌨️ Keyboard Support

The game uses the `keyboard` library for real-time input:
- Cross-platform (Windows, Linux, macOS)
- No need to press Enter
- Works in most terminals

If `keyboard` is not available, the game runs in demo mode with simple AI.

## 🧪 Development

```bash
# Run tests
uv run pytest tests/ -v

# Type checking
uv run mypy pyaisnake/

# Linting
uv run ruff check pyaisnake/

# Format
uv run ruff format pyaisnake/
```

## 📊 Statistics

Statistics are stored in `snake_stats.db` (SQLite):
- Game scores
- Duration
- Snake length
- Timestamps

## 🔧 Requirements

- Python 3.10+
- numpy
- scikit-learn
- rich
- keyboard

## 📝 License

MIT License

---

**Made with ❤️ for AI and game enthusiasts**

Play now: `uv run pyaisnake play`
