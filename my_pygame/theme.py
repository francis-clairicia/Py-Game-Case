# -*- coding: Utf-8 -*

from typing import Any, Iterator, Union, Sequence, Optional

def get_all_parent_class(cls: type[object], do_not_search_for: Optional[Sequence[type[object]]] = list()) -> Iterator[type[object]]:
    for base in cls.__bases__:
        yield base
        if base not in do_not_search_for:
            yield from get_all_parent_class(base)

_NAMESPACE = None
_THEMES = {_NAMESPACE: dict()}
_HIDDEN_THEMES = dict()
_DEFAULT_THEME = dict()
_HIDDEN_DEFAULT_THEME = dict()
_CLASSES_NOT_USING_PARENT_THEMES = list()
_CLASSES_NOT_USING_PARENT_DEFAULT_THEMES = list()

class MetaThemedObject(type):

    def __call__(cls, *args, **kwargs):
        default_theme = list()
        if cls not in _CLASSES_NOT_USING_PARENT_DEFAULT_THEMES:
            for parent in get_all_parent_class(cls, do_not_search_for=_CLASSES_NOT_USING_PARENT_DEFAULT_THEMES):
                default_theme += _DEFAULT_THEME.get(parent, list()) + _HIDDEN_DEFAULT_THEME.get(parent, list())
        default_theme += _DEFAULT_THEME.get(cls, list()) + _HIDDEN_DEFAULT_THEME.get(cls, list())
        theme = kwargs.pop("theme", None)
        if theme is None:
            theme = list()
        elif isinstance(theme, str):
            theme = [theme]
        theme_kwargs = cls.get_theme_options(*default_theme, *theme)
        return type.__call__(cls, *args, **(theme_kwargs | kwargs))

class ThemedObject(object, metaclass=MetaThemedObject):

    def __init_subclass__(cls, use_parent_theme=True, use_parent_default_theme=True, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if not use_parent_theme:
            _CLASSES_NOT_USING_PARENT_THEMES.append(cls)
            use_parent_default_theme = False
        if not use_parent_default_theme:
            _CLASSES_NOT_USING_PARENT_DEFAULT_THEMES.append(cls)

    @classmethod
    def set_theme(cls, name: str, options: dict[str, Any]) -> None:
        name = str(name)
        if not name.startswith("__"):
            theme_dict = _THEMES[_NAMESPACE].get(cls)
            if theme_dict is None:
                theme_dict = _THEMES[_NAMESPACE][cls] = dict()
        else:
            theme_dict = _HIDDEN_THEMES.get(cls)
            if theme_dict is None:
                theme_dict = _HIDDEN_THEMES[cls] = dict()
        if name not in theme_dict:
            theme_dict[name] = options
        else:
            theme_dict[name] |= options

    @classmethod
    def set_default_theme(cls, name: Union[str, Sequence[str], None]) -> None:
        if name is None:
            _DEFAULT_THEME.pop(cls, None)
        else:
            name = [name] if isinstance(name, str) else list(name)
            for theme in name:
                default_theme = _DEFAULT_THEME if not theme.startswith("__") else _HIDDEN_DEFAULT_THEME
                if cls not in default_theme:
                    default_theme[cls] = list()
                default_theme[cls].append(theme)

    @classmethod
    def get_theme_options(cls, *themes: str) -> dict[str, Any]:
        theme_kwargs = dict()
        for t in themes:
            if cls not in _CLASSES_NOT_USING_PARENT_THEMES:
                for parent in reversed(list(get_all_parent_class(cls, do_not_search_for=_CLASSES_NOT_USING_PARENT_THEMES))):
                    theme_kwargs |= cls.__get_theme_options(parent, t)
            theme_kwargs |= cls.__get_theme_options(cls, t)
        return theme_kwargs

    @staticmethod
    def __get_theme_options(cls, theme: str) -> dict[str, Any]:
        if theme.startswith("__"):
            return _HIDDEN_THEMES.get(cls, dict()).get(theme, dict())
        return _THEMES[_NAMESPACE].get(cls, dict()).get(theme, dict())

class ThemeNamespace(object):

    def __init__(self, namespace: Any):
        self.__namespace = namespace
        self.__save_namespace = None

    def __enter__(self):
        global _NAMESPACE
        self.__save_namespace = _NAMESPACE
        _NAMESPACE = self.__namespace
        if _NAMESPACE not in _THEMES:
            _THEMES[_NAMESPACE] = dict()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        global _NAMESPACE
        _NAMESPACE = self.__save_namespace