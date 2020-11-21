# -*- coding: Utf-8 -*

import os
import sys
import argparse
import packaging.version
from py_game_case import PyGameCase, __version__ as actual_version
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

    if args.game in ALL_GAMES:
        MainWindow = ALL_GAMES[args.game]
        window = MainWindow()
        return window.mainloop()

    updater = Updater()

    if args.update:
        updater.install_latest_version(actual_version)
    elif args.install:
        updater.install_version(args.install)
    window = PyGameCase()
    return window.mainloop()

if __name__ == "__main__":
    sys.exit(main())