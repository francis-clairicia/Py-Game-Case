# -*- coding: Utf-8 -*

import os
import sys
import argparse
import packaging.version
import psutil
from py_game_case import PyGameCase
from py_game_case.constants import GAMES
from navy import NavyWindow
from four_in_a_row import FourInARowWindow

def find_process_by_name(name: str) -> list[str]:
    process_list = list()
    for p in psutil.process_iter(["name", "exe", "cmdline"]):
        if name == p.info['name'] or p.info['exe'] and os.path.basename(p.info['exe']) == name or (p.info['cmdline'] and p.info['cmdline'][0] == name):
            process_list.append(p)
    return process_list

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("game", nargs="?")
    args, unknown = parser.parse_known_args()

    if args.game in GAMES:
        window = GAMES[args.game]["window"]()
    else:
        if not sys.argv[0].endswith((".py", ".pyw")):
            process = psutil.Process()
            if len(find_process_by_name(process.name())) > 1:
                return 0
        window = PyGameCase()
    return window.mainloop()

if __name__ == "__main__":
    sys.exit(main())