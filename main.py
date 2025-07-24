import tkinter as tk
from random import randint

#Настройка игры
WIDTH = 400  # Ширина игрового поля
HEIGHT = 400  # Высота игрового поля
DIRECTIONS = ["Up", "Down", "Left", "Right"]  #Список с направлениями движения змейки
CELL_SIZE = 10  # Размер одной клетки змейки и еды
DELAY = 100  # Скорость игры (задержка между движениями змейки в мс)

#Создание главного окна
root = tk.Tk()
root.title("Snake | Счет: 0")
root.resizable(width=False, height=False)

#Игровое поле
canvas = tk.Canvas(
    root,  # Родительское окно
    width=WIDTH,  # Ширина поля
    height=HEIGHT,  # Высота поля
    bg="black",  # Цвет фона (чёрный)
    highlightthickness=0  # Убираем границу
)
canvas.pack()  #Размещаем canvas в окне

# Начальное состояние игры
direction = "Right"  #Направление движения ("Up", "Down", "Left", "Right")
food = None          #Еда
score = 0            #Счет
game_over = False    #Состояние игры

#Создаем змейку
def create_snake():
    # Вычисляем максимальное значение по X и Y,
    # чтобы вся змейка (3 клетки) уместилась в пределах поля
    max_x = (WIDTH // CELL_SIZE) - 3
    max_y = (HEIGHT // CELL_SIZE) - 1

    # Случайная позиция головы змейки
    x = randint(0, max_x) * CELL_SIZE
    y = randint(0, max_y) * CELL_SIZE

    # Возвращаем список из 3 сегментов змейки, направленных вправо
    return [(x, y), (x - CELL_SIZE, y), (x - 2 * CELL_SIZE, y)]

snake = create_snake()

#Создание еды
def create_food():
    while True:
        x = randint(0, (WIDTH - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
        y = randint(0, (HEIGHT - CELL_SIZE) // CELL_SIZE) * CELL_SIZE
        if (x, y) not in snake:  #Еда внутри змейки?
            return (x, y)

food = create_food()

# Отрисовка еды
def draw_food():
    canvas.create_rectangle(
        food[0], food[1],     # Верхний левый угол (x1, y1)
        food[0] + CELL_SIZE,  # x-координата правого края
        food[1] + CELL_SIZE,  # y-координата нижнего края
        fill="blue"           # Цвет заливки
    )

#Отрисовка змейки
def draw_snake():
    for segment in snake:
        canvas.create_rectangle(
            segment[0], segment[1],  # Верхний левый угол
            segment[0] + CELL_SIZE,  # Нижний правый угол (x)
            segment[1] + CELL_SIZE,  # Нижний правый угол (y)
            fill="green",            # Цвет заливки
            outline="darkgreen"      # Цвет обводки
        )

# Перезапуск игры
def restart_game():
    global snake, direction, food, score, game_over

    # Начальное положение змейки
    snake = create_snake()
    direction = "Right"

    # Новая еда
    food = create_food()

    # Сброс счёта и статуса
    score = 0
    game_over = False

    # Очистим холст и обновим
    canvas.delete("all")
    draw_food()
    draw_snake()
    update_title()

    # Перезапускаем игровой цикл
    root.after(DELAY, game_loop)


def on_key_press(event):
    global direction
    opposites = {"Up": "Down", "Down": "Up", "Left": "Right", "Right": "Left"}
    key = event.keysym

    # Управление направлением
    if key in DIRECTIONS:
        # Запрещаем поворот в противоположную сторону
        if key in opposites and direction != opposites[key]:
            direction = key
    # Перезапуск игры
    elif key == 'space' and game_over:
        restart_game()


root.bind("<KeyPress>", on_key_press)  # Привязываем обработчик к окну

#Проверка сьедена ли еда?
def check_food_collision():
    global food, score
    if snake[0] == food:
        score += 1            # Увеличиваем счёт
        food = create_food()  # Генерируем новую еду
        return True           # Сообщаем, что еда съедена
    return False              # Еда не съедена

#Отрисовка змейки
def move_snake():
    head_x, head_y = snake[0]

    if direction == "Up":
        new_head = (head_x, head_y - CELL_SIZE)
    elif direction == "Down":
        new_head = (head_x, head_y + CELL_SIZE)
    elif direction == "Left":
        new_head = (head_x - CELL_SIZE, head_y)
    elif direction == "Right":
        new_head = (head_x + CELL_SIZE, head_y)

    snake.insert(0, new_head)  # Добавляем новую голову
    if not check_food_collision():  #Проверка - сьедена ли еда?
        snake.pop()  # Удаляем хвост если еда не съедена

#Проверка на столкновение со стенами
def check_wall_collision():
    head_x, head_y = snake[0]
    return (
        head_x < 0 or head_x >= WIDTH or
        head_y < 0 or head_y >= HEIGHT
    )

#Проверка самостолкновения
def check_self_collision():
    return snake[0] in snake[1:]

#Завершение игры
def end_game():
    global game_over
    game_over = True  # Больше не обновляем игру
    canvas.create_text(
        WIDTH // 2, HEIGHT // 2,
        text=f"Игра окончена! Счёт: {score}",
        fill="white",
        font=("Arial", 14)
    )

#Обновляем заголовок
def update_title():
    root.title(f"Snake | Счёт: {score}")

# Игровой цикл
def game_loop():
    global snake, food, score

    if game_over:
        return #Останавливаем цикл, если игра окончена

    move_snake()  #Двигаем змейку

    if check_wall_collision() or check_self_collision():
        end_game()
        return

    canvas.delete("all")  #Очищаем холст
    draw_food()  #Рисуем еду
    draw_snake()  #Рисуем змейку
    update_title()  #Обновляем заголовок
    root.after(DELAY, game_loop)  #Повторяем через DELAY мс


# Старт
#Первоначальная отрисовка
draw_food()
draw_snake()
root.after(DELAY, game_loop)
#Запуск главного цикла программы
root.mainloop()
