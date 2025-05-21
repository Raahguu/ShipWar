#Imports
import pygame
import textwrap
import string
import threading
import asyncio
import pygame.event
import websockets
import json

def get_scaled_size(base_size : int, min_size : int = None, max_size : int = None, scale_reference = (1280, 700), current_size : tuple[int, int] = None) -> int | float:
    global __SCREEN
    current_size = current_size if current_size else __SCREEN.get_size()
    min_size = min_size if min_size else base_size / 3
    max_size = max_size if max_size else base_size * 3
    scale_factor = min(current_size[0] / scale_reference[0], current_size[1] / scale_reference[1])
    scaled_size = min(max(min_size, base_size * scale_factor), max_size)
    if type(base_size) is int: return round(scaled_size)
    else: return scaled_size

def draw_button(screen : pygame.Surface, text: str, button_padding: tuple[int, int] | int, location: tuple[int, int], 
                button_color : str | tuple[int, int, int] = "black", button_border_color : str | tuple[int, int, int] = "white", 
                text_color : str | tuple[int, int, int] = "white", font : pygame.font.Font = None, 
                fixed_width : bool = False, fixed_height : bool = False, button_border : bool = True) -> pygame.Rect:
    if font is None: font = pygame.font.Font(None, get_scaled_size(18))
    if type(button_padding) is int: button_padding = (button_padding, button_padding)
    button_text = font.render(text, True, text_color)
    button_rect = pygame.Rect(0, 0, (button_text.get_width() if not fixed_width else 0) + button_padding[0], 
                              (button_text.get_height() if not fixed_height else 0) +  button_padding[1])
    button_rect.center = (location[0], location[1])
    button_text_rect = button_text.get_rect(center=button_rect.center)
    pygame.draw.rect(__SCREEN, button_color, button_rect)
    if button_border: pygame.draw.rect(__SCREEN, button_border_color, button_rect, 1)
    screen.blit(button_text, button_text_rect)

    return button_rect

def display_error_box(message : str) -> None:
    global error_thrown
    error_thrown = True

    pygame.font.init()
    font = pygame.font.Font(None, get_scaled_size(24))
    screen_width, screen_height = __SCREEN.get_size()

    # Layout settings
    max_box_width = screen_width - get_scaled_size(100)
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
                    pygame.quit()
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

        pygame.display.flip()

#Server connection logic
async def handle_server():
    global guess
    try:
        ws_connection = await websockets.connect(server_uri + ":" + server_port)
        reply = json.loads(await ws_connection.recv())
        print(reply)
    except Exception as e:
        display_error_box(f"Could not connect to server: {str(e)}")
    if reply["type"] == "welcome" and reply["player"] != 1:
        reply = json.loads(await ws_connection.recv())
        if reply["type"] == "enemy_guess_result":
            enemy_guessed_squares[reply["position"][0]][reply["position"][1]] = reply["result"]
        else: 
            display_error_box(f"Server Error {str(e)}")
    elif reply["type"] == "error":
        display_error_box("Match full")

    while True:
        if guess:
            try:
                await ws_connection.send(json.dumps({
                    "type":"guess", 
                    "position": [guess[0], guess[1]]}))
            except Exception as e:
                display_error_box(f"Failed to send guess: {str(e)}")
            
            reply = json.loads(await ws_connection.recv())
            if reply["type"] == "guess_result":
                user_guessed_squares[guess[0]][guess[1]] = reply["result"]
            else: 
                display_error_box(f"Server Error {str(e)}")
       	    
            guess = False
            
            # reply = json.loads(await ws_connection.recv())
            # if reply["type"] == "enemy_guess_result":
            #     enemy_guessed_squares[reply["position"][0]][reply["position"][1]] = reply["result"]
            # else: 
            #     display_error_box(f"Server Error {str(e)}")

def start_async_server_handling():
    asyncio.run(handle_server())
        	
