# -*- coding: Utf-8 -*

import sys
import random
import json
import pygame
from typing import Sequence, Any, Union
from my_pygame import Window, DrawableList, Grid
from my_pygame import Image, ImageButton, Text, RectangleShape, Button, Sprite
from my_pygame import GREEN, GREEN_DARK, WHITE, YELLOW, TRANSPARENT, RED, RED_DARK
from my_pygame import ClientSocket
from .constants import RESOURCES, NB_LINES_BOXES, NB_COLUMNS_BOXES, BOX_SIZE, NB_SHIPS

def print_navy_map(navy_map: dict[tuple[int, int], int], higlight_box=None) -> None:
    navy_list = [[0 for _ in range(NB_COLUMNS_BOXES)] for _ in range(NB_LINES_BOXES)]
    for (l, c), value in navy_map.items():
        navy_list[l][c] = value if higlight_box is None or (l, c) != tuple(higlight_box) else f"({value})"
    for line in navy_list:
        print(line)
    print("-" * NB_COLUMNS_BOXES)

class NavyGridBox(Button, use_parent_theme=False, draw_focus_outline=False):
    def __init__(self, master, navy, size: tuple[int, int], pos: tuple[int, int]):
        params = {
            "size": size,
            "bg": TRANSPARENT,
            "hover_bg": GREEN,
            "active_bg": GREEN_DARK,
            "disabled_bg": TRANSPARENT,
            "disabled_hover_bg": RED,
            "disabled_active_bg": RED_DARK,
            "outline_color": WHITE,
            "highlight_color": WHITE,
        }
        Button.__init__(self, master=master, callback=lambda: master.hit_a_box(navy, self), **params)
        self.pos = pos

    def reset(self) -> None:
        self.state = Button.NORMAL
        self.hover = False
        self.focus_leave()

class Ship(Image):

    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"

    def __init__(self, name: str, boxes: Sequence[tuple[int, int]], orient: str):
        Image.__init__(self, RESOURCES.IMG[name])
        self.name = name
        self.__orient = Ship.VERTICAL
        self.ship_size = len(boxes)
        self.boxes_pos = [tuple(box_pos) for box_pos in boxes]
        self.set_height(self.ship_size * BOX_SIZE[0])
        self.orient = orient
        self.__boxes_covered = list()

    def get_setup(self) -> dict[str, Any]:
        return {"name": self.name, "boxes": self.boxes_pos, "orient": self.orient}

    @property
    def orient(self) -> str:
        return self.__orient

    @orient.setter
    def orient(self, orient: str) -> None:
        if orient in (Ship.VERTICAL, Ship.HORIZONTAL) and orient != self.__orient:
            if orient == Ship.HORIZONTAL:
                self.rotate(90)
            else:
                self.rotate(-90)
            self.__orient = orient

    @property
    def boxes_covered(self) -> Sequence[NavyGridBox]:
        return self.__boxes_covered

    @boxes_covered.setter
    def boxes_covered(self, boxes: Sequence[NavyGridBox]) -> None:
        self.__boxes_covered = boxes

    def destroyed(self) -> bool:
        return all(box.state == Button.DISABLED for box in self.boxes_covered)

    def place_ship(self, boxes: Sequence[NavyGridBox]):
        left = min(boxes, key=lambda box: box.left).left
        top = min(boxes, key=lambda box: box.top).top
        right = max(boxes, key=lambda box: box.right).right
        bottom = max(boxes, key=lambda box: box.bottom).bottom
        width = right - left
        height = bottom - top
        rect = pygame.Rect(left, top, width, height)
        self.center = rect.center
        self.boxes_covered = boxes

