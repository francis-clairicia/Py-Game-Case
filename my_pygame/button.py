# -*- coding: Utf-8 -*

from typing import Optional, Any, Callable, Union
import pygame
from pygame.font import Font
from .image import Image
from .text import Text
from .shape import RectangleShape
from .clickable import Clickable
from .window import Window
from .colors import WHITE, GRAY, GRAY_LIGHT, GRAY_DARK, BLACK, BLUE, TRANSPARENT

class Button(Clickable, RectangleShape, use_parent_theme=False):
    def __init__(self, master: Window, text=str(), *, font=None, img=None, compound="left",
                 shadow=False, shadow_x=0, shadow_y=0, shadow_color=BLACK,
                 callback: Optional[Callable[..., Any]] = None, state="normal",
                 size=None, x_size=None, y_size=None, x_add_size=20, y_add_size=20,
                 bg=GRAY_LIGHT, fg=BLACK, outline=2, outline_color=BLACK,
                 hover_bg=WHITE, hover_fg=None, hover_sound=None,
                 active_bg=GRAY, active_fg=None, on_click_sound=None,
                 disabled_bg=GRAY_DARK, disabled_fg=BLACK, disabled_sound=None,
                 disabled_hover_bg=None, disabled_hover_fg=None,
                 disabled_active_bg=None, disabled_active_fg=None,
                 hover_img=None, active_img=None, disabled_img=None,
                 disabled_hover_img=None, disabled_active_img=None,
                 highlight_color=BLUE, highlight_thickness=2, cursor=None, disabled_cursor=None,
                 justify=("center", "center"), offset=(0, 0), hover_offset=(0, 0), active_offset=(0, 0),
                 theme=None, **kwargs):
        # pylint: disable=unused-argument
        self.__text = Text(
            text, font=font, color=fg, justify=Text.T_CENTER, img=img, compound=compound,
            shadow=shadow, shadow_x=shadow_x, shadow_y=shadow_y, shadow_color=shadow_color
        )
        self.__justify_x = {"left": "left", "right": "right", "center": "centerx"}[justify[0]]
        self.__justify_y = {"top": "top", "bottom": "bottom", "center": "centery"}[justify[1]]
        self.__offset = offset
        self.__text_hover_offset = hover_offset
        self.__text_active_offset = active_offset
        self.__x_add_size = round(x_add_size)
        self.__y_add_size = round(y_add_size)
        self.__x_size = int(max(round(x_size), 0)) if x_size is not None else None
        self.__y_size = int(max(round(y_size), 0)) if y_size is not None else None
        self.__custom_size = custom_size = None
        if size is None:
            size = (self.__text.w + self.__x_add_size, self.__text.h + self.__y_add_size)
        else:
            size = (int(size), int(size)) if isinstance(size, (int, float)) else tuple(size)
            custom_size = size
        RectangleShape.__init__(self, *size, color=bg, outline=outline, outline_color=outline_color, **kwargs)
        self.__custom_size = custom_size
        self.__update_size()
        self.__bg = {
            Clickable.NORMAL: {
                "normal": bg,
                "hover":  bg if hover_bg is None else hover_bg,
                "active": bg if active_bg is None else active_bg
            },
            Clickable.DISABLED: {
                "normal": disabled_bg,
                "hover":  disabled_bg if disabled_hover_bg is None else disabled_hover_bg,
                "active": disabled_bg if disabled_active_bg is None else disabled_active_bg
            }
        }
        self.__fg = {
            Clickable.NORMAL: {
                "normal": fg,
                "hover":  fg if hover_fg is None else hover_fg,
                "active": fg if active_fg is None else active_fg,
            },
            Clickable.DISABLED: {
                "normal": disabled_fg,
                "hover":  disabled_fg if disabled_hover_fg is None else disabled_hover_fg,
                "active": disabled_fg if disabled_active_fg is None else disabled_active_fg
            }
        }
        if disabled_img is None:
            disabled_img = img
        self.__img = {
            Clickable.NORMAL: {
                "normal": img,
                "hover":  img if hover_img is None else hover_img,
                "active": img if active_img is None else active_img,
            },
            Clickable.DISABLED: {
                "normal": disabled_img,
                "hover":  disabled_img if disabled_hover_img is None else disabled_hover_img,
                "active": disabled_img if disabled_active_img is None else disabled_active_img
            }
        }
        Clickable.__init__(
            self, master, callback, state, hover_sound, on_click_sound, disabled_sound,
            cursor=cursor, disabled_cursor=disabled_cursor, highlight_color=highlight_color, highlight_thickness=highlight_thickness
        )

    @property
    def text(self) -> str:
        return self.__text.message

    @text.setter
    def text(self, string: str) -> None:
        self.__text.message = string
        self.__update_size()

    @property
    def font(self) -> Font:
        return self.__text.font

    @font.setter
    def font(self, font) -> None:
        self.__text.font = font
        self.__update_size()

    @property
    def img(self) -> Image:
        return self.__text.img

    @img.setter
    def img(self, img: Image) -> None:
        self.__text.img = img
        self.__update_size()

    def __update_size(self) -> None:
        if self.__custom_size is None:
            width = self.__text.w + self.__x_add_size if self.__x_size is None else self.__x_size
            height = self.__text.h + self.__y_add_size if self.__y_size is None else self.__y_size
            RectangleShape.set_size(self, width, height)

    def focus_drawing(self, surface: pygame.Surface) -> None:
        Clickable.focus_drawing(self, surface)
        self.__text.move(**{self.__justify_x: getattr(self, self.__justify_x), self.__justify_y: getattr(self, self.__justify_y)})
        self.__text.move_ip(*self.__offset)
        if self.hover:
            self.__text.move_ip(*self.__text_hover_offset)
        if self.active and self.state == Button.NORMAL:
            self.__text.move_ip(*self.__text_active_offset)
        self.__text.draw(surface)

    def set_size(self, *size: Union[int, tuple[int, int]], smooth=True) -> None:
        RectangleShape.set_size(self, *size, smooth=smooth)
        self.__custom_size = self.size

    def set_width(self, width: float, smooth=True)-> None:
        RectangleShape.set_width(self, width, smooth=smooth)
        self.__custom_size = self.size

    def set_height(self, height: float, smooth=True) -> None:
        RectangleShape.set_height(self, height, smooth=smooth)
        self.__custom_size = self.size

    def __set_color(self, button_state: str) -> None:
        self.color = self.__bg[self.state][button_state]
        self.__text.config(color=self.__fg[self.state][button_state], img=self.__img[self.state][button_state])

    def on_hover(self) -> None:
        self.__set_color("hover")

    def on_leave(self) -> None:
        self.__set_color("normal")

    def on_active_set(self) -> None:
        self.__set_color("active")

