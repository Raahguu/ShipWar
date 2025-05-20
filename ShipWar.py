#Imports
import pygame
import textwrap
import string

#Define Classes
class Ship(pygame.sprite.Sprite):
    def __init__(self, sprite_group : pygame.sprite.Group, image_path : str, x : int = 0, y : int = 0):
        super().__init__()
        self.sprite_group = sprite_group
        sprite_group.add(self)

        self.image_path = image_path

        try:
            self.image = pygame.image.load(image_path).convert_alpha()
        except Exception as e:
            display_error_box(str(e))
            raise e
        
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
    
    def scale(self, x = 1, y = 1):
        self.image = pygame.transform.scale(self.image, (int(self.image.get_width() * x), int(self.image.get_height() * y)))

def get_scaled_size(base_size : int, min_size : int = None, max_size : int = None, scale_reference = (1280, 700), current_size : tuple[int, int] = None) -> int | float:
    current_size = current_size if current_size else __SCREEN.get_size()
    min_size = min_size if min_size else base_size / 3
    max_size = max_size if max_size else base_size * 3
    scale_factor = min(current_size[0] / scale_reference[0], current_size[1] / scale_reference[1])
    scaled_size = min(max(min_size, base_size * scale_factor), max_size)
    if type(base_size) is int: return round(scaled_size)
    else: return scaled_size

#Define funcs
def display_error_box(message : str) -> None:
    pygame.font.init()
    font = pygame.font.Font(None, get_scaled_size(24))
    screen_width, screen_height = __SCREEN.get_size()

    # Layout settings
    max_box_width = screen_width - 100
    padding = get_scaled_size(20)
    line_spacing = get_scaled_size(5)
    button_height = get_scaled_size(40)
    scroll_speed = get_scaled_size(20)  # Pixels per scroll event

    # Wrap text
    max_chars_per_line = max_box_width // font.size("A")[0]
    wrapped_lines = textwrap.wrap(message, width=max_chars_per_line)

    # Line and box dimensions
    line_height = font.get_height()
    total_text_height = len(wrapped_lines) * (line_height + line_spacing)
    visible_text_height = min(total_text_height, screen_height - button_height - 3 * padding - get_scaled_size(75))

    # Determine scrollable height
    scrollable = total_text_height > visible_text_height
    scroll_offset = 0
    max_scroll = total_text_height - visible_text_height if scrollable else 0

    box_width = max(min(max_box_width, max(font.size(line)[0] for line in wrapped_lines)), 150) + 2 * padding
    box_height = visible_text_height + 2 * padding + button_height + get_scaled_size(10)

    box_x = (screen_width - box_width) // 2
    box_y = (screen_height - box_height) // 2

    # Button
    button_width = get_scaled_size(150)
    button_x = box_x + (box_width - button_width) // 2
    button_y = box_y + visible_text_height + 2 * padding
    button_rect = pygame.Rect(button_x, button_y, button_width, button_height)

    # Scroll area surface
    scroll_area = pygame.Surface((box_width - 2 * padding, total_text_height))
    scroll_area.fill((200, 0, 0))

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Scroll up
                    scroll_offset = max(scroll_offset - scroll_speed, 0)
                elif event.button == 5:  # Scroll down
                    scroll_offset = min(scroll_offset + scroll_speed, max_scroll)
                elif button_rect.collidepoint(event.pos):
                    return

        pygame.draw.rect(__SCREEN, (200, 0, 0), (box_x, box_y, box_width, box_height))
        pygame.draw.rect(__SCREEN, (255, 255, 255), (box_x, box_y, box_width, box_height), 2)

        # Render wrapped text to scroll_area
        scroll_area.fill((200, 0, 0))
        for i, line in enumerate(wrapped_lines):
            text_surface = font.render(line, True, (255, 255, 255))
            scroll_area.blit(text_surface, (0, i * (line_height + line_spacing)))

        # Blit scroll area with offset
        visible_rect = pygame.Rect(0, scroll_offset, scroll_area.get_width(), visible_text_height)
        __SCREEN.blit(scroll_area.subsurface(visible_rect), (box_x + padding, box_y + padding))

        # Draw button
        pygame.draw.rect(__SCREEN, (50, 50, 50), button_rect)
        pygame.draw.rect(__SCREEN, (255, 255, 255), button_rect, 2)
        button_text = font.render("Close", True, (255, 255, 255))
        text_rect = button_text.get_rect(center=button_rect.center)
        __SCREEN.blit(button_text, text_rect)

        pygame.display.update()

def guess_square(row : int, col : int) -> None:
    #TODO: Will send post to API server, to let the server know of the users move
    user_guessed_squares[row][col] = 1

def draw_game_board() -> tuple[list[list[pygame.rect.Rect]], pygame.rect.Rect]:
    pygame.font.init()
    font = pygame.font.Font(None, get_scaled_size(24))
    padding = get_scaled_size(50)

    # Left board - Radar (shots fired)
    radar_buttons, guess_button = draw_grid(LEFT_TOP=(0, 0), title="Radar", label=True, font=font, padding=padding, interactable=True, guessed=user_guessed_squares)

    # Right board - Player's ships
    right_x = __SCREEN.get_width() // 2
    draw_grid(LEFT_TOP=(right_x, 0), title="Game Board", label=True, font=font, padding=padding, guessed=enemy_guessed_squares)

    return radar_buttons, guess_button

