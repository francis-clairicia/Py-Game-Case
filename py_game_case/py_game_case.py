# -*- coding: Utf-8 -*

import sys
import subprocess
from typing import Callable, Sequence
import psutil
import pygame
from my_pygame import MainWindow, Window, WindowTransition
from my_pygame import Image, ProgressBar, Button, Sprite, RectangleShape, HorizontalGradientShape
from my_pygame import ButtonListVertical, DrawableListHorizontal
from my_pygame import TRANSPARENT, WHITE, BLACK, YELLOW, GREEN
from my_pygame import set_color_alpha, change_brightness
from my_pygame import ThemeNamespace, threaded_function
from .constants import RESOURCES, GAMES, SETTINGS
from .settings import SettingsWindow, UpdaterWindow
from .updater import Updater
from .version import __version__

class GameProcess(psutil.Popen):

    def __init__(self, game_id: str):
        if sys.argv[0].endswith((".py", ".pyw")):
            args = [sys.executable, sys.argv[0], game_id]
        else:
            args = [sys.executable, game_id]
        super().__init__(args, shell=False, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.__game_id = game_id

    @property
    def game_id(self) -> str:
        return self.__game_id

class GameProcessList(list):

    def launch(self, game_id: str) -> None:
        self.append(GameProcess(game_id))

    def check_for_terminated_games(self) -> list[GameProcess]:
        process_list = list(filter(lambda process: not process.is_running(), self))
        for process in process_list:
            self.remove(process)
        return process_list

class GameLaunchTransition(WindowTransition):

    def __init__(self):
        self.bg = RectangleShape(0, 0, TRANSPARENT)

    def __color_animation(self, window: Window, color: pygame.Color, alpha_range: range) -> None:
        self.bg.size = window.size
        for alpha in alpha_range:
            self.bg.color = set_color_alpha(color, alpha)
            window.draw_screen()
            self.bg.draw(window.surface)
            window.refresh(pump=True)
            pygame.time.wait(10)

    def __hide_window(self, window: Window, color: pygame.Color) -> None:
        self.__color_animation(window, color, range(0, 256, 10))

    def __show_window(self, window: Window, color: pygame.Color) -> None:
        self.__color_animation(window, color, range(255, -1, -10))

    def hide_actual_looping_window_start_loop(self, window: Window) -> None:
        self.__hide_window(window, WHITE)

    def show_new_looping_window(self, window: Window) -> None:
        self.__show_window(window, WHITE)

    def hide_actual_looping_window_end_loop(self, window: Window) -> None:
        self.__hide_window(window, BLACK)

    def show_previous_window_end_loop(self, window: Window) -> None:
        self.__show_window(window, BLACK)

class TitleButton(Button):

    def __init__(self, master: Window, on_hover: Callable[..., None], *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.focus_on_hover(True)
        self.__on_hover = on_hover

    def after_drawing(self, surface: pygame.Surface) -> None:
        pygame.draw.line(surface, self.outline_color, self.topleft, self.topright, width=self.outline)
        pygame.draw.line(surface, self.outline_color, self.bottomleft, self.bottomright, width=self.outline)

    def focus_drawing_function(self, surface: pygame.Surface, highlight_color: pygame.Color, highlight_thickness: int) -> None:
        pygame.draw.line(surface, highlight_color, self.topleft, self.topright, width=highlight_thickness)
        pygame.draw.line(surface, highlight_color, self.bottomleft, self.bottomright, width=highlight_thickness)

    def on_hover(self) -> None:
        super().on_hover()
        self.__on_hover()

class SettingsButton(Button):

    @property
    def color(self) -> pygame.Color:
        return TRANSPARENT

    @color.setter
    def color(self, color: pygame.Color) -> None:
        self.outline_color = color

    def after_drawing(self, surface: pygame.Surface) -> None:
        pygame.draw.line(surface, self.outline_color, self.topleft, self.topright, width=self.outline)
        pygame.draw.line(surface, self.outline_color, self.midleft, self.midright, width=self.outline)
        pygame.draw.line(surface, self.outline_color, self.bottomleft, self.bottomright, width=self.outline)

class PyGameCase(MainWindow):

    RUNNING_STATE_SUFFIX = " - Running"

    def __init__(self):
        super().__init__(title=f"Py-Game-Case - v{__version__}", size=(1280, 720), bg_color=(0, 0, 100), resources=RESOURCES)

        TitleButton.set_default_theme("default")
        TitleButton.set_theme("default", {
            "font": ("calibri", 30),
            "bg": TRANSPARENT,
            "fg": WHITE,
            "outline": 0,
            "hover_bg": set_color_alpha(WHITE, 100),
            "active_bg": set_color_alpha(WHITE, 50),
            "highlight_color": WHITE,
            "highlight_thickness": 3,
            "x_add_size": self.w * 0.25,
            "y_add_size": 30,
            "justify": ("left", "center"),
            "offset": (10, 0),
            "hover_offset": (0, -5),
            "active_offset": (0, 10)
        })
        SettingsButton.set_default_theme("default")
        SettingsButton.set_theme("default", {
            "bg": WHITE,
            "hover_bg": YELLOW,
            "active_bg": change_brightness(YELLOW, -75),
            "outline": 7,
            "outline_color": WHITE,
            "highlight_thickness": 0
        })

        self.launcher_updater = Updater(__version__)

        self.image_game_preview = Sprite()
        self.bg = DrawableListHorizontal()
        left_color = BLACK
        right_color = set_color_alpha(BLACK, 60)
        self.bg.add(
            RectangleShape(self.w * 0.25, self.h, left_color),
            HorizontalGradientShape(self.w * 0.5, self.h, left_color, right_color),
            RectangleShape(self.w * 0.25, self.h, right_color),
        )
        self.logo = Image(RESOURCES.IMG["logo"], width=self.bg[0].width)

        self.buttons_game_launch = ButtonListVertical(offset=30)
        self.buttons_game_dict = dict[str, TitleButton]()
        self.window_game_dict = dict[str, MainWindow]()
        for game_id, game_infos in GAMES.items():
            button = TitleButton(
                self, lambda game_id=game_id: self.show_preview(game_id), text=game_infos["name"],
                callback=lambda game_id=game_id: self.launch_game(game_id)
            )
            self.image_game_preview.add_sprite(game_id, RESOURCES.IMG[game_id], height=self.height)
            self.buttons_game_dict[game_id] = button
        self.buttons_game_launch.add_multiple(self.buttons_game_dict.values())
        self.game_id = None
        self.game_launched_processes = GameProcessList()

        self.settings_section = SettingsWindow(self)
        self.updater_window = UpdaterWindow(self, self.launcher_updater)

        self.button_settings = SettingsButton(self, size=40, callback=self.settings_section.mainloop)
        self.button_settings.force_use_highlight_thickness(True)

        self.transition = GameLaunchTransition()

    def place_objects(self) -> None:
        self.bg.center = self.center
        self.logo.move(left=10, top=10)
        self.buttons_game_launch.move(left=10, top=self.logo.bottom + 50)
        self.image_game_preview.midright = self.midright
        self.button_settings.move(right=self.right - 20, top=20)

    def set_grid(self) -> None:
        self.button_settings.set_obj_on_side(on_bottom=self.buttons_game_launch[0], on_left=self.buttons_game_launch[0])
        self.buttons_game_launch.set_obj_on_side(on_top=self.button_settings, on_right=self.button_settings)

    @threaded_function
    def __init_games(self) -> None:
        try:
            for game_id, game_infos in filter(lambda item: item[0] not in self.window_game_dict, GAMES.items()):
                with ThemeNamespace(game_id):
                    self.window_game_dict[game_id] = game_infos["window"]()
        except:
            sys.excepthook(*sys.exc_info())
            self.stop(force=True)

    def on_start_loop(self):
        self.image_game_preview.right = self.left
        save_objects_center = list()
        for obj in self.objects.drawable:
            save_objects_center.append((obj, obj.center))
        self.buttons_game_launch.right = self.left
        self.button_settings.left = self.right
        default_logo_width = self.logo.width
        self.logo.load(RESOURCES.IMG["logo"])
        self.logo.midtop = self.midbottom
        if SETTINGS.auto_check_update: # and self.launcher_updater.has_a_new_release():
            self.logo.animate_move(self, speed=20, top=0, centerx=self.centerx)
            self.updater_window.mainloop()
            if not self.loop:
                return
        self.logo.animate_move(self, speed=20, midbottom=self.center)
        loading = ProgressBar(
            default_logo_width, 40, TRANSPARENT, GREEN,
            from_=0, to=len(GAMES), default=len(self.window_game_dict),
            outline_color=WHITE, border_radius=10
        )
        loading.center = self.logo.center
        loading.show_percent(ProgressBar.S_INSIDE, font=("calibri", 30), color=WHITE)
        self.objects.add(loading)
        self.objects.set_priority(loading, 0, relative_to=self.logo)
        loading.animate_move(self, speed=10, centerx=loading.centerx, top=self.logo.bottom + 20)
        thread = self.__init_games()
        while self.loop and (thread.is_alive() or loading.percent < 1):
            self.main_clock.tick(self.get_fps())
            loading.value = len(self.window_game_dict)
            self.draw_and_refresh(pump=True)
        if not self.loop:
            return
        pygame.time.wait(100)
        loading.animate_move(self, speed=10, center=self.logo.center)
        self.objects.remove(loading)
        self.logo.animation.rotate(angle=360, offset=5, point=self.logo.center).scale_width(width=default_logo_width, offset=7).start(self)
        for obj, center in save_objects_center:
            obj.animate_move(self, speed=20, center=center)
        self.focus_mode(Button.MODE_KEY)

    def on_quit(self) -> None:
        self.launcher_updater.close()

    def update(self) -> None:
        if self.game_launched_processes:
            for process in self.game_launched_processes.check_for_terminated_games():
                self.buttons_game_dict[process.game_id].text = GAMES[process.game_id]["name"]
                self.buttons_game_dict[process.game_id].state = Button.NORMAL
            if not self.game_launched_processes and not pygame.display.get_active():
                pass
        if all(not button.has_focus() and not button.hover for button in self.buttons_game_launch) and self.game_id is not None:
            self.image_game_preview.animate_move(self, speed=75, right=self.left)
            self.game_id = None

    def show_preview(self, game_id: str) -> None:
        if self.game_id == game_id:
            return
        self.game_id = game_id
        self.image_game_preview.animate_move_in_background(self, speed=75, right=self.left, after_animation=self.__show_preview)

    def __show_preview(self) -> None:
        self.image_game_preview.set_sprite(self.game_id)
        self.image_game_preview.animate_move_in_background(self, speed=75, right=self.right)

    def launch_game(self, game_id: str) -> None:
        if not SETTINGS.launch_in_same_window:
            self.game_launched_processes.launch(game_id)
            self.buttons_game_dict[game_id].text += PyGameCase.RUNNING_STATE_SUFFIX
            self.buttons_game_dict[game_id].state = Button.DISABLED
            self.iconify()
        else:
            self.game_id = game_id
            if self.image_game_preview.get_actual_sprite_list_name() != game_id:
                self.image_game_preview.animate_move(self, speed=75, right=self.left)
            self.image_game_preview.set_sprite(game_id)
            self.image_game_preview.animate_move(self, speed=75, right=self.right)
            window = self.window_game_dict[game_id]
            window.mainloop(transition=self.transition)

    def close(self) -> None:
        if self.game_launched_processes:
            self.iconify()
        else:
            self.stop(force=True)