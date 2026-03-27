import math
import sqlite3
import time
import tkinter as tk
from random import choice, randint
from tkinter import messagebox
from tkinter import ttk

from advanced_analytics import AdvancedGameAnalytics
from ai_tools import AdvancedSnakeAI, GameAnalyzer
from game_modes import GameMode, GameModeManager
from genetic_ai import GeneticSnakeAI
from logger import error_handler, game_logger
from neural_ai import NeuralSnakeAI
from ui_enhancements import ModernUI, PerformanceMonitor, SettingsDialog

# Попытка импорта matplotlib (может не быть установлен)
try:
    import matplotlib
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    MATPLOTLIB_AVAILABLE = True
except ImportError:
    plt = None  # type: ignore[misc,assignment]
    FigureCanvasTkAgg = None  # type: ignore[misc,assignment]
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
GENETIC_MODE = False  # Режим генетического ИИ
AI_ALGORITHM = "a_star"  # Алгоритм ИИ: a_star, neural, genetic

# Глобальные переменные
last_food_times = []
near_obstacle_streak = 0
DB_PATH = 'snake_stats.db'

# Создание главного окна
root = tk.Tk()
root.title("Snake AI | Счет: 0")
root.resizable(width=False, height=False)

# Инициализация улучшенного UI и мониторинга
performance_monitor = PerformanceMonitor()
modern_ui = ModernUI(root)

# Инициализация компонентов приоритета 2
neural_ai = NeuralSnakeAI()
advanced_analytics = AdvancedGameAnalytics()
game_mode_manager = GameModeManager()

# Инициализация генетического ИИ
genetic_ai = GeneticSnakeAI(population_size=20, genome_size=50)

# Попытка загрузки обученной нейросети
neural_ai.load_model()

# Попытка загрузки обученной популяции
genetic_ai.load_population("genetic_population.pkl")


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

# --- Безопасные функции с обработкой ошибок ---
def safe_game_loop():
    """Безопасный игровой цикл с обработкой ошибок"""
    try:
        game_loop()
    except Exception as e:
        result = error_handler.handle_error(e, "Game loop error")
        if result == "restart":
            restart_game()
        else:
            # Попытка восстановления
            root.after(DELAY, safe_game_loop)

def safe_ai_decision():
    """Безопасное принятие решений ИИ"""
    try:
        ai_decision()
    except Exception as e:
        error_handler.handle_error(e, "AI decision error", show_user=False)
        # Fallback к простому алгоритму
        simple_ai_decision()

def simple_ai_decision():
    """Простой алгоритм ИИ как fallback"""
    global direction
    if AI_MODE and not game_over and not paused:
        head = snake[0]
        safe_dirs = []
        
        for dir_name in DIRECTIONS:
            new_head = get_next_position(head, dir_name)
            if is_valid_position(new_head):
                safe_dirs.append(dir_name)
        
        if safe_dirs:
            # Простая эвристика: идем в сторону еды
            dx = food[0] - head[0]
            dy = food[1] - head[1]
            
            if dx > 0 and "Right" in safe_dirs:
                direction = "Right"
            elif dx < 0 and "Left" in safe_dirs:
                direction = "Left"
            elif dy > 0 and "Down" in safe_dirs:
                direction = "Down"
            elif dy < 0 and "Up" in safe_dirs:
                direction = "Up"
            else:
                direction = choice(safe_dirs)

def get_next_position(pos, direction):
    """Получить следующую позицию при движении"""
    x, y = pos
    if direction == "Up":
        return (x, y - CELL_SIZE)
    elif direction == "Down":
        return (x, y + CELL_SIZE)
    elif direction == "Left":
        return (x - CELL_SIZE, y)
    elif direction == "Right":
        return (x + CELL_SIZE, y)
    return pos

def is_valid_position(pos):
    """Проверка валидности позиции"""
    x, y = pos
    if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT:
        return False
    if pos in snake:
        return False
    if pos in obstacles:
        return False
    return True

def safe_restart_game():
    """Безопасный перезапуск игры"""
    try:
        restart_game()
        game_logger.log_game_event("game_restart", {"score": score})
    except Exception as e:
        error_handler.handle_error(e, "Game restart error")

