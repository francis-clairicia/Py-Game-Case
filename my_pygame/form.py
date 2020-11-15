# -*- coding: Utf-8 -*

from typing import Sequence
from .focusable import Focusable
from .list import ButtonListVertical, DrawableListHorizontal
from .entry import Entry
from .text import Text

class LineForm(Focusable, DrawableListHorizontal):
    
    def __init__(self, label: Text, entry: Entry, offset: int):
        Focusable.__init__(self, entry.master, highlight_thickness=0)
        DrawableListHorizontal.__init__(self, offset=offset)
        self.__label = label
        self.__entry = entry
        self.add(label, entry)

    def on_focus_set(self) -> None:
        self.__entry.focus_set()

    def set_obj_on_side(self, on_top=None, on_bottom=None, on_left=None, on_right=None) -> None:
        Focusable.set_obj_on_side(self, on_top=on_top, on_bottom=on_bottom, on_left=on_left, on_right=on_right)
        self.__entry.set_obj_on_side(on_top=on_top, on_bottom=on_bottom, on_left=on_left, on_right=on_right)

    def update_offset(self, max_line_width: int, max_entry_width: int) -> None:
        self.offset = max_line_width - max_entry_width - self.__label.width

class Form(ButtonListVertical):

    def __init__(self, offset=0, bg_color=None, line_offset=10):
        ButtonListVertical.__init__(self, offset=offset, bg_color=bg_color, justify="left", make_uniform_size=False)
        self.__entry = dict()
        self.__lines = dict()
        self.__line_offset = line_offset

    def add_entry(self, name: str, label: Text, entry: Entry) -> None:
        line = LineForm(label, entry, self.__line_offset)
        self.add(line)
        self.__entry[str(name)] = entry
        self.__lines[str(name)] = line
        self.__update_line_form_offsets()

    def remove_entry(self, name: str) -> None:
        self.remove(self.__lines.pop(name, None))
        self.__entry.pop(name, None)
        self.__update_line_form_offsets()

    def get_entry(self, name: str) -> Entry:
        return self.__entry[name]

    def get(self, name=None) -> str:
        if name is None:
            return {name: entry.get() for name, entry in self.__entry.items()}
        return self.get_entry(name).get()

    @property
    def lines(self) -> Sequence[LineForm]:
        return self.list

    def __update_line_form_offsets(self) -> None:
        max_line_width = self.width
        max_entry_width = max(entry.width for entry in self.__entry.values())
        for line in self.lines:
            line.update_offset(max_line_width, max_entry_width)