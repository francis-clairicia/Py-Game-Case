# -*- coding: Utf-8 -*

import pygame
from .text import Text
from .shape import RectangleShape, PolygonShape
from .clickable import Clickable
from .window import Window
from .clock import Clock
from .colors import WHITE, BLACK, GRAY

class Entry(Clickable, RectangleShape):
    def __init__(self, master: Window, width=10, font=None,
                 shadow=False, shadow_x=0, shadow_y=0, shadow_color=BLACK,
                 bg=WHITE, fg=BLACK, interval=500,
                 state="normal", highlight_color=GRAY, highlight_thickness=2,
                 hover_sound=None, on_click_sound=None, disabled_sound=None, theme=None, **kwargs):
        self.__text = Text(
            font=font, color=fg, shadow=shadow, shadow_x=shadow_x, shadow_y=shadow_y, shadow_color=shadow_color,
            img=None, compound="left", wrap=0, justify="left"
        )
        if width <= 0:
            width = 1
        self.__nb_chars = width
        width, height = self.__text.font.size("|" + "0" * (width))
        self.__cursor_height = height
        RectangleShape.__init__(self, width + 15, height + 10, bg, **kwargs)
        Clickable.__init__(
            self, master, callback=self.start_edit, state=state, highlight_color=highlight_color, highlight_thickness=highlight_thickness,
            hover_sound=hover_sound, on_click_sound=on_click_sound, disabled_sound=disabled_sound
        )
        self.__cursor_line = PolygonShape(fg, outline=2, points=[(0, 0), (0, height)])
        self.__cursor = 0
        self.__show_cursor = False
        self.__cursor_animated = False
        self.__cursor_animation_clock = Clock()
        self.__cursor_animation_interval = 0
        self.interval = interval
        self.master.bind_multiple_event([pygame.KEYDOWN, pygame.TEXTINPUT, pygame.TEXTEDITING], self.key_press)
        if self.__edit():
            self.start_edit()

    def __edit(self) -> bool:
        return self.master.text_input_enabled() and self.has_focus()

    def after_drawing(self, surface: pygame.Surface) -> None:
        RectangleShape.after_drawing(self, surface)
        self.__text.move(left=self.left + 10, centery=self.centery)
        self.__text.draw(surface)
        if self.__edit() and self.__cursor_animated:
            if self.__cursor_animation_clock.elapsed_time(self.__cursor_animation_interval):
                self.__show_cursor = not self.__show_cursor
        else:
            self.__show_cursor = False
        if self.__show_cursor:
            width = self.__text.font.size(self.__text.message[:self.cursor])[0] + 1
            self.__cursor_line.outline_color = self.__text.color
            self.__cursor_line.move(left=self.__text.left + width, centery=self.centery)
            self.__cursor_line.draw(surface)

    @property
    def cursor(self) -> int:
        return self.__cursor

    @cursor.setter
    def cursor(self, value: int):
        self.__cursor = int(value)
        if self.__cursor < 0:
            self.__cursor = 0
        elif self.__cursor > len(self.get()):
            self.__cursor = len(self.get())

    @property
    def interval(self) -> int:
        return self.__cursor_animation_interval

    @interval.setter
    def interval(self, value: int) -> None:
        self.__cursor_animation_interval = max(int(value), 0)

    def get(self) -> str:
        return self.__text.message

    def start_edit(self) -> None:
        self.master.enable_text_input(self.rect)
        self.__cursor_animated = True

    def on_focus_leave(self) -> None:
        self.stop_edit()

    def stop_edit(self) -> None:
        self.master.disable_text_input()
        self.__cursor_animated = False

    def move(self, **kwargs) -> None:
        RectangleShape.move(self, **kwargs)
        try:
            if self.__edit():
                pygame.key.set_text_input_rect(self.rect)
        except AttributeError:
            pass

    def key_press(self, event: pygame.event.Event) -> None:
        if self.__edit():
            self.__show_cursor = True
            self.__cursor_animation_clock.restart()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_BACKSPACE:
                    self.__text.message = self.__text.message[:self.cursor - 1] + self.__text.message[self.cursor:]
                    self.cursor -= 1
                elif event.key == pygame.K_DELETE:
                    self.__text.message = self.__text.message[:self.cursor] + self.__text.message[self.cursor + 1:]
                elif event.key == pygame.K_LEFT:
                    self.cursor -= 1
                elif event.key == pygame.K_RIGHT:
                    self.cursor += 1
                elif event.key == pygame.K_HOME:
                    self.cursor = 0
                elif event.key == pygame.K_END:
                    self.cursor = len(self.__text.message)
            elif event.type == pygame.TEXTEDITING:
                if event.length <= self.__nb_chars:
                    self.__text.message = event.text
                    self.cursor = event.start
            elif event.type == pygame.TEXTINPUT:
                new_text = self.__text.message[:self.cursor] + event.text + self.__text.message[self.cursor:]
                if len(new_text) <= self.__nb_chars:
                    self.__text.message = new_text
                    self.cursor += len(event.text)