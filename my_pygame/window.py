# -*- coding: Utf-8 -*

import os
import sys
import configparser
from typing import Callable, Any, Union, Optional, Sequence
import pygame
from .drawable import Drawable
from .focusable import Focusable
from .text import Text
from .shape import RectangleShape
from .progress import ProgressBar
from .list import DrawableList, AbstractDrawableListAligned
from .grid import Grid, GridCell
from .joystick import Joystick, JoystickList
from .keyboard import Keyboard
from .cursor import Cursor
from .clock import Clock
from .colors import BLACK, WHITE, BLUE, TRANSPARENT
from .resources import Resources
from .multiplayer import ServerSocket, ClientSocket
from .path import set_constant_file

def set_value_in_range(value: float, min_value: float, max_value: float) -> float:
    if value < min_value:
        value = min_value
    elif value > max_value:
        value = max_value
    return value

class WindowCallback(object):
    def __init__(self, master, wait_time: float, callback: Callable[..., Any], args: tuple[Any, ...], kwargs: dict[str, Any]):
        self.__master = master
        self.__wait_time = wait_time
        self.__callback = callback
        self.__args = args
        self.__kwargs = kwargs
        self.__clock = Clock()
        self.__clock.restart()

    def __call__(self):
        if self.__clock.elapsed_time(self.__wait_time, restart=False):
            self.__callback(*self.__args, **self.__kwargs)
            self.kill()

    def kill(self) -> None:
        self.__master.remove_window_callback(self)

class WindowCallbackList(list):

    def process(self) -> None:
        if not self:
            return
        callback_list = self.copy()
        for callback in callback_list:
            callback()

class WindowDrawableList(DrawableList):

    def __init__(self):
        super().__init__()
        self.__index = -1

    def remove(self, *obj_list: Drawable) -> None:
        super().remove(*(obj_list))
        self.__update_index()

    def remove_from_index(self, index: int) -> None:
        super().remove_from_index(index)
        self.__update_index()

    def clear(self) -> None:
        super().clear()
        self.__index = -1

    def __update_index(self) -> None:
        self.__index = min(self.__index, len(self.__get_all_focusable()) - 1)

    def focus_get(self) -> Focusable:
        if self.__index < 0:
            return None
        return self.__get_all_focusable()[self.__index]

    def focus_next(self) -> None:
        focusable_list = self.__get_all_focusable()
        if any(obj.take_focus() for obj in focusable_list):
            size = len(focusable_list)
            while True:
                self.__index = (self.__index + 1) % size
                obj = self.focus_get()
                if obj.take_focus() and not isinstance(obj, GridCell):
                    break
            self.set_focus(obj)
        else:
            self.set_focus(None)

    def focus_obj_on_side(self, side: str) -> None:
        actual_obj = self.focus_get()
        if actual_obj is None:
            self.focus_next()
        else:
            obj = actual_obj.get_obj_on_side(side)
            while obj and not obj.take_focus():
                obj = obj.get_obj_on_side(side)
            if obj:
                self.set_focus(obj)

    def set_focus(self, obj: Focusable) -> None:
        focusable_list = self.__get_all_focusable()
        if obj is not None and obj not in focusable_list:
            return
        for obj_f in focusable_list:
            obj_f.on_focus_leave()
        if isinstance(obj, Focusable):
            self.__index = focusable_list.index(obj)
            obj.on_focus_set()
        else:
            self.__index = -1

    def focus_mode_update(self) -> None:
        if not Focusable.actual_mode_is(Focusable.MODE_MOUSE) and self.focus_get() is None:
            self.focus_next()

    @property
    def index(self) -> int:
        return self.__index

    def __get_all_focusable(self) -> Sequence[Focusable]:
        obj_list = list()
        for obj in self:
            if isinstance(obj, Focusable):
                obj_list.append(obj)
            if isinstance(obj, (DrawableList, Grid)):
                if isinstance(obj, Grid):
                    obj_list.extend(obj.cells)
                obj_list.extend(obj.find_objects(Focusable))
        return obj_list

