import math
import os
import pickle
import random


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

    DIRECTIONS = ["Up", "Down", "Left", "Right"]
    CELL_SIZE = 10
    FIELD_SIZE = 400

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
        self.best_genome: Genome | None = None

        self.current_genome_index = 0
        self.genome_scores: list[int] = []

        self._initialize_population()

    def _initialize_population(self) -> None:
        """Инициализация популяции"""
        self.population = [Genome(self.genome_size) for _ in range(self.population_size)]
        self.generation = 0
        self.current_genome_index = 0
        self.genome_scores = []

    def extract_features(self, snake: list, food: tuple, obstacles: list) -> list[float]:
        """Извлечение признаков из игрового состояния"""
        head = snake[0]

        features = [
            math.sqrt((food[0] - head[0]) ** 2 + (food[1] - head[1]) ** 2) / self.FIELD_SIZE,
            len(snake) / 100,
            len(obstacles) / 50,
            self._calculate_free_space(snake, obstacles) / 1600,
            head[0] / self.FIELD_SIZE,
            head[1] / self.FIELD_SIZE,
            (food[0] - head[0]) / self.FIELD_SIZE,
            (food[1] - head[1]) / self.FIELD_SIZE,
        ]

        for direction in self.DIRECTIONS:
            dist = self._get_distance_to_wall(head, direction)
            features.append(dist / 40)

        for direction in self.DIRECTIONS:
            danger = self._is_dangerous_direction(head, direction, snake, obstacles)
            features.append(1.0 if danger else 0.0)

        for direction in self.DIRECTIONS:
            next_pos = self._get_next_position(head, direction)
            new_dist = math.sqrt((food[0] - next_pos[0]) ** 2 + (food[1] - next_pos[1]) ** 2)
            features.append(new_dist / self.FIELD_SIZE)

        for direction in self.DIRECTIONS:
            escape_count = self._count_escape_routes(
                self._get_next_position(head, direction), snake, obstacles
            )
            features.append(escape_count / 4)

        return features

    def _get_next_position(self, pos: tuple, direction: str) -> tuple:
        """Получить следующую позицию"""
        x, y = pos
        if direction == "Up":
            return (x, y - self.CELL_SIZE)
        elif direction == "Down":
            return (x, y + self.CELL_SIZE)
        elif direction == "Left":
            return (x - self.CELL_SIZE, y)
        elif direction == "Right":
            return (x + self.CELL_SIZE, y)
        return pos

    def _count_escape_routes(self, pos: tuple, snake: list, obstacles: list) -> int:
        """Подсчет путей escapes из позиции"""
        if not self._is_valid_position(pos, snake, obstacles):
            return 0

        count = 0
        for direction in self.DIRECTIONS:
            next_pos = self._get_next_position(pos, direction)
            if self._is_valid_position(next_pos, snake, obstacles):
                count += 1
        return count

    def _is_valid_position(self, pos: tuple, snake: list, obstacles: list) -> bool:
        """Проверка валидности позиции"""
        x, y = pos
        if x < 0 or x >= self.FIELD_SIZE or y < 0 or y >= self.FIELD_SIZE:
            return False
        if pos in snake:
            return False
        return pos not in obstacles

    def _calculate_free_space(self, snake: list, obstacles: list) -> int:
        """Подсчет свободного пространства"""
        total_cells = (self.FIELD_SIZE // self.CELL_SIZE) ** 2
        occupied = len(snake) + len(obstacles)
        return total_cells - occupied

    def _get_distance_to_wall(self, pos: tuple, direction: str) -> int:
        """Расстояние до стены в указанном направлении"""
        x, y = pos

        if direction == "Up":
            return y // self.CELL_SIZE
        elif direction == "Down":
            return (self.FIELD_SIZE - y) // self.CELL_SIZE
        elif direction == "Left":
            return x // self.CELL_SIZE
        elif direction == "Right":
            return (self.FIELD_SIZE - x) // self.CELL_SIZE
        return 0

    def _is_dangerous_direction(
        self, head: tuple, direction: str, snake: list, obstacles: list
    ) -> bool:
        """Проверка опасности направления"""
        new_pos = self._get_next_position(head, direction)
        return not self._is_valid_position(new_pos, snake, obstacles)

    def get_decision(
        self, genome: Genome | None, snake: list, food: tuple, obstacles: list
    ) -> str | None:
        """Получение решения от генома"""
        if genome is None:
            genome = self.get_best_genome()

        if genome is None:
            return None

        features = self.extract_features(snake, food, obstacles)
        scores: dict[str, float] = {}

        for i, direction in enumerate(self.DIRECTIONS):
            base_idx = i * 5
            if base_idx + 4 < len(genome.genes):
                score = sum(
                    features[j] * genome.genes[base_idx + j] for j in range(min(5, len(features)))
                )

                if self._is_dangerous_direction(snake[0], direction, snake, obstacles):
                    score -= 100

                escape_routes = self._count_escape_routes(
                    self._get_next_position(snake[0], direction), snake, obstacles
                )
                score += (
                    escape_routes * 5 * genome.genes[base_idx + 4]
                    if base_idx + 4 < len(genome.genes)
                    else 0
                )

                scores[direction] = score

        if not scores:
            safe_dirs = [
                d
                for d in self.DIRECTIONS
                if not self._is_dangerous_direction(snake[0], d, snake, obstacles)
            ]
            return random.choice(safe_dirs) if safe_dirs else None

        max_score = max(scores.values())
        best_dirs = [d for d, s in scores.items() if s == max_score]
        return random.choice(best_dirs)

    def record_game_result(self, score: int, steps: int, time_alive: float) -> None:
        """Запись результата игры для текущего генома"""
        if self.current_genome_index < len(self.population):
            genome = self.population[self.current_genome_index]
            genome.fitness = self.calculate_fitness(score, steps, score + 3, score, time_alive)
            self.genome_scores.append(score)

    def calculate_fitness(
        self,
        score: int,
        steps: int,
        snake_length: int,
        food_eaten: int,
        time_alive: float,
    ) -> float:
        """Расчет fitness для генома"""
        fitness = 0.0

        fitness += food_eaten * 1000

        fitness += snake_length * 50

        fitness += time_alive * 0.5

        if food_eaten > 0:
            efficiency = food_eaten / max(steps, 1)
            fitness += efficiency * 500

        if steps > 50 and food_eaten == 0:
            fitness -= (steps - 50) * 2

        return max(0, fitness)

    def advance_genome(self) -> bool:
        """Переход к следующему геному"""
        self.current_genome_index += 1

        if self.current_genome_index >= self.population_size:
            self.evolve()
            self.current_genome_index = 0
            self.genome_scores = []
            return True

        return False

    def evolve(self) -> None:
        """Эволюция популяции"""
        self.population.sort(key=lambda g: g.fitness, reverse=True)

        self.best_fitness = self.population[0].fitness
        self.avg_fitness = sum(g.fitness for g in self.population) / len(self.population)
        self.best_genome = self.population[0].copy()

        self.history.append(
            {
                "generation": self.generation,
                "best_fitness": self.best_fitness,
                "avg_fitness": self.avg_fitness,
                "best_score": max(self.genome_scores) if self.genome_scores else 0,
                "avg_score": sum(self.genome_scores) / len(self.genome_scores)
                if self.genome_scores
                else 0,
            }
        )

        new_population: list[Genome] = []

        for i in range(self.elite_size):
            elite = self.population[i].copy()
            elite.mutate(self.mutation_rate * 0.1)
            new_population.append(elite)

        while len(new_population) < self.population_size:
            parent1 = self._tournament_selection()
            parent2 = self._tournament_selection()

            if random.random() < self.crossover_rate:
                child = parent1.crossover(parent2)
            else:
                child = parent1.copy()

            child.mutate(self.mutation_rate)
            new_population.append(child)

        self.population = new_population
        self.generation += 1

        self.save_population("genetic_population.pkl")

    def _tournament_selection(self, tournament_size: int = 3) -> Genome:
        """Турнирная селекция"""
        tournament = random.sample(self.population, tournament_size)
        return max(tournament, key=lambda g: g.fitness)

    def get_best_genome(self) -> Genome:
        """Получить лучший геном"""
        if self.best_genome is not None:
            return self.best_genome
        return max(self.population, key=lambda g: g.fitness)

    def get_current_genome(self) -> Genome | None:
        """Получить текущий геном для тестирования"""
        if self.current_genome_index < len(self.population):
            return self.population[self.current_genome_index]
        return None

    def get_statistics(self) -> dict:
        """Получить статистику обучения"""
        return {
            "generation": self.generation,
            "population_size": self.population_size,
            "current_genome": self.current_genome_index,
            "best_fitness": self.best_fitness,
            "avg_fitness": self.avg_fitness,
            "history_length": len(self.history),
            "current_score": self.genome_scores[-1] if self.genome_scores else 0,
        }

    def save_population(self, filename: str) -> None:
        """Сохранение популяции в файл"""
        data = {
            "population": [(g.genes, g.fitness) for g in self.population],
            "generation": self.generation,
            "history": self.history,
            "best_genome": (
                (self.best_genome.genes, self.best_genome.fitness) if self.best_genome else None
            ),
        }
        with open(filename, "wb") as f:
            pickle.dump(data, f)

    def load_population(self, filename: str) -> bool:
        """Загрузка популяции из файла"""
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

            self.generation = data.get("generation", 0)
            self.history = data.get("history", [])

            if data.get("best_genome"):
                genes, fitness = data["best_genome"]
                self.best_genome = Genome(len(genes))
                self.best_genome.genes = genes
                self.best_genome.fitness = fitness

            return True
        except Exception:
            return False