class Navy(Grid):

    BOX_NO_HIT = 0
    BOX_HATCH = 1
    BOX_CROSS = 2
    BOX_SHIP_DESTROYED = 3

    def __init__(self, master):
        Grid.__init__(self, master, bg_color=(0, 157, 255))
        self.master = master
        self.place_multiple({
            (i, j): NavyGridBox(master, navy=self, size=BOX_SIZE, pos=(i, j))
            for i in range(NB_LINES_BOXES) for j in range(NB_COLUMNS_BOXES)
        })
        self.ships_list = DrawableList()
        self.box_hit_img = DrawableList()

    def load_setup(self, setup: Sequence[dict[str, Any]]) -> None:
        for ship_infos in setup:
            self.add_ship(Ship(**ship_infos))

    def reset(self) -> None:
        self.ships_list.clear()
        self.box_hit_img.clear()
        for box in self.boxes:
            box.reset()
        self.set_box_clickable(True)

    @property
    def map(self) -> dict[tuple[int, int], int]:
        navy_map = {box.pos: Navy.BOX_NO_HIT if box.state == Button.NORMAL else Navy.BOX_HATCH for box in self.boxes}
        for box_pos in filter(lambda pos: navy_map[pos] == Navy.BOX_HATCH, navy_map):
            for ship in self.ships:
                if box_pos in ship.boxes_pos:
                    navy_map[box_pos] = Navy.BOX_SHIP_DESTROYED if ship.destroyed() else Navy.BOX_CROSS
                    break
        return navy_map

    def after_drawing(self, surface: pygame.Surface) -> None:
        super().after_drawing(surface)
        self.ships_list.draw(surface)
        self.box_hit_img.draw(surface)

    def add_ship(self, ship: Ship) -> None:
        self.ships_list.add(ship)
        self.move()

    def get_box(self, line: int, column: int) -> NavyGridBox:
        return {box.pos: box for box in self.boxes}.get((line, column))

    def set_box_clickable(self, click: bool) -> None:
        for box in self.boxes:
            if click:
                box.enable_key_joy()
                box.enable_mouse()
            else:
                box.disable_key_joy()
                box.disable_mouse()
            box.hover = False

    def destroyed(self) -> bool:
        return len(self.ships) == NB_SHIPS and all(ship.destroyed() for ship in self.ships)

    @property
    def boxes(self) -> Sequence[NavyGridBox]:
        return self.drawable

    @property
    def ships(self) -> Sequence[Ship]:
        return self.ships_list.drawable

    def move(self, **kwargs):
        Grid.move(self, **kwargs)
        for ship in self.ships:
            ship.place_ship(list(filter(lambda box: box.pos in ship.boxes_pos, self.boxes)))

    def box_hit(self, box: NavyGridBox) -> bool:
        pass

    def set_box_hit(self, box: NavyGridBox, hit: bool) -> None:
        box.state = Button.DISABLED
        hit = bool(hit)
        img = {False: "hatch", True: "cross"}[hit]
        image = Image(RESOURCES.IMG[img], size=box.size)
        image.center = box.center
        self.box_hit_img.add(image)

    def hit_all_boxes_around_ship(self, ship: Ship):
        offsets = [
            (-1, -1),
            (0, -1),
            (1, -1),
            (-1, 0),
            (1, 0),
            (-1, 1),
            (0, 1),
            (1, 1)
        ]
        for box in ship.boxes_covered:
            line, column = box.pos
            for u, v in offsets:
                box = self.get_box(line + u, column + v)
                if box is None:
                    continue
                if box.state == Button.NORMAL:
                    self.set_box_hit(box, False)

class PlayerNavy(Navy):
    def __init__(self, master, player: ClientSocket):
        Navy.__init__(self, master)
        self.set_box_clickable(False)
        self.client_socket = player

    def box_hit(self, box: NavyGridBox) -> bool:
        attack_result = {
            "hit": False,
            "ship_destroyed": None
        }
        for ship in self.ships:
            if box in ship.boxes_covered:
                self.set_box_hit(box, True)
                attack_result["hit"] = True
                if ship.destroyed():
                    self.hit_all_boxes_around_ship(ship)
                    attack_result["ship_destroyed"] = ship.get_setup()
                self.client_socket.send("attack_result", attack_result)
                return True
        self.client_socket.send("attack_result", attack_result)
        self.set_box_hit(box, False)
        return False

    def send_non_destroyed_ships(self):
        self.client_socket.send("non_destroyed_ships", [ship.get_setup() for ship in filter(lambda ship: not ship.destroyed(), self.ships)])

class OppositeNavy(Navy):
    def __init__(self, master, player: ClientSocket):
        Navy.__init__(self, master)
        self.client_socket = player
        self.ai_setup = list()

    def box_hit(self, box: NavyGridBox) -> bool:
        if not self.client_socket.connected():
            return self.ai_box_hit(box)
        return self.player_box_hit(box)

    def ai_box_hit(self, box: NavyGridBox) -> bool:
        for ship_infos in self.ai_setup.copy():
            boxes_covered = list(filter(lambda box: box.pos in ship_infos["boxes"], self.boxes))
            if box in boxes_covered:
                self.set_box_hit(box, True)
                if all(box.state == Button.DISABLED for box in boxes_covered):
                    ship = Ship(**ship_infos)
                    self.ai_setup.remove(ship_infos)
                    self.add_ship(ship)
                    self.hit_all_boxes_around_ship(ship)
                return True
        self.set_box_hit(box, False)
        return False

    def player_box_hit(self, box: NavyGridBox) -> bool:
        self.client_socket.send("attack", json.dumps(box.pos))
        attack_result = self.client_socket.get(self.client_socket.wait_for("attack_result"))
        if not isinstance(attack_result, dict):
            return False
        if attack_result["hit"]:
            self.set_box_hit(box, True)
            if attack_result["ship_destroyed"] is not None:
                ship_infos = attack_result["ship_destroyed"]
                ship = Ship(**ship_infos)
                self.add_ship(ship)
                self.hit_all_boxes_around_ship(ship)
            return True
        self.set_box_hit(box, False)
        return False

    def show_all_non_destroyed_ships(self) -> Sequence[Ship]:
        if not self.client_socket.connected():
            ship_setup = self.ai_setup
        else:
            ship_setup = self.client_socket.get(self.client_socket.wait_for("non_destroyed_ships"))
        all_ships = list()
        for ship_infos in ship_setup:
            ship = Ship(**ship_infos)
            self.add_ship(ship)
            all_ships.append(ship)
            for box in ship.boxes_covered:
                box.hover = False
                box.state = Button.NORMAL
        return all_ships

