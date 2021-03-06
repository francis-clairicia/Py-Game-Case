# -*- coding: Utf-8 -*

from my_pygame import MainWindow, Window, Image, Button, DrawableListVertical, ButtonListVertical, Form, Scale, Text, CountDown, Entry
from my_pygame import Dialog
from my_pygame import GREEN, GREEN_DARK, GREEN_LIGHT, YELLOW, TRANSPARENT
from .constants import RESOURCES, WINDOW_CONFIG_FILE
from .navy_setup import NavySetup
from .version import __version__

class Credits(Dialog):

    def __init__(self, master: Window, **kwargs):
        Dialog.__init__(self, master=master, bg_color=GREEN, **kwargs)
        title_font = ("calibri", 32, "bold")
        simple_font = ("calibri", 32)
        self.text = DrawableListVertical(offset=50)
        self.text.add(
            Text("Images\ntaken in Google Image\n(except the logo)", font=simple_font, justify=Text.T_CENTER),
        )
        for text in self.text:
            text.set_custom_line_font(0, title_font)
        # self.button_red_cross = ImageButton(self, img=RESOURCES.IMG["red_cross"],
        #                                     active_img=RESOURCES.IMG["red_cross_hover"],
        #                                     hover_sound=RESOURCES.SFX["select"], on_click_sound=RESOURCES.SFX["back"],
        #                                     callback=self.stop, highlight_color=YELLOW)

    def place_objects(self):
        self.text.center = self.frame.center

class PlayerServer(Dialog):

    def __init__(self, master, **kwargs):
        Dialog.__init__(self, master=master, bg_color=GREEN_DARK, **kwargs)
        self.start_game = master.start_game
        self.text_title = Text("Waiting for Player 2", font=("calibri", 50))
        self.text_ip_address = Text(font=("calibri", 40))
        self.text_port_of_connection = Text(font=("calibri", 40))
        self.button_cancel = Button(self, "Return to menu", theme="option", callback=self.stop)
        self.lets_play_countdown = CountDown(self, 3, "Player 2 connected.\nGame start in {seconds} seconds", font=("calibri", 35), color=YELLOW, justify="center")

    def on_start_loop(self):
        try:
            ip, port = self.create_server(12800, 1)
            self.text_ip_address.message = f"IP address: {ip}"
            self.text_port_of_connection.message = f"Port: {port}"
        except OSError:
            self.stop()

    def on_quit(self):
        self.stop_connection()

    def place_objects(self):
        self.frame.move(center=self.center)
        self.text_title.move(centerx=self.frame.centerx, top=self.frame.top + 50)
        self.lets_play_countdown.move(center=self.text_title.center)
        self.text_ip_address.move(centerx=self.centerx, bottom=self.frame.centery - 10)
        self.text_port_of_connection.move(centerx=self.text_ip_address.centerx, top=self.text_ip_address.bottom + 20)
        self.button_cancel.move(centerx=self.frame.centerx, bottom=self.frame.bottom - 10)

    def update(self) -> None:
        if self.get_server_clients_count() > 1 and not self.lets_play_countdown.started():
            self.set_server_listen(0)
            self.text_title.hide()
            self.button_cancel.state = Button.DISABLED
            self.lets_play_countdown.start(at_end=self.play)

    def play(self):
        self.start_game.start(1)
        self.stop()

