# PyAISnake TUI

Terminal User Interface for PyAISnake using Textual.

## Installation

```bash
pip install pyaisnake
```

## Running TUI

```bash
snaketui
```

Or:

```bash
python -m pyaisnake.tui
```

## Controls

### In Menu
| Key | Action |
|-----|--------|
| Enter | Select button |
| Tab | Navigate buttons |
| Q / Esc | Quit |

### In Game
| Key | Action |
|-----|--------|
| ↑↓←→ | Move snake |
| WASD | Move snake |
| P / Space | Pause/Resume |
| R | Restart game |
| Q / Esc | Back to menu |

## Features

- Real-time snake game rendering
- Live statistics panel
- Pause and restart functionality
- Clean terminal interface

## Requirements

- Python 3.10+
- textual >= 0.47.0

## CLI Alternative

If TUI doesn't work, use the CLI:

```bash
pyaisnake play
```
