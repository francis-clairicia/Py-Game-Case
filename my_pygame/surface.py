# -*- coding: Utf-8 -*

import pygame

def create_surface(size: tuple[int, int]) -> pygame.Surface:
    return pygame.Surface(size, flags=pygame.SRCALPHA|pygame.HWSURFACE).convert_alpha()
