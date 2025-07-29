import unittest
import numpy as np
import time
import tempfile
import os
from unittest.mock import patch, MagicMock

# Импортируем модули для тестирования
import sys
sys.path.append('..')

from neural_ai import NeuralSnakeAI
from advanced_analytics import AdvancedGameAnalytics
from game_modes import GameModeManager, GameMode, TimeAttackMode, SurvivalMode, PuzzleMode

class TestNeuralSnakeAI(unittest.TestCase):
    def setUp(self):
        self.neural_ai = NeuralSnakeAI()
        self.sample_snake = [(100, 100), (90, 100), (80, 100)]
        self.sample_food = (150, 150)
        self.sample_obstacles = [(120, 100), (130, 110)]
    
    def test_initialization(self):
        """Тест инициализации нейросети"""
        self.assertIsNotNone(self.neural_ai.model)
        self.assertIsNotNone(self.neural_ai.scaler)
        self.assertEqual(len(self.neural_ai.training_data), 0)
        self.assertFalse(self.neural_ai.is_trained)
    
    def test_extract_features(self):
        """Тест извлечения признаков"""
        features = self.neural_ai.extract_features(self.sample_snake, self.sample_food, self.sample_obstacles)
        self.assertIsInstance(features, np.ndarray)
        self.assertGreater(len(features), 0)
    
    def test_get_safe_directions(self):
        """Тест получения безопасных направлений"""
        safe_dirs = self.neural_ai.get_safe_directions(self.sample_snake, self.sample_food, self.sample_obstacles)
        self.assertIsInstance(safe_dirs, list)
        self.assertLessEqual(len(safe_dirs), 4)
    
    def test_predict_best_action(self):
        """Тест предсказания действия (без обучения)"""
        action = self.neural_ai.predict_best_action(self.sample_snake, self.sample_food, self.sample_obstacles)
        # Без обучения должно возвращать None
        self.assertIsNone(action)
    
    def test_add_training_data(self):
        """Тест добавления данных для обучения"""
        initial_count = len(self.neural_ai.training_data)
        self.neural_ai.add_training_data(self.sample_snake, self.sample_food, self.sample_obstacles, "Right", 1.0)
        self.assertEqual(len(self.neural_ai.training_data), initial_count + 1)
    
    def test_get_training_stats(self):
        """Тест получения статистики обучения"""
        stats = self.neural_ai.get_training_stats()
        self.assertIn('is_trained', stats)
        self.assertIn('training_samples', stats)
        self.assertIn('model_file_exists', stats)
        self.assertIn('scaler_file_exists', stats)

class TestAdvancedGameAnalytics(unittest.TestCase):
    def setUp(self):
        self.analytics = AdvancedGameAnalytics()
        self.sample_snake = [(100, 100), (90, 100), (80, 100)]
        self.sample_food = (150, 150)
        self.sample_obstacles = [(120, 100), (130, 110)]
    
    def test_initialization(self):
        """Тест инициализации аналитики"""
        self.assertIsNotNone(self.analytics.session_data)
        self.assertIsNotNone(self.analytics.real_time_metrics)
    
    def test_record_move(self):
        """Тест записи хода"""
        initial_moves = len(self.analytics.session_data['moves'])
        self.analytics.record_move(self.sample_snake, self.sample_food, self.sample_obstacles, "Right", 5)
        self.assertEqual(len(self.analytics.session_data['moves']), initial_moves + 1)
    
    def test_calculate_move_efficiency(self):
        """Тест расчета эффективности хода"""
        efficiency = self.analytics.calculate_move_efficiency(self.sample_snake, self.sample_food, "Right")
        self.assertIsInstance(efficiency, float)
        self.assertGreaterEqual(efficiency, -1)
        self.assertLessEqual(efficiency, 1)
    
    def test_get_recommendations(self):
        """Тест получения рекомендаций"""
        recommendations = self.analytics.get_recommendations()
        self.assertIsInstance(recommendations, list)
    
    def test_get_advanced_stats(self):
        """Тест получения расширенной статистики"""
        stats = self.analytics.get_advanced_stats()
        self.assertIn('session', stats)
        self.assertIn('overall', stats)
        self.assertIn('behavior', stats)
        self.assertIn('patterns', stats)
    
    def test_reset_session(self):
        """Тест сброса сессии"""
        self.analytics.session_data['moves'] = [{'test': 'data'}]
        self.analytics.reset_session()
        self.assertEqual(len(self.analytics.session_data['moves']), 0)

