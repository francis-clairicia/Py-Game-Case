# -*- coding: Utf-8 -*

from typing import Union, Sequence, Tuple, Callable
import pygame

class Cursor:

    __actual_cursor = None

    def __init__(self, cursor: Union[int, Sequence[Tuple[int, ...]]]):
        if isinstance(cursor, int):
            self.__cursor_setter = pygame.mouse.set_system_cursor
            self.__cursor = [cursor]
        else:
            self.__cursor_setter = pygame.mouse.set_cursor
            self.__cursor = cursor

    @classmethod
    def from_xbm_file(cls, cursorfile: str, maskfile: str):
        return cls(pygame.cursors.load_xbm(cursorfile, maskfile))

    @classmethod
    def from_string_list(cls, size: Tuple[int, int], hotspot: Tuple[int, int], strings: Sequence[str], **kwargs):
        cursor = pygame.cursors.compile(strings, **kwargs)
        return cls((size, hotspot, *cursor))

    def set(self) -> None:
        if Cursor.__actual_cursor is not self:
            self.__cursor_setter(*self.__cursor)
            Cursor.__actual_cursor = self