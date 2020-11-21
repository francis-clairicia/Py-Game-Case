# -*- coding: Utf-8

from my_pygame import set_constant_directory, set_constant_file
from my_pygame import Resources

WINDOW_CONFIG_FILE = set_constant_file("window", "navy.ini", raise_error=False)

RESOURCES = Resources()

RESOURCES_FOLDER = set_constant_directory("resources", "navy", special_msg="Resources folder not present")
IMG_FOLDER = set_constant_directory(RESOURCES_FOLDER, "img", special_msg="Images folder not present")
SOUNDS_FOLDER = set_constant_directory(RESOURCES_FOLDER, "sounds", special_msg="Sounds folder not present")

RESOURCES.IMG = {
    "icon": set_constant_file(IMG_FOLDER, "icon.png"),
    "menu_bg": set_constant_file(IMG_FOLDER, "menu_background.jpg"),
    "logo": set_constant_file(IMG_FOLDER, "logo.png"),
    "settings": set_constant_file(IMG_FOLDER, "build_512px.png"),
    "arrow_blue": set_constant_file(IMG_FOLDER, "arrow.png"),
    "reload_blue": set_constant_file(IMG_FOLDER, "reload_blue.png"),
    "random": set_constant_file(IMG_FOLDER, "random.png"),
    "battleship": set_constant_file(IMG_FOLDER, "battleship.png"),
    "destroyer": set_constant_file(IMG_FOLDER, "destroyer.png"),
    "patroal_boat": set_constant_file(IMG_FOLDER, "patroal_boat.png"),
    "carrier": set_constant_file(IMG_FOLDER, "carrier.png"),
    "red_triangle": set_constant_file(IMG_FOLDER, "red_triangle.png"),
    "green_triangle": set_constant_file(IMG_FOLDER, "green_triangle.png"),
    "hatch": set_constant_file(IMG_FOLDER, "hatch.png"),
    "cross": set_constant_file(IMG_FOLDER, "cross.png")
}

RESOURCES.MUSIC = {
    "menu": set_constant_file(SOUNDS_FOLDER, "Move-it-Out.mp3"),
    "setup": set_constant_file(SOUNDS_FOLDER, "Preparing-for-Battle.mp3"),
    "gameplay": set_constant_file(SOUNDS_FOLDER, "Pirates.mp3"),
    "end": set_constant_file(SOUNDS_FOLDER, "Comrades-Always.mp3")
}

RESOURCES.SFX = {
    "splash": set_constant_file(SOUNDS_FOLDER, "sfx-splash.mp3"),
    "explosion": set_constant_file(SOUNDS_FOLDER, "sfx-explosion.mp3"),
    "destroy": set_constant_file(SOUNDS_FOLDER, "sfx-ship-explosion.mp3")
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