# -*- coding: Utf-8 -*

from typing import Callable, Union, Tuple
from pygame import Surface, Rect
from pygame.math import Vector2
from .drawable import Drawable
from .window import Window

class AnimationMove:

    def __init__(self, master: Window, drawable: Drawable):
        self.__master = master
        self.__drawable = drawable
        self.__animation_started = False
        self.__window_callback = None

    def stop(self) -> None:
        self.__animation_started = False
        self.__master.remove_window_callback(self.__window_callback)

    def started(self) -> bool:
        return self.__animation_started

    def __call__(self, milliseconds: float, speed=1, after_move=None, **kwargs) -> None:
        if self.__animation_started:
            self.stop()
        if milliseconds <= 0 or speed <= 0:
            self.__drawable.move(**kwargs)
            if callable(after_move):
                after_move()
        else:
            self.__animation_started = True
            self.__animate(milliseconds, speed, after_move, kwargs)

    def __animate(self, milliseconds: float, speed: int, after_move: Callable[..., None], kwargs: dict) -> None:
        if not self.__animation_started:
            return
        projection = Drawable(self.__drawable.image)
        projection.move(**kwargs)
        direction = Vector2(projection.center) - Vector2(self.__drawable.center)
        if speed >= direction.length():
            self.__drawable.move(**kwargs)
            self.__animation_started = False
            if callable(after_move):
                after_move()
        else:
            direction.scale_to_length(speed)
            self.__drawable.move_ip(direction.x, direction.y)
            self.__window_callback = self.__master.after(milliseconds, lambda: self.__animate(milliseconds, speed, after_move, kwargs))

class AnimationRotation:

    def __init__(self, master: Window, drawable: Drawable):
        self.__master = master
        self.__drawable = drawable
        self.__animation_started = False
        self.__window_callback = None

    def stop(self) -> None:
        self.__animation_started = False
        self.__master.remove_window_callback(self.__window_callback)

    def started(self) -> bool:
        return self.__animation_started

    def __call__(self, milliseconds: float, angle: float, angle_offset=1, point=None, after_move=None) -> None:
        if self.__animation_started:
            self.stop()
        if point is None:
            point = self.__drawable.center
        if milliseconds <= 0:
            self.__drawable.rotate_through_point(angle, point)
            if callable(after_move):
                after_move()
        else:
            self.__animation_started = True
            angle_offset = abs(angle_offset) * (angle / abs(angle))
            self.__animate(self.__drawable.image, self.__drawable.rect, milliseconds, angle, angle_offset, 0, point, after_move)

    def __animate(self, default_surface: Surface, default_rect: Rect, milliseconds: float,
                  angle: float, angle_offset: float, actual_angle: float,
                  point: Union[Tuple[int, int], Vector2], after_move: Callable[..., None]) -> None:
        if not self.__animation_started:
            return
        actual_angle += angle_offset
        if (angle_offset < 0 and actual_angle <= angle) or (angle_offset > 0 and actual_angle >= angle):
            image, rect = Drawable.surface_rotate(default_surface, default_rect, angle, point)
            self.__drawable.image = image
            self.__drawable.center = rect.center
            self.__animation_started = False
            if callable(after_move):
                after_move()
        else:
            image, rect = Drawable.surface_rotate(default_surface, default_rect, actual_angle, point)
            self.__drawable.image = image
            self.__drawable.center = rect.center
            self.__window_callback = self.__master.after(
                milliseconds,
                lambda: self.__animate(default_surface, default_rect, milliseconds, angle, angle_offset, actual_angle, point, after_move)
            )

class Animation:

    def __init__(self, master: Window, drawable: Drawable):
        self.__move = AnimationMove(master, drawable)
        self.__rotate = AnimationRotation(master, drawable)

    @property
    def move(self) -> AnimationMove:
        return self.__move

    @property
    def rotate(self) -> AnimationRotation:
        return self.__rotate

    def started(self) -> bool:
        return any(animation.started() for animation in [self.move, self.rotate])