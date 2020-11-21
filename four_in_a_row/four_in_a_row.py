# -*- coding: Utf-8 -*

import string
import pygame
from my_pygame import MainWindow, Window, Dialog, Image, ImageButton, Text, Button, ButtonListVertical, Entry, Form
from my_pygame import BLUE, BLUE_LIGHT, BLUE_DARK, GRAY_LIGHT, WHITE, BLACK, YELLOW
from .constants import RESOURCES, WINDOW_CONFIG_FILE, BACKGROUND_COLOR, AI, LOCAL_PLAYER, LAN_PLAYER
from .game import FourInARowGameplay
from .ai import FourInARowAI
from .version import __version__

class Section(Dialog):

    def __init__(self, master, title: str, gameplay: FourInARowGameplay):
        Dialog.__init__(self, master, bg_color=BLUE)
        self.master = master
        self.gameplay = gameplay
        arrow = pygame.transform.flip(RESOURCES.IMG["arrow"], True, False)
        self.button_back = ImageButton(self, img=arrow, width=50, callback=self.stop, active_offset=(0, 5), highlight_color=YELLOW)
        self.title = Text(title)

    def place_objects(self) -> None:
        self.frame.size = self.frame.width, self.master.buttons.height
        self.frame.move(left=10, top=self.master.buttons.top)
        self.button_back.move(left=self.frame.left + 5, top=self.frame.top + 5)
        self.title.move(centerx=self.frame.centerx, top=self.frame.top + 10)

class AILevelSelectorSection(Section):

    def __init__(self, master, gameplay: FourInARowGameplay):
        Section.__init__(self, master, "Choose AI level", gameplay)
        self.buttons_ai_level = ButtonListVertical(offset=100)
        theme = {
            "font": self.title.font,
            "y_add_size": -30
        }
        disabled_levels = [FourInARowAI.HARD]
        self.buttons_ai_level.add_multiple(
            Button(
                self, text=string.capwords(level), theme=["section"], **theme,
                callback=lambda ai_level=level: self.play(ai_level), state=Button.DISABLED if level in disabled_levels else Button.NORMAL
            )
            for level in FourInARowAI.get_available_levels()
        )

    def on_start_loop(self) -> None:
        self.buttons_ai_level[0].focus_set()

    def place_objects(self) -> None:
        Section.place_objects(self)
        self.buttons_ai_level.move(centerx=self.frame.centerx, top=self.title.bottom + 50)

    def set_grid(self) -> None:
        self.button_back.set_obj_on_side(on_bottom=self.buttons_ai_level[0], on_right=self.buttons_ai_level[0])
        self.buttons_ai_level.set_obj_on_side(on_top=self.button_back, on_left=self.button_back)

    def play(self, ai_level: str) -> None:
        self.gameplay.start(AI, ai_level=ai_level)
        self.stop()

class LocalPlayingSection(Section):

    def __init__(self, master, gameplay: FourInARowGameplay):
        Section.__init__(self, master, "Local Multiplaying", gameplay)
        self.form = Form(self)
        self.form.add_entry("P1", Text("P1 Name:", theme="form"), Entry(self))
        self.form.add_entry("P2", Text("P2 Name:", theme="form"), Entry(self))
        self.button_play = Button(self, "Play", theme=["option", "section"], callback=self.play)

    def on_start_loop(self) -> None:
        self.button_play.focus_set()

    def place_objects(self) -> None:
        Section.place_objects(self)
        self.form.move(left=self.frame.left + 10, top=self.title.bottom + 50)
        self.button_play.move(centerx=self.frame.centerx, bottom=self.frame.bottom - 10)

    def set_grid(self) -> None:
        self.button_back.set_obj_on_side(on_bottom=self.form[0], on_right=self.form[0])
        self.form.set_obj_on_side(on_top=self.button_back, on_left=self.button_back, on_bottom=self.button_play)
        self.button_play.set_obj_on_side(on_top=self.form[-1])

    def play(self) -> None:
        player_1_name = self.form.get_value("P1") or None
        player_2_name = self.form.get_value("P2") or None
        self.gameplay.start(LOCAL_PLAYER, player_name=player_1_name, enemy_name=player_2_name)
        self.stop()

