#!/usr/bin/env python3
"""
PyAISnake - Entry point for running as module.

Usage:
    python -m pyaisnake [command] [options]
"""

import sys

from .cli import main

if __name__ == "__main__":
    sys.exit(main())
