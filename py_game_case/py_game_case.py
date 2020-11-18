# -*- coding: Utf-8 -*

import sys
import subprocess
from typing import Callable
import pygame
from my_pygame import MainWindow, Window, Image, Button, Sprite, RectangleShape, HorizontalGradientShape
from my_pygame import ButtonListVertical, DrawableListHorizontal
from my_pygame import Clickable
from my_pygame import TRANSPARENT, WHITE, BLACK, YELLOW
from my_pygame import set_color_alpha, change_brightness
from .constants import RESOURCES, GAMES
from .settings import Settings

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

class SettingsButton(Button):

    @property
    def color(self) -> pygame.Color:
        return TRANSPARENT

    @color.setter
    def color(self, color: pygame.Color) -> None:
        self.outline_color = color

    def after_drawing(self, surface: pygame.Surface) -> None:
        pygame.draw.line(surface, self.outline_color, self.topleft, self.topright, width=self.outline)
        pygame.draw.line(surface, self.outline_color, self.midleft, self.midright, width=self.outline)
        pygame.draw.line(surface, self.outline_color, self.bottomleft, self.bottomright, width=self.outline)

class PyGameCase(MainWindow):

    def __init__(self):
        super().__init__(size=(1280, 720), bg_color=(0, 0, 100), resources=RESOURCES)
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
        SettingsButton.set_default_theme("default")
        SettingsButton.set_theme("default", {
            "bg": WHITE,
            "hover_bg": YELLOW,
            "active_bg": change_brightness(YELLOW, -75),
            "outline": 7,
            "outline_color": WHITE,
            "highlight_thickness": 0
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

        self.buttons_game_launch = ButtonListVertical(offset=30)
        for game_id, game_name in GAMES.items():
            self.buttons_game_launch.add(TitleButton(
                self, lambda game=game_id: self.show_preview(game), text=game_name,
                callback=lambda game=game_id: self.launch_game(game)
            ))
            self.image_game_preview.add_sprite(game_id, RESOURCES.IMG[game_id], size=self.size)
        self.game_id = None
        self.game_launched_processes = list()

        self.settings_section = Settings(self)

        self.button_settings = SettingsButton(self, size=40, callback=self.settings_section.mainloop)
        self.button_settings.force_use_highlight_thickness(True)

    def place_objects(self) -> None:
        self.bg.center = self.center
        self.logo.move(left=10, top=10)
        self.buttons_game_launch.move(left=10, top=self.logo.bottom + 50)
        self.image_game_preview.center = self.center
        self.button_settings.move(right=self.right - 20, top=20)

    def set_grid(self) -> None:
        self.button_settings.set_obj_on_side(on_bottom=self.buttons_game_launch[0], on_left=self.buttons_game_launch[0])
        self.buttons_game_launch.set_obj_on_side(on_top=self.button_settings, on_right=self.button_settings)

    def on_start_loop(self):
        self.image_game_preview.right = self.left
        save_objects_center = list()
        for obj in self.objects.drawable:
            save_objects_center.append(obj.center)
        self.buttons_game_launch.right = self.left
        for obj in [self.logo, self.button_settings]:
            obj.hide()
        logo = Image(RESOURCES.IMG["logo"])
        logo.midtop = self.midbottom
        self.objects.add(logo)
        logo.animate_move(self, speed=20, center=self.center)
        logo.animation.rotate(angle=360, offset=5).scale_width(self.logo.width, offset=7).start(self)
        logo.center = self.center
        logo.animate_move(self, speed=20, left=10, top=10)
        self.objects.remove(logo)
        self.logo.show()
        for obj, center in zip(self.objects.drawable, save_objects_center):
            obj.animate_move(self, speed=20, center=center)
        self.show_all()
        self.focus_mode(Button.MODE_KEY)

    def update(self) -> None:
        for process in list(filter(lambda process: process.poll() is not None, self.game_launched_processes)):
            self.game_launched_processes.remove(process)
        if all(not button.has_focus() and not button.hover for button in self.buttons_game_launch) and self.game_id is not None:
            self.image_game_preview.animate_move(self, speed=75, right=self.left)
            self.game_id = None

    def show_preview(self, game_id: str) -> None:
        if self.game_id == game_id:
            return
        self.game_id = game_id
        speed = 100
        self.image_game_preview.animate_move(self, speed=speed, right=self.left)
        self.image_game_preview.set_sprite(self.game_id)
        self.image_game_preview.animate_move(self, speed=speed, center=self.center)

    def launch_game(self, game_id: str) -> None:
        if sys.argv[0].endswith((".py", ".pyw")):
            args = [sys.executable, sys.argv[0], game_id]
        else:
            args = [sys.executable, game_id]
        process = subprocess.Popen(args, shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.game_launched_processes.append(process)

    def close(self) -> None:
        if self.game_launched_processes:
            if pygame.display.get_active():
                pygame.display.iconify()
        else:
            self.stop(force=True)