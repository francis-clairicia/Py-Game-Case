# -*- coding: Utf-8 -*

from .drawable import Drawable, AnimationMove, AnimationRotation, AnimationScaleSize, AnimationScaleWidth, AnimationScaleHeight
from .window import Window

class Animation:

    def __init__(self, master: Window, drawable: Drawable):
        self.__move = AnimationMove(master, drawable)
        self.__rotate = AnimationRotation(master, drawable)
        self.__scale_size = AnimationScaleSize(master, drawable)
        self.__scale_width = AnimationScaleWidth(master, drawable)
        self.__scale_height = AnimationScaleHeight(master, drawable)

    @property
    def move(self) -> AnimationMove:
        return self.__move

    @property
    def rotate(self) -> AnimationRotation:
        return self.__rotate

    @property
    def scale_size(self) -> AnimationScaleSize:
        return self.__scale_size

    @property
    def scale_width(self) -> AnimationScaleWidth:
        return self.__scale_width

    @property
    def scale_height(self) -> AnimationScaleHeight:
        return self.__scale_height

    def started(self) -> bool:
        return any(animation.started() for animation in [self.move, self.rotate, self.scale_size, self.scale_width, self.scale_height])