# -*- coding: Utf-8 -*

from typing import Optional, Any, Union, Callable, Iterator, Sequence
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
        self.__default_surface = self.__mask = None
        self.__resized_surface = None
        self.__rotated_surface = None
        self.__surface_to_draw = None
        self.__x = self.__y = 0
        self.__angle = 0
        self.__move_dict = dict()
        self.__draw_sprite = True
        self.__valid_size = True
        self.image = surface
        self.resize(**kwargs)
        self.set_rotation(rotate)
        self.__animation = Animation(self)

    def __getitem__(self, name: str) -> Union[int, tuple[int, int]]:
        return getattr(self.rect, name)

    def __setitem__(self, name: str, value: Any) -> None:
        if not hasattr(self.rect, name):
            raise AttributeError("pygame.Rect object hasn't attribute '{}'".format(name))
        setattr(self, name, value)

    def show(self) -> None:
        self.set_visibility(True)

    def hide(self) -> None:
        self.set_visibility(False)

    def set_visibility(self, status: bool) -> None:
        self.__draw_sprite = bool(status)

    def is_shown(self) -> bool:
        return self.__draw_sprite and self.__valid_size

    @property
    def image(self) -> pygame.Surface:
        return self.__surface_to_draw

    @image.setter
    def image(self, surface: pygame.Surface) -> None:
        if isinstance(surface, self.__class__):
            surface = surface.image
        elif not isinstance(surface, pygame.Surface):
            surface = create_surface((0, 0))
        self.__default_surface = (surface if not surface.get_locked() else surface.copy()).convert_alpha()
        self.__surface_to_draw = self.__resized_surface = self.__rotated_surface = self.__default_surface
        self.__angle = 0

    def get_rect(self, **kwargs) -> pygame.Rect:
        return self.image.get_rect(**kwargs)

    @property
    def mask(self) -> pygame.mask.Mask:
        return pygame.mask.from_surface(self.image)

    def draw(self, surface: pygame.Surface) -> None:
        if self.is_shown():
            self._before_drawing(surface)
            try:
                surface.blit(self.image, self.rect)
            except pygame.error:
                pass
            self._after_drawing(surface)
            self._focus_drawing(surface)

    def _before_drawing(self, surface: pygame.Surface) -> None:
        pass

    def _after_drawing(self, surface: pygame.Surface) -> None:
        pass

    def _focus_drawing(self, surface: pygame.Surface) -> None:
        pass

    def move(self, **kwargs) -> None:
        if not kwargs:
            return
        x = self.__x
        y = self.__y
        common = ("center", "topleft", "topright", "bottomleft", "bottomright", "midtop", "midbottom", "midleft", "midright")
        if not any(key in kwargs for key in ("x", "left", "right", "centerx", *common)):
            kwargs["x"] = x
        if not any(key in kwargs for key in ("y", "top", "bottom", "centery", *common)):
            kwargs["y"] = y
        self.__move_dict = kwargs
        self.__x = self.rect.x
        self.__y = self.rect.y

    def get_move(self) -> dict[str, Union[int, tuple[int, int]]]:
        return self.__move_dict.copy()

    def move_ip(self, x: float, y: float) -> None:
        self.__x += x
        self.__y += y
        if self.__move_dict:
            new_rect = self.get_rect(x=self.__x, y=self.__y)
            self.__move_dict = {attr: getattr(new_rect, attr) for attr in self.__move_dict}
        else:
            self.__move_dict = {"x": self.__x, "y": self.__y}

    def translate(self, vector: Union[Vector2, Sequence[float]]) -> None:
        self.move_ip(vector[0], vector[1])

    def animate_move(self, master, speed=1, milliseconds=10, at_every_frame=None, **position) -> None:
        self.__animation.move(speed=speed, milliseconds=milliseconds, **position)
        self.__animation.start(master, at_every_frame)

    def animate_move_in_background(self, master, speed=1, milliseconds=10, at_every_frame=None, after_animation=None, **position) -> None:
        self.__animation.move(speed=speed, milliseconds=milliseconds, **position)
        self.__animation.start_in_background(master, at_every_frame, after_animation)

    def rotate(self, angle: float, point: Optional[Union[tuple[int, int], Vector2, str]] = None) -> None:
        self.set_rotation(self.__angle + angle, point)

    def set_rotation(self, angle: float, point: Optional[Union[tuple[int, int], Vector2, str]] = None) -> None:
        self.__angle = angle % 360
        rect = self.rect
        self.__rotated_surface = pygame.transform.rotate(self.__default_surface, self.__angle)
        self.__surface_to_draw = pygame.transform.rotate(self.__resized_surface, self.__angle)
        if point is not None:
            rect = self.__resized_surface.get_rect(**self.__move_dict)
            if isinstance(point, str):
                point = getattr(rect, point)
            offset = Vector2(rect.center) - Vector2(point)
            self.move(center=self.__surface_to_draw.get_rect(center=point + offset.rotate(-angle)).center)

    def animate_rotate(self, master, angle: float, offset=1, point=None, milliseconds=10, at_every_frame=None) -> None:
        self.__animation.rotate(angle=angle, offset=offset, point=point, milliseconds=milliseconds)
        self.__animation.start(master, at_every_frame)

    def animate_rotate_in_background(self, master, angle: float, offset=1, point=None, milliseconds=10, at_every_frame=None, after_animation=None) -> None:
        self.__animation.rotate(angle=angle, offset=offset, point=point, milliseconds=milliseconds)
        self.__animation.start_in_background(master, at_every_frame, after_animation)

    def resize(self, *, size: Optional[Union[int, tuple[int, int]]] = None,
               width: Optional[int] = None, height: Optional[int] = None,
               min_width: Optional[int] = None, min_height: Optional[int] = None,
               max_width: Optional[int] = None, max_height: Optional[int] = None,
               smooth=True) -> None:
        if all(param is None for param in [size, width, height, min_width, min_height, max_width, max_height]):
            return
        resize_func = lambda surface: self.__surface_resize(
            surface, smooth=smooth,
            size=size, width=width, height=height,
            min_width=min_width, min_height=min_height,
            max_width=max_width, max_height=max_height
        )
        try:
            self.__surface_to_draw = self.__resized_surface = resize_func(self.__default_surface)
            if self.__angle:
                resized_surface = resize_func(self.__rotated_surface)
                self.__surface_to_draw = resized_surface
                self.__resized_surface = pygame.transform.rotate(resized_surface, -self.__angle)
        except pygame.error:
            self.__valid_size = False
        else:
            self.__valid_size = True

    @staticmethod
    def __surface_resize(surface: pygame.Surface, *, size: Optional[Union[int, tuple[int, int]]] = None,
                         width: Optional[int] = None, height: Optional[int] = None,
                         min_width: Optional[int] = None, min_height: Optional[int] = None,
                         max_width: Optional[int] = None, max_height: Optional[int] = None,
                         smooth=True) -> pygame.Surface:
        if smooth:
            scale_func = pygame.transform.smoothscale
        else:
            scale_func = pygame.transform.scale
        w, h = surface.get_size()
        if isinstance(size, (list, tuple)):
            width, height = size
        elif isinstance(size, (int, float)):
            width = height = size
        if isinstance(width, (int, float)) and isinstance(height, (int, float)):
            width = max(width, 0)
            height = max(height, 0)
        elif isinstance(width, (int, float)):
            width = max(width, 0)
            height = 0 if width == 0 else h * width / (w if w != 0 else width)
        elif isinstance(height, (int, float)):
            height = max(height, 0)
            width = 0 if height == 0 else w * height / (h if h != 0 else height)
        if width == 0:
            scale_width = 0
        elif isinstance(max_width, (int, float)) and width > max_width:
            scale_width = max_width / width
        elif isinstance(min_width, (int, float)) and width < min_width:
            scale_width = min_width / width
        else:
            scale_width = 1
        if height == 0:
            scale_height = 0
        elif isinstance(max_height, (int, float)) and height > max_height:
            scale_height = max_height / height
        elif isinstance(min_height, (int, float)) and height < min_height:
            scale_width = min_height / height
        else:
            scale_height = 1
        scale_value = min(scale_width, scale_height)
        width = round(width * scale_value)
        height = round(height * scale_value)
        return scale_func(surface, (width, height))

    def set_size(self, *size: Union[int, tuple[int, int]], smooth=True) -> None:
        size = size if len(size) == 2 else size[0]
        self.resize(size=size, smooth=smooth)

    def set_width(self, width: float, smooth=True)-> None:
        self.resize(width=width, smooth=smooth)

    def set_height(self, height: float, smooth=True) -> None:
        self.resize(height=height, smooth=smooth)

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

    def animate_stop(self) -> None:
        self.animation.stop()

    def animate_restart(self) -> None:
        self.animation.restart()

    animation = property(lambda self: self.__animation)
    rect = property(lambda self: self.image.get_rect(**self.__move_dict))
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
        projection = self.drawable.get_rect(**self.__position)
        direction = Vector2(projection.center) - Vector2(self.drawable.center)
        if direction.length() > 0 and length < direction.length():
            direction.scale_to_length(length)
            self.drawable.translate(direction)
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
            self.drawable.rotate(self.__actual_angle, self.__pivot)
        else:
            self.stop()

    def default(self) -> None:
        self.drawable.set_rotation(self.__angle, self.__pivot)

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
        default_pos = self.__drawable.get_move()
        only_move = self.__only_move_animation()
        while any(animation.started() for animation in self.__iter_animations()):
            master.handle_fps()
            self.__animate(at_every_frame)
            master.draw_and_refresh(pump=True)
            if not only_move:
                self.__drawable.image = default_image
            self.__drawable.move(**default_pos)
        self.__animate(at_every_frame)
        master.draw_and_refresh()
        self.__clear()

    def start_in_background(self, master, at_every_frame=None, after_animation=None) -> None:
        default_image = self.__drawable.image
        default_pos = self.__drawable.get_move()
        only_move = self.__only_move_animation()
        self.__start_window_callback(master, at_every_frame, after_animation, default_image, default_pos, only_move)

    def __start_window_callback(self, master, at_every_frame: Optional[Callable[..., Any]], after_animation: Optional[Callable[..., Any]],
                                default_image: pygame.Surface, default_pos: dict[str, Any], only_move: bool) -> None:
        if not only_move:
            self.__drawable.image = default_image
        if self.animation_set("move"):
            self.__drawable.move(**default_pos)
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
