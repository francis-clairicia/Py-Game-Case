# -*- coding: Utf-8 -*

import os.path
import textwrap
from typing import Tuple
import pygame
from pygame.font import Font, SysFont
from .surface import create_surface
from .drawable import Drawable
from .image import Image
from .colors import BLACK

class Text(Drawable, use_parent_theme=False):

    T_LEFT = "left"
    T_RIGHT = "right"
    T_CENTER = "center"

    def __init__(self, message=str(), font=None, color=BLACK, wrap=0,
                 justify="left", shadow=False, shadow_x=0, shadow_y=0, shadow_color=BLACK,
                 img=None, compound="left", theme=None):
        Drawable.__init__(self)
        self.__str = str()
        self.__wrap = 0
        self.__font = None
        self.__custom_font = dict()
        self.__color = BLACK
        self.__img = None
        self.__compound = self.__justify = "left"
        self.__shadow = (0, 0)
        self.__shadow_surface = Text(message=self.__str, font=self.font, color=BLACK, shadow=False) if shadow else None
        self.__shadow_color = BLACK
        self.shadow_color = shadow_color
        self.config(message=message, font=font, color=color, img=img, justify=justify, compound=compound, wrap=wrap, shadow=(shadow_x, shadow_y))
        self.__update_surface()

    @property
    def font(self) -> Font:
        return self.__font

    @font.setter
    def font(self, font) -> None:
        self.config(font=font)

    @property
    def message(self) -> str:
        return self.__str

    @message.setter
    def message(self, string: str) -> None:
        self.config(message=string)

    @property
    def wrap(self) -> str:
        return self.__wrap

    @wrap.setter
    def wrap(self, wrap: str) -> None:
        self.config(wrap=wrap)

    @property
    def img(self) -> Image:
        return self.__img

    @img.setter
    def img(self, img) -> None:
        self.config(img=img)

    @property
    def compound(self) -> str:
        return self.__compound

    @compound.setter
    def compound(self, value: str) -> None:
        self.config(compound=value)

    @property
    def justify(self) -> str:
        return self.__justify

    @justify.setter
    def justify(self, value: str) -> None:
        self.config(justify=value)

    @property
    def color(self) -> pygame.Color:
        return self.__color

    @color.setter
    def color(self, color: pygame.Color) -> None:
        self.config(color=color)

    @property
    def shadow(self) -> Tuple[int, int]:
        return self.__shadow

    @shadow.setter
    def shadow(self, pos: Tuple[int, int]) -> None:
        self.config(shadow=pos)

    @property
    def shadow_color(self) -> pygame.Color:
        return self.__shadow_color

    @shadow_color.setter
    def shadow_color(self, color: pygame.Color) -> None:
        self.__shadow_color = pygame.Color(color)
        if self.__shadow_surface:
            self.__shadow_surface.color = color

    @staticmethod
    def create_font_object(font) -> Font:
        obj = None
        if isinstance(font, (tuple, list)):
            if font[0] is not None and os.path.isfile(font[0]):
                obj = Font(*font[0:2])
                if "bold" in font:
                    obj.set_bold(True)
                if "italic" in font:
                    obj.set_italic(True)
            else:
                obj = SysFont(*font[0:2], bold=bool("bold" in font), italic=bool("italic" in font))
            if "underline" in font:
                obj.set_underline(True)
        elif isinstance(font, Font):
            obj = font
        else:
            obj = SysFont(pygame.font.get_default_font(), 15)
        return obj

    def config(self, **kwargs) -> None:
        config_for_shadow = dict()
        if "wrap" in kwargs:
            self.__wrap = max(int(kwargs["wrap"]), 0)
            config_for_shadow["message"] = self.__str = "\n".join(textwrap.wrap(self.__str, width=self.__wrap)) if self.__wrap > 0 else self.__str
        if "message" in kwargs:
            config_for_shadow["message"] = self.__str = "\n".join(textwrap.wrap(str(kwargs["message"]), width=self.__wrap)) if self.__wrap > 0 else str(kwargs["message"])
        if "font" in kwargs:
            config_for_shadow["font"] = self.__font = self.create_font_object(kwargs["font"])
        if "color" in kwargs:
            self.__color = pygame.Color(kwargs["color"])
        if "justify" in kwargs and kwargs["justify"] in ("left", "right", "center"):
            config_for_shadow["justify"] = self.__justify = kwargs["justify"]
        if "img" in kwargs:
            if isinstance(kwargs["img"], Image):
                self.__img = kwargs["img"]
            else:
                self.__img = None
        if "compound" in kwargs and kwargs["compound"] in ("left", "right", "center"):
            self.__compound = kwargs["compound"]
        if "shadow" in kwargs:
            self.__shadow = kwargs["shadow"]
            if self.__shadow_surface:
                self.__shadow_surface.set_visibility(any(value != 0 for value in self.__shadow[0:2]))
        self.__update_surface()
        if self.__shadow_surface:
            self.__shadow_surface.config(**config_for_shadow)

    def before_drawing(self, surface: pygame.Surface) -> None:
        if self.__shadow_surface and self.__shadow_surface.is_shown():
            self.__shadow_surface.move(x=self.x + self.shadow[0], y=self.y + self.shadow[1])
            self.__shadow_surface.draw(surface)

    def set_custom_line_font(self, index: int, font) -> None:
        self.__custom_font[index] = self.create_font_object(font)
        self.__update_surface()

    def remove_custom_line_font(self, index: int) -> None:
        self.__custom_font.pop(index, None)
        self.__update_surface()

    def __update_surface(self) -> None:
        render_lines = list()
        size = [0, 0]
        for index, line in enumerate(self.message.splitlines()):
            font = self.__custom_font.get(index, self.font)
            render = font.render(line, True, self.color)
            size[0] = max(size[0], render.get_width())
            size[1] += render.get_height()
            render_lines.append(render)
        if render_lines:
            text = create_surface(size)
            text.fill((0, 0, 0, 0))
            text_rect = text.get_rect()
            y = 0
            justify_parameters = {
                Text.T_LEFT:    {"left": text_rect.left},
                Text.T_RIGHT:   {"right": text_rect.right},
                Text.T_CENTER:  {"centerx": text_rect.centerx},
            }
            params = justify_parameters[self.justify]
            for render in render_lines:
                text.blit(render, render.get_rect(**params, y=y))
                y += render.get_height()
        else:
            text = create_surface((0, 0))
        if not isinstance(self.img, Image):
            self.image = text
            return
        function_to_get_size = {
            "left": {"width": sum, "height": max},
            "right": {"width": sum, "height": max},
            "top": {"width": max, "height": sum},
            "bottom": {"width": max, "height": sum},
            "center": {"width": max, "height": max},
        }
        size = {"width": 0, "height": 0}
        for field in size:
            size[field] = function_to_get_size[self.compound][field](getattr(obj, field) for obj in [text.get_rect(), self.img.rect])
        w = size["width"] + (5 if text.get_width() > 0 and self.img.width > 0 else 0)
        h = size["height"]
        surface_to_draw = create_surface((w, h))
        rect_to_draw = surface_to_draw.get_rect()
        move_text = {
            "left": {"right": rect_to_draw.right, "centery": rect_to_draw.centery},
            "right": {"left": rect_to_draw.left, "centery": rect_to_draw.centery},
            "top": {"bottom": rect_to_draw.bottom, "centerx": rect_to_draw.centerx},
            "bottom": {"top": rect_to_draw.bottom, "centerx": rect_to_draw.centerx},
            "center": {"center": rect_to_draw.center}
        }
        move_img = {
            "left": {"left": rect_to_draw.left, "centery": rect_to_draw.centery},
            "right": {"right": rect_to_draw.right, "centery": rect_to_draw.centery},
            "top": {"top": rect_to_draw.bottom, "centerx": rect_to_draw.centerx},
            "bottom": {"bottom": rect_to_draw.bottom, "centerx": rect_to_draw.centerx},
            "center": {"center": rect_to_draw.center}
        }
        self.img.move(**move_img[self.compound])
        self.img.draw(surface_to_draw)
        surface_to_draw.blit(text, text.get_rect(**move_text[self.compound]))
        self.image = surface_to_draw