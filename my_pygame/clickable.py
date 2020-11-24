# -*- coding: Utf-8 -*

from typing import Tuple, Optional, Union, Any, Callable, Dict
import pygame
from pygame.event import Event
from .focusable import Focusable
from .window import Window
from .cursor import Cursor

class Clickable(Focusable):

    NORMAL = "normal"
    DISABLED = "disabled"

    def __init__(self, master: Window, callback: Optional[Callable[..., Any]] = None,
                 state="normal", hover_sound=None, on_click_sound=None, disabled_sound=None,
                 cursor=None, disabled_cursor=None, **kwargs):
        Focusable.__init__(self, master, **kwargs)
        self.__master = master
        self.__callback = None
        self.__hover = False
        self.__active = False
        self.__hover_sound = hover_sound
        self.__on_click_sound = on_click_sound
        self.__disabled_sound = disabled_sound
        self.__enable_mouse = True
        self.__enable_key = True
        self.__state = Clickable.NORMAL
        self.hover_cursor = cursor
        self.disabled_cursor = disabled_cursor
        self.callback = callback
        self.state = state
        master.bind_multiple_event((pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.JOYBUTTONDOWN), self.event_click_down)
        master.bind_multiple_event((pygame.KEYUP, pygame.MOUSEBUTTONUP, pygame.JOYBUTTONUP), self.event_click_up)
        master.bind_mouse(self.handle_mouse_position)

    @property
    def master(self) -> Window:
        return self.__master

    @property
    def callback(self) -> Callable[..., Any]:
        return self.__callback

    @callback.setter
    def callback(self, callback: Callable[..., Any]) -> None:
        if callable(callback):
            self.__callback = callback
        else:
            self.__callback = None

    @property
    def state(self) -> str:
        return self.__state

    @state.setter
    def state(self, value: str) -> None:
        if value not in (Clickable.NORMAL, Clickable.DISABLED):
            return
        self.__state = value
        if self.active:
            self.on_active_set()
        elif self.hover:
            self.on_hover()
        else:
            self.on_leave()
        self.on_change_state()

    @property
    def hover_sound(self) -> pygame.mixer.Sound:
        return self.__hover_sound

    @property
    def on_click_sound(self) -> pygame.mixer.Sound:
        return self.__on_click_sound

    @property
    def disabled_sound(self) -> pygame.mixer.Sound:
        return self.__disabled_sound

    @property
    def active(self) -> bool:
        return self.__active

    @active.setter
    def active(self, status: bool) -> None:
        status = bool(status)
        active = self.__active
        self.__active = status
        if status is True:
            if not active:
                self.focus_set()
                self.on_active_set()
        else:
            if active:
                self.on_active_unset()

    @property
    def hover(self) -> bool:
        return self.__hover

    @hover.setter
    def hover(self, status: bool) -> None:
        status = bool(status)
        hover = self.__hover
        self.__hover = status
        if status is True:
            if not hover:
                self.play_hover_sound()
                self.on_hover()
                if self.active:
                    self.on_active_set()
        else:
            if hover:
                self.on_leave()

    @property
    def hover_cursor(self) -> Cursor:
        return self.__hover_cursor

    @hover_cursor.setter
    def hover_cursor(self, cursor: Cursor):
        if isinstance(cursor, Cursor):
            self.__hover_cursor = cursor
        else:
            self.__hover_cursor = Cursor(pygame.SYSTEM_CURSOR_HAND)

    @property
    def disabled_cursor(self) -> Cursor:
        return self.__disabled_cursor

    @disabled_cursor.setter
    def disabled_cursor(self, cursor: Cursor):
        if isinstance(cursor, Cursor):
            self.__disabled_cursor = cursor
        else:
            self.__disabled_cursor = Cursor(pygame.SYSTEM_CURSOR_NO)

    def play_hover_sound(self) -> None:
        if isinstance(self.hover_sound, pygame.mixer.Sound):
            self.hover_sound.play()

    def play_on_click_sound(self) -> None:
        if self.state == Clickable.NORMAL and isinstance(self.on_click_sound, pygame.mixer.Sound):
            self.on_click_sound.play()
        elif self.state == Clickable.DISABLED and isinstance(self.disabled_sound, pygame.mixer.Sound):
            self.disabled_sound.play()

    def valid_click(self, event: Event, down: bool) -> bool:
        mouse_event = pygame.MOUSEBUTTONDOWN if down else pygame.MOUSEBUTTONUP
        key_event = pygame.KEYDOWN if down else pygame.KEYUP
        joy_event = pygame.JOYBUTTONDOWN if down else pygame.JOYBUTTONUP
        if Focusable.actual_mode_is(Focusable.MODE_MOUSE) and self.__enable_mouse and hasattr(self, "rect"):
            if event.type == mouse_event and event.button == 1 and getattr(self, "rect").collidepoint(event.pos):
                return True
        elif Focusable.actual_mode_is(Focusable.MODE_KEY, Focusable.MODE_JOY) and self.__enable_key and self.take_focus() and self.has_focus():
            if event.type == key_event and event.key == pygame.K_RETURN:
                return True
            if event.type == joy_event and event.button == 0:
                return True
        return False

    def event_click_up(self, event: Event) -> None:
        if hasattr(self, "is_shown") and getattr(self, "is_shown")() is False:
            return
        if not self.active:
            return
        self.active = False
        self.on_click_up(event)
        if self.valid_click(event, down=False):
            self.play_on_click_sound()
            self.on_hover()
            if self.__callback and self.state != Clickable.DISABLED:
                self.__callback()

    def event_click_down(self, event: Event) -> None:
        if hasattr(self, "is_shown") and getattr(self, "is_shown")() is False:
            return
        if self.valid_click(event, down=True):
            self.active = True
            self.on_click_down(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self.focus_leave()

    def handle_mouse_position(self, mouse_pos: Tuple[int, int]) -> None:
        if not self.__enable_mouse or (hasattr(self, "is_shown") and getattr(self, "is_shown")() is False):
            return
        if Focusable.actual_mode_is(Focusable.MODE_MOUSE):
            if hasattr(self, "rect"):
                self.hover = getattr(self, "rect").collidepoint(mouse_pos)
                self.on_mouse_motion(mouse_pos)
            else:
                self.hover = False
        if self.hover:
            self.master.set_temporary_window_cursor(self.hover_cursor if self.state == Clickable.NORMAL else self.disabled_cursor)

    def set_enabled_mouse(self, status: bool) -> None:
        self.__enable_mouse = bool(status)

    def enable_mouse(self) -> None:
        self.set_enabled_mouse(True)

    def disable_mouse(self) -> None:
        self.set_enabled_mouse(False)

    def set_enabled_key_joy(self, status: bool) -> None:
        self.__enable_key = bool(status)

    def enable_key_joy(self) -> None:
        self.set_enabled_key_joy(True)

    def disable_key_joy(self) -> None:
        self.set_enabled_key_joy(False)

    def focus_update(self) -> None:
        if not Focusable.actual_mode_is(Focusable.MODE_MOUSE) and self.take_focus():
            self.hover = self.has_focus()

    def on_change_state(self) -> None:
        pass

    def on_click_down(self, event: Event) -> None:
        pass

    def on_click_up(self, event: Event) -> None:
        pass

    def on_mouse_motion(self, mouse_pos: Tuple[int, int]) -> None:
        pass

    def on_hover(self) -> None:
        pass

    def on_leave(self) -> None:
        pass

    def on_active_set(self) -> None:
        pass

    def on_active_unset(self) -> None:
        pass