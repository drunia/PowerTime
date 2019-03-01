#!/usb/bin/env python3
#-*- coding: utf-8 -*-

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
import os


class MainWindow(QMainWindow):
    """ Main control window of pt """

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowTitle("PowerTime")
        self.resize(500, 500)

        # Main menu
        menubar: QMenuBar = self.menuBar()
        menufont: QFont = menubar.font()
        menufont.setPointSize(13)
        menubar.setFont(menufont)
        menubar.setMinimumHeight(40)
        # Settings
        self.menu_settings = QMenu("Настройки")
        menubar.addMenu(self.menu_settings)
        # Devices (plugins)
        self.menu_devices = QMenu("Устройства")
        menubar.addMenu(self.menu_devices)
        self.statusBar().showMessage("*(&&*&$#")

        self._build_devices_actions()

    def _build_devices_actions(self):
        """search device-plugins in modules dir
        :return list[QAction]"""
        import pkgutil, inspect
        actions = []
        mod_info_list = list(pkgutil.iter_modules(["../plugins"]))
        for module in mod_info_list:
            mod = __import__("plugins." + module.name)
            for name, obj in inspect.getmembers(mod):
                if inspect.isclass(obj):
                    print(obj)




if __name__ == "__main__":
    app = QApplication([])
    mw = MainWindow()
    mw.show()
    app.exec()
