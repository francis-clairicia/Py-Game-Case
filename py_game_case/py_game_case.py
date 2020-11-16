# -*- coding: Utf-8 -*

import sys
import subprocess
from typing import Callable
import pygame
from my_pygame import MainWindow, Window, Image, Button, Sprite, RectangleShape, HorizontalGradientShape
from my_pygame import ButtonListVertical, DrawableListHorizontal
from my_pygame import TRANSPARENT, WHITE, BLACK
from my_pygame import set_color_alpha
from .constants import RESOURCES, GAMES

class TitleButton(Button):

    def __init__(self, master: Window, on_hover: Callable[..., None], *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.__on_hover = on_hover

    def after_drawing(self, surface: pygame.Surface) -> None:
        pygame.draw.line(surface, self.outline_color, self.topleft, self.topright, width=self.outline)
        pygame.draw.line(surface, self.outline_color, self.bottomleft, self.bottomright, width=self.outline)

    def focus_drawing_function(self, surface: pygame.Surface, highlight_color: pygame.Color, highlight_thickness: int) -> None:
        pygame.draw.line(surface, highlight_color, self.topleft, self.topright, width=highlight_thickness)
        pygame.draw.line(surface, highlight_color, self.bottomleft, self.bottomright, width=highlight_thickness)

    def on_hover(self) -> None:
        self.focus_set()
        super().on_hover()
        self.__on_hover()

class AnimationStart(Window):

    def __init__(self, master):
        Window.__init__(self, master=master)
        self.master = master
        self.bg = RectangleShape(self.w, self.h, BLACK)

    def mainloop(self) -> int:
        milliseconds = 10
        self.logo = Image(RESOURCES.IMG["logo"])
        self.logo.midtop = self.midbottom
        self.logo.animate_move(self, milliseconds, speed=20, center=self.center)
        self.logo.animate_rotate(self, milliseconds, angle=360, angle_offset=10)
        self.logo.animate_resize_width(self, milliseconds, self.master.logo.width, offset=20)
        self.logo.center = self.center
        self.logo.animate_move(self, milliseconds, speed=20, left=10, top=10)

class PyGameCase(MainWindow):

    def __init__(self):
        super().__init__(size=(1280, 720), resources=RESOURCES)
        self.set_title("Py-Game-Case")
        self.set_icon(RESOURCES.IMG["icon"])

        TitleButton.set_default_theme("default")
        TitleButton.set_theme("default", {
            "font": ("calibri", 30),
            "bg": TRANSPARENT,
            "fg": WHITE,
            "outline": 0,
            "hover_bg": set_color_alpha(WHITE, 100),
            "active_bg": set_color_alpha(WHITE, 50),
            "highlight_color": WHITE,
            "highlight_thickness": 3,
            "x_add_size": self.w * 0.25,
            "y_add_size": 30,
            "justify": ("left", "center"),
            "offset": (10, 0),
            "hover_offset": (0, -5),
            "active_offset": (0, 10)
        })

        self.image_game_preview = Sprite()
        self.bg = DrawableListHorizontal()
        left_color = BLACK
        right_color = set_color_alpha(BLACK, 50)
        self.bg.add(
            RectangleShape(self.w * 0.25, self.h, left_color),
            HorizontalGradientShape(self.w * 0.5, self.h, left_color, right_color),
            RectangleShape(self.w * 0.25, self.h, right_color),
        )
        self.logo = Image(RESOURCES.IMG["logo"], width=self.bg[0].width)

        self.buttons = ButtonListVertical(offset=30)
        for game_id, game_name in GAMES.items():
            self.buttons.add(TitleButton(
                self, lambda game=game_id: self.show_preview(game), text=game_name,
                callback=lambda game=game_id: self.launch_game(game)
            ))
            self.image_game_preview.add_sprite(game_id, RESOURCES.IMG[game_id], size=self.size)
        self.game_id = None
        self.game_launched_processes = list()

        self.animation_start = AnimationStart(self)

    def place_objects(self) -> None:
        self.logo.move(left=10, top=10)
        self.buttons.move(left=10, top=self.logo.bottom + 50)
        self.image_game_preview.move(center=self.center)

    def on_start_loop(self):
        self.image_game_preview.move(right=self.left)
        self.animation_start.mainloop()
        self.buttons[0].focus_set()

    def update(self) -> None:
        for process in list(filter(lambda process: process.poll() is not None, self.game_launched_processes)):
            self.game_launched_processes.remove(process)

    def show_preview(self, game_id: str) -> None:
        if self.game_id == game_id:
            return
        self.game_id = game_id
        milliseconds = 1
        speed = 50
        self.image_game_preview.animate_move(self, milliseconds, speed=speed, right=self.left)
        self.image_game_preview.set_sprite(self.game_id)
        self.image_game_preview.animate_move(self, milliseconds, speed=speed, center=self.center)

    def launch_game(self, game_id: str) -> None:
        if sys.argv[0].endswith((".py", ".pyw")):
            args = [sys.executable, sys.argv[0], game_id]
        else:
            args = [sys.executable, game_id]
        process = subprocess.Popen(args, shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.game_launched_processes.append(process)