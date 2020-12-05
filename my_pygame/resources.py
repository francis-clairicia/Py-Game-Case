# -*- coding: Utf-8 -*

import os
import pickle
import pygame
from typing import Union, Any, Iterator, Callable, TypeVar

_ResourceType = TypeVar('_ResourceType')

def find_in_iterable(iterable, valid_callback=None) -> Iterator[tuple[Union[int, str], ...]]:

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

def travel_container(key_path: tuple[Union[int, str], ...], container: dict[str, Any]) -> tuple[Union[int, str], Union[list[str], dict[Any, str]]]:
    for i in range(len(key_path) - 1):
        container = container[key_path[i]]
    return key_path[-1], container

def get_value_in_container(key_path: tuple[Union[int, str], ...], container: dict[str, Any]) -> Any:
    try:
        key, container = travel_container(key_path, container)
        value = container[key]
    except (IndexError, KeyError):
        return None
    return value

def find_key_in_container(key: str, container: dict[str, Any]) -> tuple[Union[int, str], ...]:
    for key_path in find_in_iterable(container):
        if key in key_path:
            return key_path[:key_path.index(key) + 1]
    return None

class ResourcesCompiler:

    __IMG_EXT = [".png", ".jpg", ".jpeg", ".bmp", ".gif"]
    # __SOUND_EXT = [".ogg", ".wav"]
    __COMPILED_IMG_EXT = ".surface"
    # __COMPILED_SOUND_EXT = ".surface"

    @staticmethod
    def get_compiled_img_extension() -> str:
        return ResourcesCompiler.__COMPILED_IMG_EXT

    @staticmethod
    def compile(path: str, *, delete=False) -> None:
        #pylint: disable=unused-variable
        path = str(path).replace("/", "\\")
        print()
        if os.path.isfile(path):
            ResourcesCompiler.__compile_file(path, delete)
        elif os.path.isdir(path):
            for root, folders, files in os.walk(path):
                for file in files:
                    ResourcesCompiler.__compile_file(os.path.join(root, file), delete)

    @staticmethod
    def __compile_file(path: str, delete: bool) -> None:
        path_without_extension, extension = os.path.splitext(path)
        if extension in ResourcesCompiler.__IMG_EXT:
            compiled_img_path = path_without_extension + ResourcesCompiler.__COMPILED_IMG_EXT
            print("->", path, "compiled to", compiled_img_path)
            surface = pygame.image.load(path)
            file_format = "RGBA"
            buffer_dict = {
                "string": pygame.image.tostring(surface, file_format),
                "size": surface.get_size(),
                "format": file_format
            }
            with open(compiled_img_path, "wb") as compiled_file:
                pickle.dump(buffer_dict, compiled_file)
            if delete:
                os.remove(path)

class ResourcesLoader(dict):

    def __init__(self, resources_loader: Callable[[str], Any]):
        super().__init__()
        self.__files = dict()
        self.__not_loaded = dict()
        self.__resources_loader = resources_loader

    def load(self) -> None:
        if not self:
            self.__not_loaded |= self.__files
        for key_path in find_in_iterable(self.__not_loaded):
            key, container = travel_container(key_path, self.__not_loaded)
            if callable(self.__resources_loader):
                container[key] = self.__resources_loader(container[key])
        super().update(self.__not_loaded)
        self.__not_loaded.clear()

    def __setitem__(self, key: str, value: Union[list[Any], dict[str, Any]]) -> None:
        self.update({key: value})

    def __contains__(self, key: str) -> bool:
        return find_key_in_container(key, self) is not None

    def update(self, resource_dict: dict[str, Any]) -> None:
        self.__files |= resource_dict
        if callable(self.__resources_loader):
            self.__not_loaded |= resource_dict
        else:
            super().update(resource_dict)

    def find(self, key: str) -> Union[_ResourceType, None]:
        key_path = find_key_in_container(key, self)
        if key_path is None:
            return None
        return get_value_in_container(key_path, self)

    def __or__(self, resource_dict: dict[str, Any]):
        return self.__not_loaded | resource_dict

class ImageLoader(ResourcesLoader):
    def __init__(self):
        super().__init__(self.__loader_function)

    def __loader_function(self, resource: str) -> pygame.Surface:
        if resource.endswith(ResourcesCompiler.get_compiled_img_extension()):
            with open(resource, "rb") as compiled_file:
                buffer_dict = pickle.load(compiled_file)
            surface = pygame.image.fromstring(buffer_dict["string"], buffer_dict["size"], buffer_dict["format"])
        else:
            surface = pygame.image.load(resource)
        surface = surface.convert_alpha()
        surface.lock()
        return surface

class FontLoader(ResourcesLoader):
    def __init__(self):
        super().__init__(None)

class MusicLoader(ResourcesLoader):
    def __init__(self):
        super().__init__(None)

class SoundLoader(ResourcesLoader):
    def __init__(self):
        super().__init__(self.__loader_function)

    def __loader_function(self, resource: str) -> pygame.mixer.Sound:
        return pygame.mixer.Sound(resource)

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

    def play_sfx(self, *key_path) -> Union[pygame.mixer.Channel, None]:
        sound = self.get_sfx(*key_path)
        if sound is None:
            return None
        return sound.play()

    def font(self, key: str, *params) -> tuple[str, ...]:
        key_path = find_key_in_container(key, self.__font)
        if key_path is None:
            font = None
        else:
            font = self.get_font(*key_path)
        return (font, *params)

    def get_img(self, *key_path) -> pygame.Surface:
        return get_value_in_container(key_path, self.__img)

    def get_font(self, *key_path) -> str:
        return get_value_in_container(key_path, self.__font)

    def get_music(self, *key_path) -> str:
        return get_value_in_container(key_path, self.__music)

    def get_sfx(self, *key_path) -> pygame.mixer.Sound:
        return get_value_in_container(key_path, self.__sfx)

    IMG = property(lambda self: self.__img, lambda self, value: self.__img.update(value))
    FONT = property(lambda self: self.__font, lambda self, value: self.__font.update(value))
    MUSIC = property(lambda self: self.__music, lambda self, value: self.__music.update(value))
    SFX = property(lambda self: self.__sfx, lambda self, value: self.__sfx.update(value))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("path", help="Resource file or directory")
    parser.add_argument("--delete", help="Delete the files after compiling", action="store_true")
    args = parser.parse_args()
    ResourcesCompiler.compile(args.path, delete=args.delete)