class TurnArrow(Sprite):
    def __init__(self, **kwargs):
        Sprite.__init__(self)
        self.__turn = True
        self.add_sprite(True, RESOURCES.IMG["green_triangle"], **kwargs)
        self.add_sprite(False, RESOURCES.IMG["red_triangle"], **kwargs)

    @property
    def turn(self) -> bool:
        return self.__turn

    @turn.setter
    def turn(self, state: bool) -> None:
        self.__turn = bool(state)
        self.set_sprite_list(self.__turn)

class AI:
    def __init__(self):
        self.box_hitted = list()
        self.possibilities = list()

    def reset(self) -> None:
        self.box_hitted.clear()
        self.possibilities = [(i, j) for i in range(NB_LINES_BOXES) for j in range(NB_COLUMNS_BOXES)]

    def play(self, navy_map: dict[tuple[int, int], int]) -> tuple[int, int]:
        for box_pos in filter(lambda pos: navy_map[pos] == Navy.BOX_SHIP_DESTROYED, self.box_hitted.copy()):
            self.box_hitted.remove(box_pos)
        for box_pos in filter(lambda pos: navy_map[pos] != Navy.BOX_NO_HIT, self.possibilities.copy()):
            if navy_map[box_pos] == Navy.BOX_CROSS:
                self.box_hitted.append(box_pos)
            self.possibilities.remove(box_pos)
        if self.box_hitted:
            return self.track_ship(navy_map)
        return random.choice(self.possibilities)

    def track_ship(self, navy_map: dict[tuple[int, int], int]) -> tuple[int, int]:
        if len(self.box_hitted) == 1:
            return self.find_ship(navy_map, *self.box_hitted[0])
        self.box_hitted.sort()
        index = 1 if self.box_hitted[0][0] == self.box_hitted[-1][0] else 0
        first, second = list(self.box_hitted[0]), list(self.box_hitted[-1])
        first[index] -= 1
        second[index] += 1
        potential_boxes = list()
        for x, y in [first, second]:
            if (x, y) in navy_map and navy_map[x, y] == Navy.BOX_NO_HIT:
                potential_boxes.append((x, y))
        if not potential_boxes:
            print_navy_map(navy_map)
            sys.exit(1)
        return random.choice(potential_boxes)

    def find_ship(self, navy_map: dict[tuple[int, int], int], line: int, column: int) -> tuple[int, int]:
        offsets = [
            (0, -1),
            (-1, 0),
            (1, 0),
            (0, 1)
        ]
        potential_boxes = list()
        for pos in [(line + u, column + v) for u, v in offsets]:
            if pos in navy_map and navy_map[pos] == Navy.BOX_NO_HIT:
                potential_boxes.append(pos)
        if not potential_boxes:
            print_navy_map(navy_map, higlight_box=(line, column))
            sys.exit(1)
        return random.choice(potential_boxes)

