import sqlite3
import time
import tkinter as tk
from random import randint
from tkinter import messagebox

from ai_tools import AdvancedSnakeAI, GameAnalyzer

# Попытка импорта matplotlib (может не быть установлен)
try:
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Настройка игры
WIDTH = 400  # Ширина игрового поля
HEIGHT = 400  # Высота игрового поля
DIRECTIONS = ["Up", "Down", "Left", "Right"]  # Список с направлениями движения змейки
CELL_SIZE = 10  # Размер одной клетки змейки и еды
DELAY = 100  # Скорость игры (задержка между движениями змейки в мс)
INIT_OBSTACLES = 0

# ИИ настройки
AI_MODE = False  # Режим автоматической игры
AI_HELPER = False  # Режим подсказок
DIFFICULTY_ANALYSIS = False  # Анализ сложности
SMART_OBSTACLES = False  # Умные препятствия

# Глобальные переменные
last_food_times = []
near_obstacle_streak = 0
DB_PATH = 'snake_stats.db'

# Создание главного окна
root = tk.Tk()
root.title("Snake AI | Счет: 0")
root.resizable(width=False, height=False)


# --- Работа с БД ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS games (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        score INTEGER,
        length INTEGER,
        duration REAL,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS achievements (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    conn.commit()
    conn.close()


def save_game_to_db(score, length, duration):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO games (score, length, duration) VALUES (?, ?, ?)', (score, length, duration))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка сохранения в БД: {e}")


def save_achievement_to_db(name):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('INSERT INTO achievements (name) VALUES (?)', (name,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Ошибка сохранения достижения: {e}")


def load_stats_from_db():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('SELECT MAX(score), AVG(score), AVG(length), AVG(duration), COUNT(*) FROM games')
        row = c.fetchone()
        stats = {
            'best_score': row[0] or 0,
            'avg_score': row[1] or 0,
            'avg_length': row[2] or 0,
            'avg_duration': row[3] or 0,
            'games_played': row[4] or 0
        }
        c.execute('SELECT name, COUNT(*) FROM achievements GROUP BY name')
        achs = dict(c.fetchall())
        conn.close()
        return stats, achs
    except Exception as e:
        print(f"Ошибка загрузки статистики: {e}")
        return {'best_score': 0, 'avg_score': 0, 'avg_length': 0, 'avg_duration': 0, 'games_played': 0}, {}


# Вызвать init_db() при запуске
init_db()


# --- Окно статистики ---
def show_stats_window():
    was_paused = paused
    if not paused:
        toggle_pause()
    stats, achs = load_stats_from_db()

    win = tk.Toplevel(root)
    win.title("Статистика и достижения")
    win.geometry("500x400")
    win.resizable(False, False)

    info = f"Лучший счет: {stats['best_score']}\n" \
           f"Средний счет: {stats['avg_score']:.1f}\n" \
           f"Средняя длина: {stats['avg_length']:.1f}\n" \
           f"Среднее время: {stats['avg_duration']:.1f} сек\n" \
           f"Игр сыграно: {stats['games_played']}\n"
    tk.Label(win, text=info, font=("Arial", 12), justify="left").pack(anchor="w", padx=10, pady=5)

    ach_text = "Достижения:\n" + ("\n".join([f"{k}: {v}" for k, v in achs.items()]) if achs else "Нет достижений")
    tk.Label(win, text=ach_text, font=("Arial", 11), justify="left").pack(anchor="w", padx=10, pady=5)

    # График прогресса (если matplotlib доступен)
    if MATPLOTLIB_AVAILABLE:
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute('SELECT score FROM games ORDER BY id')
            all_scores = [row[0] for row in c.fetchall()]
            conn.close()

            if len(all_scores) > 1:
                fig = plt.Figure(figsize=(4, 2), dpi=100)
                ax = fig.add_subplot(111)
                ax.plot(range(1, len(all_scores) + 1), all_scores, marker='o')
                ax.set_title('Динамика счета по играм')
                ax.set_xlabel('Игра')
                ax.set_ylabel('Счет')
                fig.tight_layout()
                canvas_plot = FigureCanvasTkAgg(fig, master=win)
                canvas_plot.draw()
                canvas_plot.get_tk_widget().pack(pady=10)
            else:
                tk.Label(win, text="Недостаточно данных для графика", fg="gray").pack(pady=10)
        except Exception as e:
            tk.Label(win, text=f"Ошибка создания графика: {e}", fg="red").pack(pady=10)
    else:
        tk.Label(win, text="Matplotlib не установлен - график недоступен", fg="gray").pack(pady=10)

    def on_close():
        win.destroy()
        if not was_paused:
            toggle_pause()

    win.protocol("WM_DELETE_WINDOW", on_close)


# --- Окно настроек ---
def show_settings_window():
    global WIDTH, HEIGHT, DELAY, INIT_OBSTACLES
    was_paused = paused
    if not paused:
        toggle_pause()
    settings = tk.Toplevel(root)
    settings.title("Настройки игры")
    settings.geometry("300x250")
    settings.resizable(False, False)

    tk.Label(settings, text="Размер поля (px):").pack(pady=5)
    width_var = tk.IntVar(value=WIDTH)
    height_var = tk.IntVar(value=HEIGHT)
    tk.Entry(settings, textvariable=width_var).pack()
    tk.Entry(settings, textvariable=height_var).pack()

    tk.Label(settings, text="Скорость (мс, меньше = быстрее):").pack(pady=5)
    delay_var = tk.IntVar(value=DELAY)
    tk.Entry(settings, textvariable=delay_var).pack()

    tk.Label(settings, text="Начальное количество препятствий:").pack(pady=5)
    obstacles_var = tk.IntVar(value=INIT_OBSTACLES)
    tk.Entry(settings, textvariable=obstacles_var).pack()

    def apply_settings():
        w, h, d, o = width_var.get(), height_var.get(), delay_var.get(), obstacles_var.get()
        if w >= 100 and h >= 100 and d >= 20 and o >= 0:
            globals()['WIDTH'] = w
            globals()['HEIGHT'] = h
            globals()['DELAY'] = d
            globals()['INIT_OBSTACLES'] = o
            # Применяем к canvas
            canvas.config(width=WIDTH, height=HEIGHT)
            # Пересоздаем препятствия
            create_obstacles()
            # Перерисовываем поле
            canvas.delete("all")
            draw_food()
            draw_obstacles()
            draw_snake()
            update_title()
            settings.destroy()
            if not was_paused:
                toggle_pause()
        else:
            messagebox.showerror("Ошибка", "Некорректные значения!")

    def on_close():
        settings.destroy()
        if not was_paused:
            toggle_pause()

    settings.protocol("WM_DELETE_WINDOW", on_close)
    tk.Button(settings, text="Применить", command=apply_settings).pack(pady=15)


# --- Интеграция ИИ ---
ai_advanced = AdvancedSnakeAI()
game_analyzer = GameAnalyzer()


# --- ФУНКЦИИ УПРАВЛЕНИЯ ---
def restart_game():
    global snake, direction, food, score, game_over, paused, obstacles, ai_suggestions, game_start_time
    # Начальное положение змейки
    snake = create_snake()
    direction = "Right"
    # Новая еда и препятствия
    food = create_food()
    create_obstacles()
    # Сброс счёта и статуса
    score = 0
    game_over = False
    paused = False
    ai_suggestions = []
    game_start_time = time.time()
    # Очистим холст и обновим
    canvas.delete("all")
    draw_food()
    draw_obstacles()
    draw_snake()
    update_title()
    # Перезапускаем игровой цикл
    start_countdown()


def toggle_pause():
    global paused
    paused = not paused
    pause_btn.config(
        text="▶ Продолжить" if paused else "⏸ Пауза",
        bg="lightgray" if paused else "SystemButtonFace"
    )
    if not paused:
        game_loop()


def toggle_ai_mode():
    global AI_MODE
    AI_MODE = not AI_MODE
    ai_mode_btn.config(
        text="🤖 ИИ режим ВКЛ" if AI_MODE else "🤖 ИИ режим",
        bg="lightgreen" if AI_MODE else "SystemButtonFace"
    )
    if AI_MODE:
        messagebox.showinfo("ИИ режим", "ИИ будет играть автоматически!")


def toggle_ai_helper():
    global AI_HELPER
    AI_HELPER = not AI_HELPER
    ai_helper_btn.config(
        text="💡 Подсказки ВКЛ" if AI_HELPER else "💡 Подсказки",
        bg="lightblue" if AI_HELPER else "SystemButtonFace"
    )


def toggle_difficulty_analysis():
    global DIFFICULTY_ANALYSIS
    DIFFICULTY_ANALYSIS = not DIFFICULTY_ANALYSIS
    difficulty_btn.config(
        text="📊 Анализ ВКЛ" if DIFFICULTY_ANALYSIS else "📊 Анализ",
        bg="lightyellow" if DIFFICULTY_ANALYSIS else "SystemButtonFace"
    )


def toggle_smart_obstacles():
    global SMART_OBSTACLES
    SMART_OBSTACLES = not SMART_OBSTACLES
    obstacles_btn.config(
        text="🚧 Препятствия ВКЛ" if SMART_OBSTACLES else "🚧 Препятствия",
        bg="lightcoral" if SMART_OBSTACLES else "SystemButtonFace"
    )
    if SMART_OBSTACLES:
        create_obstacles()


# Создаем меню
menu_frame = tk.Frame(root)
menu_frame.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)

# Кнопки управления ИИ
ai_buttons_frame = tk.Frame(menu_frame)
ai_buttons_frame.pack(side=tk.LEFT)

ai_mode_btn = tk.Button(ai_buttons_frame, text="🤖 ИИ режим", command=toggle_ai_mode)
ai_mode_btn.pack(side=tk.LEFT, padx=2)

ai_helper_btn = tk.Button(ai_buttons_frame, text="💡 Подсказки", command=toggle_ai_helper)
ai_helper_btn.pack(side=tk.LEFT, padx=2)

difficulty_btn = tk.Button(ai_buttons_frame, text="📊 Анализ", command=toggle_difficulty_analysis)
difficulty_btn.pack(side=tk.LEFT, padx=2)

obstacles_btn = tk.Button(ai_buttons_frame, text="🚧 Препятствия", command=toggle_smart_obstacles)
obstacles_btn.pack(side=tk.LEFT, padx=2)

# Кнопка статистики в меню
stats_btn = tk.Button(ai_buttons_frame, text="📈 Статистика", command=show_stats_window)
stats_btn.pack(side=tk.LEFT, padx=2)

# Кнопка настроек теперь в меню
settings_btn = tk.Button(ai_buttons_frame, text="⚙ Настройки", command=show_settings_window)
settings_btn.pack(side=tk.LEFT, padx=2)

# Кнопки управления игрой
game_buttons_frame = tk.Frame(menu_frame)
game_buttons_frame.pack(side=tk.RIGHT)

restart_btn = tk.Button(game_buttons_frame, text="🔄 Перезапуск", command=restart_game)
restart_btn.pack(side=tk.RIGHT, padx=2)

pause_btn = tk.Button(game_buttons_frame, text="⏸ Пауза", command=toggle_pause)
pause_btn.pack(side=tk.RIGHT, padx=2)

# Игровое поле
canvas = tk.Canvas(
    root,
    width=WIDTH,
    height=HEIGHT,
    bg="black",
    highlightthickness=0
)
canvas.pack()

# Начальное состояние игры
direction = "Right"
food = None
score = 0
game_over = False
paused = False
obstacles = []
ai_suggestions = []
game_start_time = None
achievements = set()
last_food_times = []
near_obstacle_streak = 0


# Создаем змейку
def create_snake():
    # Вычисляем максимальное значение по X и Y,
    # чтобы вся змейка (3 клетки) уместилась в пределах поля
    max_x = (WIDTH // CELL_SIZE) - 3
    max_y = (HEIGHT // CELL_SIZE) - 1

    # Случайная позиция головы змейки
    x = randint(0, max_x) * CELL_SIZE
    y = randint(0, max_y) * CELL_SIZE

    # Возвращаем список из 3 сегментов змейки, направленных вправо
    return [(x, y), (x - CELL_SIZE, y), (x - 2 * CELL_SIZE, y)]


snake = create_snake()


# Создание еды
def create_food():
    while True:
        x = randint(0, (WIDTH - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
        y = randint(0, (HEIGHT - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
        pos = (x, y)
        if pos not in snake and pos not in obstacles:
            return pos


food = create_food()


# Создание препятствий
def create_obstacles():
    global obstacles
    obstacles = []
    if SMART_OBSTACLES:
        num_obstacles = min(5, score // 5 + 1)
        for _ in range(num_obstacles):
            attempts = 0
            while attempts < 100:  # Ограничиваем попытки
                x = randint(0, (WIDTH - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
                y = randint(0, (HEIGHT - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
                pos = (x, y)
                if pos not in snake and pos != food and pos not in obstacles:
                    obstacles.append(pos)
                    break
                attempts += 1


# Отрисовка препятствий
def draw_obstacles():
    for obstacle in obstacles:
        canvas.create_rectangle(
            obstacle[0], obstacle[1],
            obstacle[0] + CELL_SIZE,
            obstacle[1] + CELL_SIZE,
            fill="red",
            outline="darkred"
        )


# Отрисовка еды
def draw_food():
    canvas.create_rectangle(
        food[0], food[1],
        food[0] + CELL_SIZE,
        food[1] + CELL_SIZE,
        fill="orange"
    )


# Отрисовка змейки
def draw_snake():
    for index, segment in enumerate(snake):
        canvas.create_rectangle(
            segment[0], segment[1],
            segment[0] + CELL_SIZE,
            segment[1] + CELL_SIZE,
            fill="lime" if index == 0 else "green",
            outline="darkgreen"
        )


# Отрисовка подсказок ИИ
def draw_ai_suggestions():
    if AI_HELPER and ai_suggestions:
        y_offset = 20
        for suggestion in ai_suggestions[:3]:
            canvas.create_text(
                10, y_offset,
                text=suggestion,
                fill="yellow",
                font=("Arial", 10),
                anchor="nw"
            )
            y_offset += 20


# Отрисовка анализа сложности
def draw_difficulty_analysis():
    if DIFFICULTY_ANALYSIS:
        difficulty = ai_advanced.analyze_difficulty(snake, food, obstacles)
        color = "green" if difficulty < 30 else "yellow" if difficulty < 60 else "red"

        canvas.create_text(
            WIDTH - 10, 20,
            text=f"Сложность: {difficulty:.0f}%",
            fill=color,
            font=("Arial", 12, "bold"),
            anchor="ne"
        )


def on_key_press(event):
    global direction
    opposites = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}
    key = event.keysym

    # Управление направлением
    if key in DIRECTIONS:
        # Запрещаем поворот в противоположную сторону
        if key in opposites and direction != opposites[key]:
            direction = key
    # Перезапуск игры
    elif key == 'space' and game_over:
        restart_game()
    # Пауза
    elif key == 'p':
        toggle_pause()
    # Переключение ИИ режима
    elif key == 'a':
        toggle_ai_mode()
    # Переключение подсказок
    elif key == 'h':
        toggle_ai_helper()


root.bind("<KeyPress>", on_key_press)


# Проверка съедена ли еда?
def check_food_collision():
    global food, score, last_food_times
    if snake[0] == food:
        score += 1
        food = create_food()
        if SMART_OBSTACLES:
            create_obstacles()
        # Фиксируем время поедания еды
        last_food_times.append(time.time())
        if len(last_food_times) > 5:
            last_food_times = last_food_times[-5:]
        check_achievements()
        return True
    return False


# Функции ачивок
def check_achievements():
    global near_obstacle_streak
    # Пример: "Съешь 10 подряд"
    if score >= 10 and "eat10" not in achievements:
        achievements.add("eat10")
        show_achievement("Съедено 10! 🏅")
    # Пример: "Выживи 2 минуты"
    if game_start_time and time.time() - game_start_time >= 120 and "survive2min" not in achievements:
        achievements.add("survive2min")
        show_achievement("Выжил 2 минуты! 🏅")
    # Пример: "Обогни 5 препятствий подряд"
    if near_obstacle_streak >= 5 and "dodge5" not in achievements:
        achievements.add("dodge5")
        show_achievement("Обогнул 5 препятствий подряд! 🏅")
    # Пример: "Съешь 3 еды за 10 секунд"
    if len(last_food_times) >= 3 and last_food_times[-1] - last_food_times[-3] <= 10 and "fast3" not in achievements:
        achievements.add("fast3")
        show_achievement("3 еды за 10 секунд! 🏅")
    # Пример: "Счет 20"
    if score >= 20 and "score20" not in achievements:
        achievements.add("score20")
        show_achievement("Счет 20! 🏅")
    # Пример: "Счет 50"
    if score >= 50 and "score50" not in achievements:
        achievements.add("score50")
        show_achievement("Счет 50! 🏅")


def show_achievement(text):
    # Всплывающее уведомление
    top = tk.Toplevel(root)
    top.overrideredirect(True)
    top.geometry(f"250x50+{root.winfo_x() + 100}+{root.winfo_y() + 100}")
    tk.Label(top, text=text, font=("Arial", 14), bg="yellow").pack(expand=True, fill=tk.BOTH)
    root.after(2000, top.destroy)
    # Сохраняем ачивку
    save_achievement_to_db(text)


# Движение змейки
def move_snake():
    global near_obstacle_streak
    head_x, head_y = snake[0]

    if direction == "Up":
        new_head = (head_x, head_y - CELL_SIZE)
    elif direction == "Down":
        new_head = (head_x, head_y + CELL_SIZE)
    elif direction == "Left":
        new_head = (head_x - CELL_SIZE, head_y)
    elif direction == "Right":
        new_head = (head_x + CELL_SIZE, head_y)

    # Проверяем обход препятствий
    near = False
    for dx, dy in [(-CELL_SIZE, 0), (CELL_SIZE, 0), (0, -CELL_SIZE), (0, CELL_SIZE)]:
        if (new_head[0] + dx, new_head[1] + dy) in obstacles:
            near = True
            break
    if near:
        near_obstacle_streak += 1
    else:
        near_obstacle_streak = 0

    snake.insert(0, new_head)
    if not check_food_collision():
        snake.pop()


# Проверка на столкновение со стенами
def check_wall_collision():
    head_x, head_y = snake[0]
    return (
            head_x < 0 or head_x >= WIDTH or
            head_y < 0 or head_y >= HEIGHT
    )


# Проверка самостолкновения
def check_self_collision():
    return snake[0] in snake[1:]


# Проверка столкновения с препятствиями
def check_obstacle_collision():
    return snake[0] in obstacles


# Завершение игры
def end_game():
    global game_over, game_start_time
    game_over = True
    canvas.create_text(
        WIDTH // 2, HEIGHT // 2,
        text=f"Игра окончена! Счёт: {score}",
        fill="white",
        font=("Arial", 14)
    )

    # Показываем статистику ИИ
    if AI_MODE or AI_HELPER:
        canvas.create_text(
            WIDTH // 2, HEIGHT // 2 + 30,
            text="ИИ помогал в игре! 🤖",
            fill="cyan",
            font=("Arial", 12)
        )
    # Сохраняем статистику
    game_time = time.time() - game_start_time if game_start_time else 0
    save_game_to_db(score, len(snake), game_time)


# Обновляем заголовок
def update_title():
    title = f"Snake AI | Счёт: {score}"
    if AI_MODE:
        title += " | ИИ режим"
    if AI_HELPER:
        title += " | Подсказки"
    if SMART_OBSTACLES:
        title += " | Препятствия"
    root.title(title)


def start_countdown():
    countdown_numbers = ["3", "2", "1", "Старт!"]

    def show_next(index):
        canvas.delete("countdown")
        if index < len(countdown_numbers):
            canvas.create_rectangle(0, 0, WIDTH, HEIGHT, fill="#000", tags="countdown")
            canvas.create_text(
                WIDTH // 2, HEIGHT // 2,
                text=countdown_numbers[index],
                fill="white",
                font=("Arial", 32, "bold"),
                tags="countdown"
            )
            root.after(1000, show_next, index + 1)
        else:
            canvas.delete("countdown")
            game_loop()

    show_next(0)


# ИИ принимает решение
def ai_decision():
    global direction
    if AI_MODE and not game_over and not paused:
        # Используем A* для поиска пути
        best_direction = ai_advanced.find_path_to_food(snake, food, obstacles)
        opposites = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}
        if best_direction and best_direction != opposites.get(direction, ""):
            direction = best_direction


# Обновление подсказок ИИ
def update_ai_suggestions():
    global ai_suggestions
    if AI_HELPER:
        ai_suggestions = ai_advanced.generate_suggestions(snake, food, obstacles)


# Игровой цикл
def game_loop():
    global snake, food, score, DELAY

    if game_over or paused:
        if not game_over:
            # Показываем сообщение о паузе
            canvas.create_text(
                WIDTH // 2, HEIGHT // 2,
                text="ПАУЗА\nНажмите 'P' для продолжения",
                fill="white",
                font=("Arial", 16),
                justify="center"
            )
        return

    # ИИ принимает решение
    ai_decision()

    # Обновляем подсказки
    update_ai_suggestions()

    # Записываем ход для анализа
    if game_start_time:
        game_analyzer.record_move(snake, food, obstacles, direction, score)

    move_snake()

    # Адаптивная сложность
    if score > 0 and score % 10 == 0:
        DELAY = max(30, 100 - score * 2)
        if SMART_OBSTACLES:
            create_obstacles()

    if check_wall_collision() or check_self_collision() or check_obstacle_collision():
        end_game()
        return

    canvas.delete("all")
    draw_food()
    draw_obstacles()
    draw_snake()
    draw_ai_suggestions()
    draw_difficulty_analysis()
    update_title()
    root.after(DELAY, game_loop)


# Функции для показа стратегических советов и рекомендаций
def show_strategic_advice():
    advice = ai_advanced.generate_strategic_advice(snake, food, obstacles)
    if advice:
        messagebox.showinfo("Стратегические советы", "\n".join(advice))


def show_recommendations():
    recs = game_analyzer.get_recommendations()
    if recs:
        messagebox.showinfo("Рекомендации", "\n".join(recs))


# Первоначальная отрисовка
draw_food()
draw_obstacles()
draw_snake()

# Запускаем обратный отсчёт вместо немедленного старта игры
start_countdown()

# Запуск главного цикла программы
root.mainloop()