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
        release = updater.get_latest_version()
        if release is not None and packaging.version.parse(release["tag_name"]) > packaging.version.parse(__version__):
            updater.install(release)
    elif args.install:
        try:
            version = packaging.version.Version(args.install)
            release = updater.get_version(str(version))
            if release is None:
                raise packaging.version.InvalidVersion(f"There is no version {version}")
        except packaging.version.InvalidVersion as e:
            sys.exit(f"{e.__class__.__name__}: {e}")
        updater.install(release)

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