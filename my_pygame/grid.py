# -*- coding: Utf-8 -*

from typing import Tuple, Dict, Union, List, Type
import pygame
from .drawable import Drawable
from .focusable import Focusable
from .colors import TRANSPARENT
from .surface import create_surface

class GridCell(Focusable, Drawable):

    def __init__(self, master, row: int, column: int):
        Drawable.__init__(self)
        Focusable.__init__(self, master, highlight_color=TRANSPARENT, highlight_thickness=0)
        self.take_focus(False)
        self.__drawable = None
        self.__justify = str()
        self.__padx = self.__pady = 0
        self.__row = row
        self.__column = column

    def __repr__(self) -> str:
        return "<{} row={}, column={}>".format(self.__class__.__name__, self.__row, self.__column)

    def __str__(self) -> str:
        return repr(self)

    def get(self) -> Union[Drawable, Focusable, None]:
        return self.__drawable

    def after_drawing(self, surface: pygame.Surface) -> None:
        if isinstance(self.__drawable, Drawable):
            move = {
                "left":   {"left":   self.left + self.__padx,   "centery": self.centery},
                "right":  {"right":  self.right - self.__padx,  "centery": self.centery},
                "top":    {"top":    self.top + self.__pady,    "centerx": self.centerx},
                "bottom": {"bottom": self.bottom - self.__pady, "centerx": self.centerx},
                "center": {"center": self.center},
            }
            self.__drawable.move(**move[self.__justify])
            self.__drawable.draw(surface)

    def set_object(self, drawable: Union[Drawable, Focusable, None], padx: int, pady: int, justify: str) -> None:
        self.__drawable = drawable
        self.__justify = justify
        self.__padx = max(int(padx), 0)
        self.__pady = max(int(pady), 0)
        self.reset()
        self.take_focus(isinstance(drawable, Focusable))

    def reset(self) -> None:
        if not isinstance(self.__drawable, Drawable):
            self.image = create_surface((0, 0))
        else:
            width = self.__drawable.width + (self.__padx * 2)
            height = self.__drawable.height + (self.__pady * 2)
            self.image = create_surface((width, height))

    def set_obj_on_side(self, on_top=None, on_bottom=None, on_left=None, on_right=None) -> None:
        Focusable.set_obj_on_side(self, on_top=on_top, on_bottom=on_bottom, on_left=on_left, on_right=on_right)
        if isinstance(self.__drawable, Focusable):
            self.__drawable.set_obj_on_side(on_top=on_top, on_bottom=on_bottom, on_left=on_left, on_right=on_right)

    def on_focus_set(self) -> None:
        if isinstance(self.__drawable, Focusable):
            self.__drawable.focus_set()
    
    row = property(lambda self: self.__row)
    column = property(lambda self: self.__column)

class GridRow:
    
    def __init__(self, master, row: int):
        self.__master = master
        self.__row = row
        self.__cells = dict()

    def __repr__(self) -> str:
        return "<{} row={}>".format(self.__class__.__name__, self.__row)

    def __str__(self) -> str:
        return repr(self)

    @property
    def cells(self) -> Dict[int, GridCell]:
        return self.__cells

    def sorted_cells(self) -> List[GridCell]:
        return [cell for index, cell in sorted(self.cells.items(), key=lambda item: item[0])]

    @property
    def nb_columns(self) -> int:
        return max(self.cells.keys(), default=0)

    def add(self, obj: Union[Drawable, Focusable], column: int, padx: int, pady: int, justify: str) -> None:
        if column in self.cells:
            cell = self.cells[column]
        else:
            cell = self.cells[column] = GridCell(self.__master, self.__row, column)
        cell.set_object(obj, padx, pady, justify)

    def move(self, left: int, top: int, width_dict: Dict[int, int]) -> None:
        for i in range(self.nb_columns + 1):
            if i in self.cells:
                cell = self.cells[i]
                cell.move(left=left, top=top)
            left += width_dict[i]

    def draw(self, surface: pygame.Surface) -> None:
        for cell in self.cells.values():
            cell.draw(surface)

    def get_width(self) -> int:
        return sum(cell.width for cell in self.cells.values())

    def get_cell_width(self, index: int) -> int:
        if index not in self.cells:
            return 0
        return self.cells[index].width

    def get_height(self) -> int:
        return max((cell.height for cell in self.cells.values()), default=0)

    def reset(self) -> None:
        for cell in self.cells.values():
            cell.reset()

    def set_cell_size(self, width_dict: Dict[int, int], height_dict: Dict[int, int]) -> None:
        for cell in self.cells.values():
            cell.image = create_surface((width_dict[cell.column], height_dict[self.__row]))

    def index(self) -> int:
        return self.__row

