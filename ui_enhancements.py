import tkinter as tk
from tkinter import ttk


class ModernUI:
    """Современный пользовательский интерфейс"""

    def __init__(self, root):
        self.root = root
        self.setup_modern_theme()
        self.create_enhanced_menu()
        self.setup_status_bar()

    def setup_modern_theme(self):
        """Настройка современной темы"""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Modern.TButton",
            background="#4CAF50",
            foreground="white",
            borderwidth=0,
            focuscolor="none",
            font=("Arial", 10, "bold"),
        )

        style.configure("Modern.TFrame", background="#f0f0f0")

        style.configure(
            "Status.TLabel", background="#2c3e50", foreground="white", font=("Arial", 9)
        )

        style.configure(
            "Title.TLabel",
            background="#34495e",
            foreground="white",
            font=("Arial", 12, "bold"),
        )

    def create_enhanced_menu(self):
        """Создание улучшенного меню"""
        main_frame = ttk.Frame(self.root, style="Modern.TFrame")
        main_frame.pack(fill="both", expand=True)

        self.create_toolbar(main_frame)

        self.game_frame = ttk.Frame(main_frame)
        self.game_frame.pack(fill="both", expand=True, padx=5, pady=5)

    def create_toolbar(self, parent):
        """Создание панели инструментов"""
        toolbar = ttk.Frame(parent, style="Modern.TFrame")
        toolbar.pack(fill="x", padx=5, pady=5)

        ai_frame = ttk.LabelFrame(toolbar, text="ИИ инструменты", padding=5)
        ai_frame.pack(side="left", fill="y", padx=5)

        game_frame = ttk.LabelFrame(toolbar, text="Управление", padding=5)
        game_frame.pack(side="right", fill="y", padx=5)

        info_frame = ttk.LabelFrame(toolbar, text="Информация", padding=5)
        info_frame.pack(side="left", fill="y", padx=5, expand=True)

        return ai_frame, game_frame, info_frame

    def setup_status_bar(self):
        """Настройка строки состояния"""
        self.status_bar = ttk.Frame(self.root, style="Status.TLabel")
        self.status_bar.pack(fill="x", side="bottom")

        self.status_label = ttk.Label(self.status_bar, text="Готов к игре", style="Status.TLabel")
        self.status_label.pack(side="left", padx=5)

        self.fps_label = ttk.Label(self.status_bar, text="FPS: 0", style="Status.TLabel")
        self.fps_label.pack(side="right", padx=5)

    def update_status(self, message):
        """Обновление статуса"""
        self.status_label.config(text=message)

    def update_fps(self, fps):
        """Обновление FPS"""
        self.fps_label.config(text=f"FPS: {fps:.1f}")


