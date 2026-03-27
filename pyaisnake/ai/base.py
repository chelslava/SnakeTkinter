import heapq
import math
import random
import time
from functools import lru_cache


class AdvancedSnakeAI:
    """Продвинутый ИИ для игры Snake с различными алгоритмами"""

    def __init__(self):
        self.memory = {}  # Кэш для запоминания решений
        self.learning_rate = 0.1
        self.exploration_rate = 0.2
        self.path_cache = {}  # Кэш для путей
        self.cache_size_limit = 1000

    def a_star_pathfinding_optimized(self, snake, food, obstacles, max_iterations=500):
        """Оптимизированный A* с приоритетной очередью и кэшированием"""
        start = snake[0]
        goal = food

        if start == goal:
            return []

        # Проверяем кэш
        cache_key = self.create_cache_key(snake, food, obstacles)
        if cache_key in self.path_cache:
            return self.path_cache[cache_key]

        # Используем heapq для эффективной работы с приоритетной очередью
        open_set = [(0, start)]  # (f_score, position)
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}
        closed_set = set()  # Для оптимизации

        iterations = 0

        while open_set and iterations < max_iterations:
            iterations += 1
            current_f, current = heapq.heappop(open_set)

            if current in closed_set:
                continue

            closed_set.add(current)

            if current == goal:
                path = self.reconstruct_path(came_from, current)
                # Сохраняем в кэш
                self.path_cache[cache_key] = path
                self.manage_cache_size()
                return path

            # Оптимизация: проверяем только валидные соседние позиции
            for direction in ["Up", "Down", "Left", "Right"]:
                neighbor = self.get_next_position(current, direction)

                if not self.is_valid_position(neighbor, snake, obstacles):
                    continue

                if neighbor in closed_set:
                    continue

                tentative_g = g_score[current] + 1

                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g
                    f_score[neighbor] = tentative_g + self.heuristic(neighbor, goal)

                    heapq.heappush(open_set, (f_score[neighbor], neighbor))

        # Путь не найден
        self.path_cache[cache_key] = None
        self.manage_cache_size()
        return None

    def create_cache_key(self, snake, food, obstacles):
        """Создание ключа для кэширования путей"""
        head = snake[0]
        # Упрощенный ключ для экономии памяти
        return f"{head}_{food}_{len(obstacles)}"

    def manage_cache_size(self):
        """Управление размером кэша"""
        if len(self.path_cache) > self.cache_size_limit:
            # Удаляем старые записи
            old_keys = list(self.path_cache.keys())[:self.cache_size_limit // 2]
            for key in old_keys:
                del self.path_cache[key]

    # pylint: disable=no-self-argument
    @staticmethod
    @lru_cache(maxsize=1000)
    def cached_heuristic(pos1, pos2):
        """Кэшированная эвристическая функция"""
        return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

    def a_star_pathfinding(self, snake, food, obstacles, max_iterations=1000):
        """Алгоритм A* для поиска кратчайшего пути к еде (оптимизированная версия)"""
        return self.a_star_pathfinding_optimized(snake, food, obstacles, max_iterations)

    def heuristic(self, pos1, pos2):
        """Манхэттенское расстояние между двумя точками"""
        return self.cached_heuristic(pos1, pos2)

    def get_next_position(self, pos, direction):
        """Получить следующую позицию при движении в заданном направлении"""
        x, y = pos
        cell_size = 10  # Размер клетки

        if direction == "Up":
            return (x, y - cell_size)
        elif direction == "Down":
            return (x, y + cell_size)
        elif direction == "Left":
            return (x - cell_size, y)
        elif direction == "Right":
            return (x + cell_size, y)
        return pos

    def is_valid_position(self, pos, snake, obstacles):
        """Проверка валидности позиции"""
        x, y = pos
        width, height = 400, 400  # Размеры игрового поля

        # Проверка границ
        if x < 0 or x >= width or y < 0 or y >= height:
            return False

        # Проверка столкновения с змеей
        if pos in snake:
            return False

        # Проверка столкновения с препятствиями
        return pos not in obstacles

    def reconstruct_path(self, came_from, current):
        """Восстановление пути из словаря came_from"""
        path = []
        while current in came_from:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path

    def predict_future_collisions(self, snake, direction, obstacles, steps=5):
        """Предсказание будущих столкновений"""
        head = snake[0]
        future_positions = []
        current_pos = head

        for _step in range(steps):
            current_pos = self.get_next_position(current_pos, direction)
            if not self.is_valid_position(current_pos, snake, obstacles):
                return True  # Столкновение предсказано
            future_positions.append(current_pos)

        return False

    def calculate_survival_probability(self, snake, food, obstacles):
        """Расчет вероятности выживания"""
        head = snake[0]
        safe_directions = 0
        total_directions = 4

        for direction in ["Up", "Down", "Left", "Right"]:
            next_pos = self.get_next_position(head, direction)
            if self.is_valid_position(next_pos, snake, obstacles):
                safe_directions += 1

        # Базовая вероятность выживания
        survival_prob = safe_directions / total_directions

        # Корректировка на основе длины змеи
        snake_length_factor = max(0.5, 1 - len(snake) * 0.02)

        # Корректировка на основе количества препятствий
        obstacle_factor = max(0.3, 1 - len(obstacles) * 0.1)

        return survival_prob * snake_length_factor * obstacle_factor

    def generate_strategic_advice(self, snake, food, obstacles):
        """Генерация стратегических советов"""
        advice = []
        snake[0]

        # Анализ текущей ситуации
        survival_prob = self.calculate_survival_probability(snake, food, obstacles)

        if survival_prob < 0.3:
            advice.append("🚨 КРИТИЧЕСКАЯ СИТУАЦИЯ! Ищите безопасный путь!")
        elif survival_prob < 0.6:
            advice.append("⚠️ Осторожно! Ограниченное пространство для маневра")

        # Анализ пути к еде
        path = self.a_star_pathfinding(snake, food, obstacles)
        if path:
            path_length = len(path)
            if path_length > 20:
                advice.append("📏 Длинный путь к еде - возможно, стоит поискать альтернативы")
            elif path_length < 5:
                advice.append("🎯 Еда близко! Будьте точны в движениях")
        else:
            advice.append("❌ Прямой путь к еде заблокирован")

        # Анализ свободного пространства
        free_space = self.calculate_free_space(snake, obstacles)
        if free_space < 50:
            advice.append("📦 Мало свободного места - планируйте движения заранее")

        return advice

    def calculate_free_space(self, snake, obstacles):
        """Подсчет свободного пространства"""
        total_cells = (400 // 10) * (400 // 10)  # Общее количество клеток
        occupied = len(snake) + len(obstacles)
        return total_cells - occupied

    def adaptive_difficulty_analysis(self, snake, food, obstacles, score):
        """Адаптивный анализ сложности с учетом счета"""
        base_difficulty = self.calculate_base_difficulty(snake, food, obstacles)

        # Корректировка на основе счета
        score_factor = min(1.5, 1 + score * 0.05)

        # Корректировка на основе времени игры (если доступно)
        time_factor = 1.0  # Можно добавить отслеживание времени

        final_difficulty = base_difficulty * score_factor * time_factor

        return min(100, final_difficulty)

    def calculate_base_difficulty(self, snake, food, obstacles):
        """Базовый расчет сложности"""
        head = snake[0]

        # Факторы сложности
        factors = {
            'snake_length': min(30, len(snake) * 2),
            'obstacles': len(obstacles) * 5,
            'space_constraint': max(0, 50 - self.calculate_free_space(snake, obstacles) / 2),
            'food_distance': min(20, math.sqrt((food[0] - head[0]) ** 2 + (food[1] - head[1]) ** 2) / 10),
            'mobility': max(0, 20 - len(self.get_safe_directions(snake, food, obstacles)) * 5)
        }

        return sum(factors.values())

    def get_safe_directions(self, snake, food, obstacles):
        """Получить безопасные направления движения"""
        head = snake[0]
        safe_dirs = []

        for direction in ["Up", "Down", "Left", "Right"]:
            next_pos = self.get_next_position(head, direction)
            if self.is_valid_position(next_pos, snake, obstacles):
                safe_dirs.append(direction)

        return safe_dirs

    def reinforcement_learning_decision(self, snake, food, obstacles, state_key):
        """Принятие решения на основе простого обучения с подкреплением"""
        if state_key not in self.memory:
            self.memory[state_key] = {'Up': 0, 'Down': 0, 'Left': 0, 'Right': 0}

        # Выбор действия (exploration vs exploitation)
        if random.random() < self.exploration_rate:
            # Исследование - случайный выбор
            safe_dirs = self.get_safe_directions(snake, food, obstacles)
            if safe_dirs:
                return random.choice(safe_dirs)
        else:
            # Эксплуатация - выбор лучшего действия
            safe_dirs = self.get_safe_directions(snake, food, obstacles)
            if safe_dirs:
                best_action = max(safe_dirs, key=lambda d: self.memory[state_key][d])
                return best_action

        return None

    def update_memory(self, state_key, action, reward):
        """Обновление памяти на основе полученной награды"""
        if state_key in self.memory and action in self.memory[state_key]:
            current_value = self.memory[state_key][action]
            self.memory[state_key][action] = current_value + self.learning_rate * (reward - current_value)

    def create_state_key(self, snake, food, obstacles):
        """Создание ключа состояния для обучения"""
        head = snake[0]
        food_direction = self.get_relative_direction(head, food)
        obstacle_directions = [self.get_relative_direction(head, obs) for obs in obstacles[:3]]

        return f"{food_direction}_{'_'.join(obstacle_directions)}_{len(snake)}"

    def get_relative_direction(self, from_pos, to_pos):
        """Получить относительное направление между двумя точками"""
        dx = to_pos[0] - from_pos[0]
        dy = to_pos[1] - from_pos[1]

        if abs(dx) > abs(dy):
            return "Right" if dx > 0 else "Left"
        else:
            return "Down" if dy > 0 else "Up"

    def find_path_to_food(self, snake, food, obstacles):
        """Найти путь к еде используя A* или простой алгоритм"""
        # Сначала пробуем A*
        path = self.a_star_pathfinding(snake, food, obstacles)
        if path and len(path) > 0:
            next_pos = path[0]
            head = snake[0]
            dx, dy = next_pos[0] - head[0], next_pos[1] - head[1]
            if dx > 0:
                return "Right"
            elif dx < 0:
                return "Left"
            elif dy > 0:
                return "Down"
            elif dy < 0:
                return "Up"

        # Fallback: простая эвристика
        head = snake[0]
        safe_dirs = self.get_safe_directions(snake, food, obstacles)

        if not safe_dirs:
            return None

        # Простая эвристика: идем в сторону еды, если это безопасно
        dx = food[0] - head[0]
        dy = food[1] - head[1]

        # Горизонтальное движение
        if dx > 0 and "Right" in safe_dirs:
            return "Right"
        elif dx < 0 and "Left" in safe_dirs:
            return "Left"

        # Вертикальное движение
        if dy > 0 and "Down" in safe_dirs:
            return "Down"
        elif dy < 0 and "Up" in safe_dirs:
            return "Up"

        # Если прямой путь невозможен, выбираем случайное безопасное направление
        return random.choice(safe_dirs) if safe_dirs else None

    def generate_suggestions(self, snake, food, obstacles):
        """Генерировать подсказки для игрока"""
        suggestions = []
        head = snake[0]
        safe_dirs = self.get_safe_directions(snake, food, obstacles)

        if not safe_dirs:
            suggestions.append("⚠️ Опасность! Нет безопасных направлений")
            return suggestions

        # Подсказка о направлении к еде
        best_dir = self.find_path_to_food(snake, food, obstacles)
        if best_dir:
            suggestions.append(f"🎯 Рекомендуемое направление: {best_dir}")

        # Подсказка о количестве безопасных направлений
        if len(safe_dirs) <= 2:
            suggestions.append(f"⚠️ Только {len(safe_dirs)} безопасных направления")

        # Подсказка о расстоянии до еды
        distance = math.sqrt((food[0] - head[0]) ** 2 + (food[1] - head[1]) ** 2)
        if distance > 100:
            suggestions.append("📏 Еда далеко, будьте осторожны")

        return suggestions

    def analyze_difficulty(self, snake, food, obstacles):
        """Анализ сложности текущей ситуации"""
        return self.calculate_base_difficulty(snake, food, obstacles)

    def count_free_space(self, snake, obstacles):
        """Подсчитать свободное пространство"""
        total_cells = (400 // 10) * (400 // 10)
        occupied_cells = len(snake) + len(obstacles)
        return total_cells - occupied_cells


class GameAnalyzer:
    """Анализатор игровых данных"""

    def __init__(self):
        self.game_history = []
        self.performance_metrics = {}

    def record_move(self, snake, food, obstacles, direction, score, timestamp=None):
        """Запись хода в историю"""
        if timestamp is None:
            timestamp = time.time()

        move_data = {
            'timestamp': timestamp,
            'snake_length': len(snake),
            'score': score,
            'direction': direction,
            'food_distance': math.sqrt((food[0] - snake[0][0]) ** 2 + (food[1] - snake[0][1]) ** 2),
            'obstacles_count': len(obstacles),
            'head_position': snake[0]
        }

        self.game_history.append(move_data)

    def analyze_performance(self):
        """Анализ производительности игры"""
        if not self.game_history:
            return {}

        metrics = {
            'total_moves': len(self.game_history),
            'max_score': max(move['score'] for move in self.game_history),
            'max_snake_length': max(move['snake_length'] for move in self.game_history),
            'avg_food_distance': sum(move['food_distance'] for move in self.game_history) / len(self.game_history),
            'direction_preference': self.analyze_direction_preference(),
            'efficiency_score': self.calculate_efficiency_score()
        }

        return metrics

    def analyze_direction_preference(self):
        """Анализ предпочтений в направлениях движения"""
        directions = [move['direction'] for move in self.game_history]
        direction_counts = {}

        for direction in directions:
            direction_counts[direction] = direction_counts.get(direction, 0) + 1

        return direction_counts

    def calculate_efficiency_score(self):
        """Расчет эффективности игры"""
        if len(self.game_history) < 2:
            return 0

        # Эффективность = (максимальный счет) / (общее количество ходов)
        max_score = max(move['score'] for move in self.game_history)
        total_moves = len(self.game_history)

        return max_score / total_moves if total_moves > 0 else 0

    def get_recommendations(self):
        """Получение рекомендаций на основе анализа"""
        metrics = self.analyze_performance()
        recommendations = []

        if metrics['efficiency_score'] < 0.1:
            recommendations.append("📈 Попробуйте более эффективную стратегию движения")

        direction_prefs = metrics['direction_preference']
        if direction_prefs:
            most_used = max(direction_prefs, key=direction_prefs.get)
            least_used = min(direction_prefs, key=direction_prefs.get)
            recommendations.append(f"🔄 Разнообразьте движения! Меньше используйте {most_used}, больше {least_used}")

        if metrics['avg_food_distance'] > 100:
            recommendations.append("🎯 Улучшите навигацию к еде")

        return recommendations
