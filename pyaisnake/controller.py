"""
CLI Controller - Keyboard input handling for Snake game.
"""

import contextlib
import threading
import time
from collections import deque
from collections.abc import Callable

from .engine import Direction

# Try to import keyboard, fallback to basic input
try:
    import keyboard

    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False


class InputEvent:
    """Represents a keyboard input event"""

    def __init__(self, key: str, action: str):
        self.key = key
        self.action = action
        self.timestamp = time.time()


class CLIController:
    """
    Keyboard input controller for Snake game.

    Usage:
        controller = CLIController(game)
        controller.bind('up', lambda: game.set_direction(Direction.UP))
        controller.start()

        # Later...
        controller.stop()
    """

    # Default key mappings
    DEFAULT_KEYS = {
        # Arrow keys
        "up": Direction.UP,
        "down": Direction.DOWN,
        "left": Direction.LEFT,
        "right": Direction.RIGHT,
        # WASD
        "w": Direction.UP,
        "s": Direction.DOWN,
        "a": Direction.LEFT,
        "d": Direction.RIGHT,
        # Vim-style
        "k": Direction.UP,
        "j": Direction.DOWN,
        "h": Direction.LEFT,
        "l": Direction.RIGHT,
    }

    def __init__(self, use_keyboard_lib: bool = True):
        self.use_keyboard_lib = use_keyboard_lib and KEYBOARD_AVAILABLE
        self.running = False
        self._thread: threading.Thread | None = None
        self._event_queue: deque = deque(maxlen=10)
        self._callbacks: dict[str, Callable] = {}
        self._last_direction: Direction | None = None

        # Set up default key bindings
        self._setup_defaults()

    def _setup_defaults(self) -> None:
        """Set up default key bindings"""
        for key, direction in self.DEFAULT_KEYS.items():
            self.bind(key, lambda d=direction: self._set_direction(d))

        # Control keys
        self.bind("p", lambda: self._emit_event("pause"))
        self.bind("space", lambda: self._emit_event("pause"))
        self.bind("r", lambda: self._emit_event("restart"))
        self.bind("q", lambda: self._emit_event("quit"))
        self.bind("esc", lambda: self._emit_event("quit"))

    def bind(self, key: str, callback: Callable) -> None:
        """Bind a key to a callback function"""
        key = key.lower()
        self._callbacks[key] = callback

        if self.use_keyboard_lib and self.running:
            keyboard.add_hotkey(key, callback)

    def _set_direction(self, direction: Direction) -> None:
        """Set direction and emit event"""
        self._last_direction = direction
        self._emit_event("move", direction=direction)

    def _emit_event(self, action: str, **kwargs) -> None:
        """Emit an input event"""
        event = {"action": action, **kwargs}
        self._event_queue.append(event)

    def get_event(self) -> dict | None:
        """Get next event from queue (non-blocking)"""
        if self._event_queue:
            return self._event_queue.popleft()
        return None

    def get_direction(self) -> Direction | None:
        """Get last pressed direction and clear it"""
        direction = self._last_direction
        self._last_direction = None
        return direction

    def start(self) -> None:
        """Start listening for keyboard input"""
        if self.running:
            return

        self.running = True

        if self.use_keyboard_lib:
            self._start_keyboard_thread()
        else:
            self._start_fallback_thread()

    def _start_keyboard_thread(self) -> None:
        """Start keyboard library listener"""
        # keyboard library hooks globally, no thread needed
        # Just ensure all bindings are registered
        import contextlib

        for key, callback in self._callbacks.items():
            with contextlib.suppress(Exception):
                keyboard.add_hotkey(key, callback)

    def _start_fallback_thread(self) -> None:
        """Start fallback input thread (limited functionality)"""
        import contextlib

        def fallback_listener():
            while self.running:
                with contextlib.suppress(Exception):
                    # This is blocking and limited
                    # For real games, use keyboard library
                    time.sleep(0.05)

        self._thread = threading.Thread(target=fallback_listener, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop listening for keyboard input"""
        self.running = False

        if self.use_keyboard_lib:
            with contextlib.suppress(Exception):
                keyboard.unhook_all()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)

    def wait_for_key(self, timeout: float = None) -> str | None:
        """
        Wait for a key press (blocking).
        Returns key name or None if timeout.
        """
        if not self.use_keyboard_lib:
            return None

        try:
            event = keyboard.read_event(timeout)
            if event and event.event_type == keyboard.KEY_DOWN:
                return event.name
        except Exception:
            pass

        return None


class SimpleController:
    """
    Simple controller without external dependencies.
    Uses stdin for input (requires Enter key).
    """

    def __init__(self):
        self.commands: dict[str, Callable] = {}

    def bind(self, key: str, callback: Callable) -> None:
        """Bind a command to a callback"""
        self.commands[key.lower()] = callback

    def process_input(self, input_str: str) -> bool:
        """
        Process input string and execute corresponding command.
        Returns True if command was found.
        """
        cmd = input_str.strip().lower()

        if cmd in self.commands:
            self.commands[cmd]()
            return True

        return False

    def run_interactive(self, prompt: str = "> ") -> None:
        """Run interactive command loop"""
        print("Commands: up/down/left/right, wasd, p=pause, q=quit")
        print("Press Enter after each command")
        print()

        while True:
            try:
                user_input = input(prompt)
                if not self.process_input(user_input):
                    if user_input.lower() == "q":
                        break
                    print(f"Unknown command: {user_input}")
            except EOFError:
                break
            except KeyboardInterrupt:
                break
