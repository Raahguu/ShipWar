#Imports
import pygame
import asyncio
import pygame.gfxdraw
import websockets
import json
import pygameWidgets

def get_cell_size(screen : pygame.Surface, padding : int):
    global GRID_SIZE
    return int(min(screen.get_width() / 2 - 2 * padding, screen.get_height() - 4 * padding) // GRID_SIZE)

async def listen_to_server(socket: websockets.ClientConnection) -> None:
    global error_message, user_guessed_squares, enemy_guessed_squares, player_id, enemy_name, still_playing, players_turn
    while still_playing:
        try:
            reply = json.loads(await socket.recv())
            print("Received:", reply)
            if reply["type"] == "welcome":
                player_id = int(reply["player"])
                if player_id != 1: players_turn = False
            elif reply["type"] == "username":
                enemy_name = reply["name"]
                still_playing.set()
            elif reply["type"] == "guess_result":
                user_guessed_squares[reply["position"][0]][reply["position"][1]] = reply["result"]
                players_turn = False
            elif reply["type"] == "enemy_guess_result":
                enemy_guessed_squares[reply["position"][0]][reply["position"][1]] = reply["result"]
                players_turn = True
            elif reply["type"] == "done":
                if reply["result"] == 1: error_message = "w"
                else: error_message = "l"
                return
            elif reply["type"] == "disconnection":
                if not error_message: error_message = "The other player disconnected"
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
    global guess, error_message, server_ip, server_port, still_playing, player_name, player_id, enemy_name, ships_placed, ship_objs

    #connect to the server
    try:
        ws_connection = await websockets.connect("ws://" + str(server_ip) + ":" + str(server_port))
    except Exception as e:
        error_message = f"Could not connect to server: {str(e)}"
        return
    
    #Add server event listener
    asyncio.create_task(listen_to_server(ws_connection))

    await ws_connection.send(json.dumps({"type":"username", "name": player_name}))

    #When ready to send the ships, send them
    await ships_placed.wait()
    try:
        message : list[list[list[int, int]]] = []
        for ship in ship_objs:
            curr_ship_locations : list[list[int, int]] = []
            for col in ship.blocks:
                for block in col:
                    cell_numbers = [(block.topleft[1] - ship.grid_origin[1]) / ship.cell_size, (block.topleft[0] - ship.grid_origin[0]) / ship.cell_size]
                    curr_ship_locations.append(cell_numbers)
            message.append(curr_ship_locations)
        await ws_connection.send(json.dumps({"type":"ships", "message": message}))
    except Exception as e:
        error_message = f"Failed to send ship locations to server. Error: {str(e)}"
        return

    await still_playing.wait()

    #loop through the game loop if were still playing and there are no errors yet
    while not error_message and still_playing.is_set():
        await asyncio.sleep(0.1)
        #if the player has guessed
        if guess:
            #Tell server guess
            try:
                await ws_connection.send(json.dumps({"type":"guess", "position": [int(guess[0]), int(guess[1])]}))
            except Exception as e:
                error_message = f"Failed to send guess: {str(e)}"
                return
            
            guess = False

    await ws_connection.send(json.dumps({"type":"disconnection"}))
    await ws_connection.close()
    still_playing.clear()

def display_win_message(screen : pygame.Surface) -> None:
    win_text = pygameWidgets.Text(screen, "You Won!!!", [0, 0], "green", font_size=48)
    ok_button = pygameWidgets.Button(screen, "OK", 20, [0, 0])

    while True:
        screen.fill("black")
        screen_height = screen.get_height()
        screen_width = screen.get_width()
        border = pygame.Rect(int(screen_width * 0.1), int(screen_height * 0.1), int(screen_width * 0.8), int(screen_height * 0.8))
        pygame.draw.rect(screen, "red", border, 1)

        #win text
        win_text.center = [int(screen_width * 0.5), int(screen_height * 0.5)]
        win_text.padding = int(screen_height * 0.2)
        win_text.draw()

        #OK button
        ok_button._block_calcs = True
        ok_button.padding = int(screen_height * 0.025)
        ok_button._block_calcs = False
        ok_button.center = [win_text.center[0], win_text.center[1] + win_text.padding[0]]
        ok_button.draw()

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if ok_button.pressed(event.pos): 
                    pygame.quit()
                    return
                
def display_lose_message(screen : pygame.Surface) -> None:
    lose_text = pygameWidgets.Text(screen, "You Lost.", [0, 0], "green", font_size=48)
    ok_button = pygameWidgets.Button(screen, "OK", 20, [0, 0])

    while True:
        screen.fill("black")
        screen_height = screen.get_height()
        screen_width = screen.get_width()
        border = pygame.Rect(int(screen_width * 0.1), int(screen_height * 0.1), int(screen_width * 0.8), int(screen_height * 0.8))
        pygame.draw.rect(screen, "red", border, 1)

        #lose text
        lose_text.center = [int(screen_width * 0.5), int(screen_height * 0.5)]
        lose_text.padding = int(screen_height * 0.2)
        lose_text.draw()

        #OK button
        ok_button._block_calcs = True
        ok_button.padding = int(screen_height * 0.025)
        ok_button._block_calcs = False
        ok_button.center = [lose_text.center[0], lose_text.center[1] + lose_text.padding[0]]
        ok_button.draw()

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            if event.type == pygame.MOUSEBUTTONDOWN:
                if ok_button.pressed(event.pos): 
                    pygame.quit()
                    return

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

    # Right board - Player'submarine_ship ships
    right_x = __SCREEN.get_width() // 2
    enemy_buttons = setup_grid(LEFT_TOP=(right_x, padding // 2), title="Game Board", label=True, font_size=font_size, padding=padding, guessed=enemy_guessed_squares)[0]

    return radar_buttons, guess_button, enemy_buttons

def draw_grid(buttons : list[list[pygameWidgets.Button]], padding : int, guess_button : pygameWidgets.Button = None, guessed=None, allowed_to_guess = False):
    can_guess = False
    circle_radius = get_cell_size(__SCREEN, padding) // 8
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            cx, cy = map(int, buttons[row][col].center)

            if guessed:
                match guessed[row][col]:
                    case 0: pygame.gfxdraw.filled_circle(__SCREEN, cx, cy, circle_radius, (80, 80, 80)) # grey for base color
                    case 1: pygame.gfxdraw.filled_circle(__SCREEN, cx, cy, circle_radius, (255, 255, 255)) # white for miss
                    case 2: pygame.gfxdraw.filled_circle(__SCREEN, cx, cy, circle_radius, (255, 165, 0)) # orange for hit, but not sink/sunk
                    case 3: pygame.gfxdraw.filled_circle(__SCREEN, cx, cy, circle_radius, (255, 0, 0)) # red for sink/sunk
                    case 4: pygame.gfxdraw.filled_circle(__SCREEN, cx, cy, circle_radius, (0, 0, 255)); can_guess = True # blue for the one the player is currently going to guess
    
    if guess_button:
        guess_button.color = "blue" if can_guess and allowed_to_guess else "grey"
        guess_button.draw()

def setup_grid(LEFT_TOP, title="", label=False, font_size : int = 24, padding=0, 
              interactable=False, guessed=None) -> tuple[list[list[pygameWidgets.Button]], pygameWidgets.Button | None]:
    CELL_SIZE = get_cell_size(__SCREEN, padding)
    grid_px = CELL_SIZE * GRID_SIZE

    # Title
    if title:
        title_text = pygameWidgets.Text(__SCREEN, title, (LEFT_TOP[0] + grid_px // 2 + padding, LEFT_TOP[1] + padding // 2), font_size=font_size)
        title_text.draw()

    buttons = [[None] * GRID_SIZE for i in range(GRID_SIZE)]

    def get_inverse_scaled_size(target_scaled_size: int, scale_reference=(1280, 700), current_size=None) -> float:
        current_size = current_size or __SCREEN.get_size()
        scale_factor = min(current_size[0] / scale_reference[0], current_size[1] / scale_reference[1])
        return round(target_scaled_size / scale_factor)

    inverted_scaled_cell_size = get_inverse_scaled_size(CELL_SIZE)

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
        guess_button = pygameWidgets.Button(__SCREEN, "Confirm", 20, [title_text.center[0], title_text.rect.bottom + title_text.rect.height + grid_px + 0.75 * padding], "grey")
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

def send_ship_locations(ship_2 : pygameWidgets.Ship, ship_3a : pygameWidgets.Ship, ship_3b : pygameWidgets.Ship, ship_4 : pygameWidgets.Ship, ship_5 : pygameWidgets.Ship) -> True:
    global ships_placed
    global ship_objs

    ship_objs = [ship_2, ship_3a, ship_3b, ship_4, ship_5]
    ships_placed.set()

    return True

def validate_ship_positions(ships : list[pygameWidgets.Ship]) -> bool:
    #Some input validation to ensure that all the ships locations are valid/on the board
    global GRID_SIZE
    def to_grid_location(ship : pygameWidgets.Ship, i : int, y_not_x = False):
        e = (i - ship.grid_origin[y_not_x]) / ship.cell_size
        print(e)
        return int(e)

    for ship in ships:
        ship._calc_rect()
        if (to_grid_location(ship, ship.border_rect.left) < 0 or to_grid_location(ship, ship.border_rect.top, 1) < 0 or
            to_grid_location(ship, ship.border_rect.left) + abs(ship.dimensions[0]) - 1 > GRID_SIZE - 1 or
            to_grid_location(ship, ship.border_rect.top, 1) + abs(ship.dimensions[1]) - 1 > GRID_SIZE - 1):
            return False
    return True

async def place_pieces() -> None:
    global error_message, __SCREEN

    #Center calculations
    padding_calc = lambda: pygameWidgets.get_scaled_size(30)

    pieces_title_center_calc = lambda: (__SCREEN.get_width() * 0.8, padding_calc())
    confirm_button_center_calc = lambda: (__SCREEN.get_width() * 0.3, __SCREEN.get_height() - padding_calc())
    dividing_line_start_point_calc = lambda: (__SCREEN.get_width() * 0.6, 0)
    dividing_line_end_point_calc = lambda: (__SCREEN.get_width() * 0.6, __SCREEN.get_height())

    starting_ship_y_padding = pygameWidgets.get_scaled_size(30)

    pieces_title = pygameWidgets.Text(__SCREEN, "Pieces", pieces_title_center_calc(), font_size=24)
    confirm_button = pygameWidgets.Button(__SCREEN, "Confirm", 0, confirm_button_center_calc())
    destroyer_ship = pygameWidgets.Ship(__SCREEN, (pieces_title.center[0], starting_ship_y_padding + __SCREEN.get_height() // 6), 1, [2, 1])
    submarine_ship = pygameWidgets.Ship(__SCREEN, (pieces_title.center[0], starting_ship_y_padding + 2 * __SCREEN.get_height() // 6), 1, [3, 1])
    cruiser_ship = pygameWidgets.Ship(__SCREEN, (pieces_title.center[0], starting_ship_y_padding + 3 * __SCREEN.get_height() // 6), 1, [3, 1])
    battleship_ship = pygameWidgets.Ship(__SCREEN, (pieces_title.center[0], starting_ship_y_padding + 4 * __SCREEN.get_height() // 6), 1, [4, 1])
    carrier_ship = pygameWidgets.Ship(__SCREEN, (pieces_title.center[0], starting_ship_y_padding + 5 * __SCREEN.get_height() // 6), 1, [5, 1])

    while not error_message:
        await asyncio.sleep(1/60)

        valid_ship_positions = validate_ship_positions([destroyer_ship, submarine_ship, cruiser_ship, battleship_ship, carrier_ship])

        __SCREEN.fill("black")

        grid_buttons = setup_grid((0, 0), "Your Board", True, padding=padding_calc())

        pygame.draw.line(__SCREEN, "white", dividing_line_start_point_calc(), dividing_line_end_point_calc(), 1)

        pieces_title.center = pieces_title_center_calc()
        pieces_title.draw()
        confirm_button._block_calcs = True
        confirm_button.padding = padding_calc()
        confirm_button.color = "blue" if valid_ship_positions else "grey"
        confirm_button._block_calcs = False
        confirm_button.center = confirm_button_center_calc()
        confirm_button.draw()

        ship_cell_size = get_cell_size(__SCREEN, padding_calc())
        destroyer_ship.cell_size = ship_cell_size
        submarine_ship.cell_size = ship_cell_size
        cruiser_ship.cell_size = ship_cell_size
        battleship_ship.cell_size = ship_cell_size                
        carrier_ship.cell_size = ship_cell_size                                                
        
        ship_grid_origin = grid_buttons[0][0][0].rect.topleft
        destroyer_ship.grid_origin = ship_grid_origin
        submarine_ship.grid_origin = ship_grid_origin
        cruiser_ship.grid_origin = ship_grid_origin
        battleship_ship.grid_origin = ship_grid_origin
        carrier_ship.grid_origin = ship_grid_origin

        destroyer_ship.draw()
        submarine_ship.draw()
        cruiser_ship.draw()
        battleship_ship.draw()                
        carrier_ship.draw()
        

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                await asyncio.sleep(1/60)
                pygame.quit()
                return False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return False
            if event.type == pygame.MOUSEBUTTONDOWN: 
                if confirm_button.pressed(event.pos) and valid_ship_positions: 
                    send_ship_locations(destroyer_ship, submarine_ship, cruiser_ship, battleship_ship, carrier_ship)
                    return True
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 or event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if destroyer_ship.flip_dragging(event): continue
                if submarine_ship.flip_dragging(event): continue
                if cruiser_ship.flip_dragging(event): continue
                if battleship_ship.flip_dragging(event): continue
                carrier_ship.flip_dragging(event)
                
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                destroyer_ship.rotate(event)
                submarine_ship.rotate(event)
                cruiser_ship.rotate(event)
                battleship_ship.rotate(event)
                carrier_ship.rotate(event)
                
        #if mouse'submarine_ship left button is held down
        if pygame.mouse.get_pressed()[0]:
            destroyer_ship.drag(pygame.mouse.get_pos())
            submarine_ship.drag(pygame.mouse.get_pos())
            cruiser_ship.drag(pygame.mouse.get_pos())
            battleship_ship.drag(pygame.mouse.get_pos())
            carrier_ship.drag(pygame.mouse.get_pos())
            

async def game() -> None:
    global __SCREEN
    global guess
    global error_message
    global still_playing
    global players_turn
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
            if event.type == pygame.QUIT:
                await asyncio.sleep(1/60)
                pygame.quit()
                return
        await asyncio.sleep(0.1)

    if (await place_pieces()) == False: return
    

    radar_buttons, guess_button, enemy_buttons = setup_game_board(pygameWidgets.get_scaled_size(50))

    while not error_message and still_playing.is_set():
        # Draw the sprites
        await asyncio.sleep(1/60)

        #update boards
        draw_grid(radar_buttons, pygameWidgets.get_scaled_size(50), guess_button, user_guessed_squares, allowed_to_guess=players_turn)
        draw_grid(enemy_buttons, pygameWidgets.get_scaled_size(50), guessed=enemy_guessed_squares)

        # Update the display
        pygame.display.flip()

        #Handle user events
        for event in pygame.event.get():
            #Let the player quit the game
            if event.type == pygame.QUIT:
                await asyncio.sleep(1/60)
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
                if last_guess and guess_button.pressed(event.pos) and players_turn:
                    guess = [last_guess[0], last_guess[1]]
                    await asyncio.sleep(0)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    await asyncio.sleep(1/60) 
                    return

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

    global ships_placed
    ships_placed = asyncio.Event()

    global ship_objs
    ship_objs = []

    global players_turn
    players_turn = True

    pygame.init()
    
    global __SCREEN
    __SCREEN = pygame.display.set_mode((1280, 700), pygame.RESIZABLE)
    pygameWidgets.SCREEN = __SCREEN

    main()
    if error_message: 
        if error_message == "w": display_win_message(__SCREEN)
        elif error_message == "l": display_lose_message(__SCREEN)
        else: pygameWidgets.display_error_box(__SCREEN, error_message)
    pygame.quit()