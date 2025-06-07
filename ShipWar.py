#Imports
import pygame
import asyncio
import websockets
import json
import pygameWidgets

def display_error_box() -> None:
    global error_message
    global __SCREEN

    scroll = pygameWidgets.TextArea(__SCREEN, [1000, 500], [0, 0],
                                        error_message
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

async def listen_to_server(socket: websockets.ClientConnection):
    global error_message, user_guessed_squares, enemy_guessed_squares, player_id, enemy_name, still_playing
    while still_playing:
        try:
            reply = json.loads(await socket.recv())
            print("Received:", reply)
            if reply["type"] == "welcome":
                player_id = int(reply["player"])
            elif reply["type"] == "username":
                enemy_name = reply["name"]
                still_playing.set()
            elif reply["type"] == "guess_result":
                user_guessed_squares[reply["position"][0]][reply["position"][1]] = reply["result"]
            elif reply["type"] == "enemy_guess_result":
                enemy_guessed_squares[reply["position"][0]][reply["position"][1]] = reply["result"]
            elif reply["type"] == "disconnection":
                error_message = "The other player disconnected"
                return
            elif reply["type"] == "error":
                error_message = reply["message"]
                return
            else:
                error_message = f"Unexpected message type: {reply['type']}"
                return
        except Exception as e:
            error_message = f"Error received from server: {e}"
            return

#Server connection logic
async def handle_server():
    global guess
    global error_message
    global server_ip
    global server_port
    global still_playing
    global player_name
    global player_id
    global enemy_name

    #connect to the server
    try:
        ws_connection = await websockets.connect("ws://" + str(server_ip) + ":" + str(server_port))
    except Exception as e:
        error_message = f"Could not connect to server: {str(e)}"
        return
    
    #Add server event listener
    asyncio.create_task(listen_to_server(ws_connection))

    await ws_connection.send(json.dumps({"type":"username", "name": player_name}))

    await still_playing.wait()

    #loop through the game loop if were still playing and there are no errors yet
    while not error_message and still_playing.is_set():
        await asyncio.sleep(0.1)
        #if the player has guessed
        if guess:
            print("Player has guessed")
            #Tell server guess
            try:
                await ws_connection.send(json.dumps({"type":"guess", "position": [guess[0], guess[1]]}))
            except Exception as e:
                error_message = f"Failed to send guess: {str(e)}"
                return
            
            guess = False

    await ws_connection.send(json.dumps({"type":"disconnection"}))
    still_playing.clear()

#Client logic
def setup_game_board(padding) -> tuple[list[list[pygameWidgets.Button]], pygameWidgets.Button, list[list[pygameWidgets.Button]]]:
    global enemy_name
    global player_name

    font_size = 24
    __SCREEN.fill((0, 0, 0)) 
    enemy_username_text = pygameWidgets.Text(__SCREEN, enemy_name, [0, padding // 2])
    enemy_username_text.rect.left = padding
    enemy_username_text.draw()
    player_username_text = pygameWidgets.Text(__SCREEN, player_name, [0, padding // 2])
    player_username_text.rect.right = __SCREEN.get_width() - padding
    player_username_text.draw()

    # Left board - Radar (shots fired)
    radar_buttons, guess_button = setup_grid(LEFT_TOP=(0, padding // 2), title="Radar", label=True, font_size=font_size, padding=padding, interactable=True, guessed=user_guessed_squares)

    # Right board - Player's ships
    right_x = __SCREEN.get_width() // 2
    enemy_buttons =  setup_grid(LEFT_TOP=(right_x, padding // 2), title="Game Board", label=True, font_size=font_size, padding=padding, guessed=enemy_guessed_squares)[0]

    return radar_buttons, guess_button, enemy_buttons

def draw_grid(buttons : list[list[pygameWidgets.Button]], padding : int, guess_button : pygameWidgets.Button = None, guessed=None):
    CELL_SIZE = int(min(__SCREEN.get_width() / 2 - 2 * padding, __SCREEN.get_height() - 4 * padding) // GRID_SIZE)

    can_guess = False
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            cx = buttons[0][0].rect.left + (col + 0.5) * CELL_SIZE
            cy = buttons[0][0].rect.top + (row + 0.5) * CELL_SIZE

            if guessed:
                match guessed[row][col]:
                    case 0: pygame.draw.circle(__SCREEN, (80, 80, 80), (cx, cy), CELL_SIZE // 8)
                    case 1: pygame.draw.circle(__SCREEN, "white", (cx, cy), CELL_SIZE // 8)
                    case 2: pygame.draw.circle(__SCREEN, "orange", (cx, cy), CELL_SIZE // 8)
                    case 3: pygame.draw.circle(__SCREEN, "red", (cx, cy), CELL_SIZE // 8)
                    case 4: pygame.draw.circle(__SCREEN, "blue", (cx, cy), CELL_SIZE // 8); can_guess = True
    
    if guess_button:
        guess_button.color = "blue" if can_guess else "grey"
        guess_button.draw()

def setup_grid(LEFT_TOP, title="", label=False, font_size : pygame.font.Font = None, padding=0, 
              interactable=False, guessed=None) -> tuple[list[list[pygameWidgets.Button]], pygameWidgets.Button | None]:
    if not font_size: font_size = 24

    CELL_SIZE = int(min(__SCREEN.get_width() / 2 - 2 * padding, __SCREEN.get_height() - 4 * padding) // GRID_SIZE)
    grid_px = CELL_SIZE * GRID_SIZE

    # Title
    if title:
        title_text = pygameWidgets.Text(__SCREEN, title, (LEFT_TOP[0] + grid_px // 2 + padding, LEFT_TOP[1] + padding // 2), font_size=font_size)
        title_text.draw()

    buttons = [[None] * GRID_SIZE for i in range(GRID_SIZE)]

    inverted_scaled_cell_size = pygameWidgets.get_scaled_size(CELL_SIZE, scale_reference=__SCREEN.get_size(), current_size=(1280, 700))

    # Grid buttons and pegs
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            #buttons
            button = pygameWidgets.Button(__SCREEN, "", inverted_scaled_cell_size, [title_text.center[0] - grid_px // 2 + (col + 0.5) * CELL_SIZE, title_text.rect.bottom + title_text.rect.height + (row + 0.5) * CELL_SIZE], 
                                          fixed_height=True, fixed_width=True, border_color=(100, 100, 100))
            button.draw()
            buttons[row][col] = button
        
    #Write board locations:
    if label: 
        for i in range(GRID_SIZE):
            row_num = pygameWidgets.Text(__SCREEN, f"ABCDEFGHIJKLMNOPQRSTUVWXYZ"[i], [title_text.center[0] - grid_px // 2 - padding // 2, title_text.rect.bottom + title_text.rect.height + (i + 0.5) * CELL_SIZE])
            row_num.draw()

            col_num = pygameWidgets.Text(__SCREEN, f"{i + 1}", [title_text.center[0] - grid_px // 2 + (i + 0.5) * CELL_SIZE, title_text.rect.bottom + title_text.rect.height - padding // 2])
            col_num.draw()
    
    #Confirm guess button
    if interactable and guessed:
        guess_button = pygameWidgets.Button(__SCREEN, "Confirm Guess", 20, [title_text.center[0], title_text.rect.bottom + title_text.rect.height + grid_px + 0.75 * padding], "grey")
        guess_button.draw()

    return buttons, guess_button if interactable else None

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
                if default_button.pressed(event.pos): pass #TODO: have the default button actually do something, or get rid of it
                elif save_button.pressed(event.pos):
                    player_name = player_name_entry_field.input.inner_text
                elif back_button.pressed(event.pos): return
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return
            elif event.type == pygame.KEYDOWN:
                player_name_entry_field.type(event)

async def game() -> None:
    global __SCREEN
    global guess
    global error_message
    global still_playing
    all_sprites = pygame.sprite.Group()
    last_guess = []

    global GRID_SIZE
    GRID_SIZE = 10
    global user_guessed_squares
    user_guessed_squares = [[0] * GRID_SIZE for i in range(GRID_SIZE)]
    global enemy_guessed_squares
    enemy_guessed_squares = [[0] * GRID_SIZE for i in range(GRID_SIZE)]

    asyncio.create_task(handle_server())

    while still_playing.is_set() == False and not error_message:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return
        await asyncio.sleep(0.1)

    radar_buttons, guess_button, enemy_buttons = setup_game_board(pygameWidgets.get_scaled_size(50))

    while not error_message and still_playing.is_set():
        # Draw the sprites
        all_sprites.draw(__SCREEN)

        #update boards
        draw_grid(radar_buttons, pygameWidgets.get_scaled_size(50), guess_button, user_guessed_squares)
        draw_grid(enemy_buttons, pygameWidgets.get_scaled_size(50), guessed=enemy_guessed_squares)

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

                radar_buttons, guess_button, enemy_buttons = setup_game_board(pygameWidgets.get_scaled_size(50))
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                for row in range(len(radar_buttons)):
                    for col in range(len(radar_buttons[row])):
                        if radar_buttons[row][col].pressed(event.pos):
                            if user_guessed_squares[row][col] != 0: break
                            if last_guess and user_guessed_squares[last_guess[0]][last_guess[1]] == 4: user_guessed_squares[last_guess[0]][last_guess[1]] = 0
                            last_guess = [row, col]
                            user_guessed_squares[row][col] = 4
                if last_guess and guess_button.pressed(event.pos):
                    guess = [last_guess[0], last_guess[1]]
                    print("guess")
                    await asyncio.sleep(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: return

def get_server_info():
    global __SCREEN
    global error_message
    global server_ip
    global server_port
    global still_playing

    title = pygameWidgets.Text(__SCREEN, "Server info", [0, 0], font_size=24)

    ip_input = pygameWidgets.EntryField(__SCREEN, [0, 0], "IP: ", input_text=server_ip)

    port_input = pygameWidgets.EntryField(__SCREEN, [0, 0], "Port: ", input_text=server_port)

    confirm_button = pygameWidgets.Button(__SCREEN, "Confirm", 0, [0, 0])

    while not error_message:
        __SCREEN.fill("black")
        box_width = int(__SCREEN.get_width() // 2)
        box_height = int(__SCREEN.get_height() // 2)
        padding = pygameWidgets.get_scaled_size(70)
    
        bounding_box = pygame.Rect(__SCREEN.get_width() // 2 - box_width // 2, __SCREEN.get_height() // 2 - box_height // 2, box_width, box_height)
        pygame.draw.rect(__SCREEN, "black", bounding_box)
        pygame.draw.rect(__SCREEN, "white", bounding_box, 1)
        
        title.center = [bounding_box.centerx, bounding_box.top + padding]
        ip_input.center = [title.rect.center[0], title.rect.bottom + padding]
        port_input.center = [ip_input.center[0], ip_input.center[1] + padding]
        confirm_button.center = [port_input.center[0], port_input.center[1] + padding]
        confirm_button.padding = int(padding // 1.5)

        title.draw()
        ip_input.draw()
        port_input.draw()
        confirm_button.draw()

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                #Entry Fields
                ip_input.pressed(event.pos)
                port_input.pressed(event.pos)
                #Buttons
                if confirm_button.pressed(event.pos): 
                    #TODO: Input validation
                    server_ip = ip_input.input.inner_text
                    server_port = port_input.input.inner_text
                    asyncio.run(game())
                    print("No longer playing")
                    still_playing.clear()
                    return
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return
            elif event.type == pygame.KEYDOWN:
                ip_input.type(event)
                port_input.type(event)

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
                    get_server_info()
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

    global server_ip
    server_ip = "localhost"

    global server_port
    server_port = "6363"

    global player_id
    player_id = 0

    global guess
    guess = False

    global player_name
    player_name = "Anonymous"

    global enemy_name
    enemy_name = "Anonymous"

    global still_playing
    still_playing = asyncio.Event()

    pygame.init()
    
    global __SCREEN
    __SCREEN = pygame.display.set_mode((1280, 700), pygame.RESIZABLE)
    pygameWidgets.SCREEN = __SCREEN

    main()
    if error_message: display_error_box()
    pygame.quit()