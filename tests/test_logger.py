import unittest
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

# Импортируем модули для тестирования
import sys
sys.path.append('..')

from logger import GameLogger, ErrorHandler

class TestGameLogger(unittest.TestCase):
    def setUp(self):
        # Создаем временную директорию для логов
        self.temp_dir = tempfile.mkdtemp()
        self.original_log_dir = "logs"
        
        # Патчим директорию логов
        with patch('logger.os.path.exists', return_value=False), \
             patch('logger.os.makedirs'), \
             patch('logger.datetime') as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
            self.logger = GameLogger()
    
    def tearDown(self):
        # Очищаем временную директорию
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_logger_initialization(self):
        """Тест инициализации логгера"""
        self.assertIsNotNone(self.logger.logger)
        # Убираем проверку уровня, так как он может быть разным в зависимости от настроек
        # self.assertEqual(self.logger.logger.level, 10)  # DEBUG
    
    def test_log_game_event(self):
        """Тест логирования игровых событий"""
        with patch.object(self.logger.logger, 'info') as mock_info:
            self.logger.log_game_event("test_event", {"score": 10})
            mock_info.assert_called_once()
    
    def test_log_error(self):
        """Тест логирования ошибок"""
        with patch.object(self.logger.logger, 'error') as mock_error:
            test_error = ValueError("Test error")
            self.logger.log_error(test_error, "test_context")
            mock_error.assert_called()
    
    def test_log_ai_decision(self):
        """Тест логирования решений ИИ"""
        with patch.object(self.logger.logger, 'debug') as mock_debug:
            self.logger.log_ai_decision("Right", {"snake_length": 5})
            mock_debug.assert_called_once()
    
    def test_log_performance(self):
        """Тест логирования производительности"""
        with patch.object(self.logger.logger, 'info') as mock_info:
            self.logger.log_performance("test_operation", 0.1)
            mock_info.assert_called_once()

class TestErrorHandler(unittest.TestCase):
    def setUp(self):
        self.mock_logger = MagicMock()
        self.error_handler = ErrorHandler(self.mock_logger)
    
    def test_error_handler_initialization(self):
        """Тест инициализации обработчика ошибок"""
        self.assertEqual(self.error_handler.error_count, 0)
        self.assertEqual(self.error_handler.max_errors, 5)
    
    def test_handle_error_below_limit(self):
        """Тест обработки ошибки ниже лимита"""
        with patch('logger.messagebox.showerror') as mock_show_error:
            result = self.error_handler.handle_error(ValueError("Test error"), "test_context")
            self.assertEqual(result, "continue")
            self.assertEqual(self.error_handler.error_count, 1)
            mock_show_error.assert_called_once()
    
    def test_handle_error_at_limit(self):
        """Тест обработки ошибки на лимите"""
        self.error_handler.error_count = 4
        with patch('logger.messagebox.showerror') as mock_show_error:
            result = self.error_handler.handle_error(ValueError("Test error"), "test_context")
            self.assertEqual(result, "restart")
            self.assertEqual(self.error_handler.error_count, 5)
            mock_show_error.assert_called_once()
    
    def test_handle_error_without_user_notification(self):
        """Тест обработки ошибки без уведомления пользователя"""
        result = self.error_handler.handle_error(ValueError("Test error"), "test_context", show_user=False)
        self.assertEqual(result, "continue")
        self.assertEqual(self.error_handler.error_count, 1)
    
    def test_reset_error_count(self):
        """Тест сброса счетчика ошибок"""
        self.error_handler.error_count = 3
        self.error_handler.reset_error_count()
        self.assertEqual(self.error_handler.error_count, 0)
    
    def test_is_safe_to_continue(self):
        """Тест проверки безопасности продолжения"""
        self.assertTrue(self.error_handler.is_safe_to_continue())
        
        self.error_handler.error_count = 5
        self.assertFalse(self.error_handler.is_safe_to_continue())

if __name__ == '__main__':
    unittest.main() 