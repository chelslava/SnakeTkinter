# AGENTS.md - Coding Agent Guidelines for SnakeTkinter

This document provides guidelines for agentic coding agents working in this repository.

## Project Overview

SnakeTkinter is a modern Snake game implementation with AI capabilities, analytics, and multiple game modes. Built with Python and tkinter GUI framework.

## Build/Lint/Test Commands

### Running the Game
```bash
# Windows (recommended)
.venv\Scripts\python.exe main.py

# Linux/Mac
source .venv/bin/activate
python main.py

# Alternative via batch files
run_game.bat          # Windows
.\run_game.ps1        # PowerShell
```

### Running Tests
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_logger.py -v
python -m pytest tests/test_priority2.py -v
python -m pytest tests/test_ai_tools.py -v

# Run single test class
python -m pytest tests/test_logger.py::TestGameLogger -v

# Run single test method
python -m pytest tests/test_logger.py::TestGameLogger::test_log_game_event -v
```

### Installing Dependencies
```bash
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

### No Linting/Type Checking Configured
This project does not have explicit lint or typecheck commands configured. Consider using:
- `ruff check .` for linting
- `mypy .` for type checking

## Code Style Guidelines

### Imports
Organize imports in the following order, separated by blank lines:
1. Standard library imports (alphabetically)
2. Third-party imports (alphabetically)
3. Local imports (alphabetically)

```python
# Standard library
import math
import os
import sqlite3
import time
from datetime import datetime
from random import randint, choice

# Third-party
import numpy as np
from sklearn.neural_network import MLPRegressor

# Local modules
from ai_tools import AdvancedSnakeAI, GameAnalyzer
from logger import game_logger, error_handler
```

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Classes | PascalCase | `GameLogger`, `AdvancedSnakeAI`, `TimeAttackMode` |
| Functions | snake_case | `create_snake()`, `get_safe_directions()` |
| Variables | snake_case | `game_over`, `snake_length`, `food_distance` |
| Constants | UPPER_SNAKE_CASE | `WIDTH`, `HEIGHT`, `CELL_SIZE`, `DELAY` |
| Global variables | UPPER_SNAKE_CASE | `AI_MODE`, `AI_HELPER`, `DB_PATH` |
| Private methods | _leading_underscore | `_calculate_internal()` |
| Enums | PascalCase | `GameMode.CLASSIC`, `GameMode.TIME_ATTACK` |

### Code Formatting

- Use 4 spaces for indentation (no tabs)
- Maximum line length: approximately 100 characters
- Blank lines between class methods
- Two blank lines between top-level functions/classes

### Docstrings and Comments

- Use Russian language for docstrings and comments (following project convention)
- Use triple-quoted docstrings for classes and public methods

```python
class AdvancedSnakeAI:
    """Продвинутый ИИ для игры Snake с различными алгоритмами"""
    
    def a_star_pathfinding(self, snake, food, obstacles):
        """Алгоритм A* для поиска кратчайшего пути к еде"""
        pass
```

### Type Hints

Type hints are optional but encouraged for function signatures:

```python
def get_safe_directions(self, snake: list, food: tuple, obstacles: list) -> list:
    """Получить безопасные направления движения"""
    pass
```

## Error Handling

### Using the ErrorHandler Class

The project uses a custom `ErrorHandler` class from `logger.py`:

```python
from logger import error_handler

try:
    risky_operation()
except Exception as e:
    result = error_handler.handle_error(e, "context_description", show_user=True)
    # result is "continue" or "restart"
```

### Safe Wrapper Functions

Use the "safe_" prefix pattern for functions with error handling:

```python
def safe_game_loop():
    """Безопасный игровой цикл с обработкой ошибок"""
    try:
        game_loop()
    except Exception as e:
        result = error_handler.handle_error(e, "Game loop error")
        if result == "restart":
            restart_game()
```

### Error Handler Limits

