# -*- coding: Utf-8 -*

import itertools
from typing import Union
import pygame
from .surface import create_surface
from .drawable import Drawable
from .image import Image
from .clock import Clock

class Sprite(Drawable, use_parent_theme=False):

    def __init__(self):
        Drawable.__init__(self)
        self.__sprites = dict()
        self.__sprite_list = list()
        self.__sprite_list_name = str()
        self.__nb_sprites = 0
        self.__sprite_idx = 0
        self.__clock = Clock()
        self.__wait_time = 0
        self.__animation = False
        self.__loop = False

    def get_sprite_dict(self) -> dict[str, list[Image]]:
        return self.__sprites

    def get_actual_sprite_list(self) -> list[Image]:
        return self.__sprite_list

    def get_actual_sprite_list_name(self) -> str:
        return self.__sprite_list_name

    def get_sprite_list(self, name: str) -> list[Image]:
        return self.__sprites.get(str(name), list())

    def get_all_sprites(self) -> list[Image]:
        return list(itertools.chain.from_iterable(self.__sprites.values()))

    def add_sprite(self, name: str, img: pygame.Surface, set_sprite=False, **kwargs) -> None:
        self.add_sprite_list(name, [img], set_sprite_list=set_sprite, **kwargs)

    def add_sprite_list(self, name: str, img_list: list[pygame.Surface], set_sprite_list=False, **kwargs) -> None:
        if not img_list or any(not isinstance(obj, pygame.Surface) for obj in img_list):
            return
        name = str(name)
        self.__sprites[name] = sprite_list = list()
        for surface in img_list:
            sprite_list.append(Image(surface, **kwargs))
        if set_sprite_list or self.__nb_sprites == 0:
            self.set_sprite_list(name)

    def add_spritesheet(self, name: str, img: pygame.Surface, rect_list: list[pygame.Rect], set_sprite_list=False, **kwargs) -> None:
        if not isinstance(img, pygame.Surface) or not rect_list:
            return
        self.add_sprite_list(name, [img.subsurface(rect) for rect in rect_list], set_sprite_list=set_sprite_list, **kwargs)

    def set_sprite(self, name: str) -> None:
        self.set_sprite_list(name)

    def set_sprite_list(self, name: str) -> None:
        self.__sprite_list = self.get_sprite_list(name)
        self.__nb_sprites = len(self.__sprite_list)
        self.__sprite_idx = 0
        if self.__nb_sprites > 0:
            self.image = self.__sprite_list[0]
            self.__sprite_list_name = str(name)
        else:
            self.image = create_surface((0, 0))
            self.__sprite_list_name = str()

    def resize_sprite_list(self, name: str, **kwargs) -> None:
        for sprite in self.get_sprite_list(name):
            sprite.image = sprite.surface_resize(sprite.image, **kwargs)

    def resize_all_sprites(self, **kwargs) -> None:
        for sprite in self.get_all_sprites():
            sprite.image = sprite.surface_resize(sprite.image, **kwargs)
        self.image = self.surface_resize(self.image, **kwargs)

    def set_size(self, *size, smooth=True) -> None:
        pass

    def set_width(self, width: float, smooth=True)-> None:
        pass

    def set_height(self, height: float, smooth=True) -> None:
        pass

    @property
    def ratio(self) -> float:
        return self.__wait_time

    @ratio.setter
    def ratio(self, value: float) -> None:
        self.__wait_time = float(value)

    def animated(self) -> bool:
        return bool(self.__animation and self.__nb_sprites > 0)

    def before_drawing(self, surface: pygame.Surface) -> None:
        if self.animated() and self.__clock.elapsed_time(self.__wait_time):
            self.__sprite_idx = (self.__sprite_idx + 1) % self.__nb_sprites
            self.image = self.__sprite_list[self.__sprite_idx]
            if self.__sprite_idx == 0 and not self.__loop:
                self.__animation = False

    def start_animation(self, loop=False) -> None:
        self.__loop = bool(loop)
        self.__sprite_idx = 0
        self.restart_animation()

    def restart_animation(self) -> None:
        self.__animation = True
        self.__clock.tick()

    def stop_animation(self) -> None:
        self.__animation = False