class LANPlayingP1(Section):

    def __init__(self, master, gameplay: FourInARowGameplay):
        Section.__init__(self, master, "Play as P1", gameplay)
        self.form = Form(self)
        self.form.add_entry("P1", Text("Your Name:", theme="form"), Entry(self))
        self.button_start_server = Button(self, theme=["option", "section"])
        self.text_game_status = Text(font=RESOURCES.font("heavy", 20), shadow_x=1, shadow_y=1)
        self.text_server_ip = Text(font=RESOURCES.font("afterglow", 45), shadow_x=2, shadow_y=1)
        self.text_server_port = Text(font=RESOURCES.font("afterglow", 45), shadow_x=2, shadow_y=1)

    def place_objects(self) -> None:
        Section.place_objects(self)
        self.form.move(left=self.frame.left + 10, top=self.title.bottom + 50)
        self.text_game_status.move(centerx=self.frame.centerx, top=self.form.bottom + 10)
        self.button_start_server.move(centerx=self.frame.centerx, top=self.form.bottom + 50)
        self.text_server_ip.move(centerx=self.frame.centerx, top=self.button_start_server.bottom + 30)
        self.text_server_port.move(centerx=self.frame.centerx, top=self.text_server_ip.bottom + 10)

    def update(self) -> None:
        if not self.client_socket.connected():
            self.button_start_server.state = Button.NORMAL if self.form.get_value("P1") else Button.DISABLED
            self.form.get_entry("P1").state = Entry.NORMAL
        else:
            self.button_start_server.state = Button.NORMAL
            self.form.get_entry("P1").state = Entry.DISABLED
            if self.get_server_clients_count() == 2:
                self.set_server_listen(0)
                self.gameplay.start(LAN_PLAYER, player=1, player_name=self.form.get_value("P1"))
                self.stop()

    def on_start_loop(self) -> None:
        self.form.get_entry("P1").focus_set()
        self.form.get_entry("P1").start_edit()
        self.stop_server()

    def on_quit(self) -> None:
        self.stop_connection()

    def set_grid(self) -> None:
        self.button_back.set_obj_on_side(on_bottom=self.form[0], on_right=self.form[0])
        self.form.set_obj_on_side(on_top=self.button_back, on_left=self.button_back, on_bottom=self.button_start_server)
        self.button_start_server.set_obj_on_side(on_top=self.form[-1], on_left=self.button_back)

    def start_server(self) -> None:
        try:
            ip, port = self.create_server(12800, 1)
        except OSError:
            self.text_game_status.message = "Cannot create server"
        else:
            self.text_game_status.message = "Waiting for player 2 to connect"
            self.text_server_ip.message = "IP: {}".format(ip)
            self.text_server_port.message = "Port: {}".format(port)
            self.text_server_ip.show()
            self.text_server_port.show()
            self.button_start_server.text = "Stop server"
            self.button_start_server.callback = self.stop_server
        self.text_game_status.show()
        self.place_objects()

    def stop_server(self) -> None:
        self.stop_connection()
        self.text_game_status.hide()
        self.text_server_ip.hide()
        self.text_server_port.hide()
        self.button_start_server.text = "Start server"
        self.button_start_server.callback = self.start_server

