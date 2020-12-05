# -*- coding: Utf-8 -*

from typing import Optional, Any, Union, Callable, Iterator
import pygame
from pygame.sprite import Sprite
from pygame.math import Vector2
from .surface import create_surface
from .theme import ThemedObject
from .clock import Clock

class Drawable(Sprite, ThemedObject):

    def __init__(self, surface: Optional[pygame.Surface] = None, rotate=0, **kwargs):
        Sprite.__init__(self)
        ThemedObject.__init__(self)
        self.__surface = self.__mask = None
        self.__surface_without_scale = None
        self.__rect = pygame.Rect(0, 0, 0, 0)
        self.__x = self.__y = 0
        self.__former_moves = dict()
        self.__draw_sprite = True
        self.__valid_size = True
        self.image = self.surface_resize(surface, **kwargs)
        self.rotate(rotate)
        self.__animation = Animation(self)

    def __getitem__(self, name: str) -> Union[int, tuple[int, int]]:
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
        self.__surface = (surface if not surface.get_locked() else surface.copy()).convert_alpha()
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
        self.__rect = self.__surface.get_rect(**kwargs)
        self.__x = self.__rect.x
        self.__y = self.__rect.y
        self.__former_moves = kwargs

    def get_former_moves(self) -> dict[str, Union[int, tuple[int, int]]]:
        return self.__former_moves.copy()

    def move_ip(self, x: float, y: float) -> None:
        self.__x += x
        self.__y += y
        self.__rect = self.__surface.get_rect(x=self.__x, y=self.__y)
        self.__former_moves = {"x": self.__x, "y": self.__y}

    def animate_move(self, master, speed=1, milliseconds=10, at_every_frame=None, **position) -> None:
        self.__animation.move(speed=speed, milliseconds=milliseconds, **position)
        self.__animation.start(master, at_every_frame)

    def animate_move_in_background(self, master, speed=1, milliseconds=10, at_every_frame=None, after_animation=None, **position) -> None:
        self.__animation.move(speed=speed, milliseconds=milliseconds, **position)
        self.__animation.start_in_background(master, at_every_frame, after_animation)

    def rotate(self, angle: float) -> None:
        angle %= 360
        self.image = pygame.transform.rotate(self.image, angle)

    def rotate_through_point(self, angle: float, point: Union[tuple[int, int], Vector2]) -> None:
        angle %= 360
        image, rect = self.surface_rotate(self.image, self.rect, angle, point)
        self.image = image
        self.center = rect.center

    def animate_rotate(self, master, angle: float, offset=1, point=None, milliseconds=10, at_every_frame=None) -> None:
        self.__animation.rotate(angle=angle, offset=offset, point=point, milliseconds=milliseconds)
        self.__animation.start(master, at_every_frame)

    def animate_rotate_in_background(self, master, angle: float, offset=1, point=None, milliseconds=10, at_every_frame=None, after_animation=None) -> None:
        self.__animation.rotate(angle=angle, offset=offset, point=point, milliseconds=milliseconds)
        self.__animation.start_in_background(master, at_every_frame, after_animation)

    @staticmethod
    def surface_rotate(surface: pygame.Surface, rect: pygame.Rect, angle: float, point: Union[tuple[int, int], Vector2]) -> tuple[pygame.Surface, pygame.Rect]:
        offset = Vector2(rect.center) - Vector2(point)
        rotated_surface = pygame.transform.rotate(surface, angle)
        rotated_offset = offset.rotate(-angle)
        return rotated_surface, rotated_surface.get_rect(center=point + rotated_offset)

    @staticmethod
    def surface_resize(surface: pygame.Surface, size: Optional[Union[int, tuple[int, int]]] = None,
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

    def set_size(self, *size: Union[int, tuple[int, int]], smooth=True) -> None:
        size = size if len(size) == 2 else size[0]
        try:
            self.image = self.surface_resize(self.image, size=size, smooth=smooth)
        except pygame.error:
            self.__valid_size = False
        else:
            self.__valid_size = True

    def set_width(self, width: float, smooth=True)-> None:
        try:
            self.image = self.surface_resize(self.image, width=width, smooth=smooth)
        except pygame.error:
            self.__valid_size = False
        else:
            self.__valid_size = True

    def set_height(self, height: float, smooth=True) -> None:
        try:
            self.image = self.surface_resize(self.image, height=height, smooth=smooth)
        except pygame.error:
            self.__valid_size = False
        else:
            self.__valid_size = True

    def animate_scale_width(self, master, width: int, offset=1, milliseconds=10, at_every_frame=None) -> None:
        self.__animation.scale_width(width=width, offset=offset, milliseconds=milliseconds)
        self.__animation.start(master, at_every_frame)

    def animate_scale_width_in_background(self, master, width: int, offset=1, milliseconds=10, at_every_frame=None, after_animation=None) -> None:
        self.__animation.scale_width(width=width, offset=offset, milliseconds=milliseconds)
        self.__animation.start_in_background(master, at_every_frame, after_animation)

    def animate_scale_height(self, master, height: int, offset=1, milliseconds=10, at_every_frame=None) -> None:
        self.__animation.scale_height(height=height, offset=offset, milliseconds=milliseconds)
        self.__animation.start(master, at_every_frame)

    def animate_scale_height_in_background(self, master, height: int, offset=1, milliseconds=10, at_every_frame=None, after_animation=None) -> None:
        self.__animation.scale_height(height=height, offset=offset, milliseconds=milliseconds)
        self.__animation.start_in_background(master, at_every_frame, after_animation)

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
        self.__projection = Drawable()
        self.__projection.move(**self.__position)
        self.__speed = speed
        self.__increment = 0

    def __call__(self) -> None:
        if self.milliseconds == 0 or self.__speed <= 0:
            self.stop()
            return
        if self.ready():
            self.__increment += 1
        length = self.__increment * self.__speed
        self.__projection.image = self.drawable.image
        direction = Vector2(self.__projection.center) - Vector2(self.drawable.center)
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

    def __rotate(self, angle: float, point: Union[tuple[int, int], Vector2, None]) -> None:
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
        self.__window_callback = None
        self.__save_window_callback = None
        self.__save_animations = None

    def move(self, speed=1, milliseconds=10, **position):
        self.stop()
        self.__animations["move"] = AnimationMove(self.__drawable, milliseconds, speed=speed, **position)
        return self

    def rotate(self, angle: float, offset=1, point=None, milliseconds=10):
        self.stop()
        self.__animations["rotate"] = AnimationRotation(self.__drawable, milliseconds, angle, offset=offset, point=point)
        return self

    def scale_width(self, width: int, offset=1, milliseconds=10):
        self.stop()
        self.__animations["scale_width"] = AnimationScaleWidth(self.__drawable, milliseconds, width, offset=offset)
        return self

    def scale_height(self, height: int, offset=1, milliseconds=10):
        self.stop()
        self.__animations["scale_height"] = AnimationScaleHeight(self.__drawable, milliseconds, height, offset=offset)
        return self

    def __get(self, animation: str) -> AbstractAnimationClass:
        return self.__animations[animation]

    def __iter_animations(self) -> Iterator[AbstractAnimationClass]:
        for animation_name in self.__animations_order:
            animation = self.__get(animation_name)
            if isinstance(animation, AbstractAnimationClass):
                yield animation

    def animation_set(self, animation: str) -> bool:
        return isinstance(self.__animations[animation], AbstractAnimationClass)

    def __only_move_animation(self) -> bool:
        return self.animation_set("move") and all(self.animation_set(name) for name in self.__animations if name != "move")

    def __clear(self) -> None:
        for key in self.__animations:
            self.__animations[key] = None

    def __animate(self, at_every_frame: Optional[Callable[..., Any]]) -> None:
        for animation in self.__iter_animations():
            if animation.started():
                animation()
            else:
                animation.default()
        if callable(at_every_frame):
            at_every_frame()

    def start(self, master, at_every_frame=None) -> None:
        default_image = self.__drawable.image
        default_pos = self.__drawable.center
        only_move = self.__only_move_animation()
        while any(animation.started() for animation in self.__iter_animations()):
            master.main_clock.tick(master.get_fps())
            self.__animate(at_every_frame)
            master.draw_and_refresh(pump=True)
            if not only_move:
                self.__drawable.image = default_image
            self.__drawable.center = default_pos
        self.__animate(at_every_frame)
        master.draw_and_refresh()
        self.__clear()

    def start_in_background(self, master, at_every_frame=None, after_animation=None) -> None:
        default_image = self.__drawable.image
        default_pos = self.__drawable.center
        only_move = self.__only_move_animation()
        self.__start_window_callback(master, at_every_frame, after_animation, default_image, default_pos, only_move)

    def __start_window_callback(self, master, at_every_frame: Optional[Callable[..., Any]], after_animation: Optional[Callable[..., Any]],
                                default_image: pygame.Surface, default_pos: tuple[int, int], only_move: bool) -> None:
        if not only_move:
            self.__drawable.image = default_image
        if self.animation_set("move"):
            self.__drawable.center = default_pos
        self.__animate(at_every_frame)
        if any(animation.started() for animation in self.__iter_animations()):
            self.__window_callback = master.after(
                0, self.__start_window_callback,
                master=master, at_every_frame=at_every_frame, after_animation=after_animation,
                default_image=default_image, default_pos=default_pos, only_move=only_move
            )
        else:
            self.__clear()
            self.__save_animations = self.__save_window_callback = None
            if callable(after_animation):
                after_animation()

    def stop(self) -> None:
        if self.__window_callback is not None:
            self.__window_callback.kill()
            self.__save_window_callback = self.__window_callback
            self.__window_callback = None
            self.__save_animations = self.__animations.copy()
            self.__clear()

    def restart(self) -> None:
        if self.__window_callback is None and self.__save_window_callback is not None:
            self.__animations = self.__save_animations.copy()
            self.__save_window_callback()
