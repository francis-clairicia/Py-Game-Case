# -*- coding: Utf-8 -*

from typing import List, Tuple, Union
import pygame
from pygame.math import Vector2
from .drawable import Drawable
from .colors import TRANSPARENT, BLACK

class Shape(Drawable, use_parent_theme=False):

    def __init__(self, color: pygame.Color, outline: int, outline_color: pygame.Color, theme=None):
        Drawable.__init__(self)
        self.color = color
        self.outline = outline
        self.outline_color = outline_color

    @property
    def color(self) -> pygame.Color:
        return self.__color

    @color.setter
    def color(self, value: pygame.Color) -> None:
        self.__color = pygame.Color(value) if value is not None else TRANSPARENT

    @property
    def outline(self) -> int:
        return self.__outline

    @outline.setter
    def outline(self, value: int) -> None:
        self.__outline = int(value)
        if self.__outline < 0:
            self.__outline = 0

    @property
    def outline_color(self) -> pygame.Color:
        return self.__outline_color

    @outline_color.setter
    def outline_color(self, value: pygame.Color) -> None:
        self.__outline_color = pygame.Color(value) if value is not None else TRANSPARENT

    def set_size(self, *size: Union[int, Tuple[int, int]], smooth=True) -> None:
        Drawable.set_size(self, *size, smooth=False)

    def set_width(self, width: float, smooth=True)-> None:
        Drawable.set_width(self, width, smooth=False)

    def set_height(self, height: float, smooth=True) -> None:
        Drawable.set_height(self, height, smooth=False)

class PolygonShape(Shape):

    def __init__(self, color: pygame.Color, outline=0, outline_color=BLACK, points=list(), theme=None):
        Shape.__init__(self, color=color, outline=outline, outline_color=outline_color)
        self.__points = list()
        self.__image_points = list()
        self.__image_points_percent = list()
        self.points = points

    @property
    def points(self) -> List[Vector2]:
        return self.__points.copy()

    @points.setter
    def points(self, points: List[Union[Tuple[int, int], Vector2]]) -> None:
        self.__points = points = [Vector2(point) for point in points]
        left = min((point.x for point in points), default=0)
        right = max((point.x for point in points), default=0)
        top = min((point.y for point in points), default=0)
        bottom = max((point.y for point in points), default=0)
        self.__image_points = [Vector2(point.x - left, point.y - top) for point in points]
        Shape.set_size(self, right - left, bottom - top)
        Shape.move(self, left=left, top=top)
        self.__image_points_percent = [
            ((point.x / self.width if self.width != 0 else 0), (point.y / self.height if self.height != 0 else 0))
            for point in self.__image_points
        ]

    def before_drawing(self, surface: pygame.Surface) -> None:
        self.image.fill(TRANSPARENT)
        if len(self.points) > 2:
            pygame.draw.polygon(self.image, self.color, self.__image_points)
        self.mask_update()

    def after_drawing(self, surface: pygame.Surface) -> None:
        if self.outline > 0:
            if len(self.points) > 2:
                pygame.draw.polygon(surface, self.outline_color, self.points, width=self.outline)
            elif len(self.points) == 2:
                pygame.draw.line(surface, self.color, *self.points, width=self.outline)

    def focus_drawing_function(self, surface: pygame.Surface, highlight_color: pygame.Color, highlight_thickness: int) -> None:
        if len(self.points) > 2:
            pygame.draw.polygon(surface, highlight_color, self.points, width=highlight_thickness)
        elif len(self.points) == 2:
            pygame.draw.line(surface, highlight_color, *self.points, width=highlight_thickness)

    def move(self, **kwargs) -> None:
        Shape.move(self, **kwargs)
        self.__points = [Vector2(point.x + self.x, point.y + self.y) for point in self.__image_points]

    def move_ip(self, x: float, y: float) -> None:
        Shape.move_ip(self, x, y)
        for point in self.points:
            point.x += x
            point.y += y

    def set_size(self, *size: Union[int, Tuple[int, int]], smooth=True) -> None:
        Shape.set_size(self, *size, smooth=smooth)
        self.__update_points_on_resize()

    def set_width(self, width: float, smooth=True)-> None:
        Shape.set_width(self, width, smooth=smooth)
        self.__update_points_on_resize()

    def set_height(self, height: float, smooth=True) -> None:
        Shape.set_height(self, height, smooth=smooth)
        self.__update_points_on_resize()

    def __update_points_on_resize(self) -> None:
        self.__image_points = [Vector2(self.width * x, self.height * y) for x, y in self.__image_points_percent]
        self.move()

