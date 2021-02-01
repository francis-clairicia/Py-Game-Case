# -*- coding: Utf-8 -*

import os.path
import sys
import pygame
from my_pygame import Window, Dialog, Text, Button, ProgressBar, CrossShape, Clickable
from my_pygame import WHITE, BLACK, BLUE, BLUE_LIGHT, CYAN, BLUE_DARK, TRANSPARENT, GREEN, YELLOW
from my_pygame import threaded_function
from .updater import Updater

class CrossShapeButton(Clickable, CrossShape):

    def __init__(self, master: Window, *args, callback=None, **kwargs):
        CrossShape.__init__(self, *args, **kwargs)
        Clickable.__init__(self, master, callback=callback, highlight_color=YELLOW)
        self.force_use_highlight_thickness(True)

class UpdaterWindow(Dialog):

    def __init__(self, master: Window, updater: Updater):
        super().__init__(master, bg_color=BLUE, outline_color=WHITE)

        Button.set_theme("dialog", {
            "bg": BLUE_LIGHT,
            "hover_bg": CYAN,
            "active_bg": BLUE_DARK,
            "fg": WHITE,
            "hover_fg": BLACK,
            "active_fg": WHITE,
            "font": ("calibri", 25),
            "highlight_color": YELLOW
        })

        self.__updater = updater
        self.__process_started = False

        cross_shape_size = min(0.1 * self.frame.w, 0.1 * self.frame.h)
        self.__button_quit = CrossShapeButton(
            self, cross_shape_size, cross_shape_size, TRANSPARENT, outline=5, outline_color=WHITE,
            callback=self.stop
        )
        self.__text = Text(
            "There is a new release.\nDo you want to install it ?",
            font=("calibri", 30), color=WHITE, justify=Text.T_CENTER
        )
        self.__button_yes = Button(self, "Yes", theme="dialog", callback=self.__start_install)
        self.__button_no = Button(self, "No", theme="dialog", callback=self.stop)

        self.__progress_bar = ProgressBar(0.5 * self.frame.w, 40, TRANSPARENT, GREEN)
        self.__progress_bar.config_label_text(font=("calibri", 25), color=WHITE)
        self.__progress_bar.config_value_text(font=("calibri", 25), color=WHITE)

    def on_start_loop(self) -> None:
        self.frame.midtop = self.midbottom
        self.frame.animate_move(self, speed=20, at_every_frame=self.place_objects, centerx=self.centerx, bottom=self.bottom - 50)

    def place_objects(self) -> None:
        self.__button_quit.move(top=self.frame.top + 10, left=self.frame.left + 10)
        self.__text.move(top=self.frame.top + 10, centerx=self.frame.centerx)
        self.__button_yes.move(bottom=self.frame.bottom - 20, centerx=self.frame.centerx - self.frame.w // 4)
        self.__button_no.move(bottom=self.frame.bottom - 20, centerx=self.frame.centerx + self.frame.w // 4)
        self.__progress_bar.center = self.frame.center

    def set_grid(self) -> None:
        self.__button_quit.set_obj_on_side(on_bottom=self.__button_yes, on_right=self.__button_yes)
        self.__button_yes.set_obj_on_side(on_left=self.__button_quit, on_right=self.__button_no, on_top=self.__button_quit)
        self.__button_no.set_obj_on_side(on_left=self.__button_yes, on_top=self.__button_quit)

    def on_quit(self) -> None:
        self.frame.animate_move(self, speed=20, at_every_frame=self.place_objects, midtop=self.midbottom)

    def stop(self, force=False, sound=None) -> None:
        if not self.__process_started:
            super().stop(force=force, sound=sound)

    def start(self, install=False):
        if not install:
            self.show_all(without=[self.__progress_bar])
            self.__button_yes.focus_set()
        else:
            self.hide_all(without=[self.__progress_bar])
            self.after(0, self.__start_install_thread)
        self.mainloop()

    def __start_install(self) -> None:
        self.hide_all(without=[self.__progress_bar])
        self.__start_install_thread(compare_versions=False)

    @threaded_function
    def __start_install_thread(self, compare_versions=True) -> None:
        self.__process_started = True
        self.__text.message = "Searching..."
        self.__text.show()
        state = self.__updater.install_latest_version(self.__progress_bar, compare_versions=compare_versions)
        self.__text.message = Updater.get_message(state)
        if state == Updater.STATE_INSTALLED:
            self.__text.message += " Restarting..."
            self.after(500, self.__call_restart_process)
        else:
            self.__process_started = False
            self.__button_quit.show()

    def __call_restart_process(self) -> None:
        self.stop(force=True)
        os.execv(sys.executable, [sys.executable])

class SettingsWindow(Dialog):

    def __init__(self, master: Window):
        super().__init__(master, width_ratio=1, height_ratio=1, outline=0, bg_color=master.bg_color, bind_escape=False)
        self.bind_key(pygame.K_ESCAPE, lambda event: self.stop())

        self.text_title = Text("Settings", font=("calibri", 100), color=WHITE)
        self.text_quit = Text("Escape: Exit settings", font=("calibri", 20), color=WHITE)

    def place_objects(self) -> None:
        self.text_title.move(centerx=self.frame.centerx, top=self.frame.top + 20)
        self.text_quit.move(left=self.frame.left + 10, top=self.frame.top + 10)

    def on_start_loop(self) -> None:
        self.frame.left = self.right
        self.frame.animate_move(self, speed=50, at_every_frame=self.place_objects, center=self.center)

    def on_quit(self) -> None:
        self.frame.animate_move(self, speed=50, at_every_frame=self.place_objects, left=self.right)
