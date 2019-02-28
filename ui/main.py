#!/usb/bin/env python3
#-*- coding: utf-8 -*-

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import os


class MainWindow(QMainWindow):
    """ Main control window of pt """

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):

        self.setWindowTitle("PowerTime")
        self.resize(500, 500)

        # Main menu
        menubar: QMenuBar = self.menuBar()
        menubar.setLayoutDirection(1)
        menufont: QFont = menubar.font()
        menufont.setPointSize(14)
        menubar.setFont(menufont)

        self.menu_devices = QMenu("Устройства")
        self.menu_settings = QMenu("Настройки")
        menubar.addMenu(self.menu_devices)
        menubar.addMenu(self.menu_settings)


        self.menu_devices.setFixedSize(100, 30)
        #self.menu_devices.setIcon(ico)




        #self.menu_devices.setIcon()
        #self.mmenu.addMenu(self.menu_devices)

        self.statusBar().showMessage("*(&&*&$#")





if __name__ == "__main__":
    app = QApplication([])
    mw = MainWindow()
    mw.show()
    app.exec()
