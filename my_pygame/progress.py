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
        self.__scale_rect = RectangleShape(0, height, color=scale_color, outline=0, **kwargs)
        self.__outline_rect = RectangleShape(width, height, color=TRANSPARENT, outline=outline, **kwargs)
        RectangleShape.__init__(self, width, height, color, outline=0, **kwargs)
        if to <= from_:
            raise ValueError("end value 'to' must be greather than 'from'")
        self.__value = self.__percent = 0
        self.__start = self.__end = 0
        self.from_value = from_
        self.to_value = to
        self.percent = 0
        if isinstance(default, (int, float)):
            self.value = float(default)
        self.__label_text = Text()
        self.__label_text_side = str()
        self.__value_text = Text()
        self.__value_text_side = str()
        self.__value_text_round_n = 0
        self.__value_text_type = str()
        self.hide_label()
        self.hide_value()

    def _before_drawing(self, surface: pygame.Surface) -> None:
        RectangleShape._before_drawing(self, surface)
        self.__scale_rect.set_size(self.width * self.percent, self.height, smooth=False)
        self.__outline_rect.set_size(self.size, smooth=False)
        self.__outline_rect.midleft = self.__scale_rect.midleft = self.midleft
        self.__scale_rect.draw(surface)

    def _after_drawing(self, surface: pygame.Surface) -> None:
        self.__outline_rect.draw(surface)
        offset = 10
        if self.__value_text.is_shown() and self.__value_text_type in ["value", "percent"]:
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
                if self.__value_text_type == "value":
                    self.__value_text.message = round(self.value, round_n) if round_n > 0 else round(self.value)
                elif self.__value_text_type == "percent":
                    value = self.percent * 100
                    self.__value_text.message = str(round(value, round_n) if round_n > 0 else round(value)) + "%"
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

    def show_value(self, side: str, round_n=0, **kwargs) -> None:
        self.__value_text.config(**kwargs)
        self.__value_text_side = side
        self.__value_text_round_n = int(round_n)
        self.__value_text_type = "value"
        self.__value_text.show()

    def hide_value(self) -> None:
        self.__value_text.hide()
        self.__value_text_side = str()
        self.__value_text_round_n = 0
        self.__value_text_type = str()

    def show_percent(self, side: str, round_n=0, **kwargs) -> None:
        self.show_value(side, round_n, **kwargs)
        self.__value_text_type = "percent"

    def hide_percent(self) -> None:
        self.hide_value()

    def config_value_text(self, **kwargs) -> None:
        kwargs.pop("message", None)
        self.__value_text.config(**kwargs)

    def show_label(self, label: str, side: str, **kwargs) -> None:
        self.__label_text.config(message=label, **kwargs)
        self.__label_text_side = side
        self.__label_text.show()

    def hide_label(self) -> None:
        self.__label_text.hide()
        self.__label_text_side = str()

    def config_label_text(self, message=None, **kwargs) -> None:
        if message is not None:
            kwargs["message"] = message
        self.__label_text.config(**kwargs)

    @property
    def outline_color(self) -> pygame.Color:
        return self.__outline_rect.outline_color

    @outline_color.setter
    def outline_color(self, value: pygame.Color) -> None:
        self.__outline_rect.outline_color = value

    @property
    def scale_color(self) -> pygame.Color:
        return self.__scale_rect.color

    @scale_color.setter
    def scale_color(self, value: pygame.Color) -> None:
        self.__scale_rect.color = value

    @property
    def percent(self) -> float:
        return self.__percent

    @percent.setter
    def percent(self, value: float) -> None:
        value = float(value)
        if value > 1:
            value = 1
        elif value < 0:
            value = 0
        self.__percent = value
        self.__value = self.__start + (self.__percent * self.__end)

    @property
    def value(self) -> float:
        return self.__value

    @value.setter
    def value(self, value: float) -> None:
        value = float(value)
        if value > self.__end:
            value = self.__end
        elif value < self.__start:
            value = self.__start
        self.__value = value
        self.__percent = (self.__value - self.__start) / (self.__end - self.__start) if self.__end > self.__start else 0

    @property
    def from_value(self) -> float:
        return self.__start

    @from_value.setter
    def from_value(self, value: float) -> None:
        self.__start = float(value)
        self.percent = self.percent

    @property
    def to_value(self) -> float:
        return self.__end

    @to_value.setter
    def to_value(self, value: float) -> None:
        self.__end = float(value)
        self.percent = self.percent
