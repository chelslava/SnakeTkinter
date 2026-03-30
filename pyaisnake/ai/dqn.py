"""
Deep Q-Network (DQN) AI for Snake game.

A reinforcement learning AI that learns to play Snake through experience.
"""

import pickle
import random
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from ..engine import Direction, SnakeGame


@dataclass
class Experience:
    """Single experience for replay buffer"""

    state: np.ndarray
    action: int
    reward: float
    next_state: np.ndarray
    done: bool


class ReplayBuffer:
    """Experience replay buffer for DQN"""

    def __init__(self, capacity: int = 50000):
        self.capacity = capacity
        self.buffer: list[Experience] = []
        self.position = 0

    def push(self, experience: Experience) -> None:
        if len(self.buffer) < self.capacity:
            self.buffer.append(experience)
        else:
            self.buffer[self.position] = experience
        self.position = (self.position + 1) % self.capacity

    def sample(self, batch_size: int) -> list[Experience]:
        return random.sample(self.buffer, min(batch_size, len(self.buffer)))

    def __len__(self) -> int:
        return len(self.buffer)


class DQNetwork:
    """Simple neural network for DQN"""

    def __init__(self, input_size: int, hidden_size: int, output_size: int):
        self.w1 = np.random.randn(input_size, hidden_size) * 0.1
        self.b1 = np.zeros(hidden_size)
        self.w2 = np.random.randn(hidden_size, hidden_size) * 0.1
        self.b2 = np.zeros(hidden_size)
        self.w3 = np.random.randn(hidden_size, output_size) * 0.1
        self.b3 = np.zeros(output_size)

    def forward(self, x: np.ndarray) -> np.ndarray:
        z1 = x @ self.w1 + self.b1
        a1 = np.maximum(0, z1)
        z2 = a1 @ self.w2 + self.b2
        a2 = np.maximum(0, z2)
        z3 = a2 @ self.w3 + self.b3
        return z3

    def predict(self, state: np.ndarray) -> int:
        q_values = self.forward(state)
        return int(np.argmax(q_values))

    def copy_from(self, other: "DQNetwork") -> None:
        self.w1 = other.w1.copy()
        self.b1 = other.b1.copy()
        self.w2 = other.w2.copy()
        self.b2 = other.b2.copy()
        self.w3 = other.w3.copy()
        self.b3 = other.b3.copy()