class Grid(Drawable, use_parent_theme=False):

    def __init__(self, master, bg_color=None):
        Drawable.__init__(self)
        self.__master = master
        self.__bg_color = TRANSPARENT
        self.bg_color = bg_color
        self.__rows_dict = dict()
        self.__max_width_columns = dict()
        self.__max_height_rows = dict()

    @property
    def rows(self) -> Dict[int, GridRow]:
        return self.__rows_dict

    def sorted_rows(self) -> List[GridRow]:
        return sorted(self.rows.values(), key=lambda row: row.index())

    @property
    def nb_rows(self) -> int:
        return max(self.rows.keys(), default=0)

    @property
    def first(self) -> int:
        if not self.rows:
            return -1
        return self.sorted_rows()[0].index()

    @property
    def last(self) -> int:
        if not self.rows:
            return -1
        return self.sorted_rows()[-1].index()

    @property
    def nb_columns(self) -> int:
        return max((row.nb_columns for row in self.rows.values()), default=0)

    @property
    def bg_color(self) -> pygame.Color:
        return self.__bg_color

    @bg_color.setter
    def bg_color(self, color: pygame.Color) -> None:
        self.__bg_color = TRANSPARENT if color is None else pygame.Color(color)
        self.__update_background(self.size)

    def __update_background(self, size: Tuple[int, int]) -> None:
        self.image = create_surface(size)
        self.fill(self.__bg_color)

    def __getitem__(self, cell: Tuple[int, int]) -> Union[Drawable, Focusable]:
        return self.get(*cell)

    def __setitem__(self, cell: Tuple[int, int], infos: Dict[str, Union[int, Drawable, Focusable]]) -> None:
        self.place(row=cell[0], column=cell[1], **infos)

    def get(self, row: int, column: int) -> Union[Drawable, Focusable]:
        if row not in self.rows or column not in self.rows[row].cells:
            return None
        return self.rows[row].cells[column].get()

    def place(self, obj: Union[Drawable, Focusable], row: int, column: int, padx=0, pady=0, justify="center") -> None:
        self.__add_object(obj, row, column, padx, pady, justify)
        self.__update_grid()

    def place_multiple(self, obj_dict: Dict[Tuple[int, int], Union[Drawable, Focusable, Dict[str, Union[int, Drawable, Focusable]]]]) -> None:
        for (row, col), item in obj_dict.items():
            if isinstance(item, dict):
                self.__add_object(row=row, column=col, **item)
            else:
                self.__add_object(item, row, col)
        self.__update_grid()

    def __add_object(self, obj: Union[Drawable, Focusable], row: int, column: int, padx=0, pady=0, justify="center") -> None:
        row = max(int(row), 0)
        column = max(int(column), 0)
        if row in self.rows:
            grid_row = self.rows[row]
        else:
            grid_row = self.rows[row] = GridRow(self.__master, row)
        grid_row.add(obj, column, padx, pady, justify)

    def __update_grid(self) -> None:
        self.__max_width_columns.clear()
        self.__max_height_rows.clear()
        if self.rows:
            for row in self.rows.values():
                row.reset()
            for i in range(self.nb_columns + 1):
                self.__max_width_columns[i] = max(row.get_cell_width(i) for row in self.rows.values())
            for i in range(self.nb_rows + 1):
                self.__max_height_rows[i] = 0 if i not in self.rows else self.rows[i].get_height()
            for row in self.rows.values():
                row.set_cell_size(self.__max_width_columns, self.__max_height_rows)
            grid_width = max(row.get_width() for row in self.rows.values())
            grid_height = sum(row.get_height() for row in self.rows.values())
            self.__update_background((grid_width, grid_height))
            self.__set_obj_on_side_intern()
            self.__update_cell_positions()
        else:
            self.image = create_surface((0, 0))

    def after_drawing(self, surface: pygame.Surface) -> None:
        for row in self.rows.values():
            row.draw(surface)

    def move(self, **kwargs) -> None:
        Drawable.move(self, **kwargs)
        self.__update_cell_positions()

    def move_ip(self, x: float, y: float) -> None:
        Drawable.move_ip(self, x, y)
        self.__update_cell_positions()

    def __update_cell_positions(self) -> None:
        if not self.rows:
            return
        top = self.top
        for i in range(self.nb_rows + 1):
            if i in self.rows:
                row = self.rows[i]
                row.move(self.left, top, self.__max_width_columns)
            top += self.__max_height_rows[i]

    def set_size(self, *size: Union[int, Tuple[int, int]], smooth=True) -> None:
        return

    def set_width(self, width: float, smooth=True)-> None:
        return

    def set_height(self, height: float, smooth=True) -> None:
        return

    def __set_obj_on_side_intern(self) -> None:
        for row_index, row in self.rows.items():
            prev_row = self.rows.get(row_index - 1)
            next_row = self.rows.get(row_index + 1)
            for column_index, cell in filter(lambda item: isinstance(item[1], Focusable), row.cells.items()):
                prev_cell = row.cells.get(column_index - 1)
                next_cell = row.cells.get(column_index + 1)
                cell.set_obj_on_side(
                    on_top=None if not isinstance(prev_row, GridRow) else prev_row.cells.get(column_index),
                    on_bottom=None if not isinstance(next_row, GridRow) else next_row.cells.get(column_index),
                    on_left=prev_cell,
                    on_right=next_cell
                )

    def set_obj_on_side(self, on_top=None, on_bottom=None, on_left=None, on_right=None) -> None:
        if isinstance(self, Focusable):
            Focusable.set_obj_on_side(self, on_top, on_bottom, on_left, on_right)
        if self.rows:
            rows = self.sorted_rows()
            for cell in rows[0].cells.values():
                cell.set_obj_on_side(on_top=on_top)
            for cell in rows[-1].cells.values():
                cell.set_obj_on_side(on_bottom=on_bottom)
            for row in rows:
                cells = row.sorted_cells()
                cells[0].set_obj_on_side(on_left=on_left)
                cells[-1].set_obj_on_side(on_right=on_right)

    def remove_obj_on_side(self, *sides: str) -> None:
        if isinstance(self, Focusable):
            Focusable.remove_obj_on_side(self, *sides)
        if self.rows:
            rows = self.sorted_rows()
            if Focusable.ON_TOP in sides:
                for cell in rows[0].cells.values():
                    cell.remove_obj_on_side(Focusable.ON_TOP)
            if Focusable.ON_BOTTOM in sides:
                for cell in rows[-1].cells.values():
                    cell.remove_obj_on_side(Focusable.ON_BOTTOM)
            for row in rows:
                cells = row.sorted_cells()
                if Focusable.ON_LEFT in sides:
                    cells[0].remove_obj_on_side(Focusable.ON_LEFT)
                if Focusable.ON_RIGHT in sides:
                    cells[-1].remove_obj_on_side(Focusable.ON_RIGHT)

    @property
    def focusable(self) -> List[Focusable]:
        return self.find_objects(Focusable)

    @property
    def drawable(self) -> List[Drawable]:
        return self.find_objects(Drawable)

    @property
    def cells(self) -> List[GridCell]:
        return [cell for row in self.rows.values() for cell in row.cells.values()]

    def find_objects(self, obj_type: Type[object]) -> List[object]:
        obj_list = list()
        for row in self.rows.values():
            for cell in row.cells.values():
                obj = cell.get()
                if isinstance(obj, obj_type):
                    obj_list.append(obj)
        return obj_list