class WindowDrawable(Drawable):
    pass

class Window(object):

    MIXER_FREQUENCY = 44100
    MIXER_SIZE = -16
    MIXER_CHANNELS = 2
    MIXER_BUFFER = 512

    __main_window = None
    __resources = Resources()
    __size = (0, 0)
    __min_size = (0, 0)
    __flags = 0
    __default_key_repeat = (0, 0)
    __text_input_enabled = False
    __all_opened = list()
    __config_file = set_constant_file("window.ini", raise_error=False)
    __sound_volume = 50
    __music_volume = 50
    __enable_music = True
    __enable_sound = True
    __actual_music = None
    __show_fps = False
    __fps = 60
    __fps_obj = None
    __joystick = JoystickList()
    __keyboard = Keyboard()
    __default_cursor = Cursor(pygame.SYSTEM_CURSOR_ARROW)
    __cursor = __default_cursor
    __all_window_event_handler_dict = dict()
    __all_window_key_handler_dict = dict()
    __all_window_key_state_dict = dict()
    __all_window_joystick_handler_dict = dict()
    __all_window_joystick_state_dict = dict()
    __all_window_mouse_handler_list = list()
    __all_window_key_enabled = True
    __server_socket = ServerSocket()
    __client_socket = ClientSocket()

    def __init__(self, master=None, bg_color=BLACK, bg_music=None):
        if not isinstance(Window.__main_window, Window):
            Window.__main_window = self
        self.__master = master
        self.__main_clock = pygame.time.Clock()
        self.__loop = False
        self.__show_fps_in_this_window = True
        self.__objects = WindowDrawableList()
        self.__event_handler_dict = dict()
        self.__key_handler_dict = dict()
        self.__key_state_dict = dict()
        self.__joystick_handler_dict = dict()
        self.__joystick_state_dict = dict()
        self.__mouse_handler_list = list()
        self.__callback_after = WindowCallbackList()
        self.rect_to_update = None
        self.bg_color = bg_color
        self.bg_music = bg_music
        focus_event = (
            pygame.KEYDOWN,
            pygame.MOUSEBUTTONDOWN,
            pygame.MOUSEBUTTONUP,
            pygame.MOUSEMOTION,
            pygame.MOUSEWHEEL,
            pygame.JOYHATMOTION
        )
        self.bind_multiple_event(focus_event, self.__handle_focus)
        self.bind_event(pygame.KEYDOWN, self.__key_handler)
        self.bind_multiple_event([pygame.JOYBUTTONDOWN, pygame.JOYAXISMOTION, pygame.JOYHATMOTION], self.__joystick_handler)
        self.bind_event(pygame.WINDOWEVENT, self.__resize_event)
        self.__key_enabled = True
        self.__screenshot = None
        self.__screenshot_window_callback = None
        self.bind_key(pygame.K_F11, lambda event: self.screenshot())
        if not Window.__fps_obj:
            Window.__fps_obj = Text(color=BLUE)

    @staticmethod
    def __init_pygame(size: tuple[int, int], flags: int, nb_joystick: int, resources: Optional[Resources], config: Optional[str]) -> None:
        if not pygame.get_init():
            pygame.mixer.pre_init(Window.MIXER_FREQUENCY, Window.MIXER_SIZE, Window.MIXER_CHANNELS, Window.MIXER_BUFFER)
            status = pygame.init()
            if status[1] > 0:
                sys.exit("Error on pygame initialization ({} modules failed to load)".format(status[1]))
            if isinstance(config, str):
                head, tail = os.path.split(config)
                if tail:
                    Window.__config_file = config
                    if head and not os.path.isdir(head):
                        os.makedirs(head)
            Window.load_config()
            Window.__joystick.set(nb_joystick)
            Window.__default_event_binding()
            if not isinstance(size, (list, tuple)) or len(size) != 2 or size[0] <= 0 or size[1] <= 0:
                size = (0, 0)
            surface = pygame.display.set_mode(size, flags)
            pygame.event.clear()
            Window.__min_size = Window.__size = surface.get_size()
            Window.__flags = flags
            if isinstance(resources, Resources):
                Window.__resources = resources
            Window.__resources.load()
            Window.__resources.set_sfx_volume(Window.__sound_volume, Window.__enable_sound)

    @staticmethod
    def __default_event_binding() -> None:
        Window.bind_multiple_event_all_window((pygame.JOYDEVICEADDED, pygame.CONTROLLERDEVICEADDED), Window.__joystick.event_connect)
        Window.bind_multiple_event_all_window((pygame.JOYDEVICEREMOVED, pygame.CONTROLLERDEVICEREMOVED), Window.__joystick.event_disconnect)

    @property
    def main_window(self) -> bool:
        return Window.__main_window is self

    @property
    def joystick(self) -> JoystickList:
        return Window.__joystick

    @property
    def keyboard(self) -> Keyboard:
        return Window.__keyboard

    @property
    def objects(self) -> WindowDrawableList:
        return self.__objects

    def __setattr__(self, name, obj) -> None:
        if name != "_Window__objects" and hasattr(self, "_Window__objects"):
            if hasattr(self, name) and isinstance(getattr(self, name), (Drawable, DrawableList)):
                self.objects.remove(getattr(self, name))
            if isinstance(obj, (Drawable, DrawableList)) and not isinstance(obj, (WindowDrawable, WindowDrawableList)):
                self.objects.add(obj)
        return object.__setattr__(self, name, obj)

    def __delattr__(self, name) -> None:
        if isinstance(obj, (Drawable, DrawableList)) and name != "_Window__objects":
            self.objects.remove(obj)
        return object.__delattr__(self, name)

    def __contains__(self, obj) -> bool:
        return bool(obj in self.objects)

    def enable_key_joy_focus(self) -> None:
        self.__key_enabled = True

    def disable_key_joy_focus(self) -> None:
        self.__key_enabled = False

    @staticmethod
    def enable_key_joy_focus_for_all_window() -> None:
        Window.__all_window_key_enabled = True

    @staticmethod
    def disable_key_joy_focus_for_all_window() -> None:
        Window.__all_window_key_enabled = False

    @staticmethod
    def set_icon(icon: pygame.Surface) -> None:
        pygame.display.set_icon(pygame.transform.smoothscale(icon, (32, 32)))

    @staticmethod
    def set_title(title: str) -> None:
        pygame.display.set_caption(title)

    @staticmethod
    def iconify() -> bool:
        return pygame.display.iconify()

    @property
    def bg_music(self) -> Union[str, None]:
        return self.__bg_music

    @bg_music.setter
    def bg_music(self, music) -> None:
        if music is None or os.path.isfile(music):
            self.__bg_music = music

    @property
    def bg_color(self) -> pygame.Color:
        return self.__bg_color

    @bg_color.setter
    def bg_color(self, color: pygame.Color) -> None:
        self.__bg_color = pygame.Color(color) if color is not None else BLACK

    @property
    def loop(self) -> bool:
        return self.__loop

    def mainloop(self) -> int:
        self.__loop = True
        Window.__all_opened.append(self)
        Window.__default_cursor.set()
        self.place_objects()
        self.set_grid()
        self.__fps_update()
        self.on_start_loop()
        while self.__loop:
            self.__main_clock.tick(Window.__fps)
            self.__handle_bg_music()
            self.__handle_cursor()
            self.__callback_after.process()
            if Focusable.actual_mode_is(Focusable.MODE_KEY, Focusable.MODE_JOY) and Window.__all_window_key_enabled and self.__key_enabled:
                self.objects.focus_mode_update()
            self.keyboard.update()
            self.update()
            self.draw_and_refresh()
            self.event_handler()
        self.__callback_after.clear()
        return 0

    def stop(self, force=False, sound=None) -> None:
        if not self.__loop:
            return
        self.__loop = False
        if sound:
            self.play_sound(sound)
        self.on_quit()
        self.set_focus(None)
        Window.__all_opened.remove(self)
        if force and not self.main_window and isinstance(Window.__main_window, Window):
            Window.__main_window.stop()
        elif self.main_window:
            for window in list(Window.__all_opened):
                window.stop()
        if not Window.__all_opened and pygame.get_init():
            Window.stop_connection()
            Window.save_config()
            pygame.quit()

    def close(self) -> None:
        self.stop(force=True)

    def on_quit(self) -> None:
        pass

    def on_start_loop(self) -> None:
        pass

    def update(self) -> None:
        pass

    def place_objects(self) -> None:
        pass

    def set_grid(self) -> None:
        pass

    def draw_screen(self, show_fps=True) -> None:
        if isinstance(self.__master, Window):
            self.__master.draw_screen(show_fps=False)
        else:
            self.surface.fill(self.bg_color)
        self.objects.draw(self.surface)
        if Window.__show_fps is True and show_fps and self.__show_fps_in_this_window:
            Window.__fps_obj.draw(self.surface)
        if isinstance(self.__screenshot, Drawable):
            self.__screenshot.draw(self.surface)
            pygame.draw.rect(self.surface, WHITE, self.__screenshot.rect, width=3)

    def refresh(self, rect=None) -> None:
        pygame.display.update(rect or self.rect_to_update or self.rect)

    def draw_and_refresh(self, show_fps=True, rect=None, pump=False) -> None:
        self.draw_screen(show_fps=show_fps)
        self.refresh(rect=rect)
        if pump:
            pygame.event.pump()

    @staticmethod
    def set_fps(framerate: int) -> None:
        Window.__fps = int(framerate)

    @staticmethod
    def get_fps() -> int:
        return Window.__fps

    @staticmethod
    def show_fps(status: bool) -> None:
        Window.__show_fps = bool(status)

    @staticmethod
    def config_fps_obj(**kwargs) -> None:
        Window.__fps_obj.config(**kwargs)

    @staticmethod
    def move_fps_object(**kwargs) -> None:
        Window.__fps_obj.move(**kwargs)

    @staticmethod
    def fps_is_shown() -> bool:
        return Window.__show_fps

    def __fps_update(self) -> None:
        if Window.__show_fps:
            Window.__fps_obj.message = f"{round(self.__main_clock.get_fps())} FPS"
        self.after(500, self.__fps_update)

    def show_fps_in_this_window(self, status: bool) -> None:
        self.__show_fps_in_this_window = bool(status)

    def show_all(self, without=list()) -> None:
        for obj in filter(lambda obj: obj not in without, self.objects):
            obj.show()

    def hide_all(self, without=list()) -> None:
        for obj in filter(lambda obj: obj not in without, self.objects):
            obj.hide()

    def event_handler(self) -> None:
        for key_state_dict in [Window.__all_window_key_state_dict, self.__key_state_dict]:
            for key_value, callback_list in key_state_dict.items():
                for callback in callback_list:
                    callback(key_value, self.keyboard.is_pressed(key_value))
        for mouse_handler_list in [Window.__all_window_mouse_handler_list, self.__mouse_handler_list]:
            for callback in mouse_handler_list:
                callback(pygame.mouse.get_pos())
        for joystick_state_dict in [Window.__all_window_joystick_state_dict, self.__joystick_state_dict]:
            for device_index in filter(lambda index: self.joystick[index] is not None, joystick_state_dict):
                for action, callback_list in joystick_state_dict[device_index].items():
                    for callback in callback_list:
                        callback(self.joystick[device_index].get_value(action))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.close()
                return
            for event_handler_dict in [Window.__all_window_event_handler_dict, self.__event_handler_dict]:
                for callback in event_handler_dict.get(event.type, tuple()):
                    callback(event)

    @staticmethod
    def __handle_cursor():
        Window.__cursor.set()
        Window.__cursor = Window.__default_cursor

    @staticmethod
    def set_temporary_window_cursor(cursor: Cursor) -> None:
        if isinstance(cursor, Cursor):
            Window.__cursor = cursor

    @staticmethod
    def set_window_cursor(cursor: Cursor):
        if isinstance(cursor, Cursor):
            Window.__default_cursor = cursor

    def __key_handler(self, event: pygame.event.Event) -> None:
        for key_handler_dict in [Window.__all_window_key_handler_dict, self.__key_handler_dict]:
            for callback in key_handler_dict.get(event.key, tuple()):
                callback(event)

    def __joystick_handler(self, event: pygame.event.Event) -> None:
        joystick = self.joystick.get_joy_by_instance_id(event.instance_id)
        for joystick_handler_dict in [Window.__all_window_joystick_handler_dict, self.__joystick_handler_dict]:
            joystick_handler_dict = joystick_handler_dict.get(joystick.device_index, dict())
            if event.type == pygame.JOYBUTTONDOWN:
                event_handler = {"event_type": "button", "index": event.button}
            elif event.type == pygame.JOYAXISMOTION:
                event_handler = {"event_type": "axis", "index": event.axis}
            else:
                event_handler = {"event_type": "hat", "index": event.hat, "hat_value": event.value}
            for callback in joystick_handler_dict.get(joystick.search_key(**event_handler), tuple()):
                callback(event)

    @staticmethod
    def allow_only_event(event_type: Union[int, Sequence[int]]) -> None:
        pygame.event.set_allowed(event_type)

    @staticmethod
    def allow_all_events() -> None:
        pygame.event.set_allowed(None)

    @staticmethod
    def block_only_event(event_type: Union[int, Sequence[int]]) -> None:
        pygame.event.set_blocked(event_type)

    def set_focus(self, obj: Focusable) -> None:
        self.objects.set_focus(obj)

    def focus_mode(self, mode: str) -> None:
        Focusable.set_mode(mode)

    def __handle_focus(self, event: pygame.event.Event) -> None:
        if event.type in [pygame.KEYDOWN, pygame.JOYHATMOTION]:
            Focusable.set_mode(Focusable.MODE_KEY if event.type == pygame.KEYDOWN else Focusable.MODE_JOY)
            if event.type == pygame.KEYDOWN and event.key in [pygame.K_LEFT, pygame.K_RIGHT] and self.text_input_enabled():
                return
            if Window.__all_window_key_enabled and self.__key_enabled:
                side_with_key_event = {
                    pygame.K_LEFT: Focusable.ON_LEFT,
                    pygame.K_RIGHT: Focusable.ON_RIGHT,
                    pygame.K_UP: Focusable.ON_TOP,
                    pygame.K_DOWN: Focusable.ON_BOTTOM,
                }
                side_with_joystick_hat_event = {
                    (-1, 0): Focusable.ON_LEFT,
                    (1, 0): Focusable.ON_RIGHT,
                    (0, 1): Focusable.ON_TOP,
                    (0, -1): Focusable.ON_BOTTOM,
                }
                if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
                    self.objects.focus_next()
                else:
                    key_events = {
                        pygame.KEYDOWN: ("key", side_with_key_event),
                        pygame.JOYHATMOTION: ("value", side_with_joystick_hat_event)
                    }
                    if event.type in key_events:
                        attr, side_dict = key_events[event.type]
                        value = getattr(event, attr)
                        if value in side_dict:
                            self.objects.focus_obj_on_side(side_dict[value])
        else:
            Focusable.set_mode(Focusable.MODE_MOUSE)

    def __resize_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.WINDOWEVENT and event.event in [pygame.WINDOWEVENT_RESIZED, pygame.WINDOWEVENT_SIZE_CHANGED, pygame.WINDOWEVENT_MAXIMIZED]:
            if self.width < Window.__min_size[0] or self.height < Window.__min_size[1]:
                size = (max(self.width, Window.__min_size[0]), max(self.height, Window.__min_size[1]))
                pygame.display.set_mode(size, flags=Window.__flags)
            for window in Window.__all_opened:
                window.place_objects()

    @staticmethod
    def set_minimum_window_size(width: int, height: int) -> None:
        Window.__min_size = max(width, 0), max(height, 0)

    def after(self, milliseconds: float, callback: Callable[..., Any], *args: Any, **kwargs: Any) -> WindowCallback:
        window_callback = WindowCallback(self, milliseconds, callback, args, kwargs)
        self.__callback_after.append(window_callback)
        return window_callback

    def remove_window_callback(self, window_callback: WindowCallback) -> None:
        if window_callback in self.__callback_after:
            self.__callback_after.remove(window_callback)

    @staticmethod
    def __bind_event(event_handler_dict: dict[int, list[Callable[..., Any]]], event_type: int, callback: Callable[..., Any]) -> None:
        event_list = event_handler_dict.get(event_type)
        if event_list is None:
            event_list = event_handler_dict[event_type] = list()
        event_list.append(callback)

    def bind_event(self, event_type: int, callback: Callable[..., Any]) -> None:
        self.__bind_event(self.__event_handler_dict, event_type, callback)

    def bind_multiple_event(self, event_type_list: Sequence[int], callback: Callable[..., Any]) -> None:
        for event_type in event_type_list:
            self.bind_event(event_type, callback)

    @staticmethod
    def bind_event_all_window(event_type: int, callback: Callable[..., Any]) -> None:
        Window.__bind_event(Window.__all_window_event_handler_dict, event_type, callback)

    @staticmethod
    def bind_multiple_event_all_window(event_type_list: Sequence[int], callback: Callable[..., Any]) -> None:
        for event_type in event_type_list:
            Window.bind_event_all_window(event_type, callback)

    @staticmethod
    def __bind_mouse(mouse_handler_list: list[Callable[..., Any]], callback: Callable[..., Any]) -> None:
        mouse_handler_list.append(callback)

    def bind_mouse(self, callback: Callable[..., Any]) -> None:
        self.__bind_mouse(self.__mouse_handler_list, callback)

    @staticmethod
    def bind_mouse_all_window(callback: Callable[..., Any]) -> None:
        Window.__bind_mouse(Window.__all_window_mouse_handler_list, callback)

    @staticmethod
    def __bind_key(key_handler_dict: dict[int, list[Callable[..., Any]]], key_state_dict: dict[int, list[Callable[..., Any]]],
                   key_value: int, callback: Callable[..., Any], hold: bool) -> None:
        if not hold:
            key_dict = key_handler_dict
        else:
            key_dict = key_state_dict
        key_list = key_dict.get(key_value)
        if key_list is None:
            key_list = key_dict[key_value] = list()
        key_list.append(callback)

    def bind_key(self, key_value: int, callback: Callable[..., Any], hold: Optional[bool] = False) -> None:
        self.__bind_key(self.__key_handler_dict, self.__key_state_dict, key_value, callback, hold)

    def bind_key_all_window(key_value: int, callback: Callable[..., Any], hold: Optional[bool] = False) -> None:
        Window.__bind_key(Window.__all_window_key_handler_dict, Window.__all_window_key_state_dict, key_value, callback, hold)

    @staticmethod
    def __bind_joystick(joystick_handler_dict: dict[int, dict[str, list[Callable[..., Any]]]],
                      joystick_state_dict: dict[int, dict[str, list[Callable[..., Any]]]],
                      joy_id: int, action: str, callback: Callable[..., Any], state: bool) -> None:
        if not state:
            joystick_joy_id_dict = joystick_handler_dict
        else:
            joystick_joy_id_dict = joystick_state_dict
        joystick_dict = joystick_joy_id_dict.get(joy_id)
        if joystick_dict is None:
            joystick_dict = joystick_joy_id_dict[joy_id] = dict()
        joystick_list = joystick_dict.get(action)
        if joystick_list is None:
            joystick_list = joystick_dict[action] = list()
        joystick_list.append(callback)

    def bind_joystick(self, joy_id: int, action: str, callback: Callable[..., Any], state: Optional[bool] = False) -> None:
        self.__bind_joystick(self.__joystick_handler_dict, self.__joystick_state_dict, joy_id, action, callback, state)

    @staticmethod
    def bind_joystick_all_window(joy_id: int, action: str, callback: Callable[..., Any], state: Optional[bool] = False) -> None:
        Window.__bind_joystick(Window.__all_window_joystick_handler_dict, Window.__all_window_joystick_state_dict, joy_id, action, callback, state)

    def screenshot(self) -> None:
        if isinstance(self.__screenshot, WindowDrawable):
            self.remove_window_callback(self.__screenshot_window_callback)
            self.__hide_screenshot_frame()
            self.draw_screen()
        i = 1
        path = os.path.join(sys.path[0], "screenshot_{}.png")
        while os.path.isfile(path.format(i)):
            i += 1
        pygame.image.save(self.surface, path.format(i))
        self.__screenshot = WindowDrawable(self.surface, width=0.15 * self.width)
        self.__screenshot.move(right=self.right - 20, top=20)
        self.__screenshot_window_callback = self.after(1000, self.__hide_screenshot_frame)

    def __hide_screenshot_frame(self) -> None:
        self.__screenshot = None
        self.__screenshot_window_callback = None

    def __handle_bg_music(self) -> None:
        if (not Window.__enable_music or self.bg_music is None) and pygame.mixer.get_busy():
            self.stop_music()
        elif Window.__enable_music and self.bg_music is not None and (not pygame.mixer.music.get_busy() or Window.__actual_music is None or Window.__actual_music != self.bg_music):
            self.play_music(self.bg_music)

    @staticmethod
    def stop_music() -> None:
        pygame.mixer.music.stop()
        Window.__actual_music = None

    @staticmethod
    def play_music(filepath: str) -> None:
        Window.stop_music()
        if Window.__enable_music:
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.set_volume(Window.__music_volume)
            pygame.mixer.music.play(-1)
            Window.__actual_music = filepath

    @staticmethod
    def play_sound(sound: pygame.mixer.Sound) -> None:
        if Window.__enable_sound and isinstance(sound, pygame.mixer.Sound):
            sound.play()

    @staticmethod
    def sound_volume() -> float:
        return Window.__sound_volume

    @staticmethod
    def music_volume() -> float:
        return Window.__music_volume

    @staticmethod
    def set_sound_volume(value: float) -> None:
        Window.__sound_volume = set_value_in_range(value, 0, 1)
        Window.__resources.set_sfx_volume(Window.__sound_volume, Window.__enable_sound)

    @staticmethod
    def set_music_volume(value: float) -> None:
        Window.__music_volume = set_value_in_range(value, 0, 1)
        pygame.mixer.music.set_volume(Window.__music_volume)

    @staticmethod
    def set_music_state(state: bool) -> None:
        Window.__enable_music = bool(state)

    @staticmethod
    def set_sound_state(state: bool) -> None:
        Window.__enable_sound = bool(state)
        Window.__resources.set_sfx_volume(Window.__sound_volume, Window.__enable_sound)

    @staticmethod
    def get_music_state() -> bool:
        return Window.__enable_music

    @staticmethod
    def get_sound_state() -> bool:
        return Window.__enable_sound

    @staticmethod
    def load_config() -> None:
        config = configparser.ConfigParser()
        config.read(Window.__config_file)
        Window.set_music_volume(config.getfloat("MUSIC", "volume", fallback=Window.__music_volume) / 100)
        Window.set_music_state(config.getboolean("MUSIC", "enable", fallback=Window.__enable_music))
        Window.set_sound_volume(config.getfloat("SFX", "volume", fallback=Window.__sound_volume) / 100)
        Window.set_sound_state(config.getboolean("SFX", "enable", fallback=Window.__enable_sound))

    @staticmethod
    def save_config() -> None:
        config_dict = {
            "MUSIC": {
                "volume": round(Window.__music_volume * 100),
                "enable": Window.get_music_state()
            },
            "SFX": {
                "volume": round(Window.__sound_volume * 100),
                "enable": Window.get_sound_state()
            }
        }
        config = configparser.ConfigParser()
        config.read_dict(config_dict)
        with open(Window.__config_file, "w") as file:
            config.write(file, space_around_delimiters=False)

    @staticmethod
    def text_input_enabled() -> bool:
        return Window.__text_input_enabled

    @staticmethod
    def enable_text_input() -> None:
        if not Window.__text_input_enabled:
            pygame.key.start_text_input()
            Window.__default_key_repeat = pygame.key.get_repeat()
            pygame.key.set_repeat(500, 50)
            Window.__text_input_enabled = True

    @staticmethod
    def disable_text_input() -> None:
        if Window.__text_input_enabled:
            pygame.key.stop_text_input()
            pygame.key.set_repeat(*Window.__default_key_repeat)
            Window.__default_key_repeat = (0, 0)
            Window.__text_input_enabled = False

    @staticmethod
    def create_server(port: int, listen: int) -> tuple[str, int]:
        Window.__server_socket.bind(port, 1)
        if not Window.__server_socket.connected():
            raise OSError
        Window.connect_to_server("localhost", port, None)
        Window.__server_socket.listen = listen
        return Window.get_server_infos()

    @staticmethod
    def connect_to_server(address: str, port: int, timeout: int) -> bool:
        return Window.__client_socket.connect(address, port, timeout)

    @staticmethod
    def stop_connection() -> None:
        Window.__client_socket.stop()
        Window.__server_socket.stop()

    @property
    def client_socket(self) -> ClientSocket:
        return Window.__client_socket

    @staticmethod
    def get_server_infos() -> tuple[str, int]:
        return (Window.__server_socket.ip, Window.__server_socket.port)

    @staticmethod
    def get_server_clients_count() -> int:
        return len(Window.__server_socket.clients)

    @staticmethod
    def set_server_listen(listen: int) -> None:
        Window.__server_socket.listen = listen

    @staticmethod
    def set_server_socket_class_handler(ServerSocketHandler: type[ServerSocket], *args, **kwargs) -> None:
        if not issubclass(ServerSocketHandler, ServerSocket):
            raise TypeError("The class must be a subclass of ServerSocket")
        Window.__server_socket = ServerSocketHandler(*args, **kwargs)

    surface = property(lambda self: pygame.display.get_surface())
    rect = property(lambda self: self.surface.get_rect())
    left = property(lambda self: self.rect.left)
    right = property(lambda self: self.rect.right)
    top = property(lambda self: self.rect.top)
    bottom = property(lambda self: self.rect.bottom)
    x = left
    y = top
    size = property(lambda self: self.rect.size)
    width = property(lambda self: self.rect.width)
    height = property(lambda self: self.rect.height)
    w = width
    h = height
    center = property(lambda self: self.rect.center)
    centerx = property(lambda self: self.rect.centerx)
    centery = property(lambda self: self.rect.centery)
    topleft = property(lambda self: self.rect.topleft)
    topright = property(lambda self: self.rect.topright)
    bottomleft = property(lambda self: self.rect.bottomleft)
    bottomright = property(lambda self: self.rect.bottomright)
    midtop = property(lambda self: self.rect.midtop)
    midbottom = property(lambda self: self.rect.midbottom)
    midleft = property(lambda self: self.rect.midleft)
    midright = property(lambda self: self.rect.midright)

class MainWindow(Window):

    def __init__(self, size=(0, 0), flags=0, bg_color=BLACK, bg_music=None, nb_joystick=0, resources=None, config=None):
        Window._Window__init_pygame(size, flags, nb_joystick, resources, config)
        super().__init__(bg_color=bg_color, bg_music=bg_music)