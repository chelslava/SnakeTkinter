# Contributing to SnakeTkinter

Спасибо за интерес к проекту SnakeTkinter! Этот документ поможет вам внести свой вклад.

## Как внести вклад

### Сообщение об ошибке

1. Проверьте, что ошибка ещё не зарегистрирована в [Issues](../../issues)
2. Создайте новый Issue с описанием:
   - Версия Python
   - Операционная система
   - Шаги для воспроизведения
   - Ожидаемое поведение
   - Фактическое поведение

### Предложение улучшения

1. Создайте Issue с тегом `enhancement`
2. Опишите предлагаемое улучшение
3. Объясните, почему оно полезно

## Разработка

### Настройка окружения

```bash
# Клонирование репозитория
git clone https://github.com/your-username/SnakeTkinter.git
cd SnakeTkinter

# Создание виртуального окружения
python -m venv .venv

# Активация (Windows)
.venv\Scripts\activate

# Активация (Linux/Mac)
source .venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### Запуск тестов

```bash
# Все тесты
python -m pytest tests/ -v

# Конкретный файл
python -m pytest tests/test_logger.py -v

# С покрытием
python -m pytest tests/ --cov=. --cov-report=html
```

### Линтинг

```bash
# Ruff
ruff check .

# MyPy
mypy . --ignore-missing-imports
```

## Стиль кода

### Импорты
Организуйте импорты в следующем порядке:
1. Стандартная библиотека
2. Сторонние библиотеки
3. Локальные модули

### Именование
- Классы: `PascalCase` (пример: `GameLogger`)
- Функции: `snake_case` (пример: `create_snake`)
- Переменные: `snake_case` (пример: `game_over`)
- Константы: `UPPER_SNAKE_CASE` (пример: `WIDTH`)

### Документация
- Используйте русский язык для docstrings и комментариев
- Документируйте все публичные методы

```python
class MyClass:
    """Описание класса"""
    
    def my_method(self, param: int) -> str:
        """Описание метода
        
        Args:
            param: Описание параметра
            
        Returns:
            Описание возвращаемого значения
        """
        pass
```

## Pull Request

1. Создайте ветку для вашей функции:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. Внесите изменения и закоммитьте:
   ```bash
   git add .
   git commit -m "feat: описание изменений"
   ```

3. Отправьте ветку:
   ```bash
   git push origin feature/my-new-feature
   ```

4. Создайте Pull Request

### Коммиты
Используйте префиксы для сообщений коммитов:
- `feat:` - новая функция
- `fix:` - исправление ошибки
- `docs:` - документация
- `test:` - тесты
- `refactor:` - рефакторинг
- `style:` - форматирование
- `chore:` - обслуживание

## Кодекс поведения

- Будьте уважительны к другим участникам
- Принимайте конструктивную критику
- Сосредоточьтесь на том, что лучше для проекта

---

Спасибо за ваш вклад! 🐍
