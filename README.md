# 🐍 PyAISnake - CLI Snake Game with AI

Modern Snake game with AI capabilities - now fully in terminal!

## 🚀 Quick Start

```bash
# Install
uv sync

# Play the game
uv run pyaisnake play

# Watch AI play
uv run pyaisnake ai --visualize

# View statistics
uv run pyaisnake stats
```

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/chelslava/SnakeTkinter.git
cd SnakeTkinter

# Install dependencies with uv
uv sync
```

---

## 🎮 Commands

### `play` - Ручная игра

Играйте в Snake вручную в терминале с клавиатуры.

```bash
uv run pyaisnake play [OPTIONS]

Options:
  --width, -W     Ширина поля (по умолчанию: 40)
  --height, -H    Высота поля (по умолчанию: 20)
  --speed, -s     Скорость игры в мс (по умолчанию: 100, меньше = быстрее)
  --obstacles, -o Количество препятствий (по умолчанию: 0)
  --ascii         Использовать ASCII вместо Unicode
```

**Управление:**
| Клавиша | Действие |
|---------|----------|
| `↑↓←→` или `WASD` | Движение |
| `P` или `Space` | Пауза |
| `R` | Рестарт |
| `Q` или `Esc` | Выход |

**Для чего нужен:**
- Ручная игра для удовольствия
- Сбор данных для обучения ИИ (игра записывается)
- Тестирование игровых механик
- Развлечение и тренировка реакции

**Примеры:**
```bash
# Обычная игра
uv run pyaisnake play

# Быстрая игра на большом поле
uv run pyaisnake play --width 60 --height 30 --speed 50

# С препятствиями
uv run pyaisnake play --obstacles 10
```

---

### `ai` - ИИ играет

Позволяет ИИ играть в Snake. Полезно для демонстрации, тестирования алгоритмов и сравнения производительности.

```bash
uv run pyaisnake ai [OPTIONS]

Options:
  --algorithm, -a  Алгоритм ИИ: a_star, neural, genetic, random (по умолчанию: a_star)
  --visualize, -V  Показать визуализацию в реальном времени
  --games, -g      Количество игр (по умолчанию: 1)
  --width, -W      Ширина поля
  --height, -H     Высота поля
  --speed, -s      Скорость в мс (только с --visualize)
```

**Для чего нужен:**
- Демонстрация работы алгоритмов ИИ
- Сравнение эффективности разных алгоритмов
- Тестирование обученных моделей
- Бенчмаркинг (запуск множества игр без визуализации)
- Наблюдение за стратегиями ИИ

**Примеры:**
```bash
# Смотреть как A* играет
uv run pyaisnake ai --visualize

# Быстрый бенчмарк - 100 игр без визуализации
uv run pyaisnake ai --algorithm a_star --games 100

# Тест нейросети
uv run pyaisnake ai --algorithm neural --visualize

# Сравнить алгоритмы
uv run pyaisnake ai --algorithm random --games 50
uv run pyaisnake ai --algorithm a_star --games 50
```

**Сравнение алгоритмов:**
| Алгоритм | Средний счёт | Скорость | Описание |
|----------|-------------|----------|----------|
| `a_star` | Высокий | Средняя | Оптимальный поиск пути |
| `neural` | Средний | Быстрая | Нейросеть требует обучения |
| `genetic` | Средний | Быстрая | Эволюционный алгоритм |
| `random` | Низкий | Очень быстрая | Случайные безопасные ходы |

---

### `train` - Обучение ИИ

Обучает модели ИИ на основе сыгранных игр. Критически важно для нейросети и генетического алгоритма.

```bash
uv run pyaisnake train [OPTIONS]

Options:
  --algorithm, -a  Алгоритм для обучения: neural, genetic (обязательно)
  --games, -g      Количество обучающих игр (по умолчанию: 100)
  --save           Сохранить модель в файл
  --load           Загрузить существующую модель для дообучения
