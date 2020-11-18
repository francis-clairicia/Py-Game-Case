# -*- coding: Utf-8 -*

from typing import Tuple, Optional, Any, Union, Callable, Dict, Iterator
import pygame
from pygame.sprite import Sprite
from pygame.math import Vector2
from .surface import create_surface
from .theme import ThemedObject
from .thread import threaded_function
from .clock import Clock

class Drawable(Sprite, ThemedObject):

    __default_scale = (1, 1)
    __trace = list()

    def __init__(self, surface: Optional[pygame.Surface] = None, rotate=0, **kwargs):
        Sprite.__init__(self)
        ThemedObject.__init__(self)
        Drawable.__trace.append(self)
        self.__surface = self.__mask = None
        self.__surface_without_scale = None
        self.__rect = pygame.Rect(0, 0, 0, 0)
        self.__x = self.__y = 0
        self.__scale = self.__default_scale
        self.__former_moves = dict()
        self.__draw_sprite = True
        self.__valid_size = True
        self.image = self.surface_resize(surface, **kwargs)
        self.rotate(rotate)
        self.__animation = Animation(self)

    def __del__(self) -> None:
        if self in Drawable.__trace:
            Drawable.__trace.remove(self)

    def __getitem__(self, name: str) -> Union[int, Tuple[int, int]]:
        return getattr(self.rect, name)

    def __setitem__(self, name: str, value: Any) -> None:
        if hasattr(self.rect, name):
            setattr(self, name, value)

    def fill(self, color: pygame.Color) -> None:
        self.image.fill(color)
        self.mask_update()

    def blit(self, source, dest, area=None, special_flags=0) -> pygame.Rect:
        rect = self.image.blit(source, dest, area=area, special_flags=special_flags)
        self.mask_update()
        return rect

    def show(self) -> None:
        self.set_visibility(True)

    def hide(self) -> None:
        self.set_visibility(False)

    def set_visibility(self, status: bool) -> None:
        self.__draw_sprite = bool(status)

    def is_shown(self) -> bool:
        return bool(self.__draw_sprite and self.__valid_size)

    @property
    def image(self) -> pygame.Surface:
        return self.__surface

    @image.setter
    def image(self, surface: pygame.Surface) -> None:
        if isinstance(surface, Drawable):
            surface = surface.image
        elif not isinstance(surface, pygame.Surface):
            surface = create_surface((0, 0))
        self.__surface_without_scale = surface
        if self.__scale != (1, 1):
            try:
                scale_w, scale_h = self.__scale
                width, height = surface.get_size()
                self.__surface = pygame.transform.smoothscale(surface, (round(width * scale_w), round(height * scale_h)))
            except pygame.error:
                self.__valid_size = False
                self.__surface = surface
            else:
                self.__valid_size = True
        else:
            self.__surface = surface
        self.__rect = self.__surface.get_rect(**self.__former_moves)
        self.mask_update()

    @property
    def rect(self) -> pygame.Rect:
        return self.__rect

    @property
    def mask(self) -> pygame.mask.Mask:
        return self.__mask

    def mask_update(self) -> None:
        self.__mask = pygame.mask.from_surface(self.__surface)

    @property
    def scale(self) -> Tuple[float, float]:
        return self.__scale

    @scale.setter
    def scale(self, scale: Tuple[float, float]) -> None:
        scale_w, scale_h = scale
        self.__scale = max(scale_w, 0), max(scale_h, 0)
        self.image = self.__surface_without_scale

    @staticmethod
    def set_default_scale(scale_w: float, scale_h: float) -> None:
        Drawable.__default_scale = max(scale_w, 0), max(scale_h, 0)
        for drawable in Drawable.__trace:
            drawable.scale = Drawable.__default_scale

    def draw(self, surface: pygame.Surface) -> None:
        if self.is_shown():
            self.before_drawing(surface)
            try:
                surface.blit(self.image, self.rect)
            except pygame.error:
                pass
            self.after_drawing(surface)
            self.focus_drawing(surface)

    def before_drawing(self, surface: pygame.Surface) -> None:
        pass

    def after_drawing(self, surface: pygame.Surface) -> None:
        pass

    def focus_drawing(self, surface: pygame.Surface) -> None:
        pass

    def move(self, **kwargs) -> None:
        if not kwargs:
            return
        x = self.__rect.x
        y = self.__rect.y
        common = ("center", "topleft", "topright", "bottomleft", "bottomright", "midtop", "midbottom", "midleft", "midright")
        if not any(key in kwargs for key in ("x", "left", "right", "centerx", *common)):
            kwargs["x"] = x
        if not any(key in kwargs for key in ("y", "top", "bottom", "centery", *common)):
            kwargs["y"] = y
        self.__rect = self.image.get_rect(**kwargs)
        self.__x = self.__rect.x
        self.__y = self.__rect.y
        self.__former_moves = kwargs

    def move_ip(self, x: float, y: float) -> None:
        self.__x += x
        self.__y += y
        self.__rect = self.__surface.get_rect(x=self.__x, y=self.__y)
        self.__former_moves = {"x": self.__x, "y": self.__y}

    def animate_move(self, master, speed=1, milliseconds=10, at_every_frame=None, **position) -> None:
        self.__animation.move(speed=speed, milliseconds=milliseconds, **position).start(master, at_every_frame)

    def rotate(self, angle: float) -> None:
        angle %= 360
        if angle == 0:
            return
        self.image = pygame.transform.rotate(self.__surface_without_scale, angle)

    def rotate_through_point(self, angle: float, point: Union[Tuple[int, int], Vector2]) -> None:
        angle %= 360
        if angle == 0:
            return
        image, rect = self.surface_rotate(self.__surface_without_scale, self.rect, angle, point)
        self.image = image
        self.center = rect.center

    def animate_rotate(self, master, angle: float, offset=1, point=None, milliseconds=10, at_every_frame=None) -> None:
        self.__animation.rotate(angle=angle, offset=offset, point=point, milliseconds=milliseconds).start(master, at_every_frame)
    
    @staticmethod
    def surface_rotate(surface: pygame.Surface, rect: pygame.Rect, angle: float, point: Union[Tuple[int, int], Vector2]) -> Tuple[pygame.Surface, pygame.Rect]:
        offset = Vector2(rect.center) - Vector2(point)
        rotated_surface = pygame.transform.rotate(surface, angle)
        rotated_offset = offset.rotate(-angle)
        return rotated_surface, rotated_surface.get_rect(center=point + rotated_offset)

    @staticmethod
    def surface_resize(surface: pygame.Surface, size: Optional[Union[int, Tuple[int, int]]] = None,
             width: Optional[int] = None, height: Optional[int] = None,
             min_width: Optional[int] = None, min_height: Optional[int] = None,
             max_width: Optional[int] = None, max_height: Optional[int] = None,
             smooth=True) -> pygame.Surface:
        if smooth:
            scale_func = pygame.transform.smoothscale
        else:
            scale_func = pygame.transform.scale
        if not isinstance(surface, pygame.Surface):
            surface = create_surface((0, 0))
        if all(param is None for param in [size, width, height, min_width, min_height, max_width, max_height]):
            return surface
        w, h = surface.get_size()
        if isinstance(size, (list, tuple)):
            width, height = size
        elif isinstance(size, int):
            width = height = size
        width = round(width) if isinstance(width, (int, float)) else None
        height = round(height) if isinstance(height, (int, float)) else None
        min_width = round(min_width) if isinstance(min_width, (int, float)) else None
        min_height = round(min_height) if isinstance(min_height, (int, float)) else None
        max_width = round(max_width) if isinstance(max_width, (int, float)) else None
        max_height = round(max_height) if isinstance(max_height, (int, float)) else None
        if isinstance(min_width, int):
            width = max(min_width, width, w) if isinstance(width, int) else max(min_width, w)
        elif isinstance(max_width, int):
            width = min(max_width, width, w) if isinstance(width, int) else min(max_width, w)
        if isinstance(min_height, int):
            height = max(min_height, height, h) if isinstance(height, int) else max(min_height, h)
        elif isinstance(max_height, int):
            height = min(max_height, height, h) if isinstance(height, int) else min(max_height, h)
        if isinstance(width, int) and isinstance(height, int):
            width = max(width, 0)
            height = max(height, 0)
            surface = scale_func(surface, (width, height))
        elif isinstance(width, int):
            width = max(width, 0)
            height = 0 if width == 0 else round(h * width / (w if w != 0 else width))
            surface = scale_func(surface, (width, height))
        elif isinstance(height, int):
            height = max(height, 0)
            width = 0 if height == 0 else round(w * height / (h if h != 0 else height))
            surface = scale_func(surface, (width, height))
        return surface

    def set_size(self, *size: Union[int, Tuple[int, int]], smooth=True) -> None:
        size = size if len(size) == 2 else size[0]
        try:
            self.image = self.surface_resize(self.__surface_without_scale, size=size, smooth=smooth)
        except pygame.error:
            self.__valid_size = False
        else:
            self.__valid_size = True

    def set_width(self, width: float, smooth=True)-> None:
        try:
            self.image = self.surface_resize(self.__surface_without_scale, width=width, smooth=smooth)
        except pygame.error:
            self.__valid_size = False
        else:
            self.__valid_size = True

    def set_height(self, height: float, smooth=True) -> None:
        try:
            self.image = self.surface_resize(self.__surface_without_scale, height=height, smooth=smooth)
        except pygame.error:
            self.__valid_size = False
        else:
            self.__valid_size = True

    def animate_resize_width(self, master, width: int, offset=1, milliseconds=10, at_every_frame=None) -> None:
        self.__animation.scale_width(width=width, offset=offset, milliseconds=milliseconds).start(master, at_every_frame)

    def animate_resize_height(self, master, height: int, offset=1, milliseconds=10, at_every_frame=None) -> None:
        self.__animation.scale_height(height=height, offset=offset, milliseconds=milliseconds).start(master, at_every_frame)

    animation = property(lambda self: self.__animation)

    left = property(lambda self: self.rect.left, lambda self, value: self.move(left=value))
    right = property(lambda self: self.rect.right, lambda self, value: self.move(right=value))
    top = property(lambda self: self.rect.top, lambda self, value: self.move(top=value))
    bottom = property(lambda self: self.rect.bottom, lambda self, value: self.move(bottom=value))
    x = left
    y = top
    size = property(lambda self: self.rect.size, lambda self, value: self.set_size(value))
    width = property(lambda self: self.rect.width, lambda self, value: self.set_width(value))
    height = property(lambda self: self.rect.height, lambda self, value: self.set_height(value))
    w = width
    h = height
    center = property(lambda self: self.rect.center, lambda self, value: self.move(center=value))
    centerx = property(lambda self: self.rect.centerx, lambda self, value: self.move(centerx=value))
    centery = property(lambda self: self.rect.centery, lambda self, value: self.move(centery=value))
    topleft = property(lambda self: self.rect.topleft, lambda self, value: self.move(topleft=value))
    topright = property(lambda self: self.rect.topright, lambda self, value: self.move(topright=value))
    bottomleft = property(lambda self: self.rect.bottomleft, lambda self, value: self.move(bottomleft=value))
    bottomright = property(lambda self: self.rect.bottomright, lambda self, value: self.move(bottomright=value))
    midtop = property(lambda self: self.rect.midtop, lambda self, value: self.move(midtop=value))
    midbottom = property(lambda self: self.rect.midbottom, lambda self, value: self.move(midbottom=value))
    midleft = property(lambda self: self.rect.midleft, lambda self, value: self.move(midleft=value))
    midright = property(lambda self: self.rect.midright, lambda self, value: self.move(midright=value))

