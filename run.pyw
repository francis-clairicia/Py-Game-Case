# -*- coding: Utf-8 -*

import os
import sys
import argparse
import packaging.version
import psutil
from py_game_case import PyGameCase, __version__ as actual_version
from navy import NavyWindow
from four_in_a_row import FourInARowWindow
from updater import Updater

ALL_GAMES = {
    "navy": NavyWindow,
    "four_in_a_row": FourInARowWindow
}

def find_process_by_name(name: str) -> list[str]:
    process_list = list()
    for p in psutil.process_iter(["name", "exe", "cmdline"]):
        if name == p.info['name'] or p.info['exe'] and os.path.basename(p.info['exe']) == name or (p.info['cmdline'] and p.info['cmdline'][0] == name):
            process_list.append(p)
    return process_list

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

    if not sys.argv[0].endswith((".py", ".pyw")):
        process = psutil.Process()
        if len(find_process_by_name(process.name())) > 1:
            return

    updater = Updater()

    if args.update:
        updater.install_latest_version(actual_version)
    elif args.install:
        updater.install_version(args.install)
    window = PyGameCase()
    return window.mainloop()

if __name__ == "__main__":
    sys.exit(main())