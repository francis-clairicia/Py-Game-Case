# -*-coding:Utf-8-*

import os
import sys
from typing import List, Tuple, Union, Optional, Iterator
import pickle
import pygame

class Joystick(object):

    def __init__(self, index: int):
        self.__index = index
        self.__joystick = pygame.joystick.Joystick(index) if index in range(Joystick.count()) else None

        self.__button_list = ["A", "B", "X", "Y", "L1", "L2", "R1", "R2", "SELECT", "START", "L3", "R3", "HOME"]
        self.__axis_list = ["AXIS_LEFT_X", "AXIS_LEFT_Y", "AXIS_RIGHT_X", "AXIS_RIGHT_Y"]
        self.__dpad_list = ["UP", "DOWN", "LEFT", "RIGHT"]

        self.__event_type = {key: [str(), -1, 0] for key in self.button_list + self.axis_list + self.dpad_list}

        self.__save_file = os.path.join(sys.path[0], "joystick.bin")
        if os.path.isfile(self.__save_file):
            with open(self.__save_file, "rb") as save:
                self.__save = pickle.load(save)
        else:
            self.__save = dict()
            self.set_default_layout()
        self.__button_axis_return_bool = False

    """-----------------------------------------------------"""

    def connected(self) -> bool:
        return bool(self.__joystick is not None)

    def event_connect(self, event: pygame.event.Event) -> None:
        if self.connected():
            return
        if event.type in (pygame.CONTROLLERDEVICEADDED, pygame.JOYDEVICEADDED) and event.device_index == self.__index:
            self.__joystick = pygame.joystick.Joystick(event.device_index)
            if self.guid in self.__save:
                self.__event_type = self.__save[self.guid]
            else:
                self.set_default_layout()

    def event_disconnect(self, event: pygame.event.Event) -> None:
        if not self.connected():
            return
        if event.type in (pygame.CONTROLLERDEVICEREMOVED, pygame.JOYDEVICEREMOVED) and event.instance_id == self.id:
            self.__joystick.quit()
            self.__joystick = None

    """------------------------------------------------------------------"""

    def set_default_layout(self) -> None:
        layout = {
            "A":             ("button", 0, 1),
            "B":             ("button", 1, 1),
            "X":             ("button", 2, 1),
            "Y":             ("button", 3, 1),
            "L1":            ("button", 4, 1),
            "R1":            ("button", 5, 1),
            "SELECT":        ("button", 6, 1),
            "START":         ("button", 7, 1),
            "L3":            ("button", 8, 1),
            "R3":            ("button", 9, 1),
            "HOME":          ("button", 10, 1),
            "UP":            ("hat", 0, (0, 1)),
            "DOWN":          ("hat", 0, (0, -1)),
            "LEFT":          ("hat", 0, (-1, 0)),
            "RIGHT":         ("hat", 0, (1, 0)),
            "L2":            ("axis", 2, 1),
            "R2":            ("axis", 5, 1),
            "AXIS_LEFT_X":   ("axis", 0, 0),
            "AXIS_LEFT_Y":   ("axis", 1, 0),
            "AXIS_RIGHT_X":  ("axis", 3, 0),
            "AXIS_RIGHT_Y":  ("axis", 4, 0),
        }
        for key, value in layout.items():
            self.__event_type[key] = list(value)

    def __save_to_file(self) -> None:
        self.__save[self.guid] = dict(self.__event_type)
        with open(self.__save_file, "wb") as save:
            pickle.dump(self.__save, save)

    """------------------------------------------------------------------"""

    @property
    def button_list(self) -> List[str]:
        return self.__button_list

    @property
    def axis_list(self) -> List[str]:
        return self.__axis_list

    @property
    def dpad_list(self) -> List[str]:
        return self.__dpad_list

    """------------------------------------------------------------------"""

    def __test(self, key: str) -> Tuple[str, str]:
        key = key.upper()
        if key.endswith(("-", "+")):
            key, suffix = key[:-1], key[-1]
        else:
            suffix = str()
        if key not in self.__event_type:
            raise NameError("{} isn't recognized".format(key))
        return key, suffix

    def get_value(self, key: str) -> float:
        key, suffix = self.__test(key)
        if not self.connected():
            return 0
        event, index, active_state = self.__event_type[key]
        active_state = {"": active_state, "-": -1, "+": 1}[suffix]
        actions = {
            "button": self.__joystick.get_button,
            "axis": self.__joystick.get_axis,
            "hat": self.__joystick.get_hat,
        }
        try:
            state = actions[event](index)
        except pygame.error:
            return 0
        if event == "button":
            return state
        if event == "hat" and isinstance(state, tuple):
            return 1 if all(active_state[i] == 0 or state[i] == active_state[i] for i in range(2)) else 0
        if event == "axis":
            if key not in self.axis_list and self.__button_axis_return_bool:
                return 1 if state >= 0.9 else 0
            return self.__get_axis_value(state, active_state)
        return 0

    def __get_axis_value(self, state: float, active_state: int) -> float:
        if active_state != 0:
            if (active_state > 0 and state < 0) or (active_state < 0 and state > 0):
                return 0
            return abs(state)
        return state

    def search_key(self, event_type: str, index: int, hat_value: Optional[Tuple[int, int]] = None, axis: Optional[int] = None) -> Union[str, None]:
        for key, (event, idx, value) in self.__event_type.items():
            if event == event_type and idx == index and (event != "hat" or value == hat_value) and (event != "axis" or axis is None or value == axis):
                return key
        return None

    def __getitem__(self, key: str) -> Union[int, float]:
        key = self.__test(key)[0]
        infos = self.__event_type[key]
        return infos[1]

    def __setitem__(self, key: str, value: Tuple[int, int, Tuple[int, int]]) -> None:
        self.set_event(key, *value)

    def set_event(self, key: str, event: int, index: int, hat_value: Optional[Tuple[int, int]] = (0, 0)) -> None:
        key = self.__test(key)[0]
        event_map = {
            pygame.JOYBUTTONDOWN: ("button", index, 1),
            pygame.JOYAXISMOTION: ("axis", index, 0 if key not in self.button_list + self.dpad_list else 1),
            pygame.JOYHATMOTION: ("hat", index, hat_value)
        }
        if event in event_map:
            self.__event_type[key] = list(event_map[event])
            self.__save_to_file()

    def set_button_axis(self, state: bool) -> None:
        self.__button_axis_return_bool = bool(state)

    def get_button_axis_state(self) -> bool:
        return self.__button_axis_return_bool

    """------------------------------------------------------------------"""

    @property
    def device_index(self) -> int:
        return self.__index

    @property
    def id(self) -> int:
        return self.__joystick.get_instance_id() if self.connected() else -1

    @property
    def guid(self) -> str:
        return self.__joystick.get_guid() if self.connected() else str()

    @property
    def name(self) -> str:
        return self.__joystick.get_name() if self.connected() else str()

    @property
    def power_level(self) -> str:
        return self.__joystick.get_power_level() if self.connected() else "unknown"

    """------------------------------------------------------------------"""

    @staticmethod
    def count() -> int:
        return pygame.joystick.get_count()

    @staticmethod
    def list() -> Tuple[str, ...]:
        try:
            joystick = tuple(pygame.joystick.Joystick(i).get_name() for i in range(Joystick.count()))
        except pygame.error:
            joystick = tuple()
        return joystick

    """------------------------------------------------------------------"""

    A = property(lambda self: self.__getitem__("A"), lambda self, value: self.set_event("A", *value))
    B = property(lambda self: self.__getitem__("B"), lambda self, value: self.set_event("B", *value))
    X = property(lambda self: self.__getitem__("X"), lambda self, value: self.set_event("X", *value))
    Y = property(lambda self: self.__getitem__("Y"), lambda self, value: self.set_event("Y", *value))
    L1 = property(lambda self: self.__getitem__("L1"), lambda self, value: self.set_event("L1", *value))
    L2 = property(lambda self: self.__getitem__("L2"), lambda self, value: self.set_event("L2", *value))
    L3 = property(lambda self: self.__getitem__("L3"), lambda self, value: self.set_event("L3", *value))
    R1 = property(lambda self: self.__getitem__("R1"), lambda self, value: self.set_event("R1", *value))
    R2 = property(lambda self: self.__getitem__("R2"), lambda self, value: self.set_event("R2", *value))
    R3 = property(lambda self: self.__getitem__("R3"), lambda self, value: self.set_event("R3", *value))
    SELECT = property(lambda self: self.__getitem__("SELECT"), lambda self, value: self.set_event("SELECT", *value))
    START = property(lambda self: self.__getitem__("START"), lambda self, value: self.set_event("START", *value))
    UP = property(lambda self: self.__getitem__("UP"), lambda self, value: self.set_event("UP", *value))
    DOWN = property(lambda self: self.__getitem__("DOWN"), lambda self, value: self.set_event("DOWN", *value))
    LEFT = property(lambda self: self.__getitem__("LEFT"), lambda self, value: self.set_event("LEFT", *value))
    RIGHT = property(lambda self: self.__getitem__("RIGHT"), lambda self, value: self.set_event("RIGHT", *value))
    AXIS_LEFT_X = property(lambda self: self.__getitem__("AXIS_LEFT_X"), lambda self, value: self.set_event("AXIS_LEFT_X", *value))
    AXIS_LEFT_Y = property(lambda self: self.__getitem__("AXIS_LEFT_Y"), lambda self, value: self.set_event("AXIS_LEFT_Y", *value))
    AXIS_RIGHT_X = property(lambda self: self.__getitem__("AXIS_RIGHT_X"), lambda self, value: self.set_event("AXIS_RIGHT_X", *value))
    AXIS_RIGHT_Y = property(lambda self: self.__getitem__("AXIS_RIGHT_Y"), lambda self, value: self.set_event("AXIS_RIGHT_Y", *value))

