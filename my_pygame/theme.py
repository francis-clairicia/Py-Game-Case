# -*- coding: Utf-8 -*

from typing import Dict, Any, Type, Iterator, Union, Sequence, Optional

def get_all_parent_class(cls: Type[object], do_not_search_for: Optional[Sequence[Type[object]]] = list()) -> Iterator[Type[object]]:
    for base in cls.__bases__:
        yield base
        if base not in do_not_search_for:
            yield from get_all_parent_class(base)

_THEMES = dict()
_DEFAULT_THEME = dict()
_CLASSES_NOT_USING_PARENT_THEMES = list()
_CLASSES_NOT_USING_PARENT_DEFAULT_THEMES = list()

class MetaThemedObject(type):
    
    def __call__(cls, *args, **kwargs):
        default_theme = list()
        if cls not in _CLASSES_NOT_USING_PARENT_DEFAULT_THEMES:
            for parent in get_all_parent_class(cls, do_not_search_for=_CLASSES_NOT_USING_PARENT_DEFAULT_THEMES):
                default_theme += _DEFAULT_THEME.get(parent, list())
        default_theme += _DEFAULT_THEME.get(cls, list())
        theme = kwargs.pop("theme", None)
        if theme is None:
            theme = list()
        elif isinstance(theme, str):
            theme = [theme]
        theme_kwargs = cls.get_theme_options(*default_theme, *theme)
        theme_kwargs.update(kwargs)
        return type.__call__(cls, *args, **theme_kwargs)

class ThemedObject(object, metaclass=MetaThemedObject):

    def __init_subclass__(cls, use_parent_theme=True, use_parent_default_theme=True, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if not use_parent_theme:
            _CLASSES_NOT_USING_PARENT_THEMES.append(cls)
            use_parent_default_theme = False
        if not use_parent_default_theme:
            _CLASSES_NOT_USING_PARENT_DEFAULT_THEMES.append(cls)

    @classmethod
    def set_theme(cls, name: str, options: Dict[str, Any]) -> None:
        theme_dict = _THEMES.get(cls)
        if theme_dict is None:
            theme_dict = _THEMES[cls] = dict()
        name = str(name)
        if name not in theme_dict:
            theme_dict[name] = options
        else:
            theme_dict[name].update(options)

    @classmethod
    def set_default_theme(cls, name: Union[str, Sequence[str], None]) -> None:
        if name is None:
            if cls in _DEFAULT_THEME and any(default_theme.startswith("__") for default_theme in _DEFAULT_THEME[cls]):
                _DEFAULT_THEME[cls] = list(filter(lambda theme: theme.startswith("__"), _DEFAULT_THEME[cls]))
            else:
                _DEFAULT_THEME.pop(cls, None)
        else:
            name = [name] if isinstance(name, str) else list(name)
            if cls not in _DEFAULT_THEME or all(not default_theme.startswith("__") for default_theme in _DEFAULT_THEME[cls]):
                _DEFAULT_THEME[cls] = name
            else:
                _DEFAULT_THEME[cls] = list(filter(lambda theme: theme.startswith("__"), _DEFAULT_THEME[cls])) + name

    @classmethod
    def get_theme_options(cls, *themes: str) -> Dict[str, Any]:
        theme_kwargs = dict()
        for t in themes:
            if cls not in _CLASSES_NOT_USING_PARENT_THEMES:
                for parent in reversed(list(get_all_parent_class(cls, do_not_search_for=_CLASSES_NOT_USING_PARENT_THEMES))):
                    theme_kwargs.update(_THEMES.get(parent, dict()).get(t, dict()))
            theme_kwargs.update(_THEMES.get(cls, dict()).get(t, dict()))
        return theme_kwargs