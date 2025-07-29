import logging
import os
import traceback
from datetime import datetime
from tkinter import messagebox

class GameLogger:
    """Система логирования для игры Snake AI"""
    
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
    
    def setup_logging(self):
        """Настройка системы логирования"""
        log_dir = "logs"
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        log_file = f"logs/snake_game_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        # Настройка форматирования
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        # Файловый обработчик
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Консольный обработчик
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # Настройка корневого логгера
        logging.basicConfig(
            level=logging.DEBUG,
            handlers=[file_handler, console_handler]
        )
    
    def log_game_event(self, event_type, data=None):
        """Логирование игровых событий"""
        self.logger.info(f"Game Event: {event_type} - {data}")
    
    def log_error(self, error, context=None):
        """Логирование ошибок"""
        error_msg = f"Error: {str(error)} - Context: {context}"
        self.logger.error(error_msg)
        self.logger.error(f"Traceback: {traceback.format_exc()}")
    
    def log_ai_decision(self, decision, state):
        """Логирование решений ИИ"""
        self.logger.debug(f"AI Decision: {decision} - State: {state}")
    
    def log_performance(self, operation, duration):
        """Логирование производительности"""
        self.logger.info(f"Performance: {operation} took {duration:.3f}s")
    
    def log_user_action(self, action, details=None):
        """Логирование действий пользователя"""
        self.logger.info(f"User Action: {action} - {details}")

class ErrorHandler:
    """Обработчик ошибок с восстановлением"""
    
    def __init__(self, logger):
        self.logger = logger
        self.error_count = 0
        self.max_errors = 5
    
    def handle_error(self, error, context=None, show_user=True):
        """Обработка ошибки с возможностью восстановления"""
        self.error_count += 1
        self.logger.log_error(error, context)
        
        if show_user:
            error_msg = f"Произошла ошибка: {str(error)}"
            if self.error_count >= self.max_errors:
                error_msg += "\n\nСлишком много ошибок. Игра будет перезапущена."
                messagebox.showerror("Критическая ошибка", error_msg)
                return "restart"
            else:
                messagebox.showerror("Ошибка", error_msg)
        
        return "continue"
    
    def reset_error_count(self):
        """Сброс счетчика ошибок"""
        self.error_count = 0
    
    def is_safe_to_continue(self):
        """Проверка безопасности продолжения"""
        return self.error_count < self.max_errors

# Глобальный экземпляр логгера
game_logger = GameLogger()
error_handler = ErrorHandler(game_logger) 