# -*- coding: Utf-8 -*

# import itertools
import pygame
from pygame.math import Vector2
from typing import Union, Iterable, Optional
from .surface import create_surface
from .drawable import Drawable
from .clock import Clock

class Sprite(Drawable, use_parent_theme=False):

    def __init__(self, *images: Union[pygame.Surface, Drawable], **kwargs):
        self.__list = [Drawable(image, **kwargs) for image in images]
        self.__resize = False
        Drawable.__init__(self, self.__list[0].image if self.__list else None)
        self.__resize = True
        self.__sprite_idx = 0
        self.__nb_sprites = len(self.__list)
        self.__clock = Clock()
        self.__wait_time = 0
        self.__animation = False
        self.__loop = False

    @classmethod
    def from_iterable(cls, iterable: Iterable[Union[pygame.Surface, Drawable]], **kwargs):
        return cls(*iterable, **kwargs)

    @classmethod
    def from_spritesheet(cls, img: pygame.Surface, rect_list: list[pygame.Rect], **kwargs) -> None:
        return cls.from_iterable((img.subsurface(rect).copy() for rect in rect_list), **kwargs)

    def get_sprite_list(self) -> list[Drawable]:
        return self.__list.copy()

    def resize(self, **kwargs) -> None:
        if self.__resize:
            for drawable in self.__list:
                drawable.resize(**kwargs)
        super().resize(**kwargs)

    def set_rotation(self, angle: float, point: Optional[Union[tuple[int, int], Vector2, str]]=None) -> None:
        for drawable in self.__list:
            drawable.set_rotation(angle, point)
        super().set_rotation(angle, point)

    @property
    def ratio(self) -> float:
        return self.__wait_time

    @ratio.setter
    def ratio(self, value: float) -> None:
        self.__wait_time = float(value)

    def animated_layers(self) -> bool:
        return bool(self.__animation and self.__nb_sprites > 0)

    def _before_drawing(self, surface: pygame.Surface) -> None:
        if self.animated_layers() and self.__clock.elapsed_time(self.__wait_time):
            self.__sprite_idx = (self.__sprite_idx + 1) % self.__nb_sprites
            self.image = self.__list[self.__sprite_idx]
            if self.__sprite_idx == 0 and not self.__loop:
                self.__animation = False

    def start_layer_animation(self, loop=False) -> None:
        self.__loop = bool(loop)
        self.__sprite_idx = 0
        self.__animation = True
        self.__clock.restart()

    def restart_layer_animation(self) -> None:
        self.__animation = True
        self.__clock.restart(reset=False)

    def stop_layer_animation(self) -> None:
        self.__animation = False

class SpriteDict(Sprite, use_parent_theme=False):

    def __init__(self):
        self.__sprite_dict = dict[str, Sprite]()
        self.__sprite_name = str()
        super().__init__()

    def get(self, name: str) -> Sprite:
        return self.__sprite_dict[str(name)]

    def set(self, name: str, sprite: Sprite):
        if isinstance(sprite, Sprite):
            self.__sprite_dict[str(name)] = sprite

    __getitem__ = get
    __setitem__ = set

    def get_actual_sprite(self) -> Union[Sprite, None]:
        return self.__sprite_dict.get(self.__sprite_name)

    def get_actual_sprite_name(self) -> str:
        return self.__sprite_name

    def use_sprite(self, name: str) -> None:
        self.animate_stop()
        self.stop_layer_animation()
        if self.__sprite_name in self.__sprite_dict:
            self.__sprite_dict[self.__sprite_name].animate_stop()
            self.__sprite_dict[self.__sprite_name].stop_layer_animation()
        self.__sprite_name = str(name)
        if self.__sprite_name in self.__sprite_dict:
            former_move = self.get_move()
            super().__init__(*self.__sprite_dict[self.__sprite_name].get_sprite_list())
            self.move(**former_move)
        else:
            self.image = create_surface((0, 0))

    def move(self, **kwargs) -> None:
        for sprite in self.__sprite_dict.values():
            sprite.move(**kwargs)
        super().move(**kwargs)

    def move_ip(self, x: float, y: float) -> None:
        for sprite in self.__sprite_dict.values():
            sprite.move_ip(x, y)
        super().move_ip(x, y)

    def resize(self, **kwargs) -> None:
        for sprite in self.__sprite_dict.values():
            sprite.resize(**kwargs)
        super().resize(**kwargs)

    def rotate(self, angle: float, point: Optional[Union[tuple[int, int], Vector2, str]]=None) -> None:
        for sprite in self.__sprite_dict.values():
            sprite.rotate(angle, point)
        super().rotate(angle, point)

    def set_rotation(self, angle: float, point: Optional[Union[tuple[int, int], Vector2, str]]=None) -> None:
        for sprite in self.__sprite_dict.values():
            sprite.set_rotation(angle, point)
        super().set_rotation(angle, point)
