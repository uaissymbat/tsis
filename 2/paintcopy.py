import pygame
import math
import tools
from tools import BRUSH_SIZES
from datetime import datetime

SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700

WHITE = (255, 255, 255)
RED = (255, 0, 0)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
GREEN = (0, 128, 0)
BLUE = (0, 0, 255)
PURPLE = (128, 0, 128)
PINK = (255, 192, 203)
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
BROWN = (139, 69, 19)
CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)
LIGHT_BLUE = (173, 216, 230)
LIGHT_GREEN = (144, 238, 144)
SALMON = (250, 128, 114)
GOLD = (255, 215, 0)
TAN = (210, 180, 140)
NAVY = (0, 0, 128)
INDIGO = (75, 0, 130)

# Размеры элементов в меню
MENU_ITEM_WIDTH = 20
MENU_ITEM_HEIGHT = 20
MENU_ITEM_SPACING = 20

ERASER_WIDTH = 40
ERASER_HEIGHT = 40

# Переменные для текстового инструмента
text_mode = False 
text_content = "" 
text_position = (0, 0)  
text_preview_surface = None  
font_size = 24  

pygame.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
screen.fill(WHITE)
pygame.display.set_caption('Paint')

# Переменные для рисования
draw_on = False
last_pos = (0, 0)
start_pos = (0, 0)  # начальная позиция для фигур
color = BLACK  # цвет по умолчанию
current_tool = "pencil"  # pencil, line, fill, text, rect, square, circle, triangle, rhombus
preview_surface = None

# Меню с цветами
menu_colors = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE, PINK, BLACK, GRAY, BROWN, CYAN, MAGENTA, LIGHT_BLUE, LIGHT_GREEN, SALMON, GOLD, TAN, NAVY, INDIGO]
for i, c in enumerate(menu_colors):
    pygame.draw.rect(screen, c, (0, MENU_ITEM_SPACING * i, MENU_ITEM_WIDTH, MENU_ITEM_HEIGHT))

# Ластик
try:
    eraser = pygame.transform.scale(pygame.image.load("eraser.png"), (ERASER_WIDTH, ERASER_HEIGHT))
    screen.blit(eraser, [0, MENU_ITEM_SPACING * len(menu_colors)])
except:
    pygame.draw.rect(screen, WHITE, (0, MENU_ITEM_SPACING * len(menu_colors), MENU_ITEM_WIDTH, MENU_ITEM_HEIGHT))
    pygame.draw.rect(screen, BLACK, (0, MENU_ITEM_SPACING * len(menu_colors), MENU_ITEM_WIDTH, MENU_ITEM_HEIGHT), 2)

def draw_tools_hint():
    font = pygame.font.SysFont('Arial', 16)
    hint_list = [
        f"Толщина: {tools.current_brush_size}px (1-мал, 2-сред, 3-бол)",
        "Pencil (непрерывная линия) - мышь",
        "Прямая линия - L (зажми мышь)",
        "Заливка - F (клик по области)",
        "ТЕКСТ - T (клик, ввод, Enter)",
        "Прямоугольник - R (зажми мышь)",
        "Квадрат - S (зажми мышь)",
        "Круг - C (зажми мышь)",
        "Равносторонний - E (зажми мышь)",
        "Ромб - O (зажми мышь)"
    ]
    
    y_offset = SCREEN_HEIGHT - len(hint_list) * 22 - 10
    for i, hint_text in enumerate(hint_list):  # переименовал tool в hint_text
        text = font.render(hint_text, True, BLACK)
        text_rect = text.get_rect()
        text_rect.topright = (SCREEN_WIDTH - 10, y_offset + i * 22)
        pygame.draw.rect(screen, WHITE, (text_rect.x - 5, text_rect.y - 2, text_rect.width + 10, text_rect.height + 4))
        pygame.draw.rect(screen, BLACK, (text_rect.x - 5, text_rect.y - 2, text_rect.width + 10, text_rect.height + 4), 1)
        screen.blit(text, text_rect)

# Функция для перерисовки меню
def redraw_menu():
    for i, c in enumerate(menu_colors):
        pygame.draw.rect(screen, c, (0, MENU_ITEM_SPACING * i, MENU_ITEM_WIDTH, MENU_ITEM_HEIGHT))
    try:
        screen.blit(eraser, [0, MENU_ITEM_SPACING * len(menu_colors)])
    except:
        pygame.draw.rect(screen, WHITE, (0, MENU_ITEM_SPACING * len(menu_colors), MENU_ITEM_WIDTH, MENU_ITEM_HEIGHT))
        pygame.draw.rect(screen, BLACK, (0, MENU_ITEM_SPACING * len(menu_colors), MENU_ITEM_WIDTH, MENU_ITEM_HEIGHT), 2)

def draw_text_preview():
    if text_mode:
        font = pygame.font.SysFont('Arial', font_size)
        if text_content:
            # Используем текущий цвет вместо BLACK
            text_surface = font.render(text_content + "|", True, color)
            screen.blit(text_surface, text_position)
        else:
            # Показываем курсор текущим цветом
            cursor_surface = font.render("|", True, color)
            screen.blit(cursor_surface, text_position)

