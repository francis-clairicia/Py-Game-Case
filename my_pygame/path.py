# -*- coding: Utf-8 -*

import os
import sys
from typing import Callable

def __set_constant_path(path_exists: Callable[[str], bool], path: str, *paths: str, special_msg=None, raise_error=True) -> str:
    all_path = os.path.join(path, *paths)
    if not os.path.isabs(all_path):
        all_path = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), all_path)
    if not path_exists(all_path) and raise_error:
        if special_msg:
            raise FileNotFoundError(f"{special_msg}: {all_path}")
        raise FileNotFoundError(f"{all_path} folder not found")
    return all_path

def set_constant_directory(path, *paths, special_msg=None, raise_error=True) -> str:
    return __set_constant_path(os.path.isdir, path, *paths, special_msg=special_msg, raise_error=raise_error)

def set_constant_file(path, *paths, special_msg=None, raise_error=True) -> str:
    return __set_constant_path(os.path.isfile, path, *paths, special_msg=special_msg, raise_error=raise_error)
