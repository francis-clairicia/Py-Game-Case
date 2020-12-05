# -*- coding: Utf-8

from my_pygame import set_constant_directory, set_constant_file
from my_pygame import Resources

WINDOW_CONFIG_FILE = set_constant_file("window", "navy.ini", raise_error=False)

RESOURCES = Resources()

RESOURCES_FOLDER = set_constant_directory("resources", "navy", special_msg="Resources folder not present")
IMG_FOLDER = set_constant_directory(RESOURCES_FOLDER, "img", special_msg="Images folder not present")

RESOURCES.IMG = {
    "icon": set_constant_file(IMG_FOLDER, "icon.surface"),
    "menu_bg": set_constant_file(IMG_FOLDER, "menu_background.surface"),
    "logo": set_constant_file(IMG_FOLDER, "logo.surface"),
    "settings": set_constant_file(IMG_FOLDER, "build_512px.surface"),
    "arrow_blue": set_constant_file(IMG_FOLDER, "arrow.surface"),
    "reload_blue": set_constant_file(IMG_FOLDER, "reload_blue.surface"),
    "random": set_constant_file(IMG_FOLDER, "random.surface"),
    "battleship": set_constant_file(IMG_FOLDER, "battleship.surface"),
    "destroyer": set_constant_file(IMG_FOLDER, "destroyer.surface"),
    "patroal_boat": set_constant_file(IMG_FOLDER, "patroal_boat.surface"),
    "carrier": set_constant_file(IMG_FOLDER, "carrier.surface"),
    "red_triangle": set_constant_file(IMG_FOLDER, "red_triangle.surface"),
    "green_triangle": set_constant_file(IMG_FOLDER, "green_triangle.surface"),
    "hatch": set_constant_file(IMG_FOLDER, "hatch.surface"),
    "cross": set_constant_file(IMG_FOLDER, "cross.surface")
}

NAVY_GRID_SIZE = 500
NB_LINES_BOXES = 10
NB_COLUMNS_BOXES = 10
BOX_SIZE = (NAVY_GRID_SIZE // NB_COLUMNS_BOXES, NAVY_GRID_SIZE // NB_LINES_BOXES)

SHIPS = {
    "carrier":      {"size": 4, "nb": 1, "offset": 0},
    "battleship":   {"size": 3, "nb": 2, "offset": 30},
    "destroyer":    {"size": 2, "nb": 3, "offset": 30},
    "patroal_boat": {"size": 1, "nb": 4, "offset": 70}
}
NB_SHIPS = sum(ship["nb"] for ship in SHIPS.values())
