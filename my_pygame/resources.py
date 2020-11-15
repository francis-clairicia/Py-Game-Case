# -*- coding: Utf-8 -*

import os
import pygame
from typing import Tuple, Union, Dict, List, Any, Iterator, Callable
from .thread import threaded_function

def find_in_iterable(iterable, valid_callback=None) -> Iterator[Tuple[Union[int, str], ...]]:

    def intern_find(iterable, *key_before, valid_callback=None):
        if isinstance(iterable, dict):
            for key, value in iterable.items():
                yield from intern_find(value, *key_before, key, valid_callback=valid_callback)
        elif isinstance(iterable, (list, tuple)):
            for index, value in enumerate(iterable):
                yield from intern_find(value, *key_before, index, valid_callback=valid_callback)
        else:
            value = iterable
            if not callable(valid_callback) or valid_callback(value):
                yield key_before

    return intern_find(iterable, valid_callback=valid_callback)

def travel_container(key_path: Tuple[Union[int, str], ...], container: Dict[str, Any]) -> Tuple[Union[int, str], Union[List[str], Dict[Any, str]]]:
    for i in range(len(key_path) - 1):
        container = container[key_path[i]]
    return key_path[-1], container

def get_value_in_container(key_path: Tuple[Union[int, str], ...], container: Dict[str, Any]) -> Any:
    try:
        key, container = travel_container(key_path, container)
        value = container[key]
    except (IndexError, KeyError):
        return None
    return value

def find_key_in_container(key: str, container: Dict[str, Any]) -> Tuple[Union[int, str], ...]:
    for key_path in find_in_iterable(container):
        if key in key_path:
            return key_path[:key_path.index(key) + 1]
    return None

class ResourcesLoader:
    
    def __init__(self, resources_loader: Callable[[str], Any]):
        self.__files = dict()
        self.__not_loaded = dict()
        self.__loaded = dict()
        self.__resources_loader = resources_loader

    def load(self) -> None:
        if not self.__loaded:
            self.__not_loaded.update(self.__files.copy())
        for key_path in find_in_iterable(self.__not_loaded, valid_callback=os.path.isfile):
            key, container = travel_container(key_path, self.__not_loaded)
            if callable(self.__resources_loader):
                container[key] = self.__resources_loader(container[key])
        self.__loaded.update(self.__not_loaded)
        self.__not_loaded.clear()

    def update(self, resource_dict: Dict[str, Any]) -> None:
        self.__files.update(resource_dict)
        self.__not_loaded.update(resource_dict.copy())

    def __contains__(self, key: Any) -> bool:
        return key in self.__loaded

    def __getitem__(self, key: Any) -> Any:
        return self.loaded[key]

    loaded = property(lambda self: self.__loaded.copy())

class ImageLoader(ResourcesLoader):
    def __init__(self):
        super().__init__(lambda resource: pygame.image.load(resource).convert_alpha())

class FontLoader(ResourcesLoader):
    def __init__(self):
        super().__init__(None)

class MusicLoader(ResourcesLoader):
    def __init__(self):
        super().__init__(None)

class SoundLoader(ResourcesLoader):
    def __init__(self):
        super().__init__(lambda resource: pygame.mixer.Sound(resource))

class Resources:

    def __init__(self):
        self.__img = ImageLoader()
        self.__font = FontLoader()
        self.__music = MusicLoader()
        self.__sfx = SoundLoader()
        self.__resources = [
            self.__img,
            self.__font,
            self.__music,
            self.__sfx,
        ]

    def load(self) -> None:
        for resources in self.__resources:
            resources.load()

    def set_sfx_volume(self, volume: float, state: bool) -> None:
        if volume < 0:
            volume = 0
        elif volume > 1:
            volume = 1
        for key_path in find_in_iterable(self.__sfx, valid_callback=lambda obj: isinstance(obj, pygame.mixer.Sound)):
            sound_obj = self.get_sfx(*key_path)
            sound_obj.set_volume(volume if bool(state) is True else 0)

    def play_sfx(self, *key_path) -> (pygame.mixer.Channel, None):
        sound = self.get_sfx(*key_path)
        if sound is None:
            return None
        return sound.play()

    def font(self, key: str, *params) -> Tuple[str, ...]:
        key_path = find_key_in_container(key, self.__font.loaded)
        if key_path is None:
            font = None
        else:
            font = self.get_font(*key_path)
        return (font, *params)

    def get_img(self, *key_path) -> pygame.Surface:
        return get_value_in_container(key_path, self.__img.loaded)

    def get_font(self, *key_path) -> str:
        return get_value_in_container(key_path, self.__font.loaded)

    def get_music(self, *key_path) -> str:
        return get_value_in_container(key_path, self.__music.loaded)

    def get_sfx(self, *key_path) -> pygame.mixer.Sound:
        return get_value_in_container(key_path, self.__sfx.loaded)

    IMG = property(lambda self: self.__img.loaded, lambda self, value: self.__img.update(value))
    FONT = property(lambda self: self.__font.loaded, lambda self, value: self.__font.update(value))
    MUSIC = property(lambda self: self.__music.loaded, lambda self, value: self.__music.update(value))
    SFX = property(lambda self: self.__sfx.loaded, lambda self, value: self.__sfx.update(value))