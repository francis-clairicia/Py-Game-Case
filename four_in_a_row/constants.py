# -*- coding: Utf-8

from my_pygame import set_constant_directory, set_constant_file
from my_pygame import Resources
from my_pygame import BLUE_DARK

WINDOW_CONFIG_FILE = set_constant_file("window", "four_in_a_row.ini", raise_error=False)

RESOURCES = Resources()

RESOURCES_FOLDER = set_constant_directory("resources", "four_in_a_row", special_msg="Resources folder not present")
IMG_FOLDER = set_constant_directory(RESOURCES_FOLDER, "img", special_msg="Images folder not present")
FONT_FOLDER = set_constant_directory(RESOURCES_FOLDER, "font", special_msg="Fonts folder not present")

RESOURCES.IMG = {
    "icon": set_constant_file(IMG_FOLDER, "icon.ico"),
    "logo": set_constant_file(IMG_FOLDER, "logo.surface"),
    "arrow": set_constant_file(IMG_FOLDER, "Right-Arrow.surface")
}

RESOURCES.FONT = {
    "afterglow": set_constant_file(FONT_FOLDER, "Afterglow-Regular.ttf"),
    "heavy": set_constant_file(FONT_FOLDER, "heavy heap.ttf"),
}

BACKGROUND_COLOR = BLUE_DARK

NB_ROWS = 6
NB_COLUMNS = 7

AI = "AI"
LOCAL_PLAYER = "local_player"
LAN_PLAYER = "LAN_player"
