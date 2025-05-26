import pygame
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