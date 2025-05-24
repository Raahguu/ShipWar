#Imports
import pygame
import textwrap
import string
import threading
import asyncio
import pygame.event
import websockets
import json
import abc

def get_scaled_size(base_size : int, min_size : int = None, max_size : int = None, scale_reference = (1280, 700), current_size : tuple[int, int] = None) -> int | float:
    global __SCREEN
    current_size = current_size if current_size else __SCREEN.get_size()
    min_size = min_size if min_size else base_size / 3
    max_size = max_size if max_size else base_size * 3
    scale_factor = min(current_size[0] / scale_reference[0], current_size[1] / scale_reference[1])
    scaled_size = min(max(min_size, base_size * scale_factor), max_size)
    if type(base_size) is int: return round(scaled_size)
    else: return scaled_size


class Widget(metaclass=abc.ABCMeta):
    @classmethod
    @abc.abstractmethod
    def _calc_rect(self):
        """
        Recalculates the Rect, in case of any changes since last calculation
        """
    @classmethod
    @abc.abstractmethod
    def draw(self):
        """
        Draw the object to the screen
        """


class Text(Widget):
    """
    A class for defining and handling Text in pygame
    """
    def __init__(self, screen : pygame.Surface, inner_text: str, center: list[int, int], 
                color : str | list[int, int, int] = "white", font_type : str = None, font_size : int = 18, 
                parent : Widget = None, padding : list[int, int] = [0, 0]):
        self.screen = screen
        self.font_type = font_type
        self.font_size = font_size

        self.inner_text = inner_text
        self.center = center
        self.color = color
        self.__parent = parent
        self.padding = padding

    @property
    def inner_text(self) -> str:
        try: return self.__inner_text
        except: return ""
    @inner_text.setter
    def inner_text(self, value : str):
        self.__inner_text = str(value)
        self._calc_surface()

    @property
    def color(self) -> list[int, int, int] | str:
        try: return self.__color
        except: return "white"
    @color.setter
    def color(self, value : list[int, int, int] | str):
        self.__color = value
        self._calc_surface()

    @property
    def center(self) -> list[int, int]:
        try: return self.__center
        except: return [0, 0]
    @center.setter
    def center(self, value : list[int, int]):
        self.__center = value
        self._calc_rect()

    @property
    def font_size(self) -> int:
        try: return self.__font_size
        except: return 12
    @font_size.setter
    def font_size(self, value : int):
        if type(value) != int: raise TypeError("The font size of text must be an integer")
        if value < 0: raise ValueError("The font size of text must be greater then 0")
        self.__font_size = value
    
    @property
    def font_type(self) -> str:
        try: return self.__font_type
        except: return None
    @font_type.setter
    def font_type(self, value : str):
        pygame.font.Font(value, self.font_size)
        self.__font_type = value

    @property
    def font(self) -> pygame.font.Font:
        try: return pygame.font.Font(self.font_type, get_scaled_size(self.font_size))
        except: return pygame.font.Font()
    @font.setter
    def font(self, value : pygame.font.Font):
        raise AttributeError("You must edit font_size, and font_type seperatly")
    
    @property
    def padding(self) -> list[int, int]:
        try: return self.__padding
        except: return [0, 0]
    @padding.setter
    def padding(self, value : list[int, int] | int):
        if type(value) not in [list, tuple, int]: raise TypeError(f"The text padding must be either a list, a tuple, or an int, not a {type(value)}")
        if type(value) in [list, tuple] and len(value) != 2: raise TypeError(f"The text padding must have a length of 2")
        if type(value) == int: value = [int(value), int(value)]
        self.__padding = list(value)

    def _calc_surface(self):
        self.surface = self.font.render(self.inner_text, True, self.color)
        self._calc_rect()
    
    def _calc_rect(self):
        self.rect = self.surface.get_rect(center=self.center)
        try: self.__parent._calc_rect()
        except: pass

    def draw(self):
        self._calc_surface()
        self.screen.blit(self.surface, self.rect)
        
