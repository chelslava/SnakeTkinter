import unittest

from ..ai_tools import AdvancedSnakeAI, GameAnalyzer


class TestAdvancedSnakeAI(unittest.TestCase):
    def setUp(self):
        self.ai = AdvancedSnakeAI()
        self.snake = [(100, 100), (90, 100), (80, 100)]
        self.food = (130, 100)
        self.obstacles = [(110, 90), (110, 110)]

    def test_heuristic(self):
        self.assertEqual(self.ai.heuristic((0, 0), (10, 10)), 20)

    def test_is_valid_position(self):
        self.assertTrue(self.ai.is_valid_position((120, 100), self.snake, self.obstacles))
        self.assertFalse(self.ai.is_valid_position((100, 100), self.snake, self.obstacles))  # snake
        self.assertFalse(self.ai.is_valid_position((110, 90), self.snake, self.obstacles))  # obstacle
        self.assertFalse(self.ai.is_valid_position((-10, 100), self.snake, self.obstacles))  # out of bounds

    def test_a_star_pathfinding(self):
        path = self.ai.a_star_pathfinding(self.snake, self.food, self.obstacles)
        self.assertIsInstance(path, list)
        self.assertGreater(len(path), 0)
        self.assertEqual(path[-1], self.food)

    def test_predict_future_collisions(self):
        result = self.ai.predict_future_collisions(self.snake, "Right", self.obstacles)
        self.assertFalse(result)

    def test_survival_probability(self):
        prob = self.ai.calculate_survival_probability(self.snake, self.food, self.obstacles)
        self.assertGreaterEqual(prob, 0)
        self.assertLessEqual(prob, 1)

    def test_generate_strategic_advice(self):
        advice = self.ai.generate_strategic_advice(self.snake, self.food, self.obstacles)
        self.assertIsInstance(advice, list)

    def test_reinforcement_learning_decision(self):
        key = self.ai.create_state_key(self.snake, self.food, self.obstacles)
        direction = self.ai.reinforcement_learning_decision(self.snake, self.food, self.obstacles, key)
        self.assertIn(direction, ["Up", "Down", "Left", "Right", None])

    def test_update_memory(self):
        key = self.ai.create_state_key(self.snake, self.food, self.obstacles)
        self.ai.reinforcement_learning_decision(self.snake, self.food, self.obstacles, key)
        self.ai.update_memory(key, "Right", 1.0)
        self.assertGreaterEqual(self.ai.memory[key]["Right"], 0.0)


class TestGameAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = GameAnalyzer()
        self.snake = [(100, 100), (90, 100), (80, 100)]
        self.food = (150, 100)
        self.obstacles = [(130, 90)]

    def test_record_and_analyze(self):
        self.analyzer.record_move(self.snake, self.food, self.obstacles, "Right", 5)
        metrics = self.analyzer.analyze_performance()
        self.assertIn("total_moves", metrics)
        self.assertGreaterEqual(metrics["total_moves"], 1)

    def test_direction_preference(self):
        self.analyzer.record_move(self.snake, self.food, self.obstacles, "Right", 5)
        prefs = self.analyzer.analyze_direction_preference()
        self.assertEqual(prefs["Right"], 1)

    def test_efficiency_score(self):
        self.analyzer.record_move(self.snake, self.food, self.obstacles, "Right", 5)
        self.analyzer.record_move(self.snake, self.food, self.obstacles, "Right", 5)
        score = self.analyzer.calculate_efficiency_score()
        self.assertGreater(score, 0)

    def test_get_recommendations(self):
        self.analyzer.record_move(self.snake, self.food, self.obstacles, "Right", 5)
        self.analyzer.record_move(self.snake, self.food, self.obstacles, "Right", 5)
        recs = self.analyzer.get_recommendations()
        self.assertIsInstance(recs, list)


if __name__ == '__main__':
    unittest.main()