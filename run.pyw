# -*- coding: Utf-8 -*

import os
import sys
import argparse
import packaging.version
from py_game_case import PyGameCase, __version__
from navy import NavyWindow
from four_in_a_row import FourInARowWindow
from updater import Updater

ALL_GAMES = {
    "navy": NavyWindow,
    "four_in_a_row": FourInARowWindow
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("game", nargs="?", help="Game to launch -> {}".format(" or ".join(ALL_GAMES)))
    parser.add_argument("--update", action="store_true", help="Update the Launcher to the latest version")
    parser.add_argument("--install", metavar="version", help="Install a specific version of the Laucher")
    args = parser.parse_args()

    updater = Updater()

    if args.update:
        updater.install_latest_version(__version__)
    elif args.install:
        updater.install_version(args.install)

    if args.game is None:
        MainWindow = PyGameCase
    elif args.game in ALL_GAMES:
        MainWindow = ALL_GAMES[args.game]
    else:
        print("Unknown game '{}'".format(args.game))
        print("The 'game' parameter must be one of these:")
        for game in ALL_GAMES:
            print(" - {}".format(game))
        return 1
    window = MainWindow()
    return window.mainloop()

if __name__ == "__main__":
    sys.exit(main())