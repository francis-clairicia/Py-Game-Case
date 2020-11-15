# -*- coding: Utf-8 -*

import sys
import argparse
from py_game_case import PyGameCase
from navy import NavyWindow
from four_in_a_row import FourInARowWindow

ALL_WINDOWS = {
    None: PyGameCase,
    "navy": NavyWindow,
    "four_in_a_row": FourInARowWindow
}

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("game", nargs="?")
    args = parser.parse_args()

    if args.game not in ALL_WINDOWS:
        print("Unknown game '{}'".format(args.game))
        print("The 'game' parameter must be one of these:")
        for game in filter(lambda game: game is not None, ALL_WINDOWS):
            print(" - {}".format(game))
        return 0
    MainWindow = ALL_WINDOWS[args.game]
    window = MainWindow()
    return window.mainloop()

if __name__ == "__main__":
    sys.exit(main())