def render_text_permanently():
    global text_mode, text_content
    if text_content:
        font = pygame.font.SysFont('Arial', font_size)
        text_surface = font.render(text_content, True, color)  # используем текущий цвет
        screen.blit(text_surface, text_position)
        # Обновляем preview_surface для заливки и других инструментов
        global preview_surface
        preview_surface = screen.copy()
    text_mode = False
    text_content = ""

def cancel_text():
    global text_mode, text_content
    text_mode = False
    text_content = ""

def save_canvas():
    # Создаем имя файла с текущей датой и временем
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"canvas_{timestamp}.png"
    
    try:
        pygame.image.save(screen, filename)
        print(f"Canvas сохранен как: {filename}")
        return True
    except Exception as e:
        print(f"Ошибка при сохранении: {e}")
        return False

# Главный цикл игры
try:
    while True:
        e = pygame.event.wait()

        if e.type == pygame.QUIT:
            raise StopIteration

        if e.type == pygame.MOUSEBUTTONDOWN:
            spot = pygame.mouse.get_pos()
    
            if text_mode:
                render_text_permanently()
    
            if spot[0] < MENU_ITEM_WIDTH:
                if 0 <= spot[1] < MENU_ITEM_SPACING * len(menu_colors):
                    color = menu_colors[spot[1] // MENU_ITEM_SPACING]
                    current_tool = "pencil"
                elif MENU_ITEM_SPACING * len(menu_colors) <= spot[1] < MENU_ITEM_SPACING * (len(menu_colors) + 1):
                    color = WHITE  # ластик
                    current_tool = "pencil"

            elif spot[0] > MENU_ITEM_WIDTH:
                if current_tool == "text" and not text_mode:
                    text_mode = True
                    text_position = spot
                    text_content = ""
                    text_preview_surface = screen.copy()
        
                elif current_tool == "fill":
                    tools.fill_tool(screen, spot, color)
                    preview_surface = screen.copy()
        
                else:
                    draw_on = True
                    start_pos = spot
                    last_pos = spot
                    preview_surface = screen.copy()
            
                    if current_tool == "pencil":
                        pygame.draw.circle(screen, color, spot, tools.current_brush_size // 2)

        elif e.type == pygame.MOUSEBUTTONUP:
            if draw_on:
                end_pos = pygame.mouse.get_pos()
                if current_tool == "line":
                    tools.draw_straight_line(screen, color, start_pos, end_pos)
                elif current_tool in tools.TOOL_FUNCTIONS:
                    tools.draw_shape(current_tool, screen, color, start_pos, end_pos)
            draw_on = False

        elif e.type == pygame.MOUSEMOTION:
            spot = pygame.mouse.get_pos()
            if draw_on and spot[0] > MENU_ITEM_WIDTH:
                if current_tool == "pencil":
                    tools.draw_pencil_line(screen, color, last_pos, e.pos)
                elif current_tool == "line":
                    screen.blit(preview_surface, (0, 0))
                    redraw_menu()
                    tools.draw_straight_line(screen, color, start_pos, spot)
                else:
                    screen.blit(preview_surface, (0, 0))
                    redraw_menu()
                    tools.draw_shape(current_tool, screen, color, start_pos, spot)
            last_pos = e.pos

        elif e.type == pygame.KEYDOWN:
            if text_mode:
                if e.key == pygame.K_RETURN:  # Enter - подтвердить текст
                    render_text_permanently()
                elif e.key == pygame.K_ESCAPE:  # Escape - отменить текст
                    cancel_text()
                elif e.key == pygame.K_BACKSPACE:  # Backspace - удалить последний символ
                    text_content = text_content[:-1]
                else:
            # Добавляем обычные символы (только печатные)
                    char = e.unicode
                    if char and char.isprintable() and len(char) == 1:
                        text_content += char
            else:
                if e.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    save_canvas()
                elif e.key in tools.BRUSH_SIZES:  
                    tools.set_brush_size(tools.BRUSH_SIZES[e.key])
                elif e.key == pygame.K_l:
                    current_tool = "line"
                elif e.key == pygame.K_f:
                    current_tool = "fill"
                elif e.key == pygame.K_t:
                    current_tool = "text"
                elif e.key == pygame.K_r:
                    current_tool = "rectangle"
                elif e.key == pygame.K_s:
                    current_tool = "square"
                elif e.key == pygame.K_c:
                    current_tool = "circle"
                elif e.key == pygame.K_y:
                    current_tool = "triangle"
                elif e.key == pygame.K_o:
                    current_tool = "rhombus"
                elif e.key == pygame.K_b:
                    current_tool = "pencil"

        draw_tools_hint()
        
        # Рисуем текущий выбранный инструмент
        font = pygame.font.SysFont('Arial', 16)
        tool_name = f"Инструмент: {current_tool}"
        text = font.render(tool_name, True, BLACK)
        text_rect = text.get_rect()
        text_rect.topleft = (MENU_ITEM_WIDTH + 10, 10)
        pygame.draw.rect(screen, WHITE, (text_rect.x - 5, text_rect.y - 2, text_rect.width + 10, text_rect.height + 4))
        screen.blit(text, text_rect)

        # Отрисовка предпросмотра текста (поверх всего)
        if text_mode:
            if text_preview_surface:
                screen.blit(text_preview_surface, (0, 0))
            draw_text_preview()
            redraw_menu()
            draw_tools_hint()

        pygame.display.flip()

except StopIteration:
    pass

pygame.quit()