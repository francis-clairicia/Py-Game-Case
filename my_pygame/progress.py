# -*- coding: Utf-8 -*

import pygame
from .text import Text
from .shape import RectangleShape
from .colors import TRANSPARENT

class ProgressBar(RectangleShape):

    S_TOP = "top"
    S_BOTTOM = "bottom"
    S_LEFT = "left"
    S_RIGHT = "right"
    S_INSIDE = "inside"

    def __init__(self, width: int, height: int, color: pygame.Color, scale_color: pygame.Color, *, outline=2, from_=0, to=1, default=None, **kwargs):
        RectangleShape.__init__(self, width, height, color=TRANSPARENT, outline=outline, **kwargs)
        if to <= from_:
            raise ValueError("end value 'to' must be greather than 'from'")
        self.start = from_
        self.end = to
        self.percent = 0
        self.__scale_rect = RectangleShape(0, height, color=scale_color, **kwargs)
        self.__bg_rect = RectangleShape(width, height, color=color, **kwargs)
        if isinstance(default, (int, float)):
            self.value = default
        self.__label_text = Text()
        self.__label_text_side = str()
        self.__value_text = Text()
        self.__value_text_side = str()
        self.__value_text_round_n = 0
        self.hide_label()
        self.hide_value()

    def before_drawing(self, surface: pygame.Surface) -> None:
        RectangleShape.before_drawing(self, surface)
        self.__scale_rect.set_size(self.width * self.percent, self.height, smooth=False)
        self.__bg_rect.set_size(self.size, smooth=False)
        self.__bg_rect.move(x=self.x, centery=self.centery)
        self.__scale_rect.move(x=self.x, centery=self.centery)
        self.__bg_rect.draw(surface)
        self.__scale_rect.draw(surface)

    def after_drawing(self, surface: pygame.Surface) -> None:
        RectangleShape.after_drawing(self, surface)
        offset = 10
        if self.__value_text.is_shown():
            movements = {
                ProgressBar.S_TOP:    {"bottom": self.top - offset, "centerx": self.centerx},
                ProgressBar.S_BOTTOM: {"top": self.bottom + offset, "centerx": self.centerx},
                ProgressBar.S_LEFT:   {"right": self.left - offset, "centery": self.centery},
                ProgressBar.S_RIGHT:  {"left": self.right + offset, "centery": self.centery},
                ProgressBar.S_INSIDE: {"center": self.center}
            }
            side = self.__value_text_side
            round_n = self.__value_text_round_n
            if side in movements:
                self.__value_text.message = round(self.value, round_n) if round_n > 0 else round(self.value)
                self.__value_text.move(**movements[side])
                self.__value_text.draw(surface)
        if self.__label_text.is_shown():
            movements = {
                ProgressBar.S_TOP:    {"bottom": self.top - offset, "centerx": self.centerx},
                ProgressBar.S_BOTTOM: {"top": self.bottom + offset, "centerx": self.centerx},
                ProgressBar.S_LEFT:   {"right": self.left - offset, "centery": self.centery},
                ProgressBar.S_RIGHT:  {"left": self.right + offset, "centery": self.centery},
            }
            side = self.__label_text_side
            if side in movements:
                self.__label_text.move(**movements[side])
                self.__label_text.draw(surface)

    def show_value(self, side: str, round_n=0, **kwargs):
        self.__value_text.config(**kwargs)
        self.__value_text_side = side
        self.__value_text_round_n = int(round_n)
        self.__value_text.show()

    def hide_value(self):
        self.__value_text.hide()
        self.__value_text_side = str()
        self.__value_text_round_n = 0

    def show_label(self, label: str, side: str, **kwargs):
        self.__label_text.config(message=label, **kwargs)
        self.__label_text_side = side
        self.__label_text.show()

    def hide_label(self):
        self.__label_text.hide()
        self.__label_text_side = str()

    @property
    def color(self) -> pygame.Color:
        return TRANSPARENT

    @color.setter
    def color(self, value: pygame.Color) -> None:
        pass

    @property
    def bg_color(self) -> pygame.Color:
        return self.__bg_rect.color

    @bg_color.setter
    def bg_color(self, value: pygame.Color) -> None:
        self.__bg_rect.color = value

    @property
    def scale_color(self) -> pygame.Color:
        return self.__scale_rect.color

    @scale_color.setter
    def scale_color(self, value: pygame.Color) -> None:
        self.__scale_rect.color = value

    @property
    def percent(self) -> float:
        return float(self.__percent)

    @percent.setter
    def percent(self, value: float) -> None:
        if value > 1:
            value = 1
        elif value < 0:
            value = 0
        self.__percent = value
        self.__value = self.__start + (self.__percent * self.__end)

    @property
    def value(self) -> float:
        return float(self.__value)

    @value.setter
    def value(self, value: float) -> None:
        if value > self.__end:
            value = self.__end
        elif value < self.__start:
            value = self.__start
        self.__value = value
        self.__percent = (self.__value - self.__start) / (self.__end - self.__start)

    @property
    def start(self) -> float:
        return self.__start

    @start.setter
    def start(self, value: float) -> None:
        self.__start = float(value)

    @property
    def end(self) -> float:
        return self.__end

    @end.setter
    def end(self, value: float) -> None:
        self.__end = float(value)