#Client logic


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
    if not font: font = pygame.font.Font(None, get_scaled_size(24))

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
        guess_button_text = font.render("Confirm Guess", True, "white")
        guess_button = pygame.Rect(0, 0, guess_button_text.get_width() + get_scaled_size(20), padding)
        guess_button.center = (x_offset + grid_px // 2, y_offset + grid_px + 0.75 * padding)
        pygame.draw.rect(__SCREEN, "blue" if can_guess else "grey", guess_button)
        pygame.draw.rect(__SCREEN, "white", guess_button, 1)
        text_rect = guess_button_text.get_rect(center=guess_button.center)
        __SCREEN.blit(guess_button_text, text_rect)

    if interactable:
        return buttons, guess_button

def draw_menu() -> tuple[pygame.Rect, pygame.Rect, pygame.Rect]:
    global __SCREEN

    #Title
    title_padding = get_scaled_size(50)
    title_font = pygame.font.Font(None, get_scaled_size(80))
    title = title_font.render("ShipWar", True, "white")
    title_rect = title.get_rect(center=(__SCREEN.get_width() // 2, title.get_height() + title_padding))
    __SCREEN.blit(title, title_rect)

    #Subtitle
    subtitle_padding = get_scaled_size(40)
    subtitle_font = pygame.font.Font(None, get_scaled_size(24))
    subtitle = subtitle_font.render("By Joshua Finlayson", True, "white")
    subtitle_rect = subtitle.get_rect(center=(__SCREEN.get_width() // 2, subtitle.get_height() + subtitle_padding + title_rect.center[1]))
    __SCREEN.blit(subtitle, subtitle_rect)

    #Buttons
    title_button_dist = get_scaled_size(50)
    button_padding = get_scaled_size(40)
    button_button_dist = get_scaled_size(40)
    button_font = pygame.font.Font(None, get_scaled_size(36))

    play_button = draw_button(__SCREEN, "Play", (get_scaled_size(200), button_padding), 
                              (__SCREEN.get_width() // 2, title_rect.center[1] + title_padding + title_button_dist + subtitle_padding), 
                              fixed_width=True, button_color="blue", font=button_font)
    settings_button = draw_button(__SCREEN, "Settings", (get_scaled_size(200), button_padding), 
                                  (__SCREEN.get_width() // 2, play_button.center[1] + button_padding + button_button_dist), 
                                  fixed_width=True, button_color="blue", font=button_font)
    quit_button = draw_button(__SCREEN, "Quit", (get_scaled_size(200), button_padding), 
                              (__SCREEN.get_width() // 2, settings_button.center[1] + button_padding + button_button_dist), 
                              fixed_width=True, button_color="blue", font=button_font)

    return play_button, settings_button, quit_button

def settings() -> None:
    print("settings")
    global __SCREEN

    __SCREEN.fill("black")
    title_padding = get_scaled_size(50)

    #Put in title
    title_font = pygame.font.Font(None, get_scaled_size(80))
    title = title_font.render("Settings", True, "white")
    title_rect = title.get_rect(center=(__SCREEN.get_width() // 2, title.get_height() + title_padding))
    __SCREEN.blit(title, title_rect)

    #Buttons
    title_button_dist = get_scaled_size(50)
    button_padding = get_scaled_size(40)
    button_button_dist = get_scaled_size(40)
    button_font = pygame.font.Font(None, get_scaled_size(36))

    #play button
    player_name_field = draw_button(__SCREEN, "a", (get_scaled_size(200), button_padding), 
                              (__SCREEN.get_width() // 2, title_rect.center[1] + title_padding + title_button_dist), 
                              fixed_width=True, button_color="blue", font=button_font)
    settings_button = draw_button(__SCREEN, "b", (get_scaled_size(200), button_padding), 
                                  (__SCREEN.get_width() // 2, player_name_field.center[1] + button_padding + button_button_dist), 
                                  fixed_width=True, button_color="blue", font=button_font)
    back_button = draw_button(__SCREEN, "Back", (get_scaled_size(200), button_padding), 
                              (__SCREEN.get_width() // 2, settings_button.center[1] + button_padding + button_button_dist), 
                              fixed_width=True, button_color="blue", font=button_font)
    
    pygame.display.flip()
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if player_name_field.collidepoint(event.pos): print("a")
                if back_button.collidepoint(event.pos): return

def game() -> None:
    global __SCREEN
    global guess
    global error_thrown
    all_sprites = pygame.sprite.Group()
    last_guess = []

    while not error_thrown:
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
                pygame.quit()
                return
            if event.type == pygame.VIDEORESIZE:
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
                    guess = [last_guess[0], last_guess[1]]
                    last_guess = []
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return

def menu() -> None:
    global __SCREEN
    global error_thrown
    while not error_thrown:
        __SCREEN.fill((0, 0, 0)) # Set background to black
        play_button, settings_button, quit_button = draw_menu()
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.quit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if play_button.collidepoint(event.pos):
                    game()
                if settings_button.collidepoint(event.pos):
                    settings()
                if quit_button.collidepoint(event.pos):
                    pygame.quit()
                    return

def main() -> None:
    #Window setup
    pygame.display.set_caption("ShipWar")
    pygame.display.set_icon(pygame.image.load("./Sprites/Window_Icon.png"))

    menu()


if __name__ == "__main__":
    global server_uri
    global server_port
    global player_id
    global guess
    global error_thrown

    error_thrown = False
    server_uri = "ws://localhost"
    server_port = "8765"
    player_id = 0
    guess = False

    pygame.init()
    
    global __SCREEN
    __SCREEN = pygame.display.set_mode((1280, 700), pygame.RESIZABLE)

    global GRID_SIZE
    GRID_SIZE = 10
    global user_guessed_squares
    user_guessed_squares = [[0] * GRID_SIZE for i in range(GRID_SIZE)]
    global enemy_guessed_squares
    enemy_guessed_squares = [[0] * GRID_SIZE for i in range(GRID_SIZE)]

    threading.Thread(target=start_async_server_handling, daemon=True).start()
    main()
    pygame.quit()

    