- Maximum 5 errors before auto-restart
- Use `show_user=False` for non-critical errors
- Call `error_handler.reset_error_count()` after successful operations

## Logging

### Using the GameLogger Class

```python
from logger import game_logger

# Log game events
game_logger.log_game_event("game_started", {"mode": "classic"})

# Log AI decisions
game_logger.log_ai_decision("Right", {"snake_length": 5})

# Log performance metrics
game_logger.log_performance("a_star_pathfinding", 0.025)

# Log user actions
game_logger.log_user_action("button_click", {"button": "pause"})
```

### Log Levels

- DEBUG: AI decisions, detailed state info
- INFO: Game events, user actions, performance
- ERROR: Exceptions, critical failures

## Project Structure

```
SnakeTkinter/
├── main.py              # Main game file, entry point
├── ai_tools.py          # AI algorithms (A*, heuristics)
├── neural_ai.py         # Neural network implementation
├── game_modes.py        # Game mode definitions
├── advanced_analytics.py # Analytics and statistics
├── logger.py            # Logging and error handling
├── ui_enhancements.py   # UI components (ModernUI, SettingsDialog)
├── requirements.txt     # Dependencies
├── tests/               # Test suite
│   ├── __init__.py
│   ├── test_logger.py
│   ├── test_priority2.py
│   └── test_ai_tools.py
└── README.md            # Project documentation
```

## Key Components

### AI System
- `AdvancedSnakeAI`: A* pathfinding, strategic advice, difficulty analysis
- `NeuralSnakeAI`: MLPRegressor-based neural network for decision making
- `GameAnalyzer`: Move analysis and performance metrics

### Game Modes (game_modes.py)
- `GameMode` enum: CLASSIC, TIME_ATTACK, SURVIVAL, PUZZLE, AI_BATTLE, SPEED_RUN, ENDLESS
- `GameModeManager`: Mode configuration and state management
- `TimeAttackMode`, `SurvivalMode`, `PuzzleMode`: Mode-specific logic

### Analytics (advanced_analytics.py)
- `AdvancedGameAnalytics`: Move tracking, efficiency calculation, player behavior analysis
- Generates recommendations and exports reports to JSON

## Testing Guidelines

### Test File Organization
- Test files in `tests/` directory
- One test class per class being tested
- Test method naming: `test_<functionality>`

### Writing Tests
```python
import unittest
from unittest.mock import patch, MagicMock

class TestMyClass(unittest.TestCase):
    def setUp(self):
        """Setup runs before each test"""
        self.instance = MyClass()
    
    def test_functionality(self):
        """Тест описания функциональности"""
        result = self.instance.method()
        self.assertEqual(result, expected_value)
```

### Test Dependencies
- `unittest` (standard library)
- `pytest` (test runner)
- `numpy` (for numerical tests)
- `unittest.mock` (for mocking)

## Database

- SQLite database: `snake_stats.db`
- Tables: `games` (score, length, duration), `achievements` (name, date)
- Use parameterized queries to prevent SQL injection

## Important Patterns

### Tkinter GUI
- Use `ttk` widgets for modern styling
- Modal dialogs: `transient()`, `grab_set()`
- Bind events: `root.bind("<KeyPress>", handler)`

### Game State Management
- Global state variables in main.py
- Reset functions for game restart
- Pause/resume pattern

### Configuration Constants
```python
WIDTH = 400          # Game field width
HEIGHT = 400         # Game field height
CELL_SIZE = 10       # Size of one cell
DELAY = 100          # Game speed (ms between updates)
```

## Common Gotchas

1. **Import paths**: Tests use `sys.path.append('..')` for imports
2. **Tkinter threading**: All UI updates must occur on main thread
3. **Matplotlib optional**: Check `MATPLOTLIB_AVAILABLE` before using
4. **Model persistence**: Neural network models saved as `.pkl` files
5. **Russian text**: Use UTF-8 encoding for file I/O
