# -*- coding: Utf-8 -*

import pygame
from .window import Window
from .shape import RectangleShape
from .colors import WHITE, BLACK

class Dialog(Window):
    def __init__(self, master: Window, width_ratio=0.5, height_ratio=0.5,
                 bg_color=WHITE, outline=3, outline_color=BLACK, bg_music=None,
                 hide_all_without=list(), show_all_without=list()):
        if not isinstance(master, Window):
            raise TypeError(f"master must be a Window instance, not {master.__class__.__name__}")
        Window.__init__(self, master=master, bg_music=bg_music or master.bg_music)
        self.__master = master
        self.__frame = RectangleShape(width_ratio * self.width, height_ratio * self.height, bg_color, outline=outline, outline_color=outline_color)
        self.__frame.center = self.center
        self.__hide_all_without = list(hide_all_without)
        self.__show_all_without = list(show_all_without)
        self.__hidden_objects_master = list(filter(lambda obj: not obj.is_shown(), self.__master.objects.drawable))

    @property
    def frame(self) -> RectangleShape:
        return self.__frame

    def mainloop(self) -> int:
        if self.__hide_all_without:
            self.__master.hide_all(without=self.__hide_all_without)
        elif self.__show_all_without:
            self.__master.show_all(without=self.__show_all_without)
        Window.mainloop(self)
        self.__master.show_all(without=self.__hidden_objects_master)
        return 0

    def close(self) -> None:
        self.__master.close()