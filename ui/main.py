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
        self.find_plugins(plugins_dir="../plugins")


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


    def find_plugins(self, plugins_dir="./plugins"):
        """search device-plugins in modules dir
        :return list[Plugin_Class...,]"""
        import pkgutil, inspect
        plugins = []
        # Find modules with classes inherited from PTBasePlugin
        mod_info_list = list(pkgutil.iter_modules([plugins_dir]))
        for module in mod_info_list:
            m = __import__("plugins." + module.name, fromlist=['object'])
            clslist = inspect.getmembers(m, inspect.isclass)
            for cls in clslist:
                bases = cls[1].__mro__
                for b in bases:
                    if b.__name__ == "PTBasePlugin" and not cls[1].__name__ == "PTBasePlugin":
                        print("{}(): Plugin class finded: {}".format(inspect.stack()[0][3], cls[1].__name__))
                        plugins.append(cls[1])
                        break
        del pkgutil, inspect
        return plugins

    def _build_devices_actions(self):
        self.find_plugins()


if __name__ == "__main__":
    app = QApplication([])
    mw = MainWindow()
    mw.show()
    app.exec()