def safe_save_game():
    """Безопасное сохранение игры"""
    try:
        game_time = time.time() - game_start_time if game_start_time else 0
        save_game_to_db(score, len(snake), game_time)
        game_logger.log_game_event("game_saved", {
            "score": score,
            "length": len(snake),
            "duration": game_time
        })
    except Exception as e:
        error_handler.handle_error(e, "Game save error", show_user=False)


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
    """Показ окна настроек с улучшенным интерфейсом"""
    global WIDTH, HEIGHT, DELAY, INIT_OBSTACLES
    
    was_paused = paused
    if not paused:
        toggle_pause()
    
    try:
        # Создаем новый диалог настроек
        settings_dialog = SettingsDialog(root)
        root.wait_window(settings_dialog.dialog)
        
        if settings_dialog.result:
            # Применяем новые настройки
            general = settings_dialog.result['general']
            ai_settings = settings_dialog.result['ai']
            visual = settings_dialog.result['visual']
            
            # Обновляем глобальные переменные
            WIDTH = general['width']
            HEIGHT = general['height']
            DELAY = general['speed']
            INIT_OBSTACLES = general['obstacles']
            
            # Обновляем параметры ИИ
            ai_advanced.learning_rate = ai_settings['learning_rate']
            ai_advanced.exploration_rate = ai_settings['exploration_rate']
            
            # Применяем визуальные настройки
            if visual['show_hints']:
                toggle_ai_helper()
            if visual['show_analysis']:
                toggle_difficulty_analysis()
            
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
            
            # Логируем изменение настроек
            game_logger.log_user_action("settings_changed", settings_dialog.result)
            
    except Exception as e:
        error_handler.handle_error(e, "Settings window error")
    finally:
        if not was_paused:
            toggle_pause()


# --- Окно расширенной аналитики ---
def show_advanced_analytics():
    """Показ расширенной аналитики"""
    was_paused = paused
    if not paused:
        toggle_pause()
    
    try:
        analytics_window = tk.Toplevel(root)
        analytics_window.title("Расширенная аналитика")
        analytics_window.geometry("600x700")
        analytics_window.resizable(False, False)
        analytics_window.transient(root)
        analytics_window.grab_set()
        
        # Создаем notebook для вкладок
        notebook = ttk.Notebook(analytics_window)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Вкладка общей статистики
        stats_frame = ttk.Frame(notebook)
        notebook.add(stats_frame, text="Общая статистика")
        
        stats = advanced_analytics.get_advanced_stats()
        
        # Общая статистика
        overall_text = f"Всего игр: {stats['overall'].get('total_games', 0)}\n"
        overall_text += f"Лучший счет: {stats['overall'].get('best_score', 0)}\n"
        overall_text += f"Средний счет: {stats['overall'].get('avg_score', 0):.1f}\n"
        overall_text += f"Среднее время: {stats['overall'].get('avg_duration', 0):.1f} сек\n"
        
        tk.Label(stats_frame, text=overall_text, font=("Arial", 12), justify="left").pack(anchor="w", padx=10, pady=5)
        
        # Вкладка поведения игрока
        behavior_frame = ttk.Frame(notebook)
        notebook.add(behavior_frame, text="Поведение игрока")
        
        behavior = stats.get('behavior', {})
        if behavior:
            behavior_text = "Предпочтения в направлениях:\n"
            direction_prefs = behavior.get('direction_preferences', {})
            for direction, count in direction_prefs.items():
                behavior_text += f"  {direction}: {count}\n"
            
            behavior_text += f"\nАнализ риска:\n"
            risk_analysis = behavior.get('risk_analysis', {})
            behavior_text += f"  Высокий риск: {risk_analysis.get('high_risk_moves', 0)}\n"
            behavior_text += f"  Низкий риск: {risk_analysis.get('low_risk_moves', 0)}\n"
            behavior_text += f"  Среднее безопасных направлений: {risk_analysis.get('avg_safe_directions', 0):.1f}\n"
            
            tk.Label(behavior_frame, text=behavior_text, font=("Arial", 11), justify="left").pack(anchor="w", padx=10, pady=5)
        
        # Вкладка рекомендаций
        recommendations_frame = ttk.Frame(notebook)
        notebook.add(recommendations_frame, text="Рекомендации")
        
        recommendations = advanced_analytics.get_recommendations()
        if recommendations:
            rec_text = "Персонализированные рекомендации:\n\n"
            for i, rec in enumerate(recommendations, 1):
                rec_text += f"{i}. {rec}\n"
        else:
            rec_text = "Недостаточно данных для рекомендаций"
        
        tk.Label(recommendations_frame, text=rec_text, font=("Arial", 11), justify="left").pack(anchor="w", padx=10, pady=5)
        
        # Вкладка нейросети
        neural_frame = ttk.Frame(notebook)
        notebook.add(neural_frame, text="Нейросеть")
        
        neural_stats = neural_ai.get_training_stats()
        neural_text = f"Обучена: {'Да' if neural_stats['is_trained'] else 'Нет'}\n"
        neural_text += f"Образцов для обучения: {neural_stats['training_samples']}\n"
        neural_text += f"Модель сохранена: {'Да' if neural_stats['model_file_exists'] else 'Нет'}\n"
        
        tk.Label(neural_frame, text=neural_text, font=("Arial", 11), justify="left").pack(anchor="w", padx=10, pady=5)
        
        # Кнопки
        button_frame = tk.Frame(analytics_window)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        def export_report():
            filename = advanced_analytics.export_analytics_report()
            if filename:
                messagebox.showinfo("Экспорт", f"Отчет сохранен в {filename}")
        
        def train_neural():
            if neural_ai.training_data:
                success = neural_ai.train(neural_ai.training_data)
                if success:
                    messagebox.showinfo("Обучение", "Нейросеть успешно обучена!")
                else:
                    messagebox.showerror("Ошибка", "Не удалось обучить нейросеть")
            else:
                messagebox.showwarning("Предупреждение", "Недостаточно данных для обучения")
        
        tk.Button(button_frame, text="Экспорт отчета", command=export_report).pack(side='left', padx=5)
        tk.Button(button_frame, text="Обучить нейросеть", command=train_neural).pack(side='left', padx=5)
        tk.Button(button_frame, text="Закрыть", command=lambda: [analytics_window.destroy(), toggle_pause() if not was_paused else None]).pack(side='right', padx=5)
        
    except Exception as e:
        error_handler.handle_error(e, "Advanced analytics error")
        if not was_paused:
            toggle_pause()


