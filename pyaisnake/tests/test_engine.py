"""
Tests for PyAISnake engine.
"""

import unittest

from pyaisnake.engine import Direction, GameConfig, GameState, PowerUp, PowerUpType, SnakeGame


class TestSnakeGame(unittest.TestCase):
    """Test SnakeGame engine"""

    def setUp(self):
        config = GameConfig(width=20, height=10)
        self.game = SnakeGame(config)

    def test_initialization(self):
        """Test game initialization"""
        self.assertEqual(self.game.state, GameState.RUNNING)
        self.assertEqual(len(self.game.snake), 3)
        self.assertIsNotNone(self.game.food)

    def test_snake_movement(self):
        """Test snake moves correctly"""
        initial_head = self.game.snake[0]
        self.game.update()

        # Snake should have moved
        new_head = self.game.snake[0]
        self.assertNotEqual(initial_head, new_head)

        # Head should be one step in direction
        self.assertEqual(new_head[0], initial_head[0] + 1)  # RIGHT direction

    def test_direction_change(self):
        """Test direction change"""
        self.assertTrue(self.game.set_direction(Direction.UP))
        self.game.update()

        head = self.game.snake[0]
        prev_head = self.game.snake[1]

        # Should move up
        self.assertEqual(head[1], prev_head[1] - 1)

    def test_opposite_direction_invalid(self):
        """Test that opposite direction is rejected"""
        # Default direction is RIGHT
        result = self.game.set_direction(Direction.LEFT)
        self.assertFalse(result)

    def test_food_eaten(self):
        """Test eating food"""
        food_eaten = [False]

        def on_food():
            food_eaten[0] = True

        self.game.on_food_eaten = on_food

        # Place food right in front of snake
        head = self.game.snake[0]
        self.game.food = (head[0] + 1, head[1])

        self.game.update()

        self.assertTrue(food_eaten[0])
        self.assertEqual(self.game.stats.score, 1)
        self.assertEqual(len(self.game.snake), 4)  # Grew by 1

    def test_wall_collision(self):
        """Test collision with wall"""
        # Move snake to right wall
        head = self.game.snake[0]
        self.game.snake[0] = (self.game.config.width - 1, head[1])

        self.game.update()

        self.assertEqual(self.game.state, GameState.GAME_OVER)

    def test_self_collision(self):
        """Test collision with self"""
        # Create snake that will collide
        self.game.snake = [
            (5, 5),
            (6, 5),
            (7, 5),
            (7, 6),
            (7, 7),
            (6, 7),
            (5, 7),
            (5, 6),
        ]
        self.game.direction = Direction.DOWN

        self.game.update()

        self.assertEqual(self.game.state, GameState.GAME_OVER)

    def test_pause(self):
        """Test pause functionality"""
        initial_head = self.game.snake[0]

        self.game.pause()
        self.assertEqual(self.game.state, GameState.PAUSED)

        # Game should not update when paused
        self.game.update()
        self.assertEqual(self.game.snake[0], initial_head)

        # Unpause
        self.game.pause()
        self.assertEqual(self.game.state, GameState.RUNNING)

    def test_reset(self):
        """Test game reset"""
        self.game.update()
        self.game.stats.score = 10

        self.game.reset()

        self.assertEqual(self.game.state, GameState.RUNNING)
        self.assertEqual(self.game.stats.score, 0)
        self.assertEqual(len(self.game.snake), 3)

    def test_get_safe_directions(self):
        """Test getting safe directions"""
        safe = self.game.get_safe_directions()

        # Should have some safe directions at start
        self.assertGreater(len(safe), 0)

        # UP and DOWN should be safe (not opposite to RIGHT)
        self.assertIn(Direction.UP, safe)
        self.assertIn(Direction.DOWN, safe)

    def test_obstacles(self):
        """Test obstacle collision"""
        config = GameConfig(width=20, height=10, initial_obstacles=5)
        game = SnakeGame(config)

        # Should have obstacles
        self.assertEqual(len(game.obstacles), 5)

    def test_mushroom_shrinks_snake_by_three_segments(self):
        """Test mushroom shrinks the snake by up to three segments"""
        self.game.snake = [(x, 5) for x in range(8, 0, -1)]
        self.game.current_power_up = PowerUp(PowerUpType.MUSHROOM, position=(0, 0))

        self.game._collect_power_up()

        self.assertEqual(len(self.game.snake), 5)
        self.assertEqual(self.game.stats.score, 1)
        self.assertEqual(self.game.stats.food_eaten, 1)

    def test_mushroom_keeps_minimum_snake_length(self):
        """Test mushroom does not shrink the snake below length three"""
        self.game.snake = [(x, 5) for x in range(5, 0, -1)]
        self.game.current_power_up = PowerUp(PowerUpType.MUSHROOM, position=(0, 0))

        self.game._collect_power_up()

        self.assertEqual(len(self.game.snake), 3)
        self.assertEqual(self.game.stats.score, 1)
        self.assertEqual(self.game.stats.food_eaten, 1)


class TestGameConfig(unittest.TestCase):
    """Test GameConfig"""

    def test_default_values(self):
        """Test default configuration"""
        config = GameConfig()

        self.assertEqual(config.width, 40)
        self.assertEqual(config.height, 40)
        self.assertEqual(config.speed_ms, 100)
        self.assertEqual(config.initial_obstacles, 0)


if __name__ == "__main__":
    unittest.main()