class AIVisualizer:
    """Визуализация работы ИИ алгоритмов"""

    def __init__(self, canvas, width=400, height=400, cell_size=10):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.cell_size = cell_size
        self.visualization_enabled = False
        self.path_items = []
        self.analysis_items = []

    def toggle_visualization(self):
        """Переключение визуализации"""
        self.visualization_enabled = not self.visualization_enabled
        if not self.visualization_enabled:
            self.clear_visualization()
        return self.visualization_enabled

    def clear_visualization(self):
        """Очистка визуализации"""
        for item in self.path_items + self.analysis_items:
            self.canvas.delete(item)
        self.path_items = []
        self.analysis_items = []

    def draw_path(self, path, color="#00FF00", width=2):
        """Отрисовка найденного пути A*"""
        if not self.visualization_enabled or not path:
            return

        self.clear_visualization()

        for i in range(len(path) - 1):
            x1, y1 = path[i]
            x2, y2 = path[i + 1]

            item = self.canvas.create_line(
                x1 + self.cell_size // 2,
                y1 + self.cell_size // 2,
                x2 + self.cell_size // 2,
                y2 + self.cell_size // 2,
                fill=color,
                width=width,
                dash=(4, 2),
            )
            self.path_items.append(item)

    def draw_safe_zones(self, snake, food, obstacles, safe_directions):
        """Отрисовка безопасных зон"""
        if not self.visualization_enabled:
            return

        head = snake[0]
        colors = {"Up": "#00FF0055", "Down": "#00FF0055", "Left": "#00FF0055", "Right": "#00FF0055"}

        for direction, color in colors.items():
            next_pos = self._get_next_position(head, direction)
            is_safe = direction in safe_directions

            if is_safe:
                item = self.canvas.create_rectangle(
                    next_pos[0],
                    next_pos[1],
                    next_pos[0] + self.cell_size,
                    next_pos[1] + self.cell_size,
                    fill=color if is_safe else "#FF000055",
                    outline="",
                )
                self.analysis_items.append(item)

    def draw_food_direction(self, snake, food):
        """Отрисовка направления к еде"""
        if not self.visualization_enabled:
            return

        head = snake[0]
        item = self.canvas.create_line(
            head[0] + self.cell_size // 2,
            head[1] + self.cell_size // 2,
            food[0] + self.cell_size // 2,
            food[1] + self.cell_size // 2,
            fill="#FFD700",
            width=1,
            dash=(2, 2),
        )
        self.analysis_items.append(item)

    def draw_danger_zones(self, snake, obstacles):
        """Отрисовка опасных зон"""
        if not self.visualization_enabled:
            return

        head = snake[0]
        danger_radius = self.cell_size * 3

        for dx in range(-danger_radius, danger_radius + 1, self.cell_size):
            for dy in range(-danger_radius, danger_radius + 1, self.cell_size):
                pos = (head[0] + dx, head[1] + dy)
                if pos in obstacles or pos in snake[1:]:
                    item = self.canvas.create_rectangle(
                        pos[0],
                        pos[1],
                        pos[0] + self.cell_size,
                        pos[1] + self.cell_size,
                        fill="#FF000033",
                        outline="",
                    )
                    self.analysis_items.append(item)

    def draw_neural_scores(self, direction_scores):
        """Отрисовка оценок направлений от нейросети"""
        if not self.visualization_enabled or not direction_scores:
            return

        directions = ["Up", "Down", "Left", "Right"]
        offsets = [(0, -30), (0, 30), (-30, 0), (30, 0)]

        for i, (_direction, _offset) in enumerate(zip(directions, offsets)):
            if i < len(direction_scores):
                score = direction_scores[i]
                self._score_to_color(score)

    def _score_to_color(self, score):
        """Преобразование оценки в цвет"""
        if score > 0.5:
            return "#00FF00"
        elif score > 0:
            return "#FFFF00"
        else:
            return "#FF0000"

    def _get_next_position(self, pos, direction):
        """Получить следующую позицию"""
        x, y = pos
        if direction == "Up":
            return (x, y - self.cell_size)
        elif direction == "Down":
            return (x, y + self.cell_size)
        elif direction == "Left":
            return (x - self.cell_size, y)
        elif direction == "Right":
            return (x + self.cell_size, y)
        return pos

    def draw_genetic_info(self, generation, best_fitness, avg_fitness):
        """Отрисовка информации о генетическом алгоритме"""
        if not self.visualization_enabled:
            return

        info_text = f"Gen: {generation} | Best: {best_fitness:.0f} | Avg: {avg_fitness:.0f}"
        item = self.canvas.create_text(
            10, self.height - 10, text=info_text, fill="#00FFFF", anchor="sw", font=("Arial", 8)
        )
        self.analysis_items.append(item)


