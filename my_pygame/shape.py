# -*- coding: Utf-8 -*

from typing import List, Tuple, Union, Callable
import pygame
from pygame.math import Vector2
from .drawable import Drawable
from .colors import TRANSPARENT, BLACK
from .surface import create_surface
from .gradients import horizontal, vertical, radial, squared

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
        self.shape_update()

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
        Drawable.set_size(self, *(size), smooth=False)
        self.shape_update()

    def set_width(self, width: float, smooth=True)-> None:
        Drawable.set_width(self, width, smooth=False)
        self.shape_update()

    def set_height(self, height: float, smooth=True) -> None:
        Drawable.set_height(self, height, smooth=False)
        self.shape_update()

    def shape_update(self) -> None:
        pass

class PolygonShape(Shape):

    def __init__(self, color: pygame.Color, *, outline=0, outline_color=BLACK, points=list(), theme=None):
        self.__points = list()
        self.__image_points = list()
        self.__image_points_percent = list()
        Shape.__init__(self, color=color, outline=outline, outline_color=outline_color)
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
        self.shape_update()

    def shape_update(self) -> None:
        self.__image_points = [Vector2(self.width * x, self.height * y) for x, y in self.__image_points_percent]
        self.move()
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

class RectangleShape(Shape):

    def __init__(self, width: int, height: int, color: pygame.Color, *, outline=0, outline_color=BLACK,
                 border_radius=0, border_top_left_radius=-1, border_top_right_radius=-1,
                 border_bottom_left_radius=-1, border_bottom_right_radius=-1, theme=None):
        self.__draw_params = {
            "border_radius": border_radius,
            "border_top_left_radius": border_top_left_radius,
            "border_top_right_radius": border_top_right_radius,
            "border_bottom_left_radius": border_bottom_left_radius,
            "border_bottom_right_radius": border_bottom_right_radius
        }
        Shape.__init__(self, color=color, outline=outline, outline_color=outline_color)
        self.set_size(width, height)

    def shape_update(self) -> None:
        self.image = create_surface(self.size)
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

    def __init__(self, radius: int, color: pygame.Color, *, outline=0, outline_color=BLACK,
                 draw_top_left=True, draw_top_right=True,
                 draw_bottom_left=True, draw_bottom_right=True, theme=None):
        self.__radius = 0
        self.__draw_params = {
            "draw_top_left": draw_top_left,
            "draw_top_right": draw_top_right,
            "draw_bottom_left": draw_bottom_left,
            "draw_bottom_right": draw_bottom_right
        }
        Shape.__init__(self, color=color, outline=outline, outline_color=outline_color)
        self.radius = radius

    @property
    def radius(self) -> int:
        return self.__radius

    @radius.setter
    def radius(self, value: int) -> None:
        self.set_size(max(int(value), 0) * 2)

    def shape_update(self) -> None:
        self.__radius = min(self.width // 2, self.height // 2)
        self.image = create_surface(self.size)
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
        size = size if len(size) == 2 else size[0]
        if isinstance(size, (int, float)):
            size = int(size), int(size)
        Shape.set_size(self, min(size), smooth=smooth)

    def set_width(self, width: float, smooth=True)-> None:
        Shape.set_size(self, width, smooth=smooth)

    def set_height(self, height: float, smooth=True) -> None:
        Shape.set_size(self, height, smooth=smooth)

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

class GradientShape(Drawable, use_parent_theme=False):

    TYPE_HORIZONTAL = horizontal
    TYPE_VERTICAL = vertical
    TYPE_RADIAL = radial
    TYPE_SQUARED = squared

    def __init__(self, left_color: pygame.Color, right_color: pygame.Color, gradient_type: Callable[..., None]):
        Drawable.__init__(self)
        self.__left_color = TRANSPARENT
        self.__right_color = TRANSPARENT
        self.__gradient_type = gradient_type
        self.left_color = left_color
        self.right_color = right_color

    @property
    def left_color(self) -> pygame.Color:
        return self.__left_color

    @left_color.setter
    def left_color(self, color: pygame.Color) -> None:
        self.__left_color = pygame.Color(color)
        self.__update_image()

    @property
    def right_color(self) -> pygame.Color:
        return self.__right_color

    @right_color.setter
    def right_color(self, color: pygame.Color) -> None:
        self.__right_color = pygame.Color(color)
        self.__update_image()

    def __update_image(self) -> None:
        if self.w > 0 and self.h > 0:
            start_color = (self.left_color.r, self.left_color.g, self.left_color.b, self.left_color.a)
            end_color = (self.right_color.r, self.right_color.g, self.right_color.b, self.right_color.a)
            if self.__gradient_type == self.TYPE_RADIAL:
                size = min(self.width // 2, self.height // 2)
            else:
                size = self.size
            self.image = self.__gradient_type(size, start_color, end_color)

    def set_size(self, *size: Union[int, Tuple[int, int]], smooth=True) -> None:
        Drawable.set_size(self, *size, smooth=False)
        self.__update_image()

    def set_width(self, width: float, smooth=True)-> None:
        Drawable.set_width(self, width, smooth=False)
        self.__update_image()

    def set_height(self, height: float, smooth=True) -> None:
        Drawable.set_height(self, height, smooth=False)
        self.__update_image()

class HorizontalGradientShape(GradientShape, use_parent_theme=False):

    def __init__(self, width: int, height: int, left_color: pygame.Color, right_color: pygame.Color):
        super().__init__(left_color, right_color, GradientShape.TYPE_HORIZONTAL)
        self.set_size(width, height)

class VerticalGradientShape(GradientShape, use_parent_theme=False):

    def __init__(self, width: int, height: int, left_color: pygame.Color, right_color: pygame.Color):
        super().__init__(left_color, right_color, GradientShape.TYPE_VERTICAL)
        self.set_size(width, height)

class SquaredGradientShape(GradientShape, use_parent_theme=False):

    def __init__(self, width: int, height: int, left_color: pygame.Color, right_color: pygame.Color):
        super().__init__(left_color, right_color, GradientShape.TYPE_SQUARED)
        self.set_size(width, height)

class RadialGradientShape(GradientShape, use_parent_theme=False):

    def __init__(self, radius: int, left_color: pygame.Color, right_color: pygame.Color):
        super().__init__(left_color, right_color, GradientShape.TYPE_RADIAL)
        self.__radius = 0
        self.radius = radius

    @property
    def radius(self) -> int:
        return self.__radius

    @radius.setter
    def radius(self, value: int) -> None:
        self.__radius = int(value)
        if self.__radius < 0:
            self.__radius = 0
        GradientShape.set_size(self, self.__radius * 2)

    def set_size(self, *size: Union[int, Tuple[int, int]], smooth=True) -> None:
        GradientShape.set_size(self, *size, smooth=smooth)
        self.__update_on_resize()

    def set_width(self, width: float, smooth=True)-> None:
        GradientShape.set_width(self, width, smooth=smooth)
        self.__update_on_resize()

    def set_height(self, height: float, smooth=True) -> None:
        GradientShape.set_height(self, height, smooth=smooth)
        self.__update_on_resize()

    def __update_on_resize(self) -> None:
        self.__radius = min(self.width // 2, self.height // 2)