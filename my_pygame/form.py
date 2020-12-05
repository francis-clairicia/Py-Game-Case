# -*- coding: Utf-8 -*

from .window import Window
from .grid import Grid, GridCell
from .entry import Entry
from .text import Text

class Form(Grid):

    def __init__(self, master: Window, *, bg_color=None, label_justify="right", entry_justify="left"):
        Grid.__init__(self, master, bg_color)
        self.__entry = dict()
        self.__label_justify = label_justify
        self.__entry_justify = entry_justify

    def __getitem__(self, index: int) -> GridCell:
        cell = self.sorted_rows()[index].cells[1]
        return cell.get()

    def add_entry(self, name: str, label: Text, entry: Entry, padx=10, pady=10) -> None:
        row = self.last + 1
        self.place(label, row, 0, padx=padx, pady=pady, justify=self.__label_justify)
        self.place(entry, row, 1, padx=padx, pady=pady, justify=self.__entry_justify)
        self.__entry[str(name)] = entry

    def get_entry(self, name: str) -> Entry:
        return self.__entry[name]

    def get(self, name=None) -> str:
        if name is None:
            return {name: entry.get() for name, entry in self.__entry.items()}
        return self.get_entry(name).get()
