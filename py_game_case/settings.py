# -*- coding: Utf-8 -*

import os.path
import sys
import configparser
import pygame
from typing import Any
from my_pygame import Window, Text
from my_pygame import WHITE

SETTINGS_FILE = os.path.join(sys.path[0], "settings.ini")

class Settings(Window):

    def __init__(self, master: Window):
        super().__init__(bg_color=master.bg_color)
        self.parser = configparser.ConfigParser()
        self.parser.read(SETTINGS_FILE)
        self.bind_key(pygame.K_ESCAPE, lambda event: self.stop())

        self.text_title = Text("Settings", font=("calibri", 100), color=WHITE)

    def place_objects(self) -> None:
        self.text_title.move(centerx=self.centerx, top=20)

    def save(self, section: str, option: str, value: Any) -> None:
        self.parser[section][option] = value
        with open(SETTINGS_FILE, "w") as file:
            self.parser.write(file, space_around_delimiters=False)