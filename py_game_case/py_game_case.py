# -*- coding: Utf-8 -*

from my_pygame import MainWindow

class PyGameCase(MainWindow):

    def __init__(self):
        super().__init__(size=(1280, 720))
        self.set_title("Py-Game-Case")