class Button(Widget):
    """
    A class for defining and handling Buttons in pygame
    """
    def __init__(self, screen : pygame.surface, inner_text: str, padding: list[int, int] | int, center: list[int, int], 
                color : str | list[int, int, int] = "black", border_color : str | list[int, int, int] = "white", 
                text_color : str | list[int, int, int] = "white", font_type : str = None, font_size : int = 18,
                fixed_width : bool = False, fixed_height : bool = False, have_border : bool = True):
        self.screen = screen
        self.text = Text(screen, inner_text, center, text_color, font_type, font_size, parent=self)

        self.padding = padding
        self.center = center
        self.color = color

        self.have_border = have_border
        self.bordor_color = border_color

        self.fixed_width = fixed_width
        self.fixed_height = fixed_height

        self._calc_rect()

    @property
    def screen(self) -> pygame.Surface:
        return self.__screen
    @screen.setter
    def screen(self, value : pygame.Surface):
        if type(value) != pygame.Surface: raise TypeError(f"The Screen attribute must be a pygame.Surface, not a {type(value)}")
        self.__screen = value
        try: self.text.screen = self.__screen
        except: pass

    @property
    def padding(self) -> list[int, int]:
        try: return self.__padding
        except: return [0, 0]
    @padding.setter
    def padding(self, value : list[int, int] | int):
        if type(value) not in (int, list, tuple) or type(value) in (list, tuple) and len(value) != 2: raise TypeError(f"The padding can only either be an int, or a list of two ints for different x and y padding; not a {type(value)}")
        if type(value) is int: value = [value, value]
        if type(value) is tuple: value = list(value)
        self.__padding = value
        self._calc_rect()
    
    @property
    def center(self) -> list[int, int]:
        try: return self.__center
        except: return [0, 0]
    @center.setter
    def center(self, value : list[int, int]):
        if type(value) not in (tuple, list) or len(value) != 2: raise TypeError(f"The center can only either be an tuple, or a list of two ints for the x, and y values; not a {type(value)}")
        self.__center = list(value)
        self._calc_rect()

    @property
    def fixed_width(self) -> bool:
        try: return self.__fixed_width
        except: return False
    @fixed_width.setter
    def fixed_width(self, value : bool):
        self.__fixed_width = bool(value)
        self._calc_rect()

    @property
    def fixed_height(self) -> bool:
        try: return self.__fixed_height
        except: return False
    @fixed_height.setter
    def fixed_height(self, value : bool):
        self.__fixed_height = bool(value)
        self._calc_rect()
       
    def _calc_rect(self) -> None:
        self.rect = pygame.Rect(0, 0, (self.text.surface.get_width() if not self.fixed_width else 0) + get_scaled_size(self.padding[0]), 
                                (self.text.surface.get_height() if not self.fixed_height else 0) +  get_scaled_size(self.padding[1]))
        self.rect.center = (self.center[0], self.center[1])

    def draw(self) -> None:
        self._calc_rect()
        pygame.draw.rect(self.screen, self.color, self.rect)
        if self.have_border: pygame.draw.rect(self.screen, self.bordor_color, self.rect, 1)
        self.text.draw()

    def pressed(self, *args):
        return self.rect.collidepoint(*args)
    

