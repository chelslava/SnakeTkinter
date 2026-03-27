import math
import os
import pickle
import random

import numpy as np
from sklearn.metrics import mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler


class NeuralSnakeAI:
    """Нейронная сеть для игры Snake"""

    DIRECTIONS = ["Up", "Down", "Left", "Right"]
    DIRECTION_TO_INDEX = {"Up": 0, "Down": 1, "Left": 2, "Right": 3}

    def __init__(self, hidden_layers=(100, 50, 25)):
        self.model = MLPRegressor(
            hidden_layer_sizes=hidden_layers,
            max_iter=1000,
            random_state=42,
            learning_rate="adaptive",
            early_stopping=True,
            validation_fraction=0.1,
        )
        self.scaler = StandardScaler()
        self.training_data: list = []
        self.is_trained = False
        self.model_file = "neural_snake_model.pkl"
        self.scaler_file = "neural_snake_scaler.pkl"

        self.min_training_samples = 100
        self.max_training_samples = 10000
        self.retrain_threshold = 0.1

    def extract_features(self, snake, food, obstacles):
        """Извлечение признаков для нейросети"""
        head = snake[0]

        features = [
            math.sqrt((food[0] - head[0]) ** 2 + (food[1] - head[1]) ** 2) / 400,
            len(snake) / 100,
            len(obstacles) / 50,
            self.calculate_free_space(snake, obstacles) / 1600,
            len(self.get_safe_directions(snake, food, obstacles)) / 4,
            head[0] / 400,
            head[1] / 400,
            (food[0] - head[0]) / 400,
            (food[1] - head[1]) / 400,
        ]

        obstacle_features = self.get_obstacle_features(head, obstacles)
        features.extend(obstacle_features)

        body_features = self.get_body_features(snake)
        features.extend(body_features)

        direction_features = self.get_direction_scores(head, food, snake, obstacles)
        features.extend(direction_features)

        return np.array(features)

    def get_direction_scores(self, head, food, snake, obstacles):
        """Вычисление оценки для каждого направления"""
        scores = []
        for direction in self.DIRECTIONS:
            next_pos = self.get_next_position(head, direction)
            if not self.is_valid_position(next_pos, snake, obstacles):
                scores.append(-1.0)
            else:
                new_distance = math.sqrt(
                    (food[0] - next_pos[0]) ** 2 + (food[1] - next_pos[1]) ** 2
                )
                scores.append(1.0 - new_distance / 400)
        return scores

    def get_obstacle_features(self, head, obstacles):
        """Получение признаков препятствий"""
        features = []
        for direction in self.DIRECTIONS:
            distance = self.get_distance_to_obstacle(head, obstacles, direction)
            features.append(distance / 400)
        return features

    def get_body_features(self, snake):
        """Получение признаков тела змеи"""
        head = snake[0]
        features = []

        min_distance = float("inf")
        for segment in snake[1:]:
            distance = math.sqrt((segment[0] - head[0]) ** 2 + (segment[1] - head[1]) ** 2)
            min_distance = min(min_distance, distance)

        features.append(min_distance / 400 if min_distance != float("inf") else 1.0)

        radius = 50
        nearby_segments = 0
        for segment in snake[1:]:
            distance = math.sqrt((segment[0] - head[0]) ** 2 + (segment[1] - head[1]) ** 2)
            if distance <= radius:
                nearby_segments += 1

        features.append(nearby_segments / 10)

        return features

    def get_distance_to_obstacle(self, head, obstacles, direction):
        """Получение расстояния до ближайшего препятствия в направлении"""
        x, y = head
        cell_size = 10
        dx, dy = 0, 0

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

        return 400

    def calculate_free_space(self, snake, obstacles):
        """Подсчет свободного пространства"""
        total_cells = (400 // 10) * (400 // 10)
        occupied = len(snake) + len(obstacles)
        return total_cells - occupied

    def get_safe_directions(self, snake, food, obstacles):
        """Получить безопасные направления движения"""
        head = snake[0]
        safe_dirs = []

        for direction in self.DIRECTIONS:
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

        if x < 0 or x >= 400 or y < 0 or y >= 400:
            return False

        if pos in snake:
            return False

        return pos not in obstacles

    def predict_best_action(self, snake, food, obstacles):
        """Предсказание лучшего действия на основе обученной модели"""
        if not self.is_trained:
            return self._heuristic_fallback(snake, food, obstacles)

        try:
            safe_dirs = self.get_safe_directions(snake, food, obstacles)
            if not safe_dirs:
                return None

            if len(safe_dirs) == 1:
                return safe_dirs[0]

            features = self.extract_features(snake, food, obstacles)

            direction_scores = features[-4:]

            best_dir = None
            best_score = float("-inf")

            for direction in safe_dirs:
                idx = self.DIRECTION_TO_INDEX[direction]
                score = direction_scores[idx]
                if score > best_score:
                    best_score = score
                    best_dir = direction

            if best_dir and best_score > 0:
                return best_dir

            return self._heuristic_fallback(snake, food, obstacles)

        except Exception as e:
            print(f"Ошибка предсказания: {e}")
            return self._heuristic_fallback(snake, food, obstacles)

    def _heuristic_fallback(self, snake, food, obstacles):
        """Эвристический fallback при отсутствии обученной модели"""
        head = snake[0]
        safe_dirs = self.get_safe_directions(snake, food, obstacles)

        if not safe_dirs:
            return None

        best_dir = None
        best_score = float("-inf")

        for direction in safe_dirs:
            next_pos = self.get_next_position(head, direction)
            new_distance = math.sqrt((food[0] - next_pos[0]) ** 2 + (food[1] - next_pos[1]) ** 2)

            escape_routes = len(self.get_safe_directions([next_pos], food, obstacles))

            score = -new_distance + escape_routes * 20

            if score > best_score:
                best_score = score
                best_dir = direction

        return best_dir or safe_dirs[0]

    def train(self, training_data):
        """Обучение нейросети с улучшенной подготовкой данных"""
        if len(training_data) < self.min_training_samples:
            print(
                f"Недостаточно данных для обучения: {len(training_data)} < {self.min_training_samples}"
            )
            return False

        try:
            X = []
            y = []

            for state, action, reward in training_data:
                features = self.extract_features(*state)
                X.append(features)

                action_score = np.zeros(4)
                if action in self.DIRECTION_TO_INDEX:
                    idx = self.DIRECTION_TO_INDEX[action]
                    action_score[idx] = reward
                y.append(action_score)

            if len(X) > self.max_training_samples:
                indices = random.sample(range(len(X)), self.max_training_samples)
                X = [X[i] for i in indices]
                y = [y[i] for i in indices]

            X = np.array(X)
            y = np.array(y)

            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )

            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)

            self.model.fit(X_train_scaled, y_train)

            y_pred = self.model.predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)

            print(f"Модель обучена. MSE: {mse:.4f}")
            self.is_trained = True

            self.save_model()

            return True

        except Exception as e:
            print(f"Ошибка обучения: {e}")
            return False

    def add_training_data(self, snake, food, obstacles, action, reward):
        """Добавление данных для обучения с автоматическим расчётом награды"""
        if reward is None:
            head = snake[0]
            next_pos = self.get_next_position(head, action)

            if not self.is_valid_position(next_pos, snake, obstacles):
                reward = -10
            else:
                old_distance = math.sqrt((food[0] - head[0]) ** 2 + (food[1] - head[1]) ** 2)
                new_distance = math.sqrt(
                    (food[0] - next_pos[0]) ** 2 + (food[1] - next_pos[1]) ** 2
                )

                if new_distance < old_distance:
                    reward = 1
                else:
                    reward = -0.5

                escape_routes = len(self.get_safe_directions([next_pos], food, obstacles))
                if escape_routes == 0:
                    reward -= 5
                elif escape_routes == 1:
                    reward -= 2

        self.training_data.append(((list(snake), food, list(obstacles)), action, reward))

        if len(self.training_data) > self.max_training_samples:
            self.training_data = self.training_data[-self.max_training_samples :]

    def save_model(self):
        """Сохранение обученной модели"""
        try:
            with open(self.model_file, "wb") as f:
                pickle.dump(self.model, f)

            with open(self.scaler_file, "wb") as f:
                pickle.dump(self.scaler, f)

            print("Модель сохранена")
        except Exception as e:
            print(f"Ошибка сохранения модели: {e}")

    def load_model(self):
        """Загрузка обученной модели"""
        try:
            if os.path.exists(self.model_file) and os.path.exists(self.scaler_file):
                with open(self.model_file, "rb") as f:
                    self.model = pickle.load(f)

                with open(self.scaler_file, "rb") as f:
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
            "is_trained": self.is_trained,
            "training_samples": len(self.training_data),
            "model_file_exists": os.path.exists(self.model_file),
            "scaler_file_exists": os.path.exists(self.scaler_file),
        }

    def retrain_if_needed(self, performance_threshold=0.1):
        """Переобучение при необходимости"""
        if not self.is_trained or len(self.training_data) < self.min_training_samples:
            return False

        if len(self.training_data) > self.min_training_samples * 2:
            print("Переобучение модели...")
            return self.train(self.training_data)

        return False