class AbstractAnimationClass:

    def __init__(self, drawable: Drawable, milliseconds: int):
        self.__drawable = drawable
        self.__animation_started = True
        self.__clock = Clock()
        self.__milliseconds = max(round(milliseconds), 0)

    def started(self) -> bool:
        return self.__animation_started

    def stop(self) -> None:
        self.__animation_started = False
        self.default()

    def ready(self) -> bool:
        return self.__clock.elapsed_time(self.__milliseconds)

    def __call__(self) -> None:
        raise NotImplementedError

    def default(self) -> None:
        raise NotImplementedError

    drawable = property(lambda self: self.__drawable)
    milliseconds = property(lambda self: self.__milliseconds)

class AnimationMove(AbstractAnimationClass):

    def __init__(self, drawable: Drawable, milliseconds: int, speed=1, **position):
        super().__init__(drawable, milliseconds)
        self.__position = position
        self.__speed = speed
        self.__increment = 0

    def __call__(self) -> None:
        if self.milliseconds == 0 or self.__speed <= 0:
            self.stop()
            return
        if self.ready():
            self.__increment += 1
        length = self.__increment * self.__speed
        projection = Drawable(self.drawable.image)
        projection.move(**self.__position)
        direction = Vector2(projection.center) - Vector2(self.drawable.center)
        if direction.length() > 0 and length < direction.length():
            direction.scale_to_length(length)
            self.drawable.move_ip(direction.x, direction.y)
        else:
            self.stop()

    def default(self) -> None:
        self.drawable.move(**self.__position)