class RectangleShape(Shape):

    def __init__(self, width: int, height: int, color: pygame.Color, outline=0, outline_color=BLACK,
                 border_radius=0, border_top_left_radius=-1, border_top_right_radius=-1,
                 border_bottom_left_radius=-1, border_bottom_right_radius=-1, theme=None):
        Shape.__init__(self, color=color, outline=outline, outline_color=outline_color)
        Shape.set_size(self, width, height)
        self.__draw_params = {
            "border_radius": border_radius,
            "border_top_left_radius": border_top_left_radius,
            "border_top_right_radius": border_top_right_radius,
            "border_bottom_left_radius": border_bottom_left_radius,
            "border_bottom_right_radius": border_bottom_right_radius
        }

    def before_drawing(self, surface: pygame.Surface) -> None:
        self.image.fill(TRANSPARENT)
        pygame.draw.rect(self.image, self.color, self.image.get_rect(), **self.__draw_params)
        self.mask_update()

    def after_drawing(self, surface: pygame.Surface) -> None:
        if self.outline > 0:
            pygame.draw.rect(surface, self.outline_color, self.rect, width=self.outline, **self.__draw_params)

    def focus_drawing_function(self, surface: pygame.Surface, highlight_color: pygame.Color, highlight_thickness: int) -> None:
        pygame.draw.rect(surface, highlight_color, self.rect, width=highlight_thickness, **self.__draw_params)

    def config(self, **kwargs) -> None:
        for key, value in filter(lambda key, value: key in self.__draw_params, kwargs.items()):
            self.__draw_params[key] = int(value)

    border_radius = property(
        lambda self: self.__draw_params["border_radius"],
        lambda self, value: self.config(border_radius=value)
    )
    border_top_left_radius = property(
        lambda self: self.__draw_params["border_top_left_radius"],
        lambda self, value: self.config(border_top_left_radius=value)
    )
    border_top_right_radius = property(
        lambda self: self.__draw_params["border_top_right_radius"],
        lambda self, value: self.config(border_top_right_radius=value)
    )
    border_bottom_left_radius = property(
        lambda self: self.__draw_params["border_bottom_left_radius"],
        lambda self, value: self.config(border_bottom_left_radius=value)
    )
    border_bottom_right_radius = property(
        lambda self: self.__draw_params["border_bottom_right_radius"],
        lambda self, value: self.config(border_bottom_right_radius=value)
    )

class CircleShape(Shape):

    def __init__(self, radius: int, color: pygame.Color, outline=0, outline_color=BLACK,
                 draw_top_left=True, draw_top_right=True,
                 draw_bottom_left=True, draw_bottom_right=True, theme=None):
        Shape.__init__(self, color=color, outline=outline, outline_color=outline_color)
        self.radius = radius
        self.__draw_params = {
            "draw_top_left": draw_top_left,
            "draw_top_right": draw_top_right,
            "draw_bottom_left": draw_bottom_left,
            "draw_bottom_right": draw_bottom_right
        }

    @property
    def radius(self) -> int:
        return self.__radius

    @radius.setter
    def radius(self, value: int) -> None:
        self.__radius = int(value)
        if self.__radius < 0:
            self.__radius = 0
        Shape.set_size(self, self.__radius * 2)

    def before_drawing(self, surface: pygame.Surface) -> None:
        self.image.fill(TRANSPARENT)
        pygame.draw.circle(self.image, self.color, (self.radius, self.radius), self.radius, **self.__draw_params)
        self.mask_update()

    def after_drawing(self, surface: pygame.Surface) -> None:
        if self.outline > 0:
            pygame.draw.circle(surface, self.outline_color, self.center, self.radius, width=self.outline, **self.__draw_params)

    def focus_drawing_function(self, surface: pygame.Surface, highlight_color: pygame.Color, highlight_thickness: int) -> None:
        pygame.draw.circle(surface, highlight_color, self.center, self.radius, width=highlight_thickness, **self.__draw_params)

    def config(self, **kwargs) -> None:
        for key, value in filter(lambda key, value: key in self.__draw_params, kwargs.items()):
            self.__draw_params[key] = bool(value)

    def set_size(self, *size: Union[int, Tuple[int, int]], smooth=True) -> None:
        Shape.set_size(self, *size, smooth=smooth)
        self.__update_on_resize()

    def set_width(self, width: float, smooth=True)-> None:
        Shape.set_width(self, width, smooth=smooth)
        self.__update_on_resize()

    def set_height(self, height: float, smooth=True) -> None:
        Shape.set_height(self, height, smooth=smooth)
        self.__update_on_resize()

    def __update_on_resize(self) -> None:
        self.radius = self.width / 2

    draw_top_left = property(
        lambda self: self.__draw_params["draw_top_left"],
        lambda self, value: self.config(draw_top_left=value)
    )
    draw_top_right = property(
        lambda self: self.__draw_params["draw_top_right"],
        lambda self, value: self.config(draw_top_right=value)
    )
    draw_bottom_left = property(
        lambda self: self.__draw_params["draw_bottom_left"],
        lambda self, value: self.config(draw_bottom_left=value)
    )
    draw_bottom_right = property(
        lambda self: self.__draw_params["draw_bottom_right"],
        lambda self, value: self.config(draw_bottom_right=value)
    )