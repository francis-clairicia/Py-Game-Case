# -*- coding: Utf-8 -*

import configparser
from typing import Any
from my_pygame import set_constant_file, set_constant_directory
from my_pygame import Resources
from navy import NavyWindow
from four_in_a_row import FourInARowWindow

RESOURCES = Resources()

RESOURCES_FOLDER = set_constant_directory("resources", "py_game_case", special_msg="Resources folder not present")
IMG_FOLDER = set_constant_directory(RESOURCES_FOLDER, "img", special_msg="Images folder not present")

RESOURCES.IMG = {
    "icon": set_constant_file(IMG_FOLDER, "icon.surface"),
    "logo": set_constant_file(IMG_FOLDER, "logo.surface"),
}

GAMES = {
    "navy":          {"name": "Navy",       "window": NavyWindow},
    "four_in_a_row": {"name": "4 in a row", "window": FourInARowWindow},
}

RESOURCES.IMG |= {game: set_constant_file(IMG_FOLDER, "preview_{}.surface".format(game)) for game in GAMES}

##########################################################################################################################

class Settings:

    def __init__(self):
        self.__file = set_constant_file("settings.ini", raise_error=False)
        self.__parser = configparser.ConfigParser()
        self.__parser.read(self.__file)

    def __save(self) -> None:
        with open(self.__file, "w") as file:
            self.__parser.write(file, space_around_delimiters=False)

    def __get(self, getter, section: str, option: str, **kwargs):
        if "fallback" not in kwargs:
            return getter(section, option, **kwargs)
        try:
            value = getter(section, option, **kwargs)
        except:
            value = kwargs["fallback"]
        return value

    def get(self, section: str, option: str, **kwargs) -> str:
        return str(self.__get(self.__parser.get, section, option, **kwargs))

    def getint(self, section: str, option: str, **kwargs) -> int:
        return int(self.__get(self.__parser.getint, section, option, **kwargs))

    def getfloat(self, section: str, option: str, **kwargs) -> float:
        return float(self.__get(self.__parser.getfloat, section, option, **kwargs))

    def getboolean(self, section: str, option: str, **kwargs) -> bool:
        return bool(self.__get(self.__parser.getboolean, section, option, **kwargs))

    def set(self, section: str, option: str, value: Any) -> None:
        if not self.__parser.has_section(section):
            self.__parser.add_section(section)
        self.__parser[section][option] = str(value)
        self.__save()

    launch_in_same_window = property(
        lambda self: self.getboolean("GENERAL", "launch_in_same_window", fallback=True),
        lambda self, value: self.set("GENERAL", "launch_in_same_window", value),
    )
    auto_check_update = property(
        lambda self: self.getboolean("UPDATER", "auto_check_update", fallback=False),
        lambda self, value: self.set("UPDATER", "auto_check_update", value),
    )

SETTINGS = Settings()
