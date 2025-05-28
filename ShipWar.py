#Imports
import pygame
import textwrap
import threading
import asyncio
import websockets
import json
import pygameWidgets

def display_error_box() -> None:
    global error_message
    global __SCREEN

    scroll = pygameWidgets.TextArea(__SCREEN, [1000, 500], [0, 0],
                                        """ABCDEFGHIJKLMNOPQRTSUVWXYZ""" * 100
                                        , padding=[15, 15])

    while True:
        __SCREEN.fill("black")
        scroll.center=[__SCREEN.get_width() // 2, __SCREEN.get_height() // 2]
        scroll.draw()
        ok_button = pygameWidgets.Button(__SCREEN, "OK", 10, [scroll.center[0], scroll.rect.bottom + pygameWidgets.get_scaled_size(25)], "blue")
        ok_button.draw()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if ok_button.pressed(event.pos):
                    pygame.quit()
                    exit()
            elif event.type == pygame.MOUSEWHEEL:
                scroll.scroll_bar.scroll(event)

        pygame.display.flip()

#Server connection logic
async def handle_server():
    global guess
    global error_message
    global server_uri
    global server_port
    try:
        ws_connection = await websockets.connect(server_uri + ":" + server_port)
        reply = json.loads(await ws_connection.recv())
        print(reply)
    except Exception as e:
        error_message = f"Could not connect to server: {str(e)}"
        return
    if reply["type"] == "welcome" and reply["player"] != 1:
        reply = json.loads(await ws_connection.recv())
        if reply["type"] == "enemy_guess_result":
            enemy_guessed_squares[reply["position"][0]][reply["position"][1]] = reply["result"]
        else: 
            error_message = f"Server Error {str(e)}"
            return
    elif reply["type"] == "error":
        error_message = "Match full"
        return

    while not error_message:
        if guess:
            try:
                await ws_connection.send(json.dumps({
                    "type":"guess", 
                    "position": [guess[0], guess[1]]}))
            except Exception as e:
                error_message = f"Failed to send guess: {str(e)}"
                return
            
            reply = json.loads(await ws_connection.recv())
            if reply["type"] == "guess_result":
                user_guessed_squares[guess[0]][guess[1]] = reply["result"]
            else: 
                error_message = f"Server Error {str(e)}"
       	    
            guess = False
            
            # reply = json.loads(await ws_connection.recv())
            # if reply["type"] == "enemy_guess_result":
            #     enemy_guessed_squares[reply["position"][0]][reply["position"][1]] = reply["result"]
            # else: 
            #     error_message = f"Server Error {str(e)}"
            #     return

def start_async_server_handling():
    asyncio.run(handle_server())
        	
#Client logic
def draw_game_board() -> tuple[list[list[pygame.rect.Rect]], pygame.rect.Rect]:
    pygame.font.init()
    font = pygame.font.Font(None, pygameWidgets.get_scaled_size(24))
    padding = pygameWidgets.get_scaled_size(50)

    # Left board - Radar (shots fired)
    radar_buttons, guess_button = draw_grid(LEFT_TOP=(0, 0), title="Radar", label=True, font=font, padding=padding, interactable=True, guessed=user_guessed_squares)

    # Right board - Player's ships
    right_x = __SCREEN.get_width() // 2
    draw_grid(LEFT_TOP=(right_x, 0), title="Game Board", label=True, font=font, padding=padding, guessed=enemy_guessed_squares)

    return radar_buttons, guess_button

def draw_grid(LEFT_TOP, title="", label=False, font : pygame.font.Font = None, padding=0, 
              interactable=False, guessed=None) -> tuple[list[list[pygame.rect.Rect]], pygame.rect.Rect] | None:
    if not font: font = pygame.font.Font(None, pygameWidgets.get_scaled_size(24))

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
            text = font.render(f"ABCDEFGHIJKLMNOPQRSTUVWXYZ"[i], True, "white")
            text_rect = text.get_rect(center=(x_offset - padding // 2, y_offset + (i + 0.5) * CELL_SIZE))
            __SCREEN.blit(text, text_rect)

            text = font.render(f"{i+1}", True, "white")
            text_rect = text.get_rect(center=(x_offset + (i + 0.5) * CELL_SIZE, y_offset - padding // 2))
            __SCREEN.blit(text, text_rect)
    
    #Confirm guess button
    if interactable and guessed:
        guess_button_text = font.render("Confirm Guess", True, "white")
        guess_button = pygame.Rect(0, 0, guess_button_text.get_width() + pygameWidgets.get_scaled_size(20), padding)
        guess_button.center = (x_offset + grid_px // 2, y_offset + grid_px + 0.75 * padding)
        pygame.draw.rect(__SCREEN, "blue" if can_guess else "grey", guess_button)
        pygame.draw.rect(__SCREEN, "white", guess_button, 1)
        text_rect = guess_button_text.get_rect(center=guess_button.center)
        __SCREEN.blit(guess_button_text, text_rect)

    if interactable:
        return buttons, guess_button

def draw_menu() -> tuple[pygameWidgets.Button, pygameWidgets.Button, pygameWidgets.Button]:
    global __SCREEN

    #Titles
    title_padding = pygameWidgets.get_scaled_size(65)
    title = pygameWidgets.Text(__SCREEN, "ShipWar", (__SCREEN.get_width() // 2, title_padding), font_size=80, padding=title_padding)
    title.draw()

    subtitle_padding = pygameWidgets.get_scaled_size(50)
    subtitle = pygameWidgets.Text(__SCREEN, "By Joshua Finlayson", (__SCREEN.get_width() // 2, title.padding[1] + title.center[1]), font_size=18, padding=subtitle_padding)
    subtitle.draw()

    #Buttons
    title_button_dist = pygameWidgets.get_scaled_size(50)
    button_padding = pygameWidgets.get_scaled_size(40)
    button_button_dist = pygameWidgets.get_scaled_size(40)

    play_button = pygameWidgets.Button(__SCREEN, "Play", (pygameWidgets.get_scaled_size(200), button_padding), 
                              (__SCREEN.get_width() // 2, subtitle.center[1] + title_button_dist + subtitle.padding[1]), 
                              fixed_width=True, color="blue", font_size=24)
    settings_button = pygameWidgets.Button(__SCREEN, "Settings", (pygameWidgets.get_scaled_size(200), button_padding), 
                                  (__SCREEN.get_width() // 2, play_button.center[1] + button_padding + button_button_dist), 
                                  fixed_width=True, color="blue", font_size=24)
    quit_button = pygameWidgets.Button(__SCREEN, "Quit", (pygameWidgets.get_scaled_size(200), button_padding), 
                              (__SCREEN.get_width() // 2, settings_button.center[1] + button_padding + button_button_dist), 
                              fixed_width=True, color="blue", font_size=24)
    play_button.draw()
    settings_button.draw()
    quit_button.draw()

    return play_button, settings_button, quit_button

def draw_settings_menu(player_name_entry_field : pygameWidgets.EntryField) -> tuple[pygameWidgets.EntryField, pygameWidgets.Button, pygameWidgets.Button, pygameWidgets.Button]:
    global __SCREEN

    __SCREEN.fill("black")
    title_padding = pygameWidgets.get_scaled_size(50)

    #Put in title
    title = pygameWidgets.Text(__SCREEN, "Settings", (__SCREEN.get_width() // 2, title_padding), font_size=80)
    title.draw()

    #Entry Fields
    title_entry_field_dist = pygameWidgets.get_scaled_size(50)

    player_name_entry_field.center = (__SCREEN.get_width() // 2, title.center[1] + title_padding + title_entry_field_dist)
    player_name_entry_field.draw()

    #Buttons
    entry_button_dist = pygameWidgets.get_scaled_size(70)
    button_padding = pygameWidgets.get_scaled_size(20)
    button_button_y_dist = pygameWidgets.get_scaled_size(40)
    button_button_x_dist =  pygameWidgets.get_scaled_size(40)
    button_width = pygameWidgets.get_scaled_size(250)

    default_button = pygameWidgets.Button(__SCREEN, "Default", (button_width, button_padding), 
                              ((__SCREEN.get_width() - button_width - button_button_x_dist) // 2, player_name_entry_field.center[1] + player_name_entry_field.rect.height + entry_button_dist), 
                              fixed_width=True, color="blue", font_size=24)
    save_button = pygameWidgets.Button(__SCREEN, "Save", (button_width, button_padding), 
                                  ((__SCREEN.get_width() + button_width + button_button_x_dist) // 2, default_button.center[1]), 
                                  fixed_width=True, color="blue", font_size=24)
    back_button = pygameWidgets.Button(__SCREEN, "Back", (button_width, button_padding), 
                              (__SCREEN.get_width() // 2, save_button.center[1] + button_padding + button_button_y_dist), 
                              fixed_width=True, color="blue", font_size=24)
    default_button.draw()
    save_button.draw()
    back_button.draw()

    return player_name_entry_field, default_button, save_button, back_button

def settings() -> None:
    global error_message
    global player_name

    player_name_entry_field = pygameWidgets.EntryField(__SCREEN, (0, 0), "Player Name: ", font_size=26, title_field_dist=20, input_padding=20, width=250, input_text=player_name)
    
    while not error_message:
        player_name_entry_field, default_button, save_button, back_button = draw_settings_menu(player_name_entry_field)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                #Entry Fields
                player_name_entry_field.pressed(event.pos)
                #Buttons
                if default_button.pressed(event.pos): pass
                elif save_button.pressed(event.pos):
                    player_name = player_name_entry_field.input.inner_text
                elif back_button.pressed(event.pos): return
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return
            elif event.type == pygame.KEYDOWN:
                if player_name_entry_field.has_focus: player_name_entry_field.type(event)


def game() -> None:
    global __SCREEN
    global guess
    global error_message
    all_sprites = pygame.sprite.Group()
    last_guess = []

    global GRID_SIZE
    GRID_SIZE = 10
    global user_guessed_squares
    user_guessed_squares = [[0] * GRID_SIZE for i in range(GRID_SIZE)]
    global enemy_guessed_squares
    enemy_guessed_squares = [[0] * GRID_SIZE for i in range(GRID_SIZE)]

    threading.Thread(target=start_async_server_handling, daemon=True).start()

    while not error_message:
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
    global error_message
    while not error_message:
        __SCREEN.fill((0, 0, 0)) # Set background to black
        play_button, settings_button, quit_button = draw_menu()
        pygame.display.flip()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT: 
                pygame.quit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if play_button.pressed(event.pos):
                    game()
                if settings_button.pressed(event.pos):
                    settings()
                if quit_button.pressed(event.pos):
                    pygame.quit()
                    return

def main() -> None:
    #Window setup
    pygame.display.set_caption("ShipWar")
    pygame.display.set_icon(pygame.image.load("./Sprites/Window_Icon.png"))

    menu()

if __name__ == "__main__":
    global error_message
    error_message = ""

    global server_uri
    server_uri = "ws://localhost"

    global server_port
    server_port = "4444"

    global player_id
    player_id = 0

    global guess
    guess = False

    global player_name
    player_name = "Anonymous"

    pygame.init()
    
    global __SCREEN
    __SCREEN = pygame.display.set_mode((1280, 700), pygame.RESIZABLE)
    pygameWidgets.SCREEN = __SCREEN

    main()
    if error_message: display_error_box()
    pygame.quit()