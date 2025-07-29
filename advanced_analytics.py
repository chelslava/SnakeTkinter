import math
import time
import json
import os
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict, deque

class AdvancedGameAnalytics:
    """Расширенная аналитика для игры Snake"""
    
    def __init__(self):
        self.analytics_file = 'game_analytics.json'
        self.session_data = {
            'start_time': time.time(),
            'moves': [],
            'scores': [],
            'durations': [],
            'patterns': defaultdict(int),
            'performance_metrics': {},
            'ai_performance': {},
            'player_behavior': {}
        }
        self.real_time_metrics = {
            'current_session_moves': 0,
            'current_session_score': 0,
            'current_session_duration': 0,
            'moves_per_second': 0,
            'efficiency_score': 0
        }
        self.load_analytics()
    
    def record_move(self, snake, food, obstacles, direction, score, timestamp=None):
        """Запись хода с расширенной аналитикой"""
        if timestamp is None:
            timestamp = time.time()
        
        head = snake[0]
        move_data = {
            'timestamp': timestamp,
            'snake_length': len(snake),
            'score': score,
            'direction': direction,
            'head_position': head,
            'food_position': food,
            'food_distance': math.sqrt((food[0] - head[0])**2 + (food[1] - head[1])**2),
            'obstacles_count': len(obstacles),
            'free_space': self.calculate_free_space(snake, obstacles),
            'safe_directions': len(self.get_safe_directions(snake, food, obstacles)),
            'move_efficiency': self.calculate_move_efficiency(snake, food, direction)
        }
        
        self.session_data['moves'].append(move_data)
        self.real_time_metrics['current_session_moves'] += 1
        self.real_time_metrics['current_session_score'] = score
        
        # Анализ паттернов
        self.analyze_move_pattern(move_data)
        
        # Обновление метрик в реальном времени
        self.update_real_time_metrics()
    
    def calculate_move_efficiency(self, snake, food, direction):
        """Расчет эффективности хода"""
        head = snake[0]
        next_pos = self.get_next_position(head, direction)
        
        # Расстояние до еды до и после хода
        distance_before = math.sqrt((food[0] - head[0])**2 + (food[1] - head[1])**2)
        distance_after = math.sqrt((food[0] - next_pos[0])**2 + (food[1] - next_pos[1])**2)
        
        # Эффективность: уменьшение расстояния = положительная эффективность
        efficiency = distance_before - distance_after
        
        # Нормализация
        return max(-1, min(1, efficiency / 50))
    
    def get_next_position(self, pos, direction):
        """Получить следующую позицию при движении"""
        x, y = pos
        cell_size = 10
        
        if direction == "Up":
            return (x, y - cell_size)
        elif direction == "Down":
            return (x, y + cell_size)
        elif direction == "Left":
            return (x - cell_size, y)
        elif direction == "Right":
            return (x + cell_size, y)
        return pos
    
    def calculate_free_space(self, snake, obstacles):
        """Подсчет свободного пространства"""
        total_cells = (400 // 10) * (400 // 10)
        occupied = len(snake) + len(obstacles)
        return total_cells - occupied
    
    def get_safe_directions(self, snake, food, obstacles):
        """Получить безопасные направления движения"""
        head = snake[0]
        safe_dirs = []
        
        for direction in ["Up", "Down", "Left", "Right"]:
            next_pos = self.get_next_position(head, direction)
            if self.is_valid_position(next_pos, snake, obstacles):
                safe_dirs.append(direction)
        
        return safe_dirs
    
    def is_valid_position(self, pos, snake, obstacles):
        """Проверка валидности позиции"""
        x, y = pos
        
        if x < 0 or x >= 400 or y < 0 or y >= 400:
            return False
        
        if pos in snake:
            return False
        
        if pos in obstacles:
            return False
        
        return True
    
    def analyze_move_pattern(self, move_data):
        """Анализ паттерна хода"""
        # Паттерн направления
        direction = move_data['direction']
        self.session_data['patterns'][f'direction_{direction}'] += 1
        
        # Паттерн эффективности
        efficiency = move_data['move_efficiency']
        if efficiency > 0.5:
            self.session_data['patterns']['high_efficiency_moves'] += 1
        elif efficiency < -0.5:
            self.session_data['patterns']['low_efficiency_moves'] += 1
        
        # Паттерн расстояния до еды
        distance = move_data['food_distance']
        if distance < 50:
            self.session_data['patterns']['close_to_food'] += 1
        elif distance > 200:
            self.session_data['patterns']['far_from_food'] += 1
    
    def update_real_time_metrics(self):
        """Обновление метрик в реальном времени"""
        if len(self.session_data['moves']) < 2:
            return
        
        # Скорость ходов
        recent_moves = self.session_data['moves'][-10:]  # Последние 10 ходов
        if len(recent_moves) >= 2:
            time_diff = recent_moves[-1]['timestamp'] - recent_moves[0]['timestamp']
            if time_diff > 0:
                self.real_time_metrics['moves_per_second'] = len(recent_moves) / time_diff
        
        # Эффективность
        efficiencies = [move['move_efficiency'] for move in recent_moves]
        self.real_time_metrics['efficiency_score'] = sum(efficiencies) / len(efficiencies)
    
    def record_game_end(self, final_score, duration, ai_mode=False):
        """Запись завершения игры"""
        game_data = {
            'final_score': final_score,
            'duration': duration,
            'ai_mode': ai_mode,
            'total_moves': len(self.session_data['moves']),
            'max_snake_length': max([move['snake_length'] for move in self.session_data['moves']]) if self.session_data['moves'] else 0,
            'avg_efficiency': np.mean([move['move_efficiency'] for move in self.session_data['moves']]) if self.session_data['moves'] else 0,
            'patterns': dict(self.session_data['patterns']),
            'timestamp': time.time()
        }
        
        self.session_data['scores'].append(final_score)
        self.session_data['durations'].append(duration)
        
        # Анализ производительности
        self.analyze_performance(game_data)
        
        # Сохранение данных
        self.save_analytics()
        
        # Сброс сессии
        self.reset_session()
    
    def analyze_performance(self, game_data):
        """Анализ производительности игры"""
        # Общая статистика
        if self.session_data['scores']:
            self.session_data['performance_metrics'] = {
                'best_score': max(self.session_data['scores']),
                'avg_score': np.mean(self.session_data['scores']),
                'total_games': len(self.session_data['scores']),
                'avg_duration': np.mean(self.session_data['durations']),
                'score_trend': self.calculate_trend(self.session_data['scores']),
                'efficiency_trend': self.calculate_trend([move['move_efficiency'] for move in self.session_data['moves']])
            }
        
        # Анализ поведения игрока
        self.analyze_player_behavior()
    
    def analyze_player_behavior(self):
        """Анализ поведения игрока"""
        if not self.session_data['moves']:
            return
        
        moves = self.session_data['moves']
        
        # Предпочтения в направлениях
        directions = [move['direction'] for move in moves]
        direction_counts = defaultdict(int)
        for direction in directions:
            direction_counts[direction] += 1
        
        # Анализ риска
        risk_analysis = {
            'high_risk_moves': sum(1 for move in moves if move['safe_directions'] <= 1),
            'low_risk_moves': sum(1 for move in moves if move['safe_directions'] >= 3),
            'avg_safe_directions': np.mean([move['safe_directions'] for move in moves])
        }
        
        # Анализ эффективности
        efficiency_analysis = {
            'high_efficiency_ratio': sum(1 for move in moves if move['move_efficiency'] > 0.3) / len(moves),
            'low_efficiency_ratio': sum(1 for move in moves if move['move_efficiency'] < -0.3) / len(moves),
            'avg_efficiency': np.mean([move['move_efficiency'] for move in moves])
        }
        
        self.session_data['player_behavior'] = {
            'direction_preferences': dict(direction_counts),
            'risk_analysis': risk_analysis,
            'efficiency_analysis': efficiency_analysis
        }
    
    def calculate_trend(self, data, window=5):
        """Расчет тренда данных"""
        if len(data) < window:
            return 0
        
        recent_data = data[-window:]
        if len(recent_data) < 2:
            return 0
        
        # Простой линейный тренд
        x = np.arange(len(recent_data))
        y = np.array(recent_data)
        
        try:
            slope = np.polyfit(x, y, 1)[0]
            return slope
        except:
            return 0
    
    def get_recommendations(self):
        """Получение персонализированных рекомендаций"""
        recommendations = []
        
        if not self.session_data['player_behavior']:
            return recommendations
        
        behavior = self.session_data['player_behavior']
        
        # Анализ направлений
        direction_prefs = behavior['direction_preferences']
        if direction_prefs:
            most_used = max(direction_prefs, key=direction_prefs.get)
            least_used = min(direction_prefs, key=direction_prefs.get)
            recommendations.append(f"🔄 Разнообразьте движения! Меньше {most_used}, больше {least_used}")
        
        # Анализ риска
        risk_analysis = behavior['risk_analysis']
        if risk_analysis['high_risk_moves'] > risk_analysis['low_risk_moves']:
            recommendations.append("⚠️ Вы часто идете на риск. Будьте осторожнее!")
        
        # Анализ эффективности
        efficiency_analysis = behavior['efficiency_analysis']
        if efficiency_analysis['avg_efficiency'] < 0:
            recommendations.append("📈 Улучшите эффективность движений - планируйте путь заранее")
        
        # Общие рекомендации
        if len(self.session_data['scores']) > 1:
            recent_scores = self.session_data['scores'][-5:]
            if max(recent_scores) < 10:
                recommendations.append("🎯 Сосредоточьтесь на достижении более высоких счетов")
        
        return recommendations
    
    def get_advanced_stats(self):
        """Получение расширенной статистики"""
        stats = {
            'session': self.real_time_metrics,
            'overall': self.session_data['performance_metrics'],
            'behavior': self.session_data['player_behavior'],
            'patterns': dict(self.session_data['patterns'])
        }
        
        return stats
    
    def reset_session(self):
        """Сброс данных сессии"""
        self.session_data['moves'] = []
        self.session_data['patterns'] = defaultdict(int)
        self.real_time_metrics['current_session_moves'] = 0
        self.real_time_metrics['current_session_score'] = 0
        self.session_data['start_time'] = time.time()
    
    def save_analytics(self):
        """Сохранение аналитики"""
        try:
            # Конвертируем defaultdict в обычный dict для JSON
            data_to_save = {
                'scores': self.session_data['scores'],
                'durations': self.session_data['durations'],
                'performance_metrics': self.session_data['performance_metrics'],
                'player_behavior': self.session_data['player_behavior'],
                'patterns': dict(self.session_data['patterns']),
                'last_updated': time.time()
            }
            
            with open(self.analytics_file, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"Ошибка сохранения аналитики: {e}")
    
    def load_analytics(self):
        """Загрузка аналитики"""
        try:
            if os.path.exists(self.analytics_file):
                with open(self.analytics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.session_data['scores'] = data.get('scores', [])
                self.session_data['durations'] = data.get('durations', [])
                self.session_data['performance_metrics'] = data.get('performance_metrics', {})
                self.session_data['player_behavior'] = data.get('player_behavior', {})
                
                # Восстанавливаем defaultdict для паттернов
                patterns = data.get('patterns', {})
                self.session_data['patterns'] = defaultdict(int, patterns)
                
        except Exception as e:
            print(f"Ошибка загрузки аналитики: {e}")
    
    def export_analytics_report(self, filename=None):
        """Экспорт отчета аналитики"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'analytics_report_{timestamp}.json'
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'session_data': self.session_data,
            'real_time_metrics': self.real_time_metrics,
            'recommendations': self.get_recommendations(),
            'advanced_stats': self.get_advanced_stats()
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            print(f"Отчет сохранен в {filename}")
            return filename
        except Exception as e:
            print(f"Ошибка экспорта отчета: {e}")
            return None 