# -*- coding: Utf-8 -*

from typing import Tuple
import pygame

def create_surface(size: Tuple[int, int]) -> pygame.Surface:
    return pygame.Surface(size, flags=pygame.SRCALPHA|pygame.HWSURFACE).convert_alpha()
