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
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("game", nargs="?")
    parser.add_argument("--update", action="store_true")
    parser.add_argument("--install", metavar="version")
    args, unknown = parser.parse_known_args()

    if args.game is not None:
        if args.game not in ALL_GAMES:
            print("Unknown game '{}'".format(args.game))
            print("The 'game' parameter must be one of these:")
            for game in ALL_GAMES:
                print(" - {}".format(game))
            return 1
        MainWindow = ALL_GAMES[args.game]
        window = MainWindow()
        return window.mainloop()

    updater = Updater()

    if args.update:
        updater.install_latest_version(__version__)
    elif args.install:
        updater.install_version(args.install)
    window = PyGameCase()
    return window.mainloop()

if __name__ == "__main__":
    sys.exit(main())