class JoystickList(object):

    __slots__ = ("__list")

    def __init__(self):
        self.__list = list()

    def set(self, nb_joystick: int) -> None:
        self.__list = [Joystick(i) for i in range(nb_joystick)]

    def __iter__(self) -> Iterator[Joystick]:
        return iter(self.__list)

    def __bool__(self) -> bool:
        return bool(self.__list)

    def __getitem__(self, index: int) -> Union[Joystick, None]:
        return self.get_joy_by_device_index(index)

    def get_joy_by_device_index(self, index: int) -> Union[Joystick, None]:
        for joy in self:
            if joy.device_index == index:
                return joy
        return None

    def get_joy_by_instance_id(self, instance_id: int) -> Union[Joystick, None]:
        for joy in self:
            if joy.id == instance_id:
                return joy
        return None

    def event_connect(self, event: pygame.event.Event) -> None:
        if event.type in (pygame.CONTROLLERDEVICEADDED, pygame.JOYDEVICEADDED):
            joystick = self.get_joy_by_device_index(event.device_index)
            if joystick is not None:
                joystick.event_connect(event)

    def event_disconnect(self, event: pygame.event.Event) -> None:
        if event.type in (pygame.CONTROLLERDEVICEREMOVED, pygame.JOYDEVICEREMOVED):
            joystick = self.get_joy_by_instance_id(event.instance_id)
            if joystick is not None:
                joystick.event_disconnect(event)