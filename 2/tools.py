import pygame
import math

# Толщина линий (глобальная для модуля)
current_brush_size = 5

# Размеры кисти
BRUSH_SIZES = {
    pygame.K_1: 2,   # маленькая - 2px
    pygame.K_2: 5,   # средняя - 5px
    pygame.K_3: 10   # большая - 10px
}

# Функция для установки толщины
def set_brush_size(size):
    global current_brush_size
    current_brush_size = size

# Функция для рисования линии (pencil tool)
def draw_pencil_line(canvas, clr, start, end):
    if start and end:
        pygame.draw.line(canvas, clr, start, end, current_brush_size)

# Функция для рисования ровной линии (straight line)
def draw_straight_line(canvas, clr, start, end):
    if start and end:
        pygame.draw.line(canvas, clr, start, end, current_brush_size)

# Функция для рисования квадрата
def draw_square(canvas, clr, start, end):
    x1, y1 = start
    x2, y2 = end
    size = max(abs(x2 - x1), abs(y2 - y1))
    x = min(x1, x2) if x2 < x1 else x1
    y = min(y1, y2) if y2 < y1 else y1
    pygame.draw.rect(canvas, clr, (x, y, size, size), current_brush_size)

# Функция для рисования прямоугольника
def draw_rectangle(canvas, clr, start, end):
    x1, y1 = start
    x2, y2 = end
    x = min(x1, x2)
    y = min(y1, y2)
    width = abs(x2 - x1)
    height = abs(y2 - y1)
    pygame.draw.rect(canvas, clr, (x, y, width, height), current_brush_size)

# Функция для рисования круга
def draw_circle_shape(canvas, clr, start, end):
    x1, y1 = start
    x2, y2 = end
    radius = int(math.hypot(x2 - x1, y2 - y1))
    pygame.draw.circle(canvas, clr, start, radius, current_brush_size)

# Функция для рисования прямоугольного треугольника (только первый)
def draw_triangle(canvas, clr, start, end):
    x1, y1 = start
    x2, y2 = end
    pygame.draw.polygon(canvas, clr, [(x1, y1), (x1, y2), (x2, y2)], current_brush_size)

# Функция для рисования ромба
def draw_rhombus(canvas, clr, start, end):
    x1, y1 = start
    x2, y2 = end
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    x = min(x1, x2)
    y = min(y1, y2)
    pygame.draw.polygon(canvas, clr, [(x + dx//2, y), (x + dx, y + dy//2), (x + dx//2, y + dy), (x, y + dy//2)], current_brush_size)

# Функция для заливки (Flood Fill)
def flood_fill(canvas, x, y, target_color, fill_color):
    """
    Заливает область начиная с (x, y)
    canvas - поверхность pygame
    target_color - цвет, который нужно заменить
    fill_color - цвет заливки
    """
    if target_color == fill_color:
        return
    
    # Получаем размеры canvas
    width, height = canvas.get_size()
    
    # Проверяем, что точка в пределах экрана
    if x < 0 or x >= width or y < 0 or y >= height:
        return
    
    # Используем стек для рекурсивного заполнения (итеративно, чтобы избежать RecursionError)
    stack = [(x, y)]
    visited = set()
    
    while stack:
        cx, cy = stack.pop()
        
        # Проверяем границы
        if cx < 0 or cx >= width or cy < 0 or cy >= height:
            continue
        
        # Проверяем, что точка уже обработана
        if (cx, cy) in visited:
            continue
        
        # Получаем цвет пикселя
        try:
            current_color = canvas.get_at((cx, cy))
        except:
            continue
        
        # Сравниваем цвета (только RGB, игнорируем альфа-канал)
        if (current_color[0], current_color[1], current_color[2]) != (target_color[0], target_color[1], target_color[2]):
            continue
        
        # Отмечаем как посещенную
        visited.add((cx, cy))
        
        # Закрашиваем пиксель
        canvas.set_at((cx, cy), fill_color)
        
        # Добавляем соседние пиксели (4 направления: вверх, вниз, влево, вправо)
        stack.append((cx + 1, cy))  # вправо
        stack.append((cx - 1, cy))  # влево
        stack.append((cx, cy + 1))  # вниз
        stack.append((cx, cy - 1))  # вверх

# Функция для заливки с проверкой границ экрана
def fill_tool(canvas, pos, fill_color):
    """Основная функция для вызова заливки"""
    x, y = pos
    try:
        target_color = canvas.get_at((x, y))
        # Игнорируем альфа-канал для сравнения
        target_color_rgb = (target_color[0], target_color[1], target_color[2])
        fill_color_rgb = (fill_color[0], fill_color[1], fill_color[2])
        
        if target_color_rgb != fill_color_rgb:
            flood_fill(canvas, x, y, target_color_rgb, fill_color)
            return True
    except:
        pass
    return False

# Словарь для вызова функций по имени инструмента
TOOL_FUNCTIONS = {
    "rectangle": draw_rectangle,
    "square": draw_square,
    "circle": draw_circle_shape,
    "triangle": draw_triangle,
    "rhombus": draw_rhombus
}

# Функция для вызова нужного инструмента
def draw_shape(tool_name, canvas, color, start, end):
    if tool_name in TOOL_FUNCTIONS:
        TOOL_FUNCTIONS[tool_name](canvas, color, start, end)
    elif tool_name == "line":
        draw_straight_line(canvas, color, start, end)
    elif tool_name == "pencil":
        draw_pencil_line(canvas, color, start, end)