def draw_grid(LEFT_TOP, title="", label=False, font : pygame.font.Font = None, padding=0, 
              interactable=False, guessed=None) -> tuple[list[list[pygame.rect.Rect]], pygame.rect.Rect] | None:
    if not font: pygame.font.Font(None, get_scaled_size(24))

    x_offset, y_offset = LEFT_TOP
    x_offset += padding
    y_offset += padding

    CELL_SIZE = min(__SCREEN.get_width() / 2 - 2 * padding, __SCREEN.get_height() - 3 * padding) // GRID_SIZE
    grid_px = CELL_SIZE * GRID_SIZE

    # Title
    if title:
        text = font.render(title, True, (255, 255, 255))
        text_rect = text.get_rect(center=(x_offset + grid_px // 2, y_offset - padding // 2))
        __SCREEN.blit(text, text_rect)
        y_offset += text.get_height() * 2

    buttons = [[None] * GRID_SIZE for i in range(GRID_SIZE)]

    # Grid buttons and pegs
    can_guess = False
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            #buttons
            button_rect = pygame.Rect(x_offset + col * CELL_SIZE, y_offset + row * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            pygame.draw.rect(__SCREEN, (0, 0, 0), button_rect)
            pygame.draw.rect(__SCREEN, (100, 100, 100), button_rect, 1)
            buttons[row][col] = button_rect
            
            #Pegs
            cx = x_offset + (col + 0.5) * CELL_SIZE
            cy = y_offset + (row + 0.5) * CELL_SIZE

            if guessed:
                match guessed[row][col]:
                    case 0: pygame.draw.circle(__SCREEN, (80, 80, 80), (cx, cy), CELL_SIZE // 8)
                    case 1: pygame.draw.circle(__SCREEN, "white", (cx, cy), CELL_SIZE // 8)
                    case 2: pygame.draw.circle(__SCREEN, "orange", (cx, cy), CELL_SIZE // 8)
                    case 3: pygame.draw.circle(__SCREEN, "red", (cx, cy), CELL_SIZE // 8)
                    case 4: pygame.draw.circle(__SCREEN, "blue", (cx, cy), CELL_SIZE // 8); can_guess = True
        
    #Write board locations:
    if label: 
        for i in range(GRID_SIZE):
            text = font.render(f"{string.ascii_uppercase[i]}", True, "white")
            text_rect = text.get_rect(center=(x_offset - padding // 2, y_offset + (i + 0.5) * CELL_SIZE))
            __SCREEN.blit(text, text_rect)

            text = font.render(f"{i+1}", True, "white")
            text_rect = text.get_rect(center=(x_offset + (i + 0.5) * CELL_SIZE, y_offset - padding // 2))
            __SCREEN.blit(text, text_rect)
    
    #Confirm guess button
    if interactable and guessed:
        guess_button_text = font.render("Confirm Guess", True, (255, 255, 255))
        guess_button = pygame.Rect(0, 0, guess_button_text.get_width() + get_scaled_size(20), padding)
        guess_button.center = (x_offset + grid_px // 2, y_offset + grid_px + 0.75 * padding)
        pygame.draw.rect(__SCREEN, "blue" if can_guess else "grey", guess_button)
        pygame.draw.rect(__SCREEN, "white", guess_button, 1)
        text_rect = guess_button_text.get_rect(center=guess_button.center)
        __SCREEN.blit(guess_button_text, text_rect)

    if interactable:
        return buttons, guess_button

#main game loop
def main() -> None:
    global __SCREEN
    running = True
    #Window setup
    pygame.display.set_caption("ShipWar")
    pygame.display.set_icon(pygame.image.load("./Sprites/Window_Icon.png"))

    all_sprites = pygame.sprite.Group()
    last_guess = []


    while running:
        # Clear the screen
        __SCREEN.fill((0, 0, 0))  # Black background

        radar_buttons, guess_button = draw_game_board()

        # Draw the sprites
        all_sprites.draw(__SCREEN)

        # Update the display
        pygame.display.flip()

        #Handle user events
        for event in pygame.event.get():
            #Let the player quit the game
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                minimum_window_size = 300
                if event.size[0] < minimum_window_size: event.size = (minimum_window_size, event.size[1])
                if event.size[1] < minimum_window_size: event.size = (event.size[0], minimum_window_size)
                __SCREEN = pygame.display.set_mode(event.size, pygame.RESIZABLE)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for row in range(len(radar_buttons)):
                    for col in range(len(radar_buttons[row])):
                        if radar_buttons[row][col].collidepoint(event.pos):
                            if user_guessed_squares[row][col] != 0: break
                            if last_guess: user_guessed_squares[last_guess[0]][last_guess[1]] = 0
                            last_guess = [row, col]
                            user_guessed_squares[row][col] = 4
                if last_guess and guess_button.collidepoint(event.pos):
                    guess_square(last_guess[0], last_guess[1])
                    last_guess = []

if __name__ == "__main__":
    pygame.init()
    
    global __SCREEN
    __SCREEN = pygame.display.set_mode((1280, 700), pygame.RESIZABLE)

    global GRID_SIZE
    GRID_SIZE = 10
    global user_guessed_squares
    user_guessed_squares = [[0] * GRID_SIZE for i in range(GRID_SIZE)]
    global enemy_guessed_squares
    enemy_guessed_squares = [[0] * GRID_SIZE for i in range(GRID_SIZE)]

    try:
        main()
    except Exception as e: 
        display_error_box(str(e))
        raise e
    pygame.quit()