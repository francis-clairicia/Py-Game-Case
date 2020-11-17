# -*- coding: Utf-8 -*

import random
from typing import Iterator, Sequence, Dict, List, Tuple
import pygame
from my_pygame import Window, Dialog, Image, ImageButton, Button, Text
from my_pygame import ButtonListHorizontal, ButtonListVertical, DrawableListVertical, Clickable, RectangleShape, CircleShape
from my_pygame import BLUE, WHITE, BLACK, GRAY_DARK, TRANSPARENT, YELLOW, RED, GREEN
from .constants import RESOURCES, BACKGROUND_COLOR, NB_ROWS, NB_COLUMNS, AI, LOCAL_PLAYER, LAN_PLAYER
from .ai import FourInARowAI

class Box(RectangleShape):

    def __init__(self, width: int, height: int, row: int, column: int):
        RectangleShape.__init__(self, width, height, TRANSPARENT)
        circle_radius = round(min(0.8 * self.width, 0.8 * self.height) / 2)
        self.__default_circle_color = BACKGROUND_COLOR
        self.__circle = CircleShape(circle_radius, self.__default_circle_color, outline=1, outline_color=WHITE)
        self.__row = row
        self.__col = column
        self.__value = 0

    @property
    def circle(self) -> CircleShape:
        return self.__circle

    def after_drawing(self, surface: pygame.Surface) -> None:
        RectangleShape.after_drawing(self, surface)
        self.__circle.center = self.center
        if self.value != 0:
            self.__circle.outline = 1
            self.__circle.outline_color = WHITE
        self.__circle.draw(surface)

    @property
    def value(self) -> int:
        return self.__value

    @value.setter
    def value(self, value: int) -> None:
        self.__circle.color = {0: self.__default_circle_color, 1: RED, 2: YELLOW}[value]
        self.__value = value

    row = property(lambda self: self.__row)
    col = property(lambda self: self.__col)
    default_circle_color = property(lambda self: self.__default_circle_color)

class ColumnGrid(Clickable, DrawableListVertical):

    def __init__(self, master, width: int, height: int, column: int):
        row_height = height // NB_ROWS
        DrawableListVertical.__init__(self, offset=0)
        for row in range(NB_ROWS):
            self.add(Box(width, row_height, row, column))
        Clickable.__init__(self, master, callback=lambda col=column: master.play(col))

    @property
    def available_boxes(self) -> Iterator[Box]:
        return filter(lambda box: box.value == 0, self.drawable)

    @property
    def boxes(self) -> Sequence[Box]:
        return self.drawable

    def full(self) -> bool:
        return (len(tuple(self.available_boxes)) == 0)

    def reset(self) -> None:
        for box in self.boxes:
            box.value = 0
        self.enable()

    def enable(self) -> None:
        self.set_enabled(True)

    def disable(self) -> None:
        self.set_enabled(False)

    def set_enabled(self, status: bool) -> None:
        self.hover = self.active = False
        self.take_focus(status)
        self.set_enabled_mouse(status)
        self.set_enabled_key_joy(status)

    def on_hover(self) -> None:
        self.focus_set()
        for box in self.available_boxes:
            box.circle.color = GRAY_DARK
            box.circle.outline_color = YELLOW
            box.circle.outline = 2

    def on_leave(self) -> None:
        for box in self.available_boxes:
            box.circle.color = box.default_circle_color
            box.circle.outline_color = WHITE
            box.circle.outline = 1

    def on_active_set(self) -> None:
        for box in self.available_boxes:
            box.circle.color = box.default_circle_color

class Grid(ButtonListHorizontal):

    def __init__(self, master, width: int, height: int):
        ButtonListHorizontal.__init__(self, offset=0, bg_color=BLUE, make_uniform_size=False)
        column_width = width // NB_COLUMNS
        for column in range(NB_COLUMNS):
            self.add(ColumnGrid(master, column_width, height, column))
        self.master = master

    @property
    def columns(self) -> Sequence[ColumnGrid]:
        return self.list

    @property
    def map(self) -> Dict[Tuple[int, int], int]:
        return {(box.row, box.col): box.value for column in self.columns for box in column.boxes}

    def after_drawing(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, WHITE, self.rect, width=2)

    def reset(self) -> None:
        for column in self.columns:
            column.reset()

    def full(self) -> bool:
        return all(column.full() for column in self.columns)

    def play(self, player: int, column: int) -> None:
        column_object = self.columns[column]
        column_object.disable()
        grid = self.map
        row = 0
        while grid.get((row + 1, column), -1) == 0:
            column_object.boxes[row].value = player
            self.master.draw_and_refresh(rect=column_object.rect)
            pygame.time.wait(35)
            column_object.boxes[row].value = 0
            row += 1
        column_object.boxes[row].value = player
        column_object.set_enabled(not column_object.full())

