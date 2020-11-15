# -*- coding: Utf-8 -*

import math
import random
from typing import Dict, Tuple, List

class FourInARowAI:

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"
    __LEVELS = [EASY, MEDIUM, HARD]

    def __init__(self):
        self.__level = FourInARowAI.EASY
        self.__level_function_dict = {
            FourInARowAI.EASY: self.__level_easy,
            FourInARowAI.MEDIUM: self.__level_medium
        }

    @property
    def level(self) -> str:
        return self.__level

    @level.setter
    def level(self, lvl: str) -> None:
        if lvl not in FourInARowAI.__LEVELS:
            raise ValueError("AI level must be one of the following: " + ", ".join(FourInARowAI.__LEVELS))
        self.__level = lvl

    @staticmethod
    def get_available_levels() -> Tuple[str, ...]:
        return tuple(FourInARowAI.__LEVELS)

    def play(self, grid: Dict[Tuple[int, int], int]) -> int:
        print("--------->")
        available_columns = self.__get_available_columns(grid)
        if len(available_columns) == 1:
            print("Last column")
            return available_columns[0]
        column = self.__check_for_line(grid)
        if column >= 0:
            return column
        columns_to_avoid = {
            1: self.__get_columns_to_avoid(grid, player=1),
            2: self.__get_columns_to_avoid(grid, player=2)
        }
        all_columns_to_avoid = list(dict.fromkeys(columns_to_avoid[1] + columns_to_avoid[2]))
        if all_columns_to_avoid:
            print("Columns to avoid:", all_columns_to_avoid)
        if all(column in all_columns_to_avoid for column in available_columns):
            print("Forced to play in a column to avoid")
            return random.choice(columns_to_avoid[2] or columns_to_avoid[1])
        return self.__level_function_dict[self.__level](grid, list(filter(lambda col: col not in all_columns_to_avoid, available_columns)))

    def __get_available_columns(self, grid: Dict[Tuple[int, int], int]) -> List[int]:
        return list(col for row, col in filter(lambda pos: (pos[0] == 0 and grid[pos] == 0), grid))

    def __check_for_line(self, grid: Dict[Tuple[int, int], int]) -> int:
        grid_pos_func_2d_list = [
            [lambda row, col, index: (row, col - index), lambda row, col, index: (row, col + index)],                 # Row (<->)
            [lambda row, col, index: (row + index, col), lambda row, col, index: tuple()],                            # Column (|)
            [lambda row, col, index: (row + index, col - index), lambda row, col, index: (row - index, col + index)], # Diagonal (/)
            [lambda row, col, index: (row + index, col + index), lambda row, col, index: (row - index, col - index)], # Diagonal (\)
        ]
        for player in [2, 1]:
            for row, col in filter(lambda pos: (grid[pos] == 0 and grid.get((pos[0] + 1, pos[1]), -1) != 0), grid):
                for grid_pos_func_list in grid_pos_func_2d_list:
                    nb_token = 0
                    for grid_pos in grid_pos_func_list:
                        index = 1
                        while grid.get(grid_pos(row, col, index), -1) == player:
                            nb_token += 1
                            index += 1
                    if nb_token >= 3:
                        print("Line of 4 for", {1: "P1", 2: "IA"}[player])
                        return col
        return -1

    def __get_columns_to_avoid(self, grid: Dict[Tuple[int, int], int], player: int) -> List[int]:
        grid_pos_func_2d_list = [
            [lambda row, col, index: (row, col - index), lambda row, col, index: (row, col + index)],                 # Row (<->)
            [lambda row, col, index: (row + index, col - index), lambda row, col, index: (row - index, col + index)], # Diagonal (/)
            [lambda row, col, index: (row + index, col + index), lambda row, col, index: (row - index, col - index)], # Diagonal (\)
        ]
        columns = list()
        for row, col in filter(lambda pos: (grid[pos] == grid.get((pos[0] + 1, pos[1]), -1) == 0 and grid.get((pos[0] + 2, pos[1]), -1) != 0), grid):
            for grid_pos_func_list in grid_pos_func_2d_list:
                nb_token = 0
                for grid_pos in grid_pos_func_list:
                    index = 1
                    while grid.get(grid_pos(row, col, index), -1) == player:
                        nb_token += 1
                        index += 1
                if nb_token >= 3 and col not in columns:
                    columns.append(col)
        return columns

    def __level_easy(self, grid: Dict[Tuple[int, int], int], valid_columns: List[int]) -> int:
        print("Full random")
        return random.choice(valid_columns)

    def __level_medium(self, grid: Dict[Tuple[int, int], int], valid_columns: List[int]) -> int:
        ## First strategy
        last_row = max(pos[0] for pos in grid)
        middle_col = math.ceil(max(pos[1] for pos in grid) / 2)
        for column in [middle_col, middle_col - 1, middle_col + 1]:
            if grid.get((last_row, column), -1) == 0:
                print("First strategy")
                return column
        ## Second strategy
        grid_pos_func_2d_list = [
            [lambda row, col: (row, col + 1),     [lambda row, col: (row, col + 2), lambda row, col: (row, col - 1)]],         # Row (->)
            [lambda row, col: (row + 1, col),     [lambda row, col: (row - 1, col)]],                                          # Column (|)
            [lambda row, col: (row + 1, col - 1), [lambda row, col: (row + 2, col - 2), lambda row, col: (row - 1, col + 1)]], # Diagonal (/)
            [lambda row, col: (row + 1, col + 1), [lambda row, col: (row + 2, col + 2), lambda row, col: (row -1, col - 1)]],  # Diagonal (\)
        ]
        line_of_two_tokens = list()
        for player in [1, 2]:
            for grid_pos, grid_pos_possibilities_list in grid_pos_func_2d_list:
                for row, col in filter(lambda pos: grid[pos] == grid.get(grid_pos(*pos), -1) == player, grid):
                    possibilities = list()
                    for grid_pos_possibility in grid_pos_possibilities_list:
                        r, c = grid_pos_possibility(row, col)
                        if grid.get((r, c), -1) == 0 and grid.get((r + 1, c), -1) != 0 and c in valid_columns:
                            possibilities.append(c)
                    if possibilities:
                        line_of_two_tokens.append(possibilities)
            if line_of_two_tokens:
                print("Second strategy")
                all_possibilities = dict()
                for nb_possibilities in [1, 2]:
                    possibilities_list = list(filter(lambda possibilities: len(possibilities) == nb_possibilities, line_of_two_tokens))
                    all_possibilities[nb_possibilities] = [column for possibility in possibilities_list for column in possibility]
                return random.choice(all_possibilities[2] or all_possibilities[1])
        #Last strategy
        print("Random")
        return random.choice(valid_columns)