class LANPlayingP2(Section):

    def __init__(self, master, gameplay: FourInARowGameplay):
        Section.__init__(self, master, "Play as P2", gameplay)
        self.form = Form(self)
        self.form.add_entry("name", Text("Your Name:", theme="form"), Entry(self))
        self.form.add_entry("IP", Text("IP address:", theme="form"), Entry(self, width=15))
        self.form.add_entry("port", Text("Port of connection:", theme="form"), Entry(self, width=15))
        self.button_connect = Button(self, "Connect to P1", theme=["option", "section"], callback=self.connection)
        self.text_game_status = Text(font=RESOURCES.font("heavy", 30), shadow_x=1, shadow_y=1)

    def place_objects(self) -> None:
        Section.place_objects(self)
        self.form.move(left=self.frame.left + 10, top=self.title.bottom + 50)
        self.text_game_status.move(centerx=self.frame.centerx, top=self.form.bottom + 10)
        self.button_connect.move(centerx=self.frame.centerx, bottom=self.frame.bottom - 10)

    def update(self) -> None:
        self.button_connect.state = Button.NORMAL if self.form.get_value("name") else Button.DISABLED

    def on_start_loop(self) -> None:
        self.form.get_entry("name").focus_set()
        self.form.get_entry("name").start_edit()
        self.text_game_status.hide()

    def on_quit(self) -> None:
        self.stop_connection()

    def set_grid(self) -> None:
        self.button_back.set_obj_on_side(on_bottom=self.form[0], on_right=self.form[0])
        self.form.set_obj_on_side(on_top=self.button_back, on_left=self.button_back, on_bottom=self.button_connect)
        self.button_connect.set_obj_on_side(on_top=self.form[-1])

    def connection(self) -> None:
        self.text_game_status.show()
        self.text_game_status.message = "Connection..."
        self.draw_and_refresh()
        if not self.connect_to_server(self.form.get_value("IP"), int(self.form.get_value("port")), 3):
            self.text_game_status.message = "Connection failed. Try again."
        else:
            self.gameplay.start(LAN_PLAYER, player=2, player_name=self.form.get_value("name"))
            self.stop()

class FourInARowWindow(MainWindow):

    def __init__(self):
        MainWindow.__init__(self, size=(1280, 720), flags=pygame.RESIZABLE, bg_color=BACKGROUND_COLOR, resources=RESOURCES, config=WINDOW_CONFIG_FILE)
        self.set_title(f"4 in a row - v{__version__}")
        self.set_icon(RESOURCES.IMG["icon"])
        self.set_minimum_window_size(self.width, self.height)
        self.logo = Image(RESOURCES.IMG["logo"])

        Text.set_default_theme("default")
        Text.set_theme("default", {
            "font": RESOURCES.font("heavy", 45),
            "color": YELLOW,
            "shadow": True,
            "shadow_x": 3,
            "shadow_y": 3
        })
        Text.set_theme("form", {
            "font": RESOURCES.font("heavy", 40),
        })
        Button.set_default_theme("default")
        Button.set_theme("default", {
            "fg": YELLOW,
            "disabled_fg": WHITE,
            "shadow": True,
            "shadow_x": 3,
            "shadow_y": 3,
            "bg": BLUE,
            "hover_bg": (0, 175, 255),
            "active_bg": BLUE,
            "outline": 0,
            "highlight_color": WHITE,
            "highlight_thickness": 1,
            "border_bottom_left_radius": 45,
            "border_top_right_radius": 45,
            "x_add_size": 150,
            "offset": (0, -5),
            "hover_offset": (-10, 0),
            "active_offset": (0, 10),
        })
        Button.set_theme("title", {
            "font": RESOURCES.font("heavy", 70),
            "y_add_size": -50
        })
        Button.set_theme("option", {
            "font": RESOURCES.font("heavy", 40),
            "y_add_size": -20
        })
        Button.set_theme("section", {
            "bg": BLUE_DARK,
            "active_bg": BLUE_DARK,
            "disabled_bg": GRAY_LIGHT
        })
        Entry.set_default_theme("default")
        Entry.set_theme("default", {
            "width": 12,
            "font": RESOURCES.font("afterglow", 30),
            "highlight_color": BLACK,
            "highlight_thickness": 3
        })

        gameplay = FourInARowGameplay()
        ai_level_selector = AILevelSelectorSection(self, gameplay)
        local_playing = LocalPlayingSection(self, gameplay)
        lan_playing_server = LANPlayingP1(self, gameplay)
        lan_playing_client = LANPlayingP2(self, gameplay)
        self.buttons = ButtonListVertical(offset=80, justify="right")
        self.buttons.add(
            Button(self, "Play against AI", theme="title", callback=ai_level_selector.mainloop),
            Button(self, "Multiplayer", theme="title", callback=local_playing.mainloop),
            Button(self, "Play as P1 (LAN)", theme="title", callback=lan_playing_server.mainloop),
            Button(self, "Play as P2 (LAN)", theme="title", callback=lan_playing_client.mainloop),
            Button(self, "Quit", theme="title", callback=self.stop),
        )

    def place_objects(self) -> None:
        self.logo.midtop = (self.centerx, 10)
        self.buttons.bottomright = (self.right - 10, self.bottom - 50)