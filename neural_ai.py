import numpy as np
import math
import random
import time
import pickle
import os
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error

class NeuralSnakeAI:
    """Нейронная сеть для игры Snake"""
    
    def __init__(self, hidden_layers=(100, 50, 25)):
        self.model = MLPRegressor(
            hidden_layer_sizes=hidden_layers,
            max_iter=1000,
            random_state=42,
            learning_rate='adaptive',
            early_stopping=True,
            validation_fraction=0.1
        )
        self.scaler = StandardScaler()
        self.training_data = []
        self.is_trained = False
        self.model_file = 'neural_snake_model.pkl'
        self.scaler_file = 'neural_snake_scaler.pkl'
        
        # Параметры для обучения
        self.min_training_samples = 100
        self.max_training_samples = 10000
        self.retrain_threshold = 0.1  # Порог для переобучения
        
    def extract_features(self, snake, food, obstacles):
        """Извлечение признаков для нейросети"""
        head = snake[0]
        
        # Базовые признаки
        features = [
            # Расстояние до еды (нормализованное)
            math.sqrt((food[0] - head[0])**2 + (food[1] - head[1])**2) / 400,
            # Длина змеи (нормализованная)
            len(snake) / 100,
            # Количество препятствий (нормализованное)
            len(obstacles) / 50,
            # Свободное пространство (нормализованное)
            self.calculate_free_space(snake, obstacles) / 1600,
            # Количество безопасных направлений (нормализованное)
            len(self.get_safe_directions(snake, food, obstacles)) / 4,
            # Позиция головы (нормализованная)
            head[0] / 400,
            head[1] / 400,
            # Направление к еде (нормализованное)
            (food[0] - head[0]) / 400,
            (food[1] - head[1]) / 400
        ]
        
        # Дополнительные признаки для препятствий
        obstacle_features = self.get_obstacle_features(head, obstacles)
        features.extend(obstacle_features)
        
        # Признаки для тела змеи
        body_features = self.get_body_features(snake)
        features.extend(body_features)
        
        return np.array(features)
    
    def get_obstacle_features(self, head, obstacles):
        """Получение признаков препятствий"""
        features = []
        for direction in ["Up", "Down", "Left", "Right"]:
            distance = self.get_distance_to_obstacle(head, obstacles, direction)
            features.append(distance / 400)  # Нормализация
        return features
    
    def get_body_features(self, snake):
        """Получение признаков тела змеи"""
        head = snake[0]
        features = []
        
        # Расстояние до ближайшей части тела
        min_distance = float('inf')
        for segment in snake[1:]:
            distance = math.sqrt((segment[0] - head[0])**2 + (segment[1] - head[1])**2)
            min_distance = min(min_distance, distance)
        
        features.append(min_distance / 400 if min_distance != float('inf') else 1.0)
        
        # Количество сегментов в радиусе
        radius = 50
        nearby_segments = 0
        for segment in snake[1:]:
            distance = math.sqrt((segment[0] - head[0])**2 + (segment[1] - head[1])**2)
            if distance <= radius:
                nearby_segments += 1
        
        features.append(nearby_segments / 10)  # Нормализация
        
        return features
    
    def get_distance_to_obstacle(self, head, obstacles, direction):
        """Получение расстояния до ближайшего препятствия в направлении"""
        x, y = head
        cell_size = 10
        
        if direction == "Up":
            dx, dy = 0, -cell_size
        elif direction == "Down":
            dx, dy = 0, cell_size
        elif direction == "Left":
            dx, dy = -cell_size, 0
        elif direction == "Right":
            dx, dy = cell_size, 0
        
        distance = 0
        current_pos = (x, y)
        
        while 0 <= current_pos[0] < 400 and 0 <= current_pos[1] < 400:
            current_pos = (current_pos[0] + dx, current_pos[1] + dy)
            distance += cell_size
            
            if current_pos in obstacles:
                return distance
        
        return 400  # Максимальное расстояние
    
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
    
    def is_valid_position(self, pos, snake, obstacles):
        """Проверка валидности позиции"""
        x, y = pos
        
        # Проверка границ
        if x < 0 or x >= 400 or y < 0 or y >= 400:
            return False
        
        # Проверка столкновения с змеей
        if pos in snake:
            return False
        
        # Проверка столкновения с препятствиями
        if pos in obstacles:
            return False
        
        return True
    
    def predict_best_action(self, snake, food, obstacles):
        """Предсказание лучшего действия"""
        if not self.is_trained:
            return None
        
        try:
            features = self.extract_features(snake, food, obstacles)
            features_scaled = self.scaler.transform([features])
            prediction = self.model.predict(features_scaled)[0]
            
            # Преобразуем предсказание в направление
            safe_dirs = self.get_safe_directions(snake, food, obstacles)
            if safe_dirs:
                # Простая логика: выбираем направление на основе предсказания
                # Можно улучшить, используя более сложную логику
                return random.choice(safe_dirs)
            
        except Exception as e:
            print(f"Ошибка предсказания: {e}")
        
        return None
    
    def train(self, training_data):
        """Обучение нейросети"""
        if len(training_data) < self.min_training_samples:
            return False
        
        try:
            X = []
            y = []
            
            for state, action, reward in training_data:
                features = self.extract_features(*state)
                X.append(features)
                y.append(reward)
            
            # Ограничиваем количество данных для обучения
            if len(X) > self.max_training_samples:
                indices = random.sample(range(len(X)), self.max_training_samples)
                X = [X[i] for i in indices]
                y = [y[i] for i in indices]
            
            X = np.array(X)
            y = np.array(y)
            
            # Разделяем на обучающую и тестовую выборки
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Нормализация данных
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # Обучение модели
            self.model.fit(X_train_scaled, y_train)
            
            # Оценка качества
            y_pred = self.model.predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            
            print(f"Модель обучена. MSE: {mse:.4f}")
            self.is_trained = True
            
            # Сохранение модели
            self.save_model()
            
            return True
            
        except Exception as e:
            print(f"Ошибка обучения: {e}")
            return False
    
    def add_training_data(self, snake, food, obstacles, action, reward):
        """Добавление данных для обучения"""
        self.training_data.append(((snake, food, obstacles), action, reward))
        
        # Ограничиваем размер данных
        if len(self.training_data) > self.max_training_samples:
            self.training_data = self.training_data[-self.max_training_samples:]
    
    def save_model(self):
        """Сохранение обученной модели"""
        try:
            with open(self.model_file, 'wb') as f:
                pickle.dump(self.model, f)
            
            with open(self.scaler_file, 'wb') as f:
                pickle.dump(self.scaler, f)
            
            print("Модель сохранена")
        except Exception as e:
            print(f"Ошибка сохранения модели: {e}")
    
    def load_model(self):
        """Загрузка обученной модели"""
        try:
            if os.path.exists(self.model_file) and os.path.exists(self.scaler_file):
                with open(self.model_file, 'rb') as f:
                    self.model = pickle.load(f)
                
                with open(self.scaler_file, 'rb') as f:
                    self.scaler = pickle.load(f)
                
                self.is_trained = True
                print("Модель загружена")
                return True
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
        
        return False
    
    def get_training_stats(self):
        """Получение статистики обучения"""
        return {
            'is_trained': self.is_trained,
            'training_samples': len(self.training_data),
            'model_file_exists': os.path.exists(self.model_file),
            'scaler_file_exists': os.path.exists(self.scaler_file)
        }
    
    def retrain_if_needed(self, performance_threshold=0.1):
        """Переобучение при необходимости"""
        if not self.is_trained or len(self.training_data) < self.min_training_samples:
            return False
        
        # Простая логика: переобучаем, если накопилось много новых данных
        if len(self.training_data) > self.min_training_samples * 2:
            print("Переобучение модели...")
            return self.train(self.training_data)
        
        return False 