class SettingsDialog:
    """Диалог настроек с улучшенным интерфейсом"""

    def __init__(self, parent):
        self.parent = parent
        self.result = None
        self.create_dialog()

    def create_dialog(self):
        """Создание диалога настроек"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Настройки игры")
        self.dialog.geometry("450x550")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        notebook = ttk.Notebook(self.dialog)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.create_general_tab(notebook)
        self.create_ai_tab(notebook)
        self.create_visual_tab(notebook)

        self.create_buttons()

    def create_general_tab(self, notebook):
        """Создание вкладки основных настроек"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Основные")

        ttk.Label(frame, text="Размер поля:").pack(anchor="w", padx=10, pady=5)
        self.width_var = tk.IntVar(value=400)
        self.height_var = tk.IntVar(value=400)

        size_frame = ttk.Frame(frame)
        size_frame.pack(fill="x", padx=10)
        ttk.Label(size_frame, text="Ширина:").pack(side="left")
        ttk.Entry(size_frame, textvariable=self.width_var, width=10).pack(side="left", padx=5)
        ttk.Label(size_frame, text="Высота:").pack(side="left", padx=(10, 0))
        ttk.Entry(size_frame, textvariable=self.height_var, width=10).pack(side="left", padx=5)

        ttk.Label(frame, text="Скорость игры (мс):").pack(anchor="w", padx=10, pady=5)
        self.speed_var = tk.IntVar(value=100)
        speed_scale = ttk.Scale(
            frame, from_=20, to=200, variable=self.speed_var, orient="horizontal"
        )
        speed_scale.pack(fill="x", padx=10)

        ttk.Label(frame, text="Начальные препятствия:").pack(anchor="w", padx=10, pady=5)
        self.obstacles_var = tk.IntVar(value=0)
        obstacles_scale = ttk.Scale(
            frame, from_=0, to=20, variable=self.obstacles_var, orient="horizontal"
        )
        obstacles_scale.pack(fill="x", padx=10)

    def create_ai_tab(self, notebook):
        """Создание вкладки ИИ настроек"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="ИИ")

        ttk.Label(frame, text="Алгоритм ИИ:").pack(anchor="w", padx=10, pady=5)
        self.ai_algorithm = tk.StringVar(value="a_star")
        algorithms = [
            ("A* (оптимизированный)", "a_star"),
            ("Нейросеть", "neural"),
            ("Генетический", "genetic"),
            ("Простой", "simple"),
        ]
        for text, value in algorithms:
            ttk.Radiobutton(frame, text=text, variable=self.ai_algorithm, value=value).pack(
                anchor="w", padx=20
            )

        ttk.Label(frame, text="Скорость обучения:").pack(anchor="w", padx=10, pady=5)
        self.learning_rate = tk.DoubleVar(value=0.1)
        learning_scale = ttk.Scale(
            frame, from_=0.01, to=0.5, variable=self.learning_rate, orient="horizontal"
        )
        learning_scale.pack(fill="x", padx=10)

        ttk.Label(frame, text="Уровень исследования:").pack(anchor="w", padx=10, pady=5)
        self.exploration_rate = tk.DoubleVar(value=0.2)
        exploration_scale = ttk.Scale(
            frame, from_=0.0, to=1.0, variable=self.exploration_rate, orient="horizontal"
        )
        exploration_scale.pack(fill="x", padx=10)

        self.show_ai_visualization = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame, text="Визуализация работы ИИ", variable=self.show_ai_visualization
        ).pack(anchor="w", padx=10, pady=5)

    def create_visual_tab(self, notebook):
        """Создание вкладки визуальных настроек"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Визуал")

        ttk.Label(frame, text="Цветовая схема:").pack(anchor="w", padx=10, pady=5)
        self.color_scheme = tk.StringVar(value="classic")
        schemes = [("Классическая", "classic"), ("Темная", "dark"), ("Яркая", "bright")]
        for text, value in schemes:
            ttk.Radiobutton(frame, text=text, variable=self.color_scheme, value=value).pack(
                anchor="w", padx=20
            )

        self.show_hints = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Показывать подсказки ИИ", variable=self.show_hints).pack(
            anchor="w", padx=10, pady=5
        )

        self.show_analysis = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame, text="Показывать анализ сложности", variable=self.show_analysis
        ).pack(anchor="w", padx=10, pady=5)

        self.enable_animations = tk.BooleanVar(value=True)
        ttk.Checkbutton(frame, text="Включить анимации", variable=self.enable_animations).pack(
            anchor="w", padx=10, pady=5
        )

    def create_buttons(self):
        """Создание кнопок"""
        button_frame = ttk.Frame(self.dialog)
        button_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(button_frame, text="Применить", command=self.apply_settings).pack(
            side="right", padx=5
        )
        ttk.Button(button_frame, text="Отмена", command=self.cancel).pack(side="right", padx=5)
        ttk.Button(button_frame, text="Сброс", command=self.reset_settings).pack(
            side="left", padx=5
        )

    def apply_settings(self):
        """Применение настроек"""
        self.result = {
            "general": {
                "width": self.width_var.get(),
                "height": self.height_var.get(),
                "speed": self.speed_var.get(),
                "obstacles": self.obstacles_var.get(),
            },
            "ai": {
                "algorithm": self.ai_algorithm.get(),
                "learning_rate": self.learning_rate.get(),
                "exploration_rate": self.exploration_rate.get(),
                "show_visualization": self.show_ai_visualization.get(),
            },
            "visual": {
                "color_scheme": self.color_scheme.get(),
                "show_hints": self.show_hints.get(),
                "show_analysis": self.show_analysis.get(),
                "enable_animations": self.enable_animations.get(),
            },
        }
        self.dialog.destroy()

    def cancel(self):
        """Отмена настроек"""
        self.dialog.destroy()

    def reset_settings(self):
        """Сброс настроек"""
        self.width_var.set(400)
        self.height_var.set(400)
        self.speed_var.set(100)
        self.obstacles_var.set(0)
        self.ai_algorithm.set("a_star")
        self.learning_rate.set(0.1)
        self.exploration_rate.set(0.2)
        self.show_ai_visualization.set(False)
        self.color_scheme.set("classic")
        self.show_hints.set(True)
        self.show_analysis.set(True)
        self.enable_animations.set(True)


class PerformanceMonitor:
    """Монитор производительности"""

    def __init__(self):
        self.frame_times = []
        self.max_samples = 60

    def record_frame(self, frame_time):
        """Запись времени кадра"""
        self.frame_times.append(frame_time)
        if len(self.frame_times) > self.max_samples:
            self.frame_times.pop(0)

    def get_fps(self):
        """Получение FPS"""
        if not self.frame_times:
            return 0
        avg_frame_time = sum(self.frame_times) / len(self.frame_times)
        return 1.0 / avg_frame_time if avg_frame_time > 0 else 0

    def get_performance_stats(self):
        """Получение статистики производительности"""
        if not self.frame_times:
            return {}

        return {
            "fps": self.get_fps(),
            "avg_frame_time": sum(self.frame_times) / len(self.frame_times),
            "min_frame_time": min(self.frame_times),
            "max_frame_time": max(self.frame_times),
        }