class EnemyQuitGame(Dialog):

    def __init__(self, master: Window):
        Dialog.__init__(self, master, bg_color=BLUE, outline=2, outline_color=WHITE)
        self.master = master
        self.bg = RectangleShape(self.width, self.height, (0, 0, 0, 170))
        self.text = Text(font=RESOURCES.font("heavy", 50))
        self.button_quit = Button(self, "Return to menu", theme=["section"], font=RESOURCES.font("heavy", 40), y_add_size=-25, callback=self.stop)
        self.objects.set_priority(self.bg, 0)
        self.master = master

    def on_quit(self) -> None:
        self.master.stop()

    def on_start_loop(self) -> None:
        self.button_quit.focus_set()

    def place_objects(self) -> None:
        self.text.center = self.frame.center
        self.button_quit.move(centerx=self.frame.centerx, bottom=self.frame.bottom - 10)

class FourInARowGameplay(Window):
    def __init__(self):
        Window.__init__(self, bg_color=BACKGROUND_COLOR)
        self.bind_key(pygame.K_ESCAPE, lambda event: self.stop())

        self.logo = Image(RESOURCES.IMG["logo"])
        arrow = pygame.transform.flip(RESOURCES.IMG["arrow"], True, False)
        self.button_back = ImageButton(self, img=arrow, width=100, callback=self.stop, active_offset=(0, 5), highlight_color=YELLOW)
        self.grid = Grid(self, self.width / 2, self.height * 0.75)
        self.__player_turn = 0
        self.player_who_start_first = 0
        self.player = 0
        self.__turn = str()
        self.__turn_dict = dict()
        self.__score_player = self.__score_enemy = 0
        self.__highlight_line_window_callback = None
        self.enemy = str()

        self.ai = FourInARowAI()

        self.text_score = Text()
        self.text_player_turn = Text()
        self.left_options = ButtonListVertical(offset=50)
        self.left_options.add(
            Button(self, "Restart", theme="option", callback=self.restart),
            Button(self, "Quit game", theme="option", callback=self.close)
        )
        self.text_winner = Text()
        self.text_drawn_match = Text("Drawn match.")

        self.enemy_quit_dialog = EnemyQuitGame(self)

    def start(self, enemy: str, player=1, player_name=None, enemy_name=None, ai_level=None) -> None:
        self.player = player
        self.enemy = enemy
        if enemy == LAN_PLAYER:
            player_name = str(player_name)
            self.client_socket.send("name", player_name)
            result = self.client_socket.wait_for("name")
            if result == self.client_socket.QUIT_MESSAGE:
                return
            enemy_name = str(self.client_socket.get(result))
            self.__turn_dict = {
                1: {1: player_name, 2: enemy_name}[player],
                2: {1: enemy_name, 2: player_name}[player]
            }
            self.left_options[0].callback = self.LAN_restart
        else:
            player_name = str(player_name) if player_name is not None else "P1"
            enemy_name = str(enemy_name) if enemy_name is not None else "P2"
            self.__turn_dict = {
                1: "You" if self.enemy == AI else player_name,
                2: "AI" if self.enemy == AI else enemy_name
            }
            if self.enemy == AI:
                self.ai.level = ai_level
            self.left_options[0].callback = self.restart
        self.mainloop()

    def on_start_loop(self) -> None:
        self.grid[0].focus_set()
        self.score_player = self.score_enemy = 0
        self.player_who_start_first = 0
        self.text_winner.hide()
        self.restart()

    def on_quit(self) -> None:
        self.stop_connection()

    def restart(self) -> None:
        self.grid.reset()
        self.remove_window_callback(self.__highlight_line_window_callback)
        if self.player_who_start_first == 0:
            if self.enemy == AI:
                self.player_turn = 1
            elif self.enemy == LOCAL_PLAYER or (self.enemy == LAN_PLAYER and self.player == 1):
                self.player_turn = random.randint(1, 2)
                if self.enemy == LAN_PLAYER:
                    self.client_socket.send("player_turn", int(self.player_turn))
            elif self.enemy == LAN_PLAYER and self.player == 2:
                result = self.client_socket.wait_for("player_turn")
                if result == self.client_socket.QUIT_MESSAGE:
                    self.stop()
                    return
                self.player_turn = self.client_socket.get(result)
        elif self.text_winner.is_shown():
            self.player_turn = (self.player_who_start_first % 2) + 1
        else:
            self.player_turn = self.player_who_start_first
        self.player_who_start_first = self.player_turn
        self.text_winner.hide()
        self.text_drawn_match.hide()

    def LAN_restart(self) -> None:
        self.client_socket.send("restart")
        self.restart()

    def place_objects(self) -> None:
        self.logo.move(centerx=self.centerx, top=10)
        self.grid.midbottom = self.midbottom
        self.text_score.move(left=10, top=self.grid.top)
        self.text_player_turn.move(left=self.text_score.left, top=self.text_score.bottom + 50)
        self.left_options.move(centerx=(self.left + self.grid.left) // 2, top=self.text_player_turn.bottom + 50)
        self.text_winner.center = ((self.grid.right + self.right) // 2, self.grid.centery)
        self.text_drawn_match.center = self.text_winner.center

    def set_grid(self) -> None:
        self.grid.set_obj_on_side(on_top=self.button_back, on_left=self.left_options[0])
        self.button_back.set_obj_on_side(on_bottom=self.left_options[0], on_right=self.grid[0])
        self.left_options.set_obj_on_side(on_top=self.button_back, on_right=self.grid[0])

    @property
    def player_turn(self) -> int:
        return self.__player_turn

    @player_turn.setter
    def player_turn(self, player: int) -> None:
        self.__player_turn = player
        self.__turn = turn = self.__turn_dict[player]
        self.text_player_turn.message = f"Player turn:\n{turn}"
        self.place_objects()
        if self.enemy != LOCAL_PLAYER:
            for column in filter(lambda column: not column.full(), self.grid.columns):
                column.set_enabled(self.player_turn == self.player)
            if self.enemy == AI and self.player_turn == 2:
                self.after(500, lambda: self.play(self.ai.play(self.grid.map)))

    @property
    def score_player(self) -> int:
        return self.__score_player

    @score_player.setter
    def score_player(self, value: int) -> None:
        self.__score_player = value
        self.__update_text_score()

    @property
    def score_enemy(self) -> int:
        return self.__score_enemy

    @score_enemy.setter
    def score_enemy(self, value: int) -> None:
        self.__score_enemy = value
        self.__update_text_score()

    def __update_text_score(self) -> None:
        self.text_score.message = "Score:\n{you}: {score_1}\n{enemy}: {score_2}".format(
            you=self.__turn_dict[1], enemy=self.__turn_dict[2],
            score_1=self.score_player, score_2=self.score_enemy
        )
        self.place_objects()

    def update(self) -> None:
        if self.enemy == LAN_PLAYER:
            if self.client_socket.recv("column"):
                self.play(self.client_socket.get("column"))
            if self.client_socket.recv("restart"):
                self.restart()
            if self.client_socket.recv(self.client_socket.QUIT_MESSAGE):
                self.enemy_quit_dialog.text.message = "{}\nhas left the game".format(self.__turn_dict[(self.player % 2) + 1])
                self.enemy_quit_dialog.mainloop()

    def play(self, column: int) -> None:
        self.block_only_event([
            pygame.KEYDOWN,
            pygame.KEYUP,
            pygame.JOYBUTTONDOWN,
            pygame.JOYBUTTONUP,
            pygame.MOUSEBUTTONDOWN,
            pygame.MOUSEBUTTONUP
        ])
        if self.enemy == LAN_PLAYER and self.player_turn == self.player:
            self.client_socket.send("column", column)
        self.grid.play(self.player_turn, column)
        line = self.check_victory()
        if line:
            for column in self.grid.columns:
                column.disable()
            self.left_options[0].focus_set()
            self.update_winner()
            self.highlight_line(line)
        elif self.grid.full():
            self.left_options[0].focus_set()
            self.text_drawn_match.show()
        else:
            self.player_turn = (self.player_turn % 2) + 1
        self.allow_all_events()

    def check_victory(self) -> List[Tuple[int, int]]:
        grid = self.grid.map
        grid_pos_getter = [
            lambda row, col, index: (row, col + index),         # Check row (->)
            lambda row, col, index: (row, col - index),         # Check row (<-)
            lambda row, col, index: (row + index, col),         # Check column
            lambda row, col, index: (row + index, col - index), # Check diagonal (/)
            lambda row, col, index: (row + index, col + index), # Check diagonal (\)
        ]
        all_box_pos = list()
        box_pos = list()
        for row, column in filter(lambda pos: grid[pos] != 0, grid):
            for grid_pos in grid_pos_getter:
                index = 0
                box_pos.clear()
                while grid.get(grid_pos(row, column, index), -1) == grid[row, column]:
                    box_pos.append(grid_pos(row, column, index))
                    index += 1
                if len(box_pos) >= 4:
                    all_box_pos.extend(filter(lambda pos: pos not in all_box_pos, box_pos))
        return all_box_pos

    def highlight_line(self, line: List[Tuple[int, int]], highlight=True):
        for row, col in line:
            box = self.grid.columns[col].boxes[row]
            if highlight:
                box.circle.color = GREEN
            else:
                box.value = box.value
        self.__highlight_line_window_callback = self.after(500, lambda: self.highlight_line(line, not highlight))

    def update_winner(self):
        if self.player_turn == 1:
            self.score_player += 1
        else:
            self.score_enemy += 1
        winner = self.__turn
        self.text_winner.message = f"Winner:\n{winner}"
        self.text_winner.show()