class AnimationRotation(AbstractAnimationClass):

    def __init__(self, drawable: Drawable, milliseconds: int, angle: float, offset=1, point=None):
        super().__init__(drawable, milliseconds)
        self.__angle = angle
        self.__offset = abs(offset) * (angle / abs(angle)) if angle != 0 else 0
        self.__actual_angle = 0
        self.__pivot = point

    def __call__(self) -> None:
        if self.milliseconds == 0 or self.__angle == 0 or self.__offset == 0:
            self.stop()
            return
        if self.ready():
            self.__actual_angle += self.__offset
        if (self.__offset < 0 and self.__actual_angle > self.__angle) or (self.__offset > 0 and self.__actual_angle < self.__angle):
            self.__rotate(self.__actual_angle, self.__pivot)
        else:
            self.stop()

    def default(self) -> None:
        self.__rotate(self.__angle, self.__pivot)

    def __rotate(self, angle: float, point: Union[Tuple[int, int], Vector2, None]) -> None:
        if point is None:
            self.drawable.rotate(angle)
        else:
            self.drawable.rotate_through_point(angle, point)

class AnimationScaleSize(AbstractAnimationClass):

    def __init__(self, drawable: Drawable, milliseconds: int, field: str, size: int, offset=1):
        super().__init__(drawable, milliseconds)
        self.__size = round(max(size, 0))
        self.__field = field
        if offset == 0 or self.__size == self.drawable[field]:
            self.__offset = 0
        else:
            self.__offset = abs(offset) * ((self.__size - self.drawable[field]) // abs(self.__size - self.drawable[field]))
        self.__actual_size = self.drawable[field]

    def __call__(self) -> None:
        if self.milliseconds == 0 or self.__offset == 0:
            self.stop()
            return
        if self.ready():
            self.__actual_size += self.__offset
        not_size_set = lambda size, actual_size, offset: (offset < 0 and actual_size > size) or (offset > 0 and actual_size < size)
        if not_size_set(self.__size, self.__actual_size, self.__offset):
            self.drawable[self.__field] = self.__actual_size
        else:
            self.stop()

    def default(self) -> None:
        self.drawable[self.__field] = self.__size

class AnimationScaleWidth(AnimationScaleSize):
    
    def __init__(self, drawable: Drawable, milliseconds: int, width: int, offset=1):
        super().__init__(drawable, milliseconds, "width", width, offset=offset)

class AnimationScaleHeight(AnimationScaleSize):

    def __init__(self, drawable: Drawable, milliseconds: int, height: int, offset=1):
        super().__init__(drawable, milliseconds, "height", height, offset=offset)

class Animation:

    def __init__(self, drawable: Drawable):
        self.__drawable = drawable
        self.__animations_order = ["scale_width", "scale_height", "rotate", "move"]
        self.__animations = dict.fromkeys(self.__animations_order)
        self.__clock = pygame.time.Clock()

    def move(self, speed=1, milliseconds=10, **position):
        self.__animations["move"] = AnimationMove(self.__drawable, milliseconds, speed=speed, **position)
        return self

    def rotate(self, angle: float, offset=1, point=None, milliseconds=10):
        self.__animations["rotate"] = AnimationRotation(self.__drawable, milliseconds, angle, offset=offset, point=point)
        return self

    def scale_width(self, width: int, offset=1, milliseconds=10):
        self.__animations["scale_width"] = AnimationScaleWidth(self.__drawable, milliseconds, width, offset=offset)
        return self

    def scale_height(self, height: int, offset=1, milliseconds=10):
        self.__animations["scale_height"] = AnimationScaleHeight(self.__drawable, milliseconds, height, offset=offset)
        return self

    def __get(self, animation: str) -> AbstractAnimationClass:
        return self.__animations[animation]

    def __iter_animations(self) -> Iterator[AbstractAnimationClass]:
        for animation_name in self.__animations_order:
            animation = self.__get(animation_name)
            if isinstance(animation, AbstractAnimationClass):
                yield animation

    def __only_move_animation(self) -> bool:
        return (isinstance(self.__animations["move"], AbstractAnimationClass) and all(not isinstance(anim, AbstractAnimationClass) for name, anim in self.__animations.items() if name != "move"))

    def start(self, master, at_every_frame=None) -> None:
        default_image = self.__drawable.image
        default_pos = self.__drawable.center
        only_move = self.__only_move_animation()
        while any(animation.started() for animation in self.__iter_animations()):
            self.__clock.tick(master.get_framerate())
            for animation in self.__iter_animations():
                if animation.started():
                    animation()
                else:
                    animation.default()
            if callable(at_every_frame):
                at_every_frame()
            master.draw_and_refresh(pump=True)
            self.__drawable.image = default_image
            self.__drawable.center = default_pos
        for animation in self.__iter_animations():
            animation.default()
        if callable(at_every_frame):
            at_every_frame()
        master.draw_and_refresh()
        for key in self.__animations:
            self.__animations[key] = None