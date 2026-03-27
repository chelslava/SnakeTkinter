import time
from enum import Enum


class GameMode(Enum):
    """Перечисление игровых режимов"""
    CLASSIC = "classic"
    TIME_ATTACK = "time_attack"
    SURVIVAL = "survival"
    PUZZLE = "puzzle"
    AI_BATTLE = "ai_battle"
    SPEED_RUN = "speed_run"
    ENDLESS = "endless"

class GameModeManager:
    """Менеджер игровых режимов"""

    def __init__(self):
        self.current_mode = GameMode.CLASSIC
        self.mode_configs = {
            GameMode.CLASSIC: {
                'name': 'Классический',
                'description': 'Стандартная игра Snake',
                'time_limit': None,
                'obstacles': False,
                'speed_increase': False,
                'special_rules': []
            },
            GameMode.TIME_ATTACK: {
                'name': 'Гонка со временем',
                'description': 'Соберите как можно больше очков за ограниченное время',
                'time_limit': 120,  # 2 минуты
                'obstacles': True,
                'speed_increase': True,
                'special_rules': ['time_pressure']
            },
            GameMode.SURVIVAL: {
                'name': 'Режим выживания',
                'description': 'Выживите как можно дольше с растущей сложностью',
                'time_limit': None,
                'obstacles': True,
                'speed_increase': True,
                'special_rules': ['adaptive_difficulty', 'obstacle_growth']
            },
            GameMode.PUZZLE: {
                'name': 'Головоломка',
                'description': 'Решите головоломки с препятствиями',
                'time_limit': None,
                'obstacles': True,
                'speed_increase': False,
                'special_rules': ['puzzle_levels', 'goal_oriented']
            },
            GameMode.AI_BATTLE: {
                'name': 'Битва с ИИ',
                'description': 'Соревнуйтесь с ИИ в реальном времени',
                'time_limit': None,
                'obstacles': True,
                'speed_increase': False,
                'special_rules': ['ai_competition', 'dual_play']
            },
            GameMode.SPEED_RUN: {
                'name': 'Спидран',
                'description': 'Достигните цели за минимальное время',
                'time_limit': None,
                'obstacles': False,
                'speed_increase': False,
                'special_rules': ['speed_focus', 'time_tracking']
            },
            GameMode.ENDLESS: {
                'name': 'Бесконечный',
                'description': 'Играйте без ограничений',
                'time_limit': None,
                'obstacles': True,
                'speed_increase': True,
                'special_rules': ['no_death', 'continuous_play']
            }
        }

        self.mode_state = {}
        self.reset_mode_state()

    def set_mode(self, mode):
        """Установка игрового режима"""
        if isinstance(mode, str):
            mode = GameMode(mode)

        self.current_mode = mode
        self.reset_mode_state()
        return self.get_mode_config()

    def get_mode_config(self):
        """Получение конфигурации текущего режима"""
        return self.mode_configs[self.current_mode]

    def reset_mode_state(self):
        """Сброс состояния режима"""
        config = self.get_mode_config()
        self.mode_state = {
            'start_time': time.time(),
            'time_remaining': config['time_limit'],
            'difficulty_level': 1,
            'obstacle_count': 0,
            'speed_multiplier': 1.0,
            'score_multiplier': 1.0,
            'special_events': [],
            'puzzle_level': 1,
            'ai_score': 0,
            'player_score': 0
        }

    def update_mode_state(self, game_state):
        """Обновление состояния режима"""
        current_time = time.time()
        elapsed_time = current_time - self.mode_state['start_time']

        config = self.get_mode_config()

        # Обновление времени для режимов с ограничением времени
        if config['time_limit']:
            self.mode_state['time_remaining'] = max(0, config['time_limit'] - elapsed_time)

        # Адаптивная сложность для режима выживания
        if 'adaptive_difficulty' in config['special_rules']:
            self.update_adaptive_difficulty(game_state)

        # Рост препятствий
        if 'obstacle_growth' in config['special_rules']:
            self.update_obstacle_growth(game_state)

        # Увеличение скорости
        if config['speed_increase']:
            self.update_speed_increase(game_state)

        # Специальные события
        self.update_special_events(game_state)

    def update_adaptive_difficulty(self, game_state):
        """Обновление адаптивной сложности"""
        score = game_state.get('score', 0)
        snake_length = game_state.get('snake_length', 3)

        # Увеличиваем сложность на основе счета и длины змеи
        difficulty_level = 1 + (score // 10) + (snake_length // 5)
        self.mode_state['difficulty_level'] = difficulty_level

        # Корректируем множители
        self.mode_state['speed_multiplier'] = 1.0 + (difficulty_level * 0.1)
        self.mode_state['score_multiplier'] = 1.0 + (difficulty_level * 0.05)

    def update_obstacle_growth(self, game_state):
        """Обновление роста препятствий"""
        score = game_state.get('score', 0)
        base_obstacles = 2
        new_obstacles = base_obstacles + (score // 5)

        if new_obstacles != self.mode_state['obstacle_count']:
            self.mode_state['obstacle_count'] = new_obstacles
            self.mode_state['special_events'].append({
                'type': 'obstacle_increase',
                'count': new_obstacles,
                'timestamp': time.time()
            })

    def update_speed_increase(self, game_state):
        """Обновление увеличения скорости"""
        score = game_state.get('score', 0)
        speed_increase = 1.0 + (score // 20) * 0.1
        self.mode_state['speed_multiplier'] = speed_increase

    def update_special_events(self, game_state):
        """Обновление специальных событий"""
        current_time = time.time()

        # Очищаем старые события (старше 5 секунд)
        self.mode_state['special_events'] = [
            event for event in self.mode_state['special_events']
            if current_time - event['timestamp'] < 5
        ]

        # Специальная логика для режима AI_BATTLE
        if self.current_mode == GameMode.AI_BATTLE:
            self.update_ai_battle_events(game_state)

    def update_ai_battle_events(self, game_state):
        """Обновление событий для режима битвы с ИИ"""
        current_time = time.time()

        # Инициализация счетчиков ИИ
        if 'ai_score' not in self.mode_state:
            self.mode_state['ai_score'] = 0
            self.mode_state['ai_moves'] = 0
            self.mode_state['ai_efficiency'] = 0.0
            self.mode_state['battle_start_time'] = current_time

        # Обновляем статистику ИИ каждые 10 ходов
        if game_state.get('score', 0) % 10 == 0 and game_state.get('score', 0) > 0:
            # ИИ получает очки на основе эффективности
            ai_efficiency = min(1.0, self.mode_state['ai_efficiency'])
            ai_score_increase = int(game_state.get('score', 0) * ai_efficiency * 0.3)
            self.mode_state['ai_score'] += ai_score_increase

            # Добавляем событие
            self.mode_state['special_events'].append({
                'type': 'ai_score',
                'message': f"ИИ получил {ai_score_increase} очков!",
                'timestamp': current_time
            })

        # Обновляем эффективность ИИ
        if game_state.get('score', 0) > 0:
            self.mode_state['ai_efficiency'] = min(1.0,
                (self.mode_state['ai_score'] / max(game_state.get('score', 1), 1)) * 0.8)

    def check_mode_conditions(self, game_state):
        """Проверка условий режима"""
        config = self.get_mode_config()
        conditions = {
            'game_over': False,
            'mode_complete': False,
            'special_message': None
        }

        # Проверка времени для режимов с ограничением
        if config['time_limit'] and self.mode_state['time_remaining'] <= 0:
            conditions['game_over'] = True
            conditions['mode_complete'] = True
            conditions['special_message'] = f"Время вышло! Финальный счет: {game_state.get('score', 0)}"

        # Проверка головоломки
        if 'puzzle_levels' in config['special_rules'] and self.check_puzzle_completion(game_state):
            conditions['mode_complete'] = True
            conditions['special_message'] = f"Уровень {self.mode_state['puzzle_level']} пройден!"

        # Проверка спидрана
        if 'speed_focus' in config['special_rules']:
            target_score = 20
            if game_state.get('score', 0) >= target_score:
                conditions['mode_complete'] = True
                conditions['special_message'] = f"Цель достигнута за {time.time() - self.mode_state['start_time']:.1f} секунд!"

        # Проверка битвы с ИИ
        if self.current_mode == GameMode.AI_BATTLE:
            battle_result = self.check_ai_battle_conditions(game_state)
            if battle_result['game_over']:
                conditions.update(battle_result)

        return conditions

    def check_ai_battle_conditions(self, game_state):
        """Проверка условий битвы с ИИ"""
        player_score = game_state.get('score', 0)
        ai_score = self.mode_state.get('ai_score', 0)
        battle_duration = time.time() - self.mode_state.get('battle_start_time', time.time())

        conditions = {
            'game_over': False,
            'mode_complete': False,
            'special_message': None
        }

        # Игра заканчивается при достижении 50 очков любым участником
        if player_score >= 50 or ai_score >= 50:
            conditions['game_over'] = True
            conditions['mode_complete'] = True

            if player_score >= 50:
                conditions['special_message'] = f"🏆 ПОБЕДА! Вы победили ИИ со счетом {player_score}:{ai_score}"
            else:
                conditions['special_message'] = f"🤖 ПОРАЖЕНИЕ! ИИ победил со счетом {ai_score}:{player_score}"

        # Альтернативное условие: игра длится 3 минуты
        elif battle_duration >= 180:  # 3 минуты
            conditions['game_over'] = True
            conditions['mode_complete'] = True

            if player_score > ai_score:
                conditions['special_message'] = f"🏆 ПОБЕДА! Вы победили ИИ со счетом {player_score}:{ai_score}"
            elif ai_score > player_score:
                conditions['special_message'] = f"🤖 ПОРАЖЕНИЕ! ИИ победил со счетом {ai_score}:{player_score}"
            else:
                conditions['special_message'] = f"🤝 НИЧЬЯ! Счет {player_score}:{ai_score}"

        return conditions

    def check_puzzle_completion(self, game_state):
        """Проверка завершения головоломки"""
        # Простая логика: достижение определенного счета
        target_score = self.mode_state['puzzle_level'] * 10
        return game_state.get('score', 0) >= target_score

    def get_mode_display_info(self):
        """Получение информации для отображения режима"""
        config = self.get_mode_config()
        info = {
            'name': config['name'],
            'description': config['description'],
            'time_remaining': self.mode_state['time_remaining'],
            'difficulty_level': self.mode_state['difficulty_level'],
            'speed_multiplier': self.mode_state['speed_multiplier'],
            'score_multiplier': self.mode_state['score_multiplier']
        }

        # Дополнительная информация для режима AI_BATTLE
        if self.current_mode == GameMode.AI_BATTLE:
            ai_score = self.mode_state.get('ai_score', 0)
            ai_efficiency = self.mode_state.get('ai_efficiency', 0.0)
            battle_duration = time.time() - self.mode_state.get('battle_start_time', time.time())

            info.update({
                'ai_score': ai_score,
                'ai_efficiency': ai_efficiency,
                'battle_duration': battle_duration,
                'battle_time_remaining': max(0, 180 - battle_duration)  # 3 минуты
            })

        return info

    def get_available_modes(self):
        """Получение списка доступных режимов"""
        return [mode.value for mode in GameMode]

class TimeAttackMode:
    """Режим гонки со временем"""

    def __init__(self, time_limit=120):
        self.time_limit = time_limit
        self.start_time = None
        self.time_remaining = time_limit

    def start(self):
        """Начало режима"""
        self.start_time = time.time()
        self.time_remaining = self.time_limit

    def update(self):
        """Обновление времени"""
        if self.start_time:
            elapsed = time.time() - self.start_time
            self.time_remaining = max(0, self.time_limit - elapsed)

    def is_time_up(self):
        """Проверка окончания времени"""
        return self.time_remaining <= 0

    def get_time_display(self):
        """Получение времени для отображения"""
        minutes = int(self.time_remaining // 60)
        seconds = int(self.time_remaining % 60)
        return f"{minutes:02d}:{seconds:02d}"

class SurvivalMode:
    """Режим выживания"""

    def __init__(self):
        self.difficulty_level = 1
        self.speed_multiplier = 1.0
        self.obstacle_multiplier = 1.0
        self.last_update = time.time()

    def update_difficulty(self, score, snake_length):
        """Обновление сложности"""
        current_time = time.time()

        # Обновляем каждые 10 секунд
        if current_time - self.last_update >= 10:
            self.difficulty_level = 1 + (score // 10) + (snake_length // 5)
            self.speed_multiplier = 1.0 + (self.difficulty_level * 0.1)
            self.obstacle_multiplier = 1.0 + (self.difficulty_level * 0.2)
            self.last_update = current_time

    def get_obstacle_count(self):
        """Получение количества препятствий"""
        return int(2 * self.obstacle_multiplier)

    def get_speed_delay(self, base_delay):
        """Получение задержки с учетом скорости"""
        return max(20, int(base_delay / self.speed_multiplier))

class PuzzleMode:
    """Режим головоломки"""

    def __init__(self):
        self.current_level = 1
        self.levels = {
            1: {'target_score': 10, 'obstacles': 3, 'time_limit': 60},
            2: {'target_score': 20, 'obstacles': 5, 'time_limit': 90},
            3: {'target_score': 30, 'obstacles': 7, 'time_limit': 120},
            4: {'target_score': 40, 'obstacles': 10, 'time_limit': 150},
            5: {'target_score': 50, 'obstacles': 12, 'time_limit': 180}
        }

    def get_current_level_config(self):
        """Получение конфигурации текущего уровня"""
        return self.levels.get(self.current_level, self.levels[1])

    def check_level_completion(self, score):
        """Проверка завершения уровня"""
        config = self.get_current_level_config()
        return score >= config['target_score']

    def advance_level(self):
        """Переход на следующий уровень"""
        if self.current_level < max(self.levels.keys()):
            self.current_level += 1
            return True
        return False

    def get_level_display(self):
        """Получение информации об уровне"""
        config = self.get_current_level_config()
        return {
            'level': self.current_level,
            'target_score': config['target_score'],
            'obstacles': config['obstacles'],
            'time_limit': config['time_limit']
        }
