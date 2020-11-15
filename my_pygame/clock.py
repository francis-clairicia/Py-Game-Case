# -*- coding: Utf-8 -*

import pygame.time

class Clock(object):

    __slots__ = ("__time", "__clock")

    def __init__(self):
        self.__time = 0
        self.__clock = pygame.time.Clock()

    def get_elapsed_time(self) -> int:
        self.__clock.tick()
        self.__time += self.__clock.get_rawtime()
        return self.__time

    def elapsed_time(self, milliseconds: int, restart=True) -> bool:
        if self.get_elapsed_time() >= milliseconds:
            if restart:
                self.restart()
            return True
        return False

    def restart(self) -> None:
        self.__clock.tick()
        self.__time = 0

    def tick(self):
        self.__clock.tick()