class DQNTrainer:
    """Trainer for DQN"""

    def __init__(
        self,
        policy_net: DQNetwork,
        target_net: DQNetwork,
        learning_rate: float = 0.001,
        gamma: float = 0.99,
        tau: float = 0.005,
    ):
        self.policy_net = policy_net
        self.target_net = target_net
        self.lr = learning_rate
        self.gamma = gamma
        self.tau = tau

    def train_step(self, batch: list[Experience]) -> float:
        states = np.array([e.state for e in batch])
        actions = np.array([e.action for e in batch])
        rewards = np.array([e.reward for e in batch])
        next_states = np.array([e.next_state for e in batch])
        dones = np.array([e.done for e in batch], dtype=np.float32)

        current_q = self.policy_net.forward(states)
        next_q = self.target_net.forward(next_states)
        target_q = current_q.copy()

        for i in range(len(batch)):
            if dones[i]:
                target_q[i, actions[i]] = rewards[i]
            else:
                target_q[i, actions[i]] = rewards[i] + self.gamma * np.max(next_q[i])

        loss = self._update_weights(states, target_q)
        self._soft_update()
        return loss

    def _update_weights(self, states: np.ndarray, targets: np.ndarray) -> float:
        x = states
        z1 = x @ self.policy_net.w1 + self.policy_net.b1
        a1 = np.maximum(0, z1)
        z2 = a1 @ self.policy_net.w2 + self.policy_net.b2
        a2 = np.maximum(0, z2)
        output = a2 @ self.policy_net.w3 + self.policy_net.b3

        loss = np.mean((output - targets) ** 2)

        d_output = 2 * (output - targets) / len(states)
        d_w3 = a2.T @ d_output
        d_b3 = np.sum(d_output, axis=0)

        d_a2 = d_output @ self.policy_net.w3.T
        d_z2 = d_a2 * (z2 > 0)
        d_w2 = a1.T @ d_z2
        d_b2 = np.sum(d_z2, axis=0)

        d_a1 = d_z2 @ self.policy_net.w2.T
        d_z1 = d_a1 * (z1 > 0)
        d_w1 = x.T @ d_z1
        d_b1 = np.sum(d_z1, axis=0)

        self.policy_net.w3 -= self.lr * d_w3
        self.policy_net.b3 -= self.lr * d_b3
        self.policy_net.w2 -= self.lr * d_w2
        self.policy_net.b2 -= self.lr * d_b2
        self.policy_net.w1 -= self.lr * d_w1
        self.policy_net.b1 -= self.lr * d_b1

        return float(loss)

    def _soft_update(self) -> None:
        self.target_net.w1 = self.tau * self.policy_net.w1 + (1 - self.tau) * self.target_net.w1
        self.target_net.b1 = self.tau * self.policy_net.b1 + (1 - self.tau) * self.target_net.b1
        self.target_net.w2 = self.tau * self.policy_net.w2 + (1 - self.tau) * self.target_net.w2
        self.target_net.b2 = self.tau * self.policy_net.b2 + (1 - self.tau) * self.target_net.b2
        self.target_net.w3 = self.tau * self.policy_net.w3 + (1 - self.tau) * self.target_net.w3
        self.target_net.b3 = self.tau * self.policy_net.b3 + (1 - self.tau) * self.target_net.b3