class TestGameModeManager(unittest.TestCase):
    def setUp(self):
        self.mode_manager = GameModeManager()
    
    def test_initialization(self):
        """Тест инициализации менеджера режимов"""
        self.assertEqual(self.mode_manager.current_mode, GameMode.CLASSIC)
        self.assertIsNotNone(self.mode_manager.mode_configs)
    
    def test_set_mode(self):
        """Тест установки режима"""
        config = self.mode_manager.set_mode(GameMode.TIME_ATTACK)
        self.assertEqual(self.mode_manager.current_mode, GameMode.TIME_ATTACK)
        self.assertEqual(config['name'], 'Гонка со временем')
    
    def test_get_mode_config(self):
        """Тест получения конфигурации режима"""
        config = self.mode_manager.get_mode_config()
        self.assertIn('name', config)
        self.assertIn('description', config)
    
    def test_update_mode_state(self):
        """Тест обновления состояния режима"""
        game_state = {'score': 10, 'snake_length': 5, 'obstacles_count': 2, 'ai_mode': False}
        self.mode_manager.update_mode_state(game_state)
        self.assertIsNotNone(self.mode_manager.mode_state)
    
    def test_check_mode_conditions(self):
        """Тест проверки условий режима"""
        game_state = {'score': 10, 'snake_length': 5, 'obstacles_count': 2, 'ai_mode': False}
        conditions = self.mode_manager.check_mode_conditions(game_state)
        self.assertIn('game_over', conditions)
        self.assertIn('mode_complete', conditions)
        self.assertIn('special_message', conditions)
    
    def test_get_available_modes(self):
        """Тест получения доступных режимов"""
        modes = self.mode_manager.get_available_modes()
        self.assertIsInstance(modes, list)
        self.assertGreater(len(modes), 0)

class TestTimeAttackMode(unittest.TestCase):
    def setUp(self):
        self.time_attack = TimeAttackMode(time_limit=60)
    
    def test_initialization(self):
        """Тест инициализации режима времени"""
        self.assertEqual(self.time_attack.time_limit, 60)
        self.assertIsNone(self.time_attack.start_time)
    
    def test_start(self):
        """Тест начала режима"""
        self.time_attack.start()
        self.assertIsNotNone(self.time_attack.start_time)
        self.assertEqual(self.time_attack.time_remaining, 60)
    
    def test_update(self):
        """Тест обновления времени"""
        self.time_attack.start()
        initial_time = self.time_attack.time_remaining
        time.sleep(0.1)  # Небольшая задержка
        self.time_attack.update()
        self.assertLess(self.time_attack.time_remaining, initial_time)
    
    def test_get_time_display(self):
        """Тест отображения времени"""
        self.time_attack.time_remaining = 65
        display = self.time_attack.get_time_display()
        self.assertEqual(display, "01:05")

class TestSurvivalMode(unittest.TestCase):
    def setUp(self):
        self.survival = SurvivalMode()
    
    def test_initialization(self):
        """Тест инициализации режима выживания"""
        self.assertEqual(self.survival.difficulty_level, 1)
        self.assertEqual(self.survival.speed_multiplier, 1.0)
    
    def test_update_difficulty(self):
        """Тест обновления сложности"""
        self.survival.update_difficulty(score=20, snake_length=10)
        self.assertGreaterEqual(self.survival.difficulty_level, 1)
    
    def test_get_obstacle_count(self):
        """Тест получения количества препятствий"""
        count = self.survival.get_obstacle_count()
        self.assertIsInstance(count, int)
        self.assertGreaterEqual(count, 0)
    
    def test_get_speed_delay(self):
        """Тест получения задержки скорости"""
        delay = self.survival.get_speed_delay(100)
        self.assertIsInstance(delay, int)
        self.assertGreaterEqual(delay, 20)

class TestPuzzleMode(unittest.TestCase):
    def setUp(self):
        self.puzzle = PuzzleMode()
    
    def test_initialization(self):
        """Тест инициализации режима головоломки"""
        self.assertEqual(self.puzzle.current_level, 1)
        self.assertIsNotNone(self.puzzle.levels)
    
    def test_get_current_level_config(self):
        """Тест получения конфигурации уровня"""
        config = self.puzzle.get_current_level_config()
        self.assertIn('target_score', config)
        self.assertIn('obstacles', config)
        self.assertIn('time_limit', config)
    
    def test_check_level_completion(self):
        """Тест проверки завершения уровня"""
        # Уровень 1 требует 10 очков
        self.assertTrue(self.puzzle.check_level_completion(15))
        self.assertFalse(self.puzzle.check_level_completion(5))
    
    def test_advance_level(self):
        """Тест перехода на следующий уровень"""
        initial_level = self.puzzle.current_level
        success = self.puzzle.advance_level()
        self.assertTrue(success)
        self.assertEqual(self.puzzle.current_level, initial_level + 1)
    
    def test_get_level_display(self):
        """Тест получения информации об уровне"""
        display = self.puzzle.get_level_display()
        self.assertIn('level', display)
        self.assertIn('target_score', display)
        self.assertIn('obstacles', display)
        self.assertIn('time_limit', display)

if __name__ == '__main__':
    unittest.main() 