class ImageButton(Button):

    def __init__(self, master: Window,
                 img: pygame.Surface,
                 hover_img: Optional[pygame.Surface] = None,
                 active_img: Optional[pygame.Surface] = None,
                 disabled_img: Optional[pygame.Surface] = None,
                 disabled_hover_img: Optional[pygame.Surface] = None,
                 disabled_active_img: Optional[pygame.Surface] = None,
                 size=None, width=None, height=None, rotate=0, **kwargs):
        surfaces = [
            ("hover_img", hover_img),
            ("active_img", active_img),
            ("disabled_img", disabled_img),
            ("disabled_hover_img", disabled_hover_img),
            ("disabled_active_img", disabled_active_img)
        ]
        images = dict()
        images["img"] = Image(img, size=size, width=width, height=height, rotate=rotate)
        for image_key, image_surface in filter(lambda image: isinstance(image[1], pygame.Surface), surfaces):
            images[image_key] = Image(image_surface, size=size, width=width, height=height, rotate=rotate)
        Button.__init__(self, master, **images, **kwargs)

ImageButton.set_default_theme("__default_theme")
ImageButton.set_theme("__default_theme", {
    "bg": TRANSPARENT,
    "hover_bg": TRANSPARENT,
    "active_bg": TRANSPARENT,
    "disabled_bg": TRANSPARENT,
    "outline": 0,
    "x_add_size": 20,
    "y_add_size": 20,
    "border_radius": 0,
    "border_top_left_radius": -1,
    "border_top_right_radius": -1,
    "border_bottom_left_radius": -1,
    "border_bottom_right_radius": -1,
    "justify": ("center", "center"),
    "offset": (0, 0),
    "hover_offset": (0, 0),
    "active_offset": (0, 3)
})