class DQNAI:
    """Deep Q-Network AI for Snake"""

    STATE_SIZE = 11
    ACTION_SIZE = 4
    HIDDEN_SIZE = 256

    ACTIONS = ["UP", "DOWN", "LEFT", "RIGHT"]

    def __init__(
        self,
        game: "SnakeGame",
        epsilon_start: float = 1.0,
        epsilon_end: float = 0.01,
        epsilon_decay: float = 0.995,
    ):
        self.game = game
        self.epsilon = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay

        self.policy_net = DQNetwork(self.STATE_SIZE, self.HIDDEN_SIZE, self.ACTION_SIZE)
        self.target_net = DQNetwork(self.STATE_SIZE, self.HIDDEN_SIZE, self.ACTION_SIZE)
        self.target_net.copy_from(self.policy_net)

        self.trainer = DQNTrainer(self.policy_net, self.target_net)
        self.memory = ReplayBuffer()

        self._last_state: np.ndarray | None = None
        self._last_action: int = 0
        self._training_mode = False
        self._total_steps = 0

    def get_state(self) -> np.ndarray:
        """Extract state representation from game"""
        head = self.game.snake[0]
        food = self.game.food or (0, 0)

        danger_straight = 0
        danger_right = 0
        danger_left = 0

        dir_idx = self._get_direction_index()
        for i, danger_idx in enumerate([(dir_idx) % 4, (dir_idx + 1) % 4, (dir_idx + 3) % 4]):
            new_pos = self._get_next_position(head, self.ACTIONS[danger_idx])
            if not self._is_safe(new_pos):
                if i == 0:
                    danger_straight = 1
                elif i == 1:
                    danger_right = 1
                else:
                    danger_left = 1

        moving_up = 1 if self.game.direction.value == "Up" else 0
        moving_down = 1 if self.game.direction.value == "Down" else 0
        moving_left = 1 if self.game.direction.value == "Left" else 0
        moving_right = 1 if self.game.direction.value == "Right" else 0

        food_left = 1 if food[0] < head[0] else 0
        food_right = 1 if food[0] > head[0] else 0
        food_up = 1 if food[1] < head[1] else 0
        food_down = 1 if food[1] > head[1] else 0

        return np.array(
            [
                danger_straight,
                danger_right,
                danger_left,
                moving_up,
                moving_down,
                moving_left,
                moving_right,
                food_left,
                food_right,
                food_up,
                food_down,
            ],
            dtype=np.float32,
        )

    def _get_direction_index(self) -> int:
        return self.ACTIONS.index(self.game.direction.value.upper())

    def _get_next_position(self, pos: tuple[int, int], action: str) -> tuple[int, int]:
        x, y = pos
        if action == "UP":
            return (x, y - 1)
        elif action == "DOWN":
            return (x, y + 1)
        elif action == "LEFT":
            return (x - 1, y)
        else:
            return (x + 1, y)

    def _is_safe(self, pos: tuple[int, int]) -> bool:
        x, y = pos
        if x < 0 or x >= self.game.config.width:
            return False
        if y < 0 or y >= self.game.config.height:
            return False
        if pos in set(self.game.snake[:-1]):
            return False
        return pos not in self.game.obstacles

    def get_direction(self) -> "Direction | None":
        """Get next direction using DQN"""
        from ..engine import Direction

        state = self.get_state()

        if self._training_mode and self._last_state is not None:
            reward = self._calculate_reward()
            done = self.game.state.value == "game_over"
            experience = Experience(
                state=self._last_state,
                action=self._last_action,
                reward=reward,
                next_state=state,
                done=done,
            )
            self.memory.push(experience)

        if random.random() < self.epsilon:
            action = random.randint(0, 3)
        else:
            action = self.policy_net.predict(state)

        self._last_state = state
        self._last_action = action
        self._total_steps += 1

        if self._training_mode and len(self.memory) >= 100:
            batch = self.memory.sample(32)
            self.trainer.train_step(batch)

            self.epsilon = max(self.epsilon_end, self.epsilon * self.epsilon_decay)

        return getattr(Direction, self.ACTIONS[action])

    def _calculate_reward(self) -> float:
        """Calculate reward based on game state"""
        if self.game.state.value == "game_over":
            return -10.0

        head = self.game.snake[0]
        food = self.game.food

        if food and head == food:
            return 10.0

        last_state = self._last_state
        if food and last_state is not None:
            dist_old = abs(last_state[7] - last_state[8]) + abs(last_state[9] - last_state[10])
            new_state = self.get_state()
            dist_new = abs(new_state[7] - new_state[8]) + abs(new_state[9] - new_state[10])
            if dist_new < dist_old:
                return 0.1
            else:
                return -0.1

        return -0.01

    def start_training(self) -> None:
        """Enable training mode"""
        self._training_mode = True
        self._last_state = None

    def stop_training(self) -> None:
        """Disable training mode"""
        self._training_mode = False

    def save_model(self, path: str) -> None:
        """Save model to file"""
        data = {
            "policy_net": {
                "w1": self.policy_net.w1,
                "b1": self.policy_net.b1,
                "w2": self.policy_net.w2,
                "b2": self.policy_net.b2,
                "w3": self.policy_net.w3,
                "b3": self.policy_net.b3,
            },
            "epsilon": self.epsilon,
            "total_steps": self._total_steps,
        }
        with open(path, "wb") as f:
            pickle.dump(data, f)

    def load_model(self, path: str) -> None:
        """Load model from file"""
        model_path = Path(path)
        if not model_path.exists():
            return

        with open(model_path, "rb") as f:
            data = pickle.load(f)

        weights = data["policy_net"]
        self.policy_net.w1 = weights["w1"]
        self.policy_net.b1 = weights["b1"]
        self.policy_net.w2 = weights["w2"]
        self.policy_net.b2 = weights["b2"]
        self.policy_net.w3 = weights["w3"]
        self.policy_net.b3 = weights["b3"]
        self.target_net.copy_from(self.policy_net)

        self.epsilon = data.get("epsilon", 0.01)
        self._total_steps = data.get("total_steps", 0)
