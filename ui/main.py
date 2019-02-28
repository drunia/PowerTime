#!/usb/bin/env python3
#-*- coding: utf-8 -*-

from PyQt5.QtWidgets import *

class MainWindow(QWidget):
    """ Main control window of pt """

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle("PowerTime")