class EntryField(Widget):
    class Cursor(Widget):
        def __init__(self, screen : pygame.Surface, visible : bool, editing_text : Text, starting_index : int = None, width : int = 1, color : list[int, int, int] | str = "white", height_padding : int = 5):
            self.screen = screen
            self.visible = visible
            self.editing_text = editing_text
            self.width = width
            self.color = color
            self.index = starting_index
            self.height_padding = height_padding
        
        @property
        def width(self):
            try: return self.__width
            except: 0
        @width.setter
        def width(self, value : int):
            if type(value) != int or value < 0: raise TypeError("The Entry Fields Cursor's width needs to be an integer greater than or equal to 0")
            self.__width = value
            self._calc_rect()

        @property
        def index(self):
            try: return self.__index
            except: 0
        @index.setter
        def index(self, value : int):
            if value == None: value = len(self.editing_text.inner_text)
            if type(value) != int: raise TypeError("The Entry Fields Cursor's index needs to be an integer")
            if value < 0: value = 0
            if value > len(self.editing_text.inner_text): value = len(self.editing_text.inner_text)
            self.__index = value
            self._calc_rect()

        @property
        def height_padding(self) -> int:
            try: return self.__height_padding
            except: return 0
        @height_padding.setter
        def height_padding(self, value : int):
            if value == None: value = 0
            if type(value) != int: raise TypeError("The Entry Fields Cursor's height padding needs to be an integer")
            if value < 0: value = 0
            self.__height_padding = value
            self._calc_rect()

        @property
        def editting_text(self):
            return self.__editting_text
        @editting_text.setter
        def editting_text(self, value : Text):
            if type(value) != Text: raise TypeError("The Entry Fields Cursor's editting_text needs to be of the type Text")
            self.__editting_text = value
            self._calc_rect()

        def _calc_rect(self):
            self.rect = pygame.Rect(0, 0, get_scaled_size(self.width), self.editing_text.rect.height + get_scaled_size(self.height_padding))
            self.rect.center = (self.editing_text.center[0] - self.editing_text.rect.width // 2 +  int(self.editing_text.font.size(self.editing_text.inner_text[:self.index])[0]), self.editing_text.center[1])

        def draw(self):
            self._calc_rect()
            if self.visible: pygame.draw.rect(self.screen, self.color, self.rect)

    def __init__(self, screen : pygame.Surface, center : list[int, int], title_text : str = "title", title_field_dist : int = 20, 
                 text_color : list[int, int, int] | str = "white", font_type : str = None, font_size : int = 26, input_text : str = "", 
                 input_padding : list[int, int] = [20, 20], width : int = 250, color : list[int, int, int] | str = "grey30",
                 visible_cursor : bool = True, cursor_color : list[int, int, int] | str = "white", cursor_width : int = 1,
                 cursor_height_padding : int = 5): 
        self.screen = screen
        self.has_focus = False
        self.title_field_dist = title_field_dist
        self.color = color

        self.title = Text(self.screen, title_text, (0, 0), text_color, font_type, font_size, self)
        self.input = Text(self.screen, input_text, (0, 0), text_color, font_type, font_size, self, input_padding)
        self.cursor = EntryField.Cursor(self.screen, visible_cursor, self.input, width=cursor_width, color=cursor_color, height_padding=cursor_height_padding)

        self.center = center
        self.width = width

        self._calc_rect()

    @property
    def screen(self) -> pygame.Surface:
        return self.__screen
    @screen.setter
    def screen(self, value : pygame.Surface):
        if type(value) != pygame.Surface: raise TypeError("The Entry Field's screen, must be a surface")
        self.__screen = value
        try:
            self.title.screen = self.screen
            self.input.screen = self.screen
        except: pass

    @property
    def center(self) -> list[int, int]:
        try: return self.__center
        except: return [0, 0]
    @center.setter
    def center(self, value : list[int, int]):
        if type(value) not in (list, tuple) or type(value) in (list, tuple) and len(value) != 2: raise ValueError("The center must be a list or tuple of length 2")
        self.__center = list(value)
        self.title.center = (self.center[0] - self.title.font.size(self.title.inner_text)[0] - get_scaled_size(self.title_field_dist) // 2, self.center[1])
        self._calc_rect()
        self.input.center = (self.rect.center[0] - self.rect.width // 2 + self.input.rect.width // 2 + get_scaled_size(self.input.padding[0]), self.rect.center[1])

    @property
    def width(self) -> int:
        """Width of the Entry Field"""
        try: return self.__width
        except: return 0
    @width.setter
    def width(self, value : int):
        if type(value) != int or value < 0: raise TypeError("The Width must be an int greater than or equal to 0")
        self.__width = value
        self._calc_rect()

    def _calc_rect(self):
        self.rect = pygame.Rect(0, 0, get_scaled_size(self.width), self.input.rect.height + get_scaled_size(self.input.padding[1]))
        self.rect.center = (self.title.center[0] + self.title.rect.width // 2 + get_scaled_size(self.title_field_dist) + self.rect.width // 2, self.title.center[1])

    def draw(self) -> None:
        self._calc_rect()
        self.title.draw()
        pygame.draw.rect(self.screen, self.color, self.rect)
        self.input.draw()
        if self.has_focus: self.cursor.draw()

    def pressed(self, *args):
        self.has_focus = self.rect.collidepoint(*args)

    def type(self, event : pygame.event.Event):
        """Handels typing to the Entry Field"""
        if not self.has_focus: return
        if event.key == pygame.K_BACKSPACE: 
            self.input.inner_text = self.input.inner_text[:self.cursor.index - 1] + self.input.inner_text[self.cursor.index:]
            self.cursor.index -= 1
        elif event.key == pygame.K_DELETE: 
            self.input.inner_text = self.input.inner_text[:self.cursor.index] + self.input.inner_text[self.cursor.index + 1:]
        elif event.key == pygame.K_LEFT: self.cursor.index -= 1
        elif event.key == pygame.K_RIGHT: self.cursor.index += 1
        elif not event.key in (pygame.K_RETURN, pygame.K_DELETE, pygame.K_TAB): 
            if self.input.font.size(self.input.inner_text + event.unicode)[0] >= self.width - self.input.padding[0] * 2: return
            self.input.inner_text = self.input.inner_text[:self.cursor.index] + event.unicode + self.input.inner_text[self.cursor.index:]
            self.cursor.index += 1

def display_error_box() -> None:
    global error_message

    screen = __SCREEN
    screen_width, screen_height = screen.get_size()
    font_size = 24
    font = pygame.font.Font(None, get_scaled_size(font_size))

    padding = get_scaled_size(20)
    line_spacing = get_scaled_size(5)
    button_height = get_scaled_size(40)
    scroll_speed = get_scaled_size(20)

    max_box_width = screen_width - get_scaled_size(100)
    max_chars_per_line = max_box_width // font.size("A")[0]
    wrapped_lines = textwrap.wrap(error_message, width=max_chars_per_line)

    line_height = font.get_height()
    total_text_height = len(wrapped_lines) * (line_height + line_spacing)
    visible_text_height = min(total_text_height, screen_height - button_height - 3 * padding - get_scaled_size(75))

    scroll_offset = 0
    scrollable = total_text_height > visible_text_height
    max_scroll = total_text_height - visible_text_height if scrollable else 0

    box_width = max(min(max_box_width, max(font.size(line)[0] for line in wrapped_lines)), 150) + 2 * padding
    box_height = visible_text_height + 2 * padding + button_height + get_scaled_size(10)
    box_x = (screen_width - box_width) // 2
    box_y = (screen_height - box_height) // 2

    # OK button
    ok_button = Button(__SCREEN, "OK", [20, 10], [box_x + box_width // 2, box_y + box_height - button_height // 2 - padding], color="red", font_size=font_size)

    # Create a surface for the scrollable area
    scroll_area_rect = pygame.Rect(box_x + padding, box_y + padding, box_width - 2 * padding, visible_text_height)
    scroll_surface = pygame.Surface(scroll_area_rect.size)
    scroll_surface.set_colorkey((0, 0, 0))
    print(error_message)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if ok_button.pressed(event.pos):
                    pygame.quit()
                    exit()
            elif event.type == pygame.MOUSEWHEEL and scrollable:
                scroll_offset -= event.y * scroll_speed
                scroll_offset = max(0, min(scroll_offset, max_scroll))

        screen.fill("black")

        # Draw box
        pygame.draw.rect(screen, "grey30", (box_x, box_y, box_width, box_height))
        pygame.draw.rect(screen, "white", (box_x, box_y, box_width, box_height), 1)

        # Prepare scrollable text surface
        scroll_surface.fill("grey30")

        y = -scroll_offset
        for line in wrapped_lines:
            text_surface = font.render(line, True, "white")
            scroll_surface.blit(text_surface, (0, y))
            y += line_height + line_spacing

        # Blit the scroll area with clipping
        screen.set_clip(scroll_area_rect)
        screen.blit(scroll_surface, scroll_area_rect.topleft)
        screen.set_clip(None)

        # Draw scroll bar
        if scrollable:
            bar_width = get_scaled_size(10)
            bar_height = max(visible_text_height * visible_text_height // total_text_height, get_scaled_size(20))
            scroll_ratio = scroll_offset / max_scroll if max_scroll > 0 else 0
            bar_y = scroll_area_rect.y + int(scroll_ratio * (visible_text_height - bar_height))
            bar_rect = pygame.Rect(scroll_area_rect.right - bar_width, bar_y, bar_width, bar_height)
            pygame.draw.rect(screen, "white", bar_rect)

        # Draw OK button
        ok_button.draw()

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

def draw_menu() -> tuple[Button, Button, Button]:
    global __SCREEN

    #Titles
    title_padding = get_scaled_size(50)
    title = Text(__SCREEN, "ShipWar", (__SCREEN.get_width() // 2, title_padding), font_size=80, padding=title_padding)
    title.draw()

    subtitle_padding = get_scaled_size(50)
    subtitle = Text(__SCREEN, "By Joshua Finlayson", (__SCREEN.get_width() // 2, title.padding[1] + title.center[1]), font_size=24, padding=subtitle_padding)
    subtitle.draw()

    #Buttons
    title_button_dist = get_scaled_size(50)
    button_padding = get_scaled_size(40)
    button_button_dist = get_scaled_size(40)

    play_button = Button(__SCREEN, "Play", (get_scaled_size(200), button_padding), 
                              (__SCREEN.get_width() // 2, subtitle.center[1] + title_button_dist + subtitle.padding[1]), 
                              fixed_width=True, color="blue", font_size=36)
    settings_button = Button(__SCREEN, "Settings", (get_scaled_size(200), button_padding), 
                                  (__SCREEN.get_width() // 2, play_button.center[1] + button_padding + button_button_dist), 
                                  fixed_width=True, color="blue", font_size=36)
    quit_button = Button(__SCREEN, "Quit", (get_scaled_size(200), button_padding), 
                              (__SCREEN.get_width() // 2, settings_button.center[1] + button_padding + button_button_dist), 
                              fixed_width=True, color="blue", font_size=36)
    play_button.draw()
    settings_button.draw()
    quit_button.draw()

    return play_button, settings_button, quit_button

def draw_settings_menu(player_name_entry_field : EntryField) -> tuple[EntryField, Button, Button, Button]:
    global __SCREEN

    __SCREEN.fill("black")
    title_padding = get_scaled_size(50)

    #Put in title
    title = Text(__SCREEN, "Settings", (__SCREEN.get_width() // 2, title_padding), font_size=80)
    title.draw()

    #Entry Fields
    title_entry_field_dist = get_scaled_size(50)

    player_name_entry_field.center = (__SCREEN.get_width() // 2, title.center[1] + title_padding + title_entry_field_dist)
    player_name_entry_field.draw()

    #Buttons
    entry_button_dist = get_scaled_size(70)
    button_padding = get_scaled_size(40)
    button_button_y_dist = get_scaled_size(40)
    button_button_x_dist =  get_scaled_size(40)
    button_width = get_scaled_size(250)

    default_button = Button(__SCREEN, "Set all to Default", (button_width, button_padding), 
                              ((__SCREEN.get_width() - button_width - button_button_x_dist) // 2, player_name_entry_field.center[1] + player_name_entry_field.rect.height + entry_button_dist), 
                              fixed_width=True, color="blue", font_size=36)
    save_button = Button(__SCREEN, "Save", (button_width, button_padding), 
                                  ((__SCREEN.get_width() + button_width + button_button_x_dist) // 2, default_button.center[1]), 
                                  fixed_width=True, color="blue", font_size=36)
    back_button = Button(__SCREEN, "Back", (button_width, button_padding), 
                              (__SCREEN.get_width() // 2, save_button.center[1] + button_padding + button_button_y_dist), 
                              fixed_width=True, color="blue", font_size=36)
    default_button.draw()
    save_button.draw()
    back_button.draw()

    return player_name_entry_field, default_button, save_button, back_button

def settings() -> None:
    global error_message
    global player_name

    player_name_entry_field = EntryField(__SCREEN, (0, 0), "Player Name: ", font_size=26, title_field_dist=20, input_padding=20, width=250, input_text=player_name)
    
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
    player_name = "Default"

    pygame.init()
    
    global __SCREEN
    __SCREEN = pygame.display.set_mode((1280, 700), pygame.RESIZABLE)

    main()
    if error_message: display_error_box()
    pygame.quit()