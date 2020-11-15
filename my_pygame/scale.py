# -*- coding: Utf-8 -*

from typing import Tuple
import pygame
from .progress import ProgressBar
from .clickable import Clickable
from .window import Window
from .colors import BLUE

class Scale(Clickable, ProgressBar):
    def __init__(self, master: Window, callback=None, state="normal",
                 highlight_color=BLUE, highlight_thickness=2, hover_sound=None, on_click_sound=None, disabled_sound=None, **kwargs):
        ProgressBar.__init__(self, **kwargs)
        Clickable.__init__(
            self, master, self.call_update, state=state, highlight_color=highlight_color, highlight_thickness=highlight_thickness,
            hover_sound=hover_sound, on_click_sound=on_click_sound, disabled_sound=disabled_sound
        )
        self.__callback = callback
        self.master.bind_joystick(0, "AXIS_LEFT_X", self.axis_event, state=True)
        self.master.bind_key(pygame.K_KP_MINUS, self.key_event, hold=True)
        self.master.bind_key(pygame.K_KP_PLUS, self.key_event, hold=True)

    def on_mouse_motion(self, mouse_pos: Tuple[int, int]) -> None:
        if self.active:
            self.percent = (mouse_pos[0] - self.x) / self.width
            self.call_update()

    def axis_event(self, value: float) -> None:
        if self.has_focus():
            self.percent += (0.01 * value)
            self.call_update()

    def key_event(self, key_value: int, key_state: bool) -> None:
        if self.has_focus():
            offset = 0
            if key_value == pygame.K_KP_MINUS:
                offset = -1
            elif key_value == pygame.K_KP_PLUS:
                offset = 1
            self.percent += offset * key_state * 0.005
            self.call_update()

    def on_click_down(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.on_mouse_motion(event.pos)

    def call_update(self) -> None:
        if callable(self.__callback):
            self.__callback(self.value, self.percent)