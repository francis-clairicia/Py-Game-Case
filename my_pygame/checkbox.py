# -*- coding: Utf-8 -*

from typing import Optional, Any, Callable
import pygame
from .shape import RectangleShape
from .image import Image
from .clickable import Clickable
from .window import Window
from .colors import BLUE

class CheckBox(Clickable, RectangleShape, use_parent_theme=False):
    def __init__(self, master: Window, width: int, height: int, color: pygame.Color, *, value=None, on_value=True, off_value=False,
                 outline=2, img: Optional[Image] = None, callback: Optional[Callable[..., Any]] = None,
                 highlight_color=BLUE, highlight_thickness=2, state="normal", cursor=None, disabled_cursor=None,
                 hover_sound=None, on_click_sound=None, disabled_sound=None, theme=None, **kwargs):
        # pylint: disable=unused-argument
        RectangleShape.__init__(self, width, height, color=color, outline=outline, **kwargs)
        Clickable.__init__(
            self, master, self.change_value, state, highlight_color=highlight_color, highlight_thickness=highlight_thickness,
            hover_sound=hover_sound, on_click_sound=on_click_sound, disabled_sound=disabled_sound, cursor=cursor, disabled_cursor=disabled_cursor
        )
        self.__on_changed_value = callback
        self.__active_img = img
        self.__on_value = on_value
        self.__off_value = off_value
        if on_value == off_value:
            raise ValueError("'On' value and 'Off' value are identical")
        self.value = value

    @property
    def value(self) -> Any:
        return self.__value

    @value.setter
    def value(self, value: Any):
        if value is None:
            value = self.__off_value
        elif value not in [self.__on_value, self.__off_value]:
            return
        self.__value = value
        if callable(self.__on_changed_value):
            self.__on_changed_value(self.__value)

    def after_drawing(self, surface: pygame.Surface) -> None:
        RectangleShape.after_drawing(self, surface)
        if self.value == self.__on_value:
            if isinstance(self.__active_img, Image):
                self.__active_img.center = self.center
                self.__active_img.draw(surface)
            else:
                x, y = self.center
                w, h = self.size
                pygame.draw.line(
                    surface, self.outline_color,
                    (x - (0.7*w)//2, y + (0.7*h)//2),
                    (x + (0.7*w)//2, y - (0.7*h)//2),
                    width=2
                )
                pygame.draw.line(
                    surface, self.outline_color,
                    (x - (0.7*w)//2, y - (0.7*h)//2),
                    (x + (0.7*w)//2, y + (0.7*h)//2),
                    width=2
                )

    def change_value(self) -> None:
        self.value = self.__on_value if self.value == self.__off_value else self.__off_value