```

**Для чего нужен:**
- **Нейросеть**: Обучается на данных о ходах и наградах
- **Генетический алгоритм**: Эволюционирует популяцию геномов
- Дообучение существующих моделей
- Создание оптимальных стратегий

**Как работает обучение:**

#### Нейросеть (Neural Network)
```
1. Играет множество игр, собирая данные
2. Извлекает признаки из каждого состояния
3. Вычисляет награду за каждый ход
4. Обучает MLPRegressor предсказывать лучшие действия
5. Сохраняет модель для использования
```

#### Генетический алгоритм (Genetic)
```
1. Создаёт популяцию геномов (веса решений)
2. Каждый геном играет игру
3. Оценивается fitness (счёт, эффективность)
4. Лучшие геномы скрещиваются
5. Происходит мутация
6. Повторяется много поколений
```

**Примеры:**
```bash
# Обучить нейросеть с нуля
uv run pyaisnake train --algorithm neural --games 1000 --save neural_model.pkl

# Дообучить существующую модель
uv run pyaisnake train --algorithm neural --load neural_model.pkl --games 500 --save neural_model_v2.pkl

# Обучить генетический алгоритм
uv run pyaisnake train --algorithm genetic --games 500 --save genetic_model.pkl

# Быстрое обучение для тестирования
uv run pyaisnake train --algorithm neural --games 100
```

**Рекомендации по обучению:**
| Модель | Мин. игры | Рекомендуется | Время обучения |
|--------|-----------|---------------|----------------|
| Neural | 100 | 1000-5000 | 1-10 минут |
| Genetic | 50 | 200-1000 | 30 сек - 5 минут |

---

### `stats` - Статистика

Просмотр истории игр и статистики. Данные сохраняются в SQLite базу.

```bash
uv run pyaisnake stats [OPTIONS]

Options:
  --top, -t   Показать топ N результатов (по умолчанию: 10)
  --export    Экспортировать статистику в JSON файл
```

**Для чего нужен:**
- Просмотр лучших результатов
- Анализ прогресса
- Экспорт данных для внешнего анализа
- Сравнение стратегий

**Примеры:**
```bash
# Топ 10 результатов
uv run pyaisnake stats

# Топ 20
uv run pyaisnake stats --top 20

