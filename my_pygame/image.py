# -*- coding: Utf-8 -*

import pygame
from .drawable import Drawable

class Image(Drawable, use_parent_theme=False):

    def __init__(self, surface: pygame.Surface, **kwargs):
        Drawable.__init__(self, surface=surface, **kwargs)

    @classmethod
    def from_filepath(cls, filepath: str, **kwargs):
        return cls(surface=pygame.image.load(filepath).convert_alpha(), **kwargs)

    def load(self, surface: pygame.Surface, **kwargs) -> None:
        self.image = self.surface_resize(surface, **kwargs)
