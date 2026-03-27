import os
import tempfile
import unittest

from genetic_ai import GeneticSnakeAI, Genome


class TestGenome(unittest.TestCase):
    def setUp(self):
        self.genome = Genome(size=100)

    def test_initialization(self):
        """Тест инициализации генома"""
        self.assertEqual(len(self.genome.genes), 100)
        self.assertEqual(self.genome.fitness, 0.0)

    def test_genes_range(self):
        """Тест диапазона генов"""
        for gene in self.genome.genes:
            self.assertGreaterEqual(gene, -1)
            self.assertLessEqual(gene, 1)

    def test_mutate(self):
        """Тест мутации"""
        original_genes = self.genome.genes.copy()
        self.genome.mutate(mutation_rate=1.0)  # Высокая вероятность мутации
        # Гены должны измениться при 100% вероятности мутации
        self.assertNotEqual(self.genome.genes, original_genes)

    def test_crossover(self):
        """Тест скрещивания"""
        partner = Genome(100)
        child = self.genome.crossover(partner)
        self.assertEqual(len(child.genes), 100)
        self.assertIsInstance(child, Genome)

    def test_copy(self):
        """Тест копирования"""
        self.genome.fitness = 5.0
        copy = self.genome.copy()
        self.assertEqual(copy.genes, self.genome.genes)
        self.assertEqual(copy.fitness, self.genome.fitness)
        # Изменение копии не должно влиять на оригинал
        copy.genes[0] = 999
        self.assertNotEqual(copy.genes[0], self.genome.genes[0])


class TestGeneticSnakeAI(unittest.TestCase):
    def setUp(self):
        self.ai = GeneticSnakeAI(population_size=10, genome_size=50)
        self.snake = [(100, 100), (90, 100), (80, 100)]
        self.food = (130, 100)
        self.obstacles = [(110, 90), (110, 110)]

    def test_initialization(self):
        """Тест инициализации ИИ"""
        self.assertEqual(len(self.ai.population), 10)
        self.assertEqual(self.ai.generation, 0)
        self.assertEqual(self.ai.best_fitness, 0.0)

    def test_extract_features(self):
        """Тест извлечения признаков"""
        features = self.ai.extract_features(self.snake, self.food, self.obstacles)
        self.assertIsInstance(features, list)
        self.assertGreater(len(features), 0)

        # Все признаки должны быть в диапазоне [0, 1]
        for feature in features[:8]:
            self.assertGreaterEqual(feature, 0)
            self.assertLessEqual(feature, 1)

    def test_calculate_free_space(self):
        """Тест расчета свободного пространства"""
        space = self.ai._calculate_free_space(self.snake, self.obstacles)
        self.assertGreater(space, 0)

    def test_get_distance_to_wall(self):
        """Тест расстояния до стены"""
        head = (200, 200)

        dist_up = self.ai._get_distance_to_wall(head, "Up")
        dist_down = self.ai._get_distance_to_wall(head, "Down")
        dist_left = self.ai._get_distance_to_wall(head, "Left")
        dist_right = self.ai._get_distance_to_wall(head, "Right")

        self.assertGreater(dist_up, 0)
        self.assertGreater(dist_down, 0)
        self.assertGreater(dist_left, 0)
        self.assertGreater(dist_right, 0)

    def test_is_dangerous_direction(self):
        """Тест проверки опасных направлений"""
        head = self.snake[0]

        # Безопасное направление
        self.assertFalse(self.ai._is_dangerous_direction(head, "Right", self.snake, self.obstacles))

        # Опасное направление - врезается в змею
        self.assertTrue(self.ai._is_dangerous_direction(head, "Left", self.snake, self.obstacles))

    def test_get_decision(self):
        """Тест получения решения"""
        genome = self.ai.population[0]
        decision = self.ai.get_decision(genome, self.snake, self.food, self.obstacles)
        self.assertIn(decision, ["Up", "Down", "Left", "Right", None])

    def test_calculate_fitness(self):
        """Тест расчета fitness"""
        fitness = self.ai.calculate_fitness(
            score=10, steps=100, snake_length=13, food_eaten=10, time_alive=30.0
        )
        self.assertGreater(fitness, 0)

    def test_evolve(self):
        """Тест эволюции"""
        # Устанавливаем fitness для всех геномов
        for i, genome in enumerate(self.ai.population):
            genome.fitness = i * 10

        self.ai.evolve()

        self.assertEqual(self.ai.generation, 1)
        self.assertGreater(self.ai.best_fitness, 0)
        self.assertIn("generation", self.ai.history[0])

    def test_get_best_genome(self):
        """Тест получения лучшего генома"""
        for i, genome in enumerate(self.ai.population):
            genome.fitness = i * 10

        best = self.ai.get_best_genome()
        self.assertEqual(best.fitness, 90)  # Последний имеет наибольший fitness

    def test_get_statistics(self):
        """Тест получения статистики"""
        stats = self.ai.get_statistics()

        self.assertIn("generation", stats)
        self.assertIn("population_size", stats)
        self.assertIn("best_fitness", stats)
        self.assertIn("avg_fitness", stats)

    def test_save_load_population(self):
        """Тест сохранения и загрузки популяции"""
        with tempfile.NamedTemporaryFile(suffix=".pkl", delete=False) as f:
            filename = f.name

        try:
            # Устанавливаем fitness
            for i, genome in enumerate(self.ai.population):
                genome.fitness = i

            self.ai.generation = 5

            # Сохраняем
            self.ai.save_population(filename)

            # Создаем новый ИИ и загружаем
            new_ai = GeneticSnakeAI(population_size=10, genome_size=50)
            success = new_ai.load_population(filename)

            self.assertTrue(success)
            self.assertEqual(new_ai.generation, 5)
            self.assertEqual(len(new_ai.population), 10)
        finally:
            if os.path.exists(filename):
                os.remove(filename)

    def test_load_nonexistent_file(self):
        """Тест загрузки несуществующего файла"""
        result = self.ai.load_population("nonexistent_file.pkl")
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