# Экспорт для анализа
uv run pyaisnake stats --top 100 --export stats.json
```

**Структура статистики:**
- Score - количество съеденной еды
- Length - длина змейки
- Duration - время игры
- Date - дата игры

---

## 🧠 AI Algorithms

### A* (A Star) - Оптимальный поиск пути

```
┌─────────────────────────────────────────────────────────────┐
│  A* находит кратчайший путь к еде, обходя препятствия      │
│                                                             │
│  🐍 ────→ ────→ ────→ 🍎                                   │
│       ↑           ↓                                         │
│       ╰──────────╯                                          │
│                                                             │
│  Преимущества:                                              │
│  ✓ Гарантированно находит путь                             │
│  ✓ Оптимальный маршрут                                     │
│  ✓ Не требует обучения                                     │
│                                                             │
│  Недостатки:                                                │
│  ✗ Может застрять в ловушке                                │
│  ✗ Не учитывает будущее заполнение                         │
└─────────────────────────────────────────────────────────────┘
```

**Когда использовать:**
- Достижение максимального счёта
- Демонстрация оптимальной игры
- Бенчмарк для сравнения

### Neural Network - Нейросеть

```
┌─────────────────────────────────────────────────────────────┐
│  MLPRegressor учится на данных об игре                     │
│                                                             │
│  Входные признаки:                                          │
│  ├── Расстояние до еды                                      │
│  ├── Длина змейки                                          │
│  ├── Позиция головы                                        │
│  ├── Расстояния до стен                                    │
│  ├── Опасные направления                                   │
│  └── Пути отхода                                            │
│                                                             │
│  Скрытые слои: 100 → 50 → 25 нейронов                      │
│                                                             │
│  Выход: Оценка каждого направления (Up/Down/Left/Right)    │
│                                                             │
│  Требует обучения через: uv run pyaisnake train            │
└─────────────────────────────────────────────────────────────┘
```

**Когда использовать:**
- После обучения на достаточном количестве игр
- Для исследований машинного обучения
- Когда нужно быстрое принятие решений

### Genetic Algorithm - Эволюционный алгоритм

```
┌─────────────────────────────────────────────────────────────┐
│  Эволюция популяции геномов                                 │
│                                                             │
│  Generation 1:  [A][B][C][D][E]  (случайные)               │
│       ↓                                                      │
│  Оценка fitness (играют игры)                               │
│       ↓                                                      │
│  Selection: лучший [A], [C]                                 │
│       ↓                                                      │
│  Crossover: [A+C][C+A]                                       │
│       ↓                                                      │
│  Mutation: [A+C!][C!+A]                                      │
│       ↓                                                      │
│  Generation 2: улучшенные геномы                            │
│       ↓                                                      │
│  ...повторять 100+ поколений                                │
└─────────────────────────────────────────────────────────────┘
```

**Когда использовать:**
- Оптимизация без учителя
- Исследования эволюционных алгоритмов
- Поиск нестандартных стратегий

### Random - Случайный выбор

```
┌─────────────────────────────────────────────────────────────┐
│  Выбирает случайное безопасное направление                  │
│                                                             │
│  Преимущества:                                              │
│  ✓ Очень быстро                                            │
│  ✓ Никогда не идёт в стену                                 │
│  ✓ Базовый уровень для сравнения                           │
│                                                             │
│  Недостатки:                                                │
│  ✗ Низкий счёт                                             │
│  ✗ Нет стратегии                                           │
└─────────────────────────────────────────────────────────────┘
```

**Когда использовать:**
- Базовый уровень для сравнения
- Быстрое тестирование
- Когда нужна простая игра

---

## 📁 Project Structure

```
pyaisnake/
├── __init__.py      # Package init
├── __main__.py      # python -m pyaisnake
├── cli.py           # CLI entry point
├── engine.py        # Game logic (pure Python)
├── renderer.py      # Rich-based CLI renderer
├── controller.py    # Keyboard input handler
├── ai/              # AI algorithms
│   ├── base.py      # A* pathfinding
│   ├── neural.py    # Neural network
│   └── genetic.py   # Genetic algorithm
├── modes.py         # Game modes
├── analytics.py     # Game analytics
└── logger.py        # Logging system
```

---

## 🎯 Типичные сценарии использования

### Сценарий 1: Просто поиграть
```bash
uv run pyaisnake play
```

### Сценарий 2: Посмотреть как играет ИИ
```bash
uv run pyaisnake ai --visualize
```

### Сценарий 3: Обучить свой ИИ
```bash
# Шаг 1: Обучить модель
uv run pyaisnake train --algorithm neural --games 2000 --save my_model.pkl

# Шаг 2: Протестировать
uv run pyaisnake ai --algorithm neural --visualize

# Шаг 3: Дообучить если нужно
uv run pyaisnake train --algorithm neural --load my_model.pkl --games 1000
```

### Сценарий 4: Сравнить алгоритмы
```bash
# Тест каждого алгоритма
uv run pyaisnake ai --algorithm random --games 50
uv run pyaisnake ai --algorithm a_star --games 50
uv run pyaisnake ai --algorithm neural --games 50
uv run pyaisnake ai --algorithm genetic --games 50

# Посмотреть результаты
uv run pyaisnake stats --top 20
```

### Сценарий 5: Бенчмарк производительности
```bash
# 100 игр A* без визуализации (быстро)
time uv run pyaisnake ai --algorithm a_star --games 100
```

---

## ⌨️ Keyboard Support

The game uses the `keyboard` library for real-time input:
- Cross-platform (Windows, Linux, macOS)
- No need to press Enter
- Works in most terminals

If `keyboard` is not available, the game runs in demo mode with simple AI.

---

## 🧪 Development

```bash
# Run tests
uv run pytest pyaisnake/tests/ -v

# Type checking
uv run mypy pyaisnake/

# Linting
uv run ruff check pyaisnake/

# Format
uv run ruff format pyaisnake/
```

---

## 📊 Statistics

Statistics are stored in `snake_stats.db` (SQLite):
- Game scores
- Duration
- Snake length
- Timestamps

---

## 🔧 Requirements

- Python 3.10+
- numpy
- scikit-learn
- rich
- keyboard

---

## 📝 License

MIT License

---

**Made with ❤️ for AI and game enthusiasts**

Play now: `uv run pyaisnake play`