# --- Окно выбора режима ---
def show_mode_selection():
    """Показ окна выбора режима с правильным скроллингом"""
    was_paused = paused
    if not paused:
        toggle_pause()
    
    try:
        mode_window = tk.Toplevel(root)
        mode_window.title("Выбор игрового режима")
        mode_window.geometry("550x700")
        mode_window.resizable(False, False)
        mode_window.transient(root)
        mode_window.grab_set()
        
        # Заголовок (фиксированный)
        header_frame = tk.Frame(mode_window)
        header_frame.pack(fill='x', padx=10, pady=10)
        
        tk.Label(header_frame, text="🎮 Выбор игрового режима", 
                font=("Arial", 16, "bold")).pack()
        
        tk.Label(header_frame, text="Выберите режим и нажмите 'Применить' для смены", 
                font=("Arial", 10), fg="gray").pack()
        
        # Создаем основной контейнер для скроллинга
        main_container = tk.Frame(mode_window)
        main_container.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Создаем Canvas и Scrollbar
        canvas = tk.Canvas(main_container, bg="white", highlightthickness=0)
        scrollbar = tk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        
        # Создаем фрейм для содержимого
        content_frame = tk.Frame(canvas, bg="white")
        
        # Настраиваем скроллинг
        def configure_scroll(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        content_frame.bind("<Configure>", configure_scroll)
        
        # Создаем окно в canvas для content_frame
        canvas_window = canvas.create_window((0, 0), window=content_frame, anchor="nw")
        
        # Настраиваем canvas
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Упаковываем canvas и scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Информация о текущем режиме
        current_mode = game_mode_manager.current_mode
        current_config = game_mode_manager.mode_configs[current_mode]
        
        current_info = tk.Frame(content_frame, bg="lightblue", relief="groove", bd=2)
        current_info.pack(fill='x', padx=5, pady=5)
        
        tk.Label(current_info, text=f"📋 Текущий режим: {current_config['name']}", 
                font=("Arial", 12, "bold"), fg="blue", bg="lightblue").pack(anchor='w', padx=10, pady=5)
        
        # Создаем список режимов
        available_modes = game_mode_manager.get_available_modes()
        mode_var = tk.StringVar(value=game_mode_manager.current_mode.value)
        
        # Заголовок для списка режимов
        tk.Label(content_frame, text="📝 Доступные режимы:", 
                font=("Arial", 12, "bold"), bg="white").pack(anchor='w', padx=5, pady=5)
        
        for mode_value in available_modes:
            mode = GameMode(mode_value)
            config = game_mode_manager.mode_configs[mode]
            
            # Создаем фрейм для каждого режима
            mode_frame = tk.Frame(content_frame, relief="groove", bd=2, bg="white")
            mode_frame.pack(fill='x', padx=5, pady=3)
            
            # Радиокнопка с названием режима
            radio_frame = tk.Frame(mode_frame, bg="white")
            radio_frame.pack(fill='x', padx=10, pady=5)
            
            tk.Radiobutton(
                radio_frame, 
                text=f"🎮 {config['name']}", 
                variable=mode_var, 
                value=mode_value,
                font=("Arial", 12, "bold"),
                bg="white"
            ).pack(anchor='w')
            
            # Описание режима
            desc_frame = tk.Frame(mode_frame, bg="white")
            desc_frame.pack(fill='x', padx=25, pady=2)
            
            tk.Label(desc_frame, text=config['description'], 
                    font=("Arial", 10), fg="gray", justify="left", bg="white").pack(anchor='w')
            
            # Детали режима
            details_frame = tk.Frame(mode_frame, bg="white")
            details_frame.pack(fill='x', padx=25, pady=2)
            
            details = []
            if config['time_limit']:
                details.append(f"⏱ Время: {config['time_limit']} сек")
            if config['obstacles']:
                details.append("🚧 Препятствия: Да")
            else:
                details.append("🚧 Препятствия: Нет")
            if config['speed_increase']:
                details.append("⚡ Увеличение скорости: Да")
            else:
                details.append("⚡ Увеличение скорости: Нет")
            
            for detail in details:
                tk.Label(details_frame, text=f"  • {detail}", 
                        font=("Arial", 9), fg="darkgreen", bg="white").pack(anchor='w')
        
        # Настраиваем ширину canvas
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Устанавливаем ширину окна canvas равной ширине content_frame
            canvas.itemconfig(canvas_window, width=event.width)
        
        content_frame.bind("<Configure>", on_frame_configure)
        
        # Настраиваем прокрутку мышью
        def on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        # Функции для кнопок
        def apply_mode():
            selected_mode = mode_var.get()
            if selected_mode != game_mode_manager.current_mode.value:
                # Показываем сообщение о смене режима
                selected_config = game_mode_manager.mode_configs[GameMode(selected_mode)]
                messagebox.showinfo("Смена режима", 
                                  f"Режим изменен на: {selected_config['name']}\n\n"
                                  f"Игра будет перезапущена с новыми настройками.")
                
                # Устанавливаем новый режим
                game_mode_manager.set_mode(selected_mode)
                
                # Перезапускаем игру
                restart_game()
                
                # Обновляем заголовок окна
                mode_window.title(f"Режим: {selected_config['name']}")
                
                # Логируем смену режима
                game_logger.log_user_action("mode_changed", {
                    "old_mode": game_mode_manager.current_mode.value,
                    "new_mode": selected_mode
                })
            else:
                # Если режим не изменился, просто закрываем окно
                messagebox.showinfo("Режим", "Режим не изменился")
            
            # Отключаем обработчик мыши
            canvas.unbind_all("<MouseWheel>")
            mode_window.destroy()
            if not was_paused:
                toggle_pause()
        
        def cancel():
            # Отключаем обработчик мыши
            canvas.unbind_all("<MouseWheel>")
            mode_window.destroy()
            if not was_paused:
                toggle_pause()
        
        # Кнопки (фиксированные внизу)
        button_frame = tk.Frame(mode_window)
        button_frame.pack(fill='x', padx=10, pady=10)
        
        # Кнопка отмены
        cancel_btn = tk.Button(button_frame, text="❌ Отмена", command=cancel, 
                             font=("Arial", 10), bg="lightcoral")
        cancel_btn.pack(side='left', padx=5)
        
        # Кнопка применения
        apply_btn = tk.Button(button_frame, text="✅ Применить и перезапустить", 
                            command=apply_mode, font=("Arial", 10, "bold"), bg="lightgreen")
        apply_btn.pack(side='right', padx=5)
        
        # Подсказка
        hint_frame = tk.Frame(mode_window)
        hint_frame.pack(fill='x', padx=10, pady=5)
        
        tk.Label(hint_frame, text="💡 Совет: Используйте колесо мыши для прокрутки списка режимов", 
                font=("Arial", 9), fg="blue").pack()
        
        # Обработчик закрытия окна
        def on_closing():
            canvas.unbind_all("<MouseWheel>")
            mode_window.destroy()
            if not was_paused:
                toggle_pause()
        
        mode_window.protocol("WM_DELETE_WINDOW", on_closing)
        
    except Exception as e:
        error_handler.handle_error(e, "Mode selection error")
        if not was_paused:
            toggle_pause()


# --- Интеграция ИИ ---
ai_advanced = AdvancedSnakeAI()
game_analyzer = GameAnalyzer()


# --- ФУНКЦИИ УПРАВЛЕНИЯ ---
def restart_game():
    global snake, direction, food, score, game_over, paused, obstacles, ai_suggestions, game_start_time
    global ai_snake, ai_direction, ai_score  # Добавляем переменные ИИ
    
    # Начальное положение змейки
    snake = create_snake()
    direction = "Right"
    
    # Инициализация змейки ИИ
    ai_snake = create_ai_snake()
    ai_direction = "Left"
    ai_score = 0
    
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
    draw_ai_snake()  # Отрисовываем змейку ИИ
    update_title()
    update_mode_button()  # Обновляем кнопку режимов
    
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


def toggle_ai_algorithm():
    """Переключение алгоритма ИИ"""
    global AI_ALGORITHM
    algorithms = ["a_star", "neural", "genetic"]
    current_idx = algorithms.index(AI_ALGORITHM)
    AI_ALGORITHM = algorithms[(current_idx + 1) % len(algorithms)]
    
    labels = {"a_star": "A*", "neural": "🧠 Нейро", "genetic": "🧬 Генет"}
    colors = {"a_star": "SystemButtonFace", "neural": "lightblue", "genetic": "lightgreen"}
    
    ai_algo_btn.config(
        text=f"{labels[AI_ALGORITHM]}",
        bg=colors[AI_ALGORITHM]
    )
    
    game_logger.log_user_action("ai_algorithm_changed", {"algorithm": AI_ALGORITHM})


def update_mode_button():
    """Обновляет текст кнопки режимов"""
    mode_info = game_mode_manager.get_mode_display_info()
    mode_btn.config(
        text=f"🎮 {mode_info['name']}",
        bg="lightblue"
    )


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

# Кнопка переключения алгоритма ИИ
ai_algo_btn = tk.Button(ai_buttons_frame, text="🧬 A*", command=toggle_ai_algorithm)
ai_algo_btn.pack(side=tk.LEFT, padx=2)

# Кнопка статистики в меню
stats_btn = tk.Button(ai_buttons_frame, text="📈 Статистика", command=show_stats_window)
stats_btn.pack(side=tk.LEFT, padx=2)

# Кнопка расширенной аналитики
analytics_btn = tk.Button(ai_buttons_frame, text="📊 Аналитика", command=show_advanced_analytics)
analytics_btn.pack(side=tk.LEFT, padx=2)

# Кнопка выбора режима
mode_btn = tk.Button(ai_buttons_frame, text="🎮 Режимы", command=show_mode_selection)
mode_btn.pack(side=tk.LEFT, padx=2)

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
direction: str = "Right"
food: tuple[int, int] | None = None
score: int = 0
game_over: bool = False
paused: bool = False
obstacles: list[tuple[int, int]] = []
ai_suggestions: list[str] = []
game_start_time: float | None = None
achievements: set[str] = set()
last_food_times: list[float] = []
near_obstacle_streak: int = 0

# Переменные для битвы с ИИ
ai_snake: list[tuple[int, int]] = []
ai_direction: str = "Left"
ai_score: int = 0
ai_food = None


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


def create_ai_snake():
    """Создание змейки ИИ в противоположном углу"""
    # Размещаем ИИ в левом верхнем углу
    x = randint(0, 3) * CELL_SIZE
    y = randint(0, 3) * CELL_SIZE
    
    # Создаем змейку ИИ, направленную влево
    return [(x, y), (x + CELL_SIZE, y), (x + 2 * CELL_SIZE, y)]


snake = create_snake()
ai_snake = create_ai_snake()


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
    if food is None:
        return
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


def draw_ai_snake():
    """Отрисовка змейки ИИ"""
    for index, segment in enumerate(ai_snake):
        canvas.create_rectangle(
            segment[0], segment[1],
            segment[0] + CELL_SIZE,
            segment[1] + CELL_SIZE,
            fill="red" if index == 0 else "darkred",
            outline="maroon"
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


def draw_ai_battle_events():
    """Отрисовка событий битвы с ИИ"""
    if game_mode_manager.current_mode == GameMode.AI_BATTLE:
        special_events = game_mode_manager.mode_state.get('special_events', [])
        current_time = time.time()
        
        # Показываем последние 3 события
        recent_events = [event for event in special_events 
                        if current_time - event['timestamp'] < 3]
        
        y_offset = 80
        for event in recent_events[-3:]:
            color = "orange" if event['type'] == 'ai_score' else "yellow"
            canvas.create_text(
                10, y_offset,
                text=event['message'],
                fill=color,
                font=("Arial", 10, "bold"),
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
    new_head: tuple[int, int] = (head_x, head_y)  # default value

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


def move_ai_snake():
    """Движение змейки ИИ"""
    global ai_direction, ai_score
    
    # ИИ принимает решение о направлении
    ai_decision_for_battle()
    
    head_x, head_y = ai_snake[0]
    new_head: tuple[int, int] = (head_x, head_y)  # default value

    if ai_direction == "Up":
        new_head = (head_x, head_y - CELL_SIZE)
    elif ai_direction == "Down":
        new_head = (head_x, head_y + CELL_SIZE)
    elif ai_direction == "Left":
        new_head = (head_x - CELL_SIZE, head_y)
    elif ai_direction == "Right":
        new_head = (head_x + CELL_SIZE, head_y)

    # Проверяем валидность позиции для ИИ
    if is_valid_position_for_ai(new_head):
        ai_snake.insert(0, new_head)
        if not check_ai_food_collision():
            ai_snake.pop()


def is_valid_position_for_ai(pos):
    """Проверка валидности позиции для змейки ИИ"""
    x, y = pos
    if x < 0 or x >= WIDTH or y < 0 or y >= HEIGHT:
        return False
    if pos in ai_snake:
        return False
    if pos in snake:  # ИИ не может пересекаться с игроком
        return False
    if pos in obstacles:
        return False
    return True


def ai_decision_for_battle():
    """ИИ принимает решение для битвы"""
    global ai_direction
    
    if not ai_snake or not food:
        return
    
    head = ai_snake[0]
    
    # Простой алгоритм: ИИ идет к еде
    dx = food[0] - head[0]
    dy = food[1] - head[1]
    
    # Определяем приоритетное направление
    if abs(dx) > abs(dy):
        # Горизонтальное движение приоритетнее
        if dx > 0 and is_valid_position_for_ai((head[0] + CELL_SIZE, head[1])):
            ai_direction = "Right"
        elif dx < 0 and is_valid_position_for_ai((head[0] - CELL_SIZE, head[1])):
            ai_direction = "Left"
        elif dy > 0 and is_valid_position_for_ai((head[0], head[1] + CELL_SIZE)):
            ai_direction = "Down"
        elif dy < 0 and is_valid_position_for_ai((head[0], head[1] - CELL_SIZE)):
            ai_direction = "Up"
    else:
        # Вертикальное движение приоритетнее
        if dy > 0 and is_valid_position_for_ai((head[0], head[1] + CELL_SIZE)):
            ai_direction = "Down"
        elif dy < 0 and is_valid_position_for_ai((head[0], head[1] - CELL_SIZE)):
            ai_direction = "Up"
        elif dx > 0 and is_valid_position_for_ai((head[0] + CELL_SIZE, head[1])):
            ai_direction = "Right"
        elif dx < 0 and is_valid_position_for_ai((head[0] - CELL_SIZE, head[1])):
            ai_direction = "Left"
    
    # Если нет безопасного пути к еде, ищем альтернативный путь
    if not is_valid_position_for_ai(get_next_position(head, ai_direction)):
        # Пробуем другие направления
        for test_direction in ["Up", "Down", "Left", "Right"]:
            if is_valid_position_for_ai(get_next_position(head, test_direction)):
                ai_direction = test_direction
                break


def check_ai_food_collision():
    """Проверка съедения еды змейкой ИИ"""
    global food, ai_score
    if ai_snake[0] == food:
        ai_score += 1
        food = create_food()
        return True
    return False


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
    """Завершение игры с расширенной аналитикой"""
    global game_over, game_start_time
    game_over = True  # Больше не обновляем игру
    
    try:
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
        
        # Записываем данные в расширенную аналитику
        game_time = time.time() - game_start_time if game_start_time else 0
        advanced_analytics.record_game_end(score, game_time, AI_MODE)
        
        # Безопасное сохранение статистики
        safe_save_game()
        
        # Логируем завершение игры
        game_logger.log_game_event("game_ended", {
            "score": score,
            "length": len(snake),
            "duration": game_time,
            "ai_mode": AI_MODE,
            "ai_helper": AI_HELPER,
            "game_mode": game_mode_manager.current_mode.value
        })
        
        # Сброс счетчика ошибок при успешном завершении
        error_handler.reset_error_count()
        
        # Попытка переобучения нейросети
        if neural_ai.is_trained and len(neural_ai.training_data) > neural_ai.min_training_samples:
            neural_ai.retrain_if_needed()
        
    except Exception as e:
        error_handler.handle_error(e, "Game end error")


def end_game_with_message(message):
    """Завершение игры с специальным сообщением"""
    global game_over
    game_over = True
    
    try:
        # Показываем основное сообщение
        canvas.create_text(
            WIDTH // 2, HEIGHT // 2,
            text=message or f"Игра окончена! Счёт: {score}",
            fill="white",
            font=("Arial", 14)
        )
        
        # Показываем результат битвы с ИИ
        if game_mode_manager.current_mode == GameMode.AI_BATTLE:
            canvas.create_text(
                WIDTH // 2, HEIGHT // 2 + 40,
                text=f"🎮 Игрок: {score} | 🤖 ИИ: {ai_score}",
                fill="cyan",
                font=("Arial", 12)
            )
        
        # Записываем данные в расширенную аналитику
        game_time = time.time() - game_start_time if game_start_time else 0
        advanced_analytics.record_game_end(score, game_time, AI_MODE)
        
        # Логируем завершение игры
        game_logger.log_game_event("game_ended_with_message", {
            "score": score,
            "message": message,
            "mode": game_mode_manager.current_mode.value,
            "ai_score": ai_score if game_mode_manager.current_mode == GameMode.AI_BATTLE else 0
        })
        
    except Exception as e:
        error_handler.handle_error(e, "Game end with message error")

def draw_mode_info():
    """Отрисовка информации о режиме"""
    mode_info = game_mode_manager.get_mode_display_info()
    
    # Отображаем информацию о режиме в правом верхнем углу
    info_text = f"🎮 {mode_info['name']}"
    
    if mode_info['time_remaining']:
        minutes = int(mode_info['time_remaining'] // 60)
        seconds = int(mode_info['time_remaining'] % 60)
        info_text += f"\n⏱ {minutes:02d}:{seconds:02d}"
    
    if mode_info['difficulty_level'] > 1:
        info_text += f"\n📈 Уровень: {mode_info['difficulty_level']}"
    
    if mode_info['speed_multiplier'] > 1.0:
        info_text += f"\n⚡ Скорость: x{mode_info['speed_multiplier']:.1f}"
    
    if mode_info['score_multiplier'] > 1.0:
        info_text += f"\n🏆 Множитель: x{mode_info['score_multiplier']:.1f}"
    
    # Специальная информация для режима AI_BATTLE
    if game_mode_manager.current_mode == GameMode.AI_BATTLE:
        mode_ai_score = mode_info.get('ai_score', 0)
        ai_efficiency = mode_info.get('ai_efficiency', 0.0)
        battle_time = mode_info.get('battle_time_remaining', 0)
        
        info_text += f"\n🤖 ИИ: {mode_ai_score} очков"
        info_text += f"\n📊 Эффективность ИИ: {ai_efficiency:.1%}"
        
        if battle_time > 0:
            minutes = int(battle_time // 60)
            seconds = int(battle_time % 60)
            info_text += f"\n⏱ Битва: {minutes:02d}:{seconds:02d}"
    
    # Показываем счет ИИ в режиме битвы
    if game_mode_manager.current_mode == GameMode.AI_BATTLE:
        info_text += f"\n🎮 Игрок: {score} | 🤖 ИИ: {ai_score}"
    
    canvas.create_text(
        WIDTH - 10, 50,
        text=info_text,
        fill="cyan",
        font=("Arial", 10, "bold"),
        anchor="ne"
    )


# Обновляем заголовок
def update_title():
    mode_info = game_mode_manager.get_mode_display_info()
    title = f"Snake AI | Счёт: {score} | 🎮 {mode_info['name']}"
    
    if AI_MODE:
        title += " | 🤖 ИИ режим"
    if AI_HELPER:
        title += " | 💡 Подсказки"
    if SMART_OBSTACLES:
        title += " | 🚧 Препятствия"
    
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
    """ИИ принимает решение с использованием различных алгоритмов"""
    global direction
    if AI_MODE and not game_over and not paused and food is not None:
        try:
            # Записываем данные для аналитики
            advanced_analytics.record_move(snake, food, obstacles, direction, score)
            
            # Выбор алгоритма на основе настроек
            if AI_ALGORITHM == "genetic":
                # Использование генетического алгоритма
                best_genome = genetic_ai.get_best_genome()
                genetic_decision = genetic_ai.get_decision(best_genome, snake, food, obstacles)
                if genetic_decision:
                    opposites = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}
                    if genetic_decision != opposites.get(direction, ""):
                        direction = genetic_decision
                        game_logger.log_ai_decision(genetic_decision, {
                            "ai_type": "genetic",
                            "generation": genetic_ai.generation
                        })
                        return
            
            elif AI_ALGORITHM == "neural":
                # Попытка использования нейросети
                neural_decision = neural_ai.predict_best_action(snake, food, obstacles)
                
                if neural_decision and neural_ai.is_trained:
                    opposites = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}
                    if neural_decision != opposites.get(direction, ""):
                        direction = neural_decision
                        game_logger.log_ai_decision(neural_decision, {
                            "ai_type": "neural_network",
                            "snake_length": len(snake),
                            "food_distance": math.sqrt((food[0] - snake[0][0])**2 + (food[1] - snake[0][1])**2)
                        })
                        
                        reward = 1.0 if check_food_collision() else 0.1
                        neural_ai.add_training_data(snake, food, obstacles, neural_decision, reward)
                        return
            
            # Fallback к A* алгоритму (по умолчанию)
            path = ai_advanced.a_star_pathfinding(snake, food, obstacles)
            if path and len(path) > 0:
                next_pos = path[0]
                head = snake[0]
                dx, dy = next_pos[0] - head[0], next_pos[1] - head[1]
                if dx > 0:
                    best_direction = "Right"
                elif dx < 0:
                    best_direction = "Left"
                elif dy > 0:
                    best_direction = "Down"
                elif dy < 0:
                    best_direction = "Up"
                else:
                    best_direction = direction
                opposites = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}
                if best_direction != opposites.get(direction, ""):
                    direction = best_direction
                    game_logger.log_ai_decision(best_direction, {
                        "ai_type": "a_star",
                        "snake_length": len(snake),
                        "food_distance": math.sqrt((food[0] - head[0])**2 + (food[1] - head[1])**2)
                    })
            else:
                best_direction = ai_advanced.find_path_to_food(snake, food, obstacles)
                opposites = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}
                if best_direction and best_direction != opposites.get(direction, ""):
                    direction = best_direction
                    game_logger.log_ai_decision(best_direction, {"ai_type": "simple", "fallback": True})
                    
        except Exception as e:
            error_handler.handle_error(e, "AI decision error", show_user=False)
            simple_ai_decision()


# Обновление подсказок ИИ
def update_ai_suggestions():
    global ai_suggestions
    if AI_HELPER:
        ai_suggestions = ai_advanced.generate_suggestions(snake, food, obstacles)


# Игровой цикл
def game_loop():
    """Игровой цикл с поддержкой режимов и аналитики"""
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

    try:
        # Засекаем время начала кадра
        frame_start = time.time()
        
        # Обновляем состояние игрового режима
        game_state = {
            'score': score,
            'snake_length': len(snake),
            'obstacles_count': len(obstacles),
            'ai_mode': AI_MODE
        }
        game_mode_manager.update_mode_state(game_state)
        
        # Проверяем условия режима
        mode_conditions = game_mode_manager.check_mode_conditions(game_state)
        if mode_conditions['game_over']:
            end_game_with_message(mode_conditions['special_message'])
            return
        
        # ИИ принимает решение
        safe_ai_decision()
        
        # Обновляем подсказки
        update_ai_suggestions()

        move_snake()  # Двигаем змейку
        
        # Двигаем змейку ИИ в режиме битвы
        if game_mode_manager.current_mode == GameMode.AI_BATTLE:
            move_ai_snake()

        # Адаптивная сложность на основе режима
        mode_config = game_mode_manager.get_mode_config()
        if mode_config['speed_increase']:
            speed_multiplier = game_mode_manager.mode_state['speed_multiplier']
            DELAY = max(30, int(100 / speed_multiplier))
        
        # Обновление препятствий для режимов с препятствиями
        if mode_config['obstacles']:
            obstacle_count = game_mode_manager.mode_state['obstacle_count']
            if len(obstacles) != obstacle_count:
                create_obstacles()

        if check_wall_collision() or check_self_collision() or check_obstacle_collision():
            end_game()
            return

        canvas.delete("all")  # Очищаем холст
        draw_food()  # Рисуем еду
        draw_obstacles()  # Рисуем препятствия
        draw_snake()  # Рисуем змейку
        draw_ai_snake()  # Рисуем змейку ИИ
        draw_ai_suggestions()  # Рисуем подсказки
        draw_ai_battle_events()  # Рисуем события битвы с ИИ
        draw_difficulty_analysis()  # Рисуем анализ сложности
        draw_mode_info()  # Рисуем информацию о режиме
        update_title()  # Обновляем заголовок
        
        # Мониторинг производительности
        frame_time = time.time() - frame_start
        performance_monitor.record_frame(frame_time)
        
        # Обновление UI
        fps = performance_monitor.get_fps()
        modern_ui.update_fps(fps)
        
        # Расширенная информация в статусе
        mode_info = game_mode_manager.get_mode_display_info()
        status_text = f"Счет: {score} | Длина: {len(snake)} | FPS: {fps:.1f}"
        if mode_info['time_remaining']:
            status_text += f" | Время: {mode_info['time_remaining']:.0f}s"
        modern_ui.update_status(status_text)
        
        # Логируем производительность
        game_logger.log_performance("game_loop", frame_time)
        
        root.after(DELAY, safe_game_loop)  # Повторяем через DELAY мс
        
    except Exception as e:
        result = error_handler.handle_error(e, "Game loop error")
        if result == "restart":
            safe_restart_game()
        else:
            # Попытка восстановления
            root.after(DELAY, safe_game_loop)


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

# Инициализация кнопки режимов
update_mode_button()

# Запускаем обратный отсчёт вместо немедленного старта игры
start_countdown()

# Запуск главного цикла программы
root.mainloop()