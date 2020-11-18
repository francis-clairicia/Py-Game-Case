# -*- coding: Utf-8 -*

import os.path
import sys
import configparser
import pygame
from typing import Any
from my_pygame import Window, Dialog, Text
from my_pygame import WHITE

SETTINGS_FILE = os.path.join(sys.path[0], "settings.ini")

class Settings(Dialog):

    def __init__(self, master: Window):
        super().__init__(master, width_ratio=1, height_ratio=1, outline=0, bg_color=master.bg_color)
        self.parser = configparser.ConfigParser()
        self.parser.read(SETTINGS_FILE)
        self.bind_key(pygame.K_ESCAPE, lambda event: self.animate_quit())

        self.text_title = Text("Settings", font=("calibri", 100), color=WHITE)

    def place_objects(self) -> None:
        self.text_title.move(centerx=self.frame.centerx, top=self.frame.top + 20)

    def on_start_loop(self) -> None:
        self.frame.left = self.right
        self.frame.animate_move(self, speed=50, at_every_frame=self.place_objects, center=self.center)

    def animate_quit(self) -> None:
        self.frame.animate_move(self, speed=50, at_every_frame=self.place_objects, left=self.right)
        self.stop()

    def save(self, section: str, option: str, value: Any) -> None:
        self.parser[section][option] = value
        with open(SETTINGS_FILE, "w") as file:
            self.parser.write(file, space_around_delimiters=False)