class FinishWindow(Window):
    def __init__(self, master):
        Window.__init__(self, master=master)
        self.master = master
        self.bg = RectangleShape(self.width, self.height, (0, 0, 0, 170))
        self.frame = RectangleShape(0.5 * self.width, 0.5 * self.height, GREEN_DARK, outline=2)
        self.victory = None
        self.text_finish = Text(font=(None, 70))
        self.button_restart = Button(self, "Restart", font=(None, 40), callback=self.restart)
        self.button_return_to_menu = Button(self, "Return to menu", font=(None, 40), callback=self.stop)
        self.ask_restart = False
        self.bind_key(pygame.K_ESCAPE, lambda event: self.stop())

    def start(self, victory: bool) -> None:
        self.victory = victory
        if victory is not None:
            self.text_finish.message = "{winner} won".format(winner="You" if victory else "Enemy")
        else:
            self.text_finish.message = "The enemy has left\nthe game"
        self.ask_restart = False
        self.mainloop()

    def update(self):
        if self.ask_restart:
            if self.master.client_socket.recv("restart"):
                self.master.restart = True
                self.stop()
            elif self.master.client_socket.recv("quit"):
                self.text_finish.message = "The enemy has left\nthe game"

    def place_objects(self):
        self.frame.center = self.center
        self.text_finish.center = self.frame.center
        if self.victory is not None:
            self.button_restart.move(bottom=self.frame.bottom - 20, centerx=self.frame.centerx - (self.frame.w // 4))
            self.button_return_to_menu.move(bottom=self.frame.bottom - 20, centerx=self.frame.centerx + (self.frame.w // 4))
        else:
            self.button_restart.hide()
            self.button_return_to_menu.move(bottom=self.frame.bottom - 20, centerx=self.frame.centerx)

    def restart(self):
        if self.master.client_socket.connected():
            self.ask_restart = True
            self.master.client_socket.send("restart")
            self.text_finish.message = "Waiting for\nenemy response"
            self.button_restart.hide()
            self.button_return_to_menu.move(bottom=self.frame.bottom - 20, centerx=self.frame.centerx)
        else:
            self.master.restart = True
            self.stop()

class Gameplay(Window):
    def __init__(self):
        Window.__init__(self, bg_color=(0, 200, 255))
        self.player_id = 0
        self.button_back = ImageButton(self, RESOURCES.IMG["arrow_blue"], rotate=180, size=50, callback=self.stop, highlight_color=YELLOW)
        self.player_grid = PlayerNavy(self, self.client_socket)
        self.opposite_grid = OppositeNavy(self, self.client_socket)
        self.ai = AI()
        self.turn_checker = TurnArrow()
        self.restart = False
        self.bind_key(pygame.K_ESCAPE, lambda event: self.stop())
        self.text_finish = Text("Finish !!!", font=(None, 120), color=WHITE)
        self.window_finish = FinishWindow(self)
        self.game_finished = False

    def start(self, navy_setup: Sequence[dict[str, Any]], ai_setup=None) -> None:
        self.player_grid.load_setup(navy_setup)
        self.opposite_grid.ai_setup = ai_setup or list()
        self.turn_checker.turn = self.get_default_turn()
        self.game_finished = self.restart = False
        self.ai.reset()
        self.mainloop()

    def on_quit(self) -> None:
        self.player_grid.reset()
        self.opposite_grid.reset()
        self.objects.set_focus(None)

    def update(self) -> None:
        self.text_finish.set_visibility(self.game_finished)
        if self.game_finished:
            return
        if self.client_socket.connected():
            if self.client_socket.recv("attack"):
                self.hit_a_box(self.player_grid, json.loads(self.client_socket.get("attack")))
            elif self.client_socket.recv("quit"):
                self.finish(None)

    def get_default_turn(self) -> bool:
        if not self.client_socket.connected():
            return True
        if self.player_id == 1:
            my_turn = random.choice([True, False])
            self.client_socket.send("turn", not my_turn)
            return my_turn
        result = self.client_socket.wait_for("turn")
        if result == "quit":
            return False
        return bool(self.client_socket.get("turn"))

    def finish(self, victory: bool) -> None:
        self.window_finish.start(victory)
        self.stop()

    def highlight_ships(self, ships: Sequence[Ship]):
        for ship in ships:
            for box in ship.boxes_covered:
                box.hover = not box.hover
        self.after(500, self.highlight_ships, ships)

    def place_objects(self) -> None:
        self.button_back.move(x=20, y=20)
        self.text_finish.move(y=20, centerx=self.centerx)
        self.player_grid.move(x=20, centery=self.centery)
        self.opposite_grid.move(right=self.right - 20, centery=self.centery)
        self.turn_checker.resize_all_sprites(width=self.opposite_grid.left - self.player_grid.right - 150)
        self.turn_checker.move(center=self.center)

    def hit_a_box(self, navy: Navy, box: Union[tuple[int, int], NavyGridBox]) -> None:
        if isinstance(box, (list, tuple)):
            box = navy.get_box(*box)
        hitted = navy.box_hit(box)
        if navy.destroyed():
            self.opposite_grid.set_box_clickable(False)
            if navy is self.player_grid:
                self.highlight_ships(self.opposite_grid.show_all_non_destroyed_ships())
                victory = False
            elif navy is self.opposite_grid:
                self.player_grid.send_non_destroyed_ships()
                victory = True
            self.after(3000, self.finish, victory=victory)
            self.game_finished = True
            return
        turn = hitted if navy == self.opposite_grid else not hitted
        self.opposite_grid.set_box_clickable(False)
        self.set_turn(turn)

    def set_turn(self, turn: bool) -> None:
        self.turn_checker.turn = turn
        if self.turn_checker.turn is True:
            self.opposite_grid.set_box_clickable(True)
        if self.turn_checker.turn is False and not self.client_socket.connected() and not self.player_grid.destroyed():
            self.after(1000, self.hit_a_box, self.player_grid, self.ai.play(self.player_grid.map))
