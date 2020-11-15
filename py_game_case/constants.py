# -*- coding: Utf-8 -*

from my_pygame import set_constant_file, set_constant_directory
from my_pygame import Resources

RESOURCES = Resources()

RESOURCES_FOLDER = set_constant_directory("resources", "py_game_case", special_msg="Resources folder not present")
IMG_FOLDER = set_constant_directory(RESOURCES_FOLDER, "img", special_msg="Images folder not present")

IMG = {
    "icon": set_constant_file(IMG_FOLDER, "icon.png"),
    "logo": set_constant_file(IMG_FOLDER, "logo.png"),
}

GAMES = {
    "navy": "Navy",
    "four_in_a_row": "4 in a row",
}
for game in GAMES:
    IMG[game] = set_constant_file(IMG_FOLDER, "preview_{}.png".format(game))

RESOURCES.IMG = IMG