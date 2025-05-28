import pygame
import abc

global SCREEN
SCREEN = None

def get_scaled_size(base_size : int, min_size : int = 1, max_size : int = None, scale_reference = (1280, 700), current_size : tuple[int, int] = None) -> int | float:
    global SCREEN
    current_size = current_size if current_size else SCREEN.get_size()
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
                color : str | list[int, int, int] = "white", font_type : str = 'droid-sans-mono.ttf', font_size : int = 18, 
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

class TextArea(Widget):
    """
    A class for having multiple lines of text
    """
    class scrollBar(Widget):
        def __init__(self, screen : pygame.surface, size : list[int, int], right : int, scroll_range : list[int, int], 
                     color : str | list[int, int] = "white", scroll_speed = 5, visible = True, parent : Widget = None, scroll_offset : int = 0):
            self.screen = screen
            self.size = size
            self.right = right
            self.scroll_range = scroll_range
            self.color = color
            self.visible = visible
            self.scroll_speed = scroll_speed
            self.parent = parent
            self.scroll_offset = scroll_offset

            self._calc_rect()
        
        def _calc_rect(self):
            self.rect = pygame.Rect(self.right - self.size[0], self.scroll_range[0] + self.scroll_offset, self.size[0], self.size[1])

        def scroll(self, event : pygame.event.Event):
            self.scroll_offset -= event.y * self.scroll_speed
            self.scroll_offset = max(0, min(self.scroll_offset, self.scroll_range[1] - self.scroll_range[0]))
            try: self.parent.scroll_offset = self.scroll_offset
            except: pass
            self._calc_rect()
        
        def draw(self):
            if self.size[1] > self.scroll_range[1] - self.scroll_range[0]: return
            pygame.draw.rect(self.screen, self.color, self.rect)

    def __init__(self, screen : pygame.surface, size : list[int, int], center : list[int, int], inner_text : str, text_color : str | list[int, int, int] = "white", 
                 backdrop_color : str | list[int, int, int] = "black", scroll_bar_width : int = 5, scroll_offset : int = 0,
                 padding : int | list[int, int] = [0, 0], font_size : int = 18, font_type : str = 'droid-sans-mono.ttf'):
        self.screen = screen
        self.size = size
        self.center = center
        self.inner_text = inner_text
        self.text_color = text_color
        self.backdrop_color = backdrop_color
        self.padding = padding
        self.font_size = font_size
        self.font_type = font_type
        self.scroll_offset = scroll_offset
        self.scroll_bar_width = scroll_bar_width

        self._calc_wrap_text()
        
    @property
    def font(self):
        return pygame.font.Font(self.font_type, get_scaled_size(self.font_size))
    @font.setter
    def font(self, value):
        raise AttributeError("You need to edit the font_type and font_size seperately")
    
    @property
    def screen(self) -> pygame.Surface:
        return self.__screen
    @screen.setter
    def screen(self, value : pygame.Surface):
        self.__screen = value
        self._calc_wrap_text()

    @property
    def size(self) -> list[int, int]:
        try: return self.__size
        except: return [0, 0]
    @size.setter
    def size(self, value : list[int, int]):
        if type(value) not in [list, tuple] or len(value) != 2: raise TypeError(f"The size must be a list of two integers, not a {type(value)}")
        self.__size = list(value)
        self._calc_wrap_text()

    @property
    def center(self) -> list[int, int]:
        try: return self.__center
        except: return [0, 0]
    @center.setter
    def center(self, value : list[int, int]):
        if type(value) not in [list, tuple] or len(value) != 2: raise TypeError(f"The center must be a list of two integers, not a {type(value)}")
        self.__center = list(value)
        self._calc_text_centers()
    
    @property
    def inner_text(self) -> str:
        try: return self.__inner_text
        except: return "e"
    @inner_text.setter
    def inner_text(self, value : str):
        self.__inner_text = str(value)
        self._calc_wrap_text()
    
    @property
    def text_color(self) -> list[int, int, int] | str:
        try: return self.__text_color
        except: return "white"
    @text_color.setter
    def text_color(self, value : list[int, int, int] | str):
        if type(value) not in [str, list, tuple] or type(value) in [list, tuple] and len(value) != 3: raise TypeError(f"The text_color must be a list of three integers or a string, not a {type(value)}")
        if type(value) == tuple: value = list(value)
        self.__text_color = value
        self._calc_wrap_text()
    
    @property
    def backdrop_color(self) -> list[int, int, int] | str:
        try: return self.__backdrop_color
        except: return "black"
    @backdrop_color.setter
    def backdrop_color(self, value : list[int, int, int] | str):
        if type(value) not in [str, list, tuple] or type(value) in [list, tuple] and len(value) != 3: raise TypeError(f"The size must be a list of three integers or a string, not a {type(value)}")
        if type(value) == tuple: value = list(value)
        self.__backdrop_color = value
        self._calc_wrap_text()
    
    @property
    def padding(self) -> list[int, int]:
        try: return self.__padding
        except: return [0, 0]
    @padding.setter
    def padding(self, value : list[int, int] | int):
        if type(value) == int: value = [value, value]
        self.__padding = value
        self._calc_wrap_text()
    
    @property
    def font_size(self) -> int:
        try: return self.__font_size
        except: return 12
    @font_size.setter
    def font_size(self, value : int):
        if type(value) != int or value <= 0: raise TypeError("The font_size must be an integer greater than 0")
        self.__font_size = value
        self._calc_wrap_text()
    
    @property
    def font_type(self) -> str:
        try: return self.__font_type
        except: return "droid-sans-mono.ttf"
    @font_type.setter
    def font_type(self, value : str):
        if type(value) not in [str, None]: raise TypeError("The font_type must be a string, or 'None'")
        try: pygame.font.Font(value, self.font_size)
        except: raise AttributeError("Font type invalid")
        self.__font_type = value
        self._calc_wrap_text()
    
    @property
    def scroll_offset(self) -> int:
        try: return self.__scroll_offset
        except: return 0
    @scroll_offset.setter
    def scroll_offset(self, value : int):
        if type(value) != int: raise TypeError("The scroll_offset must be an int")
        self.__scroll_offset = value
        self._calc_wrap_text()
    
    @property
    def scroll_bar_width(self) -> int:
        try: return self.__scroll_bar_width
        except: return 0
    @scroll_bar_width.setter
    def scroll_bar_width(self, value : int):
        self.__scroll_bar_width = value

    def _calc_wrap_text(self):
        """
        Calculates the wrapping of text, so that it is segmented into lines that wift within the text area
        """
        calculated_text = self.inner_text.strip()
        text_list = []
        for i in calculated_text.split():
            text_list += [[i, self.font.size(i)[0]]]

        max_text_width = get_scaled_size(self.size[0]) - 3 * get_scaled_size(self.padding[0])

        size_of_space = self.font.size(" ")[0]
        
        wrapped_text = []
        length = -size_of_space
        last_i = 0
        for i, word in enumerate(text_list):
            #If the word is too long to display by itself
            if word[1] > max_text_width:
                for j in range(1, len(word[0])):
                    part_length = self.font.size(word[0][0:j])[0]
                    if part_length > max_text_width:
                        text_list.insert(i + 1, [word[0][j:-1], word[1] - part_length - size_of_space])
                        word = [word[0][0:j], part_length]
                        text_list[i] = word
                        break
            
            length += word[1] + size_of_space
            if length > max_text_width:
                wrapped_text += [[" ".join([j[0] for j in text_list[last_i:i]]), length - word[1] - size_of_space]]
                length = word[1]
                last_i = i
            elif i == len(text_list) - 1:
                wrapped_text += [[" ".join([j[0] for j in text_list[last_i:i + 1]]), length]]
        
        self.wrapped_text = wrapped_text
        self._calc_rect()
        self._calc_scroll_bar()
    
    def _calc_scroll_bar(self):
        self.scroll_bar = TextArea.scrollBar(self.screen, [get_scaled_size(self.scroll_bar_width), self.size[1] ** 2 / (len(self.wrapped_text) * self.font.get_height())], 
                                             self.rect.right, [self.rect.top, self.rect.bottom],
                                             visible=(len(self.wrapped_text) * self.font.get_height() + 2*get_scaled_size(self.padding[1]) > self.size[1]), parent=self, scroll_offset=self.scroll_offset)

    def _calc_rect(self):
        self.rect = pygame.Rect(0, 0, get_scaled_size(self.size[0]), get_scaled_size(self.size[1]))
        self.rect.center = [self.center[0], self.center[1]]
        self._calc_texts()
    
    def _calc_texts(self):
        text_lines : list[Text] = []
        for line in self.wrapped_text:
            line_text = Text(self.screen, line[0], [0, 0], self.text_color, self.font_type, self.font_size)
            text_lines += [line_text]
        self.text_lines = text_lines
        self._calc_text_centers()

    def _calc_text_centers(self):
        line_height = self.font.get_height()
        for i, line in enumerate(self.text_lines):
            text_center = [self.rect.left + get_scaled_size(self.padding[0]) + line.rect.width // 2, self.rect.top + get_scaled_size(self.padding[1]) + (i + 0.5) * line_height - self.scroll_offset]
            line.center = text_center

    def draw(self):
        pygame.draw.rect(self.screen, self.backdrop_color, self.rect)
        pygame.draw.rect(self.screen, "red", self.rect, 1)

        for line in self.text_lines:
            if line.center[1] < self.rect.top + get_scaled_size(self.padding[0]) or line.center[1] > self.rect.bottom - get_scaled_size(self.padding[1]): continue
            line.draw()
        
        self.scroll_bar.draw()

class Button(Widget):
    """
    A class for defining and handling Buttons in pygame
    """
    def __init__(self, screen : pygame.surface, inner_text: str, padding: list[int, int] | int, center: list[int, int], 
                color : str | list[int, int, int] = "black", border_color : str | list[int, int, int] = "white", 
                text_color : str | list[int, int, int] = "white", font_type : str = 'droid-sans-mono.ttf', font_size : int = 18,
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
                 text_color : list[int, int, int] | str = "white", font_type : str = 'droid-sans-mono.ttf', font_size : int = 26, input_text : str = "", 
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
        self.title.draw()
        self._calc_rect()
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