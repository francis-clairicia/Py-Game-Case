# -*- coding: Utf-8 -*

import configparser
from my_pygame import set_constant_file, set_constant_directory
from my_pygame import Resources

RESOURCES = Resources()

RESOURCES_FOLDER = set_constant_directory("resources", "py_game_case", special_msg="Resources folder not present")
IMG_FOLDER = set_constant_directory(RESOURCES_FOLDER, "img", special_msg="Images folder not present")

RESOURCES.IMG = {
    "icon": set_constant_file(IMG_FOLDER, "icon.png"),
    "logo": set_constant_file(IMG_FOLDER, "logo.png"),
}

GAMES = {
    "navy": "Navy",
    "four_in_a_row": "4 in a row",
}

RESOURCES.IMG = {game: set_constant_file(IMG_FOLDER, "preview_{}.png".format(game)) for game in GAMES}

##########################################################################################################################

class Settings:

    def __init__(self):
        self.__file = set_constant_file("settings.ini", raise_error=False)
        self.__parser = configparser.ConfigParser()
        self.__parser.read(self.__file)

    def __save(self) -> None:
        with open(self.__file, "w") as file:
            self.__parser.write(file, space_around_delimiters=False)

SETTINGS = Settings()