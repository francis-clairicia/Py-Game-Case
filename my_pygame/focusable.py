# -*- coding: Utf-8 -*

from typing import Optional
import pygame
from .theme import ThemedObject
from .colors import BLUE

class Focusable(ThemedObject):

    MODE_MOUSE = "mouse"
    MODE_KEY = "keyboard"
    MODE_JOY = "joystick"
    __mode = MODE_MOUSE
    ON_LEFT = "on_left"
    ON_RIGHT = "on_right"
    ON_TOP = "on_top"
    ON_BOTTOM = "on_bottom"
    __draw_focus_outline = dict()

    def __init_subclass__(cls, draw_focus_outline=True, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        Focusable.__draw_focus_outline[cls] = bool(draw_focus_outline)

    def __init__(self, master, highlight_color=BLUE, highlight_thickness=2):
        self.__focus = False
        self.__side = dict.fromkeys((Focusable.ON_LEFT, Focusable.ON_RIGHT, Focusable.ON_TOP, Focusable.ON_BOTTOM))
        self.__take_focus = True
        self.__from_master = False
        self.__master = master
        self.__highlight_color = pygame.Color(highlight_color)
        self.__highlight_thickness = highlight_thickness
        self.__force_use_highlight_thickness = False

    @staticmethod
    def get_mode() -> str:
        return Focusable.__mode

    @staticmethod
    def set_mode(mode: str) -> None:
        if mode in [Focusable.MODE_MOUSE, Focusable.MODE_KEY, Focusable.MODE_JOY]:
            Focusable.__mode = mode

    @staticmethod
    def actual_mode_is(*mode: str) -> bool:
        return Focusable.get_mode() in mode

    def get_obj_on_side(self, side: Optional[str] = None):
        if side is None:
            return self.__side.copy()
        return self.__side.get(side, None)

    def set_obj_on_side(self, on_top=None, on_bottom=None, on_left=None, on_right=None) -> None:
        for side, obj in ((Focusable.ON_TOP, on_top), (Focusable.ON_BOTTOM, on_bottom), (Focusable.ON_LEFT, on_left), (Focusable.ON_RIGHT, on_right)):
            if side in self.__side and isinstance(obj, Focusable):
                self.__side[side] = obj

    def remove_obj_on_side(self, *sides: str) -> None:
        for side in sides:
            if side in self.__side:
                self.__side[side] = None

    def focus_drawing(self, surface: pygame.Surface) -> None:
        if not self.__draw_focus_outline.get(self.__class__, True) or not self.has_focus():
            return
        if hasattr(self, "rect"):
            if not self.__force_use_highlight_thickness:
                outline = getattr(self, "outline", self.__highlight_thickness)
                if outline <= 0:
                    outline = self.__highlight_thickness
            else:
                outline = self.__highlight_thickness
            if outline > 0:
                getattr(self, "focus_drawing_function", self.__default_focus_drawing_func)(surface, self.__highlight_color, outline)

    def __default_focus_drawing_func(self, surface: pygame.Surface, highlight_color: pygame.Color, highlight_thickness: int) -> None:
        pygame.draw.rect(surface, highlight_color, getattr(self, "rect"), width=highlight_thickness)

    def force_use_highlight_thickness(self, status: bool) -> None:
        self.__force_use_highlight_thickness = bool(status)

    @classmethod
    def draw_focus_outline(cls, status: bool) -> None:
        Focusable.__draw_focus_outline[cls] = bool(status)

    def has_focus(self) -> bool:
        return self.__master.objects.focus_get() is self

    def take_focus(self, status=None) -> bool:
        if status is not None:
            self.__take_focus = bool(status)
        shown = True
        if hasattr(self, "is_shown") and callable(self.is_shown) and not self.is_shown():
            shown = False
        return bool(self.__take_focus and shown)

    def focus_set(self) -> None:
        if not self.has_focus():
            self.__master.set_focus(self)

    def focus_leave(self) -> None:
        if self.has_focus():
            self.__master.set_focus(None)

    def focus_update(self) -> None:
        pass

    def on_focus_set(self) -> None:
        pass

    def on_focus_leave(self) -> None:
        pass