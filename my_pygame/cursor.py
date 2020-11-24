# -*- coding: Utf-8 -*

from typing import Union, Sequence, Tuple, Callable
import pygame

class AbstractCursor:

    __actual_cursor = None

    def __init__(self, function: Callable[..., None], cursor: Union[int, Sequence[Tuple[int, ...]]]):
        self.__cursor_setter = function
        self.__cursor = [cursor] if isinstance(cursor, int) else cursor

    def set(self) -> None:
        if AbstractCursor.__actual_cursor is not self:
            self.__cursor_setter(*self.__cursor)
            AbstractCursor.__actual_cursor = self

class Cursor(AbstractCursor):

    def __init__(self, cursor: Sequence[Tuple[int, ...]]):
        super().__init__(pygame.mouse.set_cursor, cursor)

    @classmethod
    def from_xbm_file(cls, cursorfile: str, maskfile: str):
        return cls(pygame.cursors.load_xbm(cursorfile, maskfile))

    @classmethod
    def from_string_list(cls, size: Tuple[int, int], hotspot: Tuple[int, int], strings: Sequence[str], **kwargs):
        cursor = pygame.cursors.compile(strings, **kwargs)
        return cls((size, hotspot, *cursor))

class SystemCursor(AbstractCursor):

    def __init__(self, cursor: int):
        super().__init__(pygame.mouse.set_system_cursor, cursor)