class PlayerClient(Dialog):

    def __init__(self, master, **kwargs):
        Dialog.__init__(self, master=master, bg_color=GREEN_DARK, **kwargs)
        self.start_game = master.start_game
        self.text_title = Text("Connect to Player 1", font=("calibri", 50))
        self.form = Form(self)
        self.form.add_entry("IP", Text("IP address", font=("calibri", 40), color=YELLOW), Entry(self, width=15, font=("calibri", 30), bg=GREEN, highlight_color=YELLOW, outline=2))
        self.form.add_entry("Port", Text("Port", font=("calibri", 40), color=YELLOW), Entry(self, width=15, font=("calibri", 30), bg=GREEN, highlight_color=YELLOW, outline=2))
        self.text_connection = Text(font=("calibri", 25), color=YELLOW)
        self.text_connection.hide()
        self.button_connect = Button(self, "Connection", theme="option", callback=self.connection)
        self.button_cancel = Button(self, "Return to menu", theme="option", callback=self.stop)
        self.lets_play_countdown = CountDown(self, 3, "Connected.\nGame start in {seconds} seconds", font=("calibri", 35), color=YELLOW, justify="center")

    def on_quit(self):
        self.stop_connection()

    def place_objects(self):
        self.frame.move(center=self.center)
        self.text_title.move(centerx=self.frame.centerx, top=self.frame.top + 50)
        self.lets_play_countdown.move(center=self.text_title.center)
        self.form.move(center=self.frame.center)
        self.text_connection.move(centerx=self.frame.centerx, top=self.form.bottom + 5)
        self.button_connect.move(centerx=self.frame.centerx - (self.frame.width // 4), bottom=self.frame.bottom - 10)
        self.button_cancel.move(centerx=self.frame.centerx + (self.frame.width // 4), bottom=self.frame.bottom - 10)

    def connection(self):
        self.text_connection.show()
        self.text_connection.message = "Connection..."
        self.draw_and_refresh()
        try:
            address = self.form.get("IP")
            port = int(self.form.get("Port"))
        except ValueError:
            self.text_connection.message = "The port of connection must be a number."
            return
        if not self.connect_to_server(address, port, 3):
            self.text_connection.message = "Connection failed. Try again."
        else:
            self.text_connection.hide()
            self.text_title.hide()
            self.button_connect.state = self.button_cancel.state = Button.DISABLED
            self.button_connect.focus_leave()
            self.lets_play_countdown.start(at_end=self.play)

    def play(self):
        self.start_game.start(2)
        self.stop()

class NavyWindow(MainWindow):
    def __init__(self):
        MainWindow.__init__(self, title=f"Navy - v{__version__}", size=(1280, 720), resources=RESOURCES, config=WINDOW_CONFIG_FILE)

        self.bg = Image(RESOURCES.IMG["menu_bg"], size=self.size)
        self.logo = Image(RESOURCES.IMG["logo"])

        Button.set_default_theme("default")
        Button.set_theme("default", {
            "bg": GREEN,
            "hover_bg": GREEN_LIGHT,
            "active_bg": GREEN_DARK,
            "highlight_color": YELLOW,
            "outline": 3,
        })
        Button.set_theme("title", {
            "font": (None, 100),
        })
        Button.set_theme("option", {
            "font": ("calibri", 30),
        })
        Scale.set_default_theme("default")
        Scale.set_theme("default", {
            "color": TRANSPARENT,
            "scale_color": GREEN,
            "highlight_color": YELLOW,
            "outline": 3
        })

        params_for_dialogs = {
            "outline": 5,
            "hide_all_without": [self.bg, self.logo]
        }

        self.start_game = NavySetup()
        self.multiplayer_server = PlayerServer(self, **params_for_dialogs)
        self.multiplayer_client = PlayerClient(self, **params_for_dialogs)
        self.dialog_credits = Credits(self, **params_for_dialogs)

        self.menu_buttons = ButtonListVertical(offset=30)
        self.menu_buttons.add(
            Button(self, "Play against AI", theme="title", callback=lambda: self.start_game.start(1)),
            Button(self, "Play as P1", theme="title", callback=self.multiplayer_server.mainloop),
            Button(self, "Play as P2", theme="title", callback=self.multiplayer_client.mainloop),
            Button(self, "Quit", theme="title", callback=self.stop)
        )

        self.button_credits = Button(self, "Credits", font=("calibri", 50), callback=self.dialog_credits.mainloop)

    def on_start_loop(self) -> None:
        self.disable_key_joy_focus_for_all_window()
        Button.draw_focus_outline(False)

    def on_quit(self) -> None:
        self.enable_key_joy_focus_for_all_window()
        Button.draw_focus_outline(True)

    def place_objects(self):
        self.bg.center = self.center
        self.logo.centerx = self.centerx
        self.menu_buttons.move(centerx=self.centerx, bottom=self.bottom - 20)
        self.button_credits.move(right=self.right - 10, bottom=self.bottom - 10)
