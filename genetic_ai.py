import math
import random
from typing import Optional


class Genome:
    """Геном для генетического алгоритма"""

    def __init__(self, size: int = 100):
        self.genes: list[float] = [random.uniform(-1, 1) for _ in range(size)]
        self.fitness: float = 0.0

    def mutate(self, mutation_rate: float = 0.1) -> None:
        """Мутация генома"""
        for i in range(len(self.genes)):
            if random.random() < mutation_rate:
                self.genes[i] += random.gauss(0, 0.5)
                self.genes[i] = max(-1, min(1, self.genes[i]))

    def crossover(self, partner: "Genome") -> "Genome":
        """Скрещивание с другим геномом"""
        child = Genome(len(self.genes))
        midpoint = random.randint(0, len(self.genes) - 1)
        for i in range(len(self.genes)):
            if i < midpoint:
                child.genes[i] = self.genes[i]
            else:
                child.genes[i] = partner.genes[i]
        return child

    def copy(self) -> "Genome":
        """Создать копию генома"""
        new_genome = Genome(len(self.genes))
        new_genome.genes = self.genes.copy()
        new_genome.fitness = self.fitness
        return new_genome


class GeneticSnakeAI:
    """Генетический алгоритм для игры Snake"""

    def __init__(
        self,
        population_size: int = 50,
        genome_size: int = 100,
        mutation_rate: float = 0.1,
        crossover_rate: float = 0.7,
        elite_size: int = 5,
    ):
        self.population_size = population_size
        self.genome_size = genome_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elite_size = elite_size

        self.population: list[Genome] = []
        self.generation: int = 0
        self.best_fitness: float = 0.0
        self.avg_fitness: float = 0.0
        self.history: list[dict] = []

        self._initialize_population()

    def _initialize_population(self) -> None:
        """Инициализация популяции"""
        self.population = [Genome(self.genome_size) for _ in range(self.population_size)]
        self.generation = 0

    def extract_features(self, snake: list, food: tuple, obstacles: list) -> list[float]:
        """Извлечение признаков из игрового состояния"""
        head = snake[0]

        features = [
            # Расстояние до еды (нормализованное)
            math.sqrt((food[0] - head[0]) ** 2 + (food[1] - head[1]) ** 2) / 400,
            # Длина змеи (нормализованная)
            len(snake) / 100,
            # Количество препятствий (нормализованное)
            len(obstacles) / 50,
            # Свободное пространство (нормализованное)
            self._calculate_free_space(snake, obstacles) / 1600,
            # Позиция головы (нормализованная)
            head[0] / 400,
            head[1] / 400,
            # Направление к еде
            (food[0] - head[0]) / 400,
            (food[1] - head[1]) / 400,
        ]

        # Расстояния до стен в 4 направлениях
        for direction in ["Up", "Down", "Left", "Right"]:
            dist = self._get_distance_to_wall(head, direction)
            features.append(dist / 400)

        # Опасность в 4 направлениях (1 = опасно, 0 = безопасно)
        for direction in ["Up", "Down", "Left", "Right"]:
            danger = self._is_dangerous_direction(head, direction, snake, obstacles)
            features.append(1.0 if danger else 0.0)

        return features

    def _calculate_free_space(self, snake: list, obstacles: list) -> int:
        """Подсчет свободного пространства"""
        total_cells = (400 // 10) * (400 // 10)
        occupied = len(snake) + len(obstacles)
        return total_cells - occupied

    def _get_distance_to_wall(self, pos: tuple, direction: str) -> int:
        """Расстояние до стены в указанном направлении"""
        x, y = pos
        cell_size = 10

        if direction == "Up":
            return y // cell_size
        elif direction == "Down":
            return (400 - y) // cell_size
        elif direction == "Left":
            return x // cell_size
        elif direction == "Right":
            return (400 - x) // cell_size
        return 0

    def _is_dangerous_direction(
        self, head: tuple, direction: str, snake: list, obstacles: list
    ) -> bool:
        """Проверка опасности направления"""
        cell_size = 10
        x, y = head

        if direction == "Up":
            new_pos = (x, y - cell_size)
        elif direction == "Down":
            new_pos = (x, y + cell_size)
        elif direction == "Left":
            new_pos = (x - cell_size, y)
        elif direction == "Right":
            new_pos = (x + cell_size, y)
        else:
            return True

        # Проверка границ
        if new_pos[0] < 0 or new_pos[0] >= 400 or new_pos[1] < 0 or new_pos[1] >= 400:
            return True

        # Проверка столкновения с змеёй
        if new_pos in snake:
            return True

        # Проверка столкновения с препятствиями
        return new_pos in obstacles

    def get_decision(
        self, genome: Genome, snake: list, food: tuple, obstacles: list
    ) -> Optional[str]:
        """Получение решения от генома"""
        features = self.extract_features(snake, food, obstacles)

        # Используем первые гены для весов
        genome.genes[:len(features)]

        # Вычисляем взвешенную сумму для каждого направления
        directions = ["Up", "Down", "Left", "Right"]
        scores = {}

        for i, direction in enumerate(directions):
            base_idx = i * 4
            if base_idx + 3 < len(genome.genes):
                score = sum(
                    f * genome.genes[base_idx + j]
                    for j, f in enumerate(features[:4])
                )
                # Добавляем штраф за опасные направления
                if self._is_dangerous_direction(snake[0], direction, snake, obstacles):
                    score -= 10
                scores[direction] = score

        if not scores:
            return None

        # Выбираем направление с максимальным score
        return max(scores, key=lambda k: scores[k])

    def calculate_fitness(
        self,
        score: int,
        steps: int,
        snake_length: int,
        food_eaten: int,
        time_alive: float,
    ) -> float:
        """Расчет fitness для генома"""
        # Основные факторы
        fitness = 0.0

        # Награда за съеденную еду (главный фактор)
        fitness += food_eaten * 100

        # Награда за длину змеи
        fitness += snake_length * 10

        # Награда за время выживания
        fitness += time_alive * 0.1

        # Штраф за много шагов без еды
        if food_eaten > 0:
            efficiency = food_eaten / max(steps, 1)
            fitness += efficiency * 50

        return fitness

    def evolve(self) -> None:
        """Эволюция популяции"""
        # Сортировка по fitness
        self.population.sort(key=lambda g: g.fitness, reverse=True)

        # Сохранение статистики
        self.best_fitness = self.population[0].fitness
        self.avg_fitness = sum(g.fitness for g in self.population) / len(self.population)

        self.history.append({
            "generation": self.generation,
            "best_fitness": self.best_fitness,
            "avg_fitness": self.avg_fitness,
        })

        # Создание нового поколения
        new_population: list[Genome] = []

        # Элита - лучшие геномы без изменений
        for i in range(self.elite_size):
            new_population.append(self.population[i].copy())

        # Скрещивание и мутация для остальных
        while len(new_population) < self.population_size:
            # Селекция (турнирная)
            parent1 = self._tournament_selection()
            parent2 = self._tournament_selection()

            # Скрещивание
            if random.random() < self.crossover_rate:
                child = parent1.crossover(parent2)
            else:
                child = parent1.copy()

            # Мутация
            child.mutate(self.mutation_rate)

            new_population.append(child)

        self.population = new_population
        self.generation += 1

    def _tournament_selection(self, tournament_size: int = 3) -> Genome:
        """Турнирная селекция"""
        tournament = random.sample(self.population, tournament_size)
        return max(tournament, key=lambda g: g.fitness)

    def get_best_genome(self) -> Genome:
        """Получить лучший геном"""
        return max(self.population, key=lambda g: g.fitness)

    def get_statistics(self) -> dict:
        """Получить статистику обучения"""
        return {
            "generation": self.generation,
            "population_size": self.population_size,
            "best_fitness": self.best_fitness,
            "avg_fitness": self.avg_fitness,
            "history_length": len(self.history),
        }

    def save_population(self, filename: str) -> None:
        """Сохранение популяции в файл"""
        import pickle
        data = {
            "population": [(g.genes, g.fitness) for g in self.population],
            "generation": self.generation,
            "history": self.history,
        }
        with open(filename, "wb") as f:
            pickle.dump(data, f)

    def load_population(self, filename: str) -> bool:
        """Загрузка популяции из файла"""
        import os
        import pickle

        if not os.path.exists(filename):
            return False

        try:
            with open(filename, "rb") as f:
                data = pickle.load(f)

            self.population = []
            for genes, fitness in data["population"]:
                genome = Genome(len(genes))
                genome.genes = genes
                genome.fitness = fitness
                self.population.append(genome)

            self.generation = data["generation"]
            self.history = data["history"]
            return True
        except Exception:
            return False
