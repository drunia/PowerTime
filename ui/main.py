#!/usb/bin/env python3
#-*- coding: utf-8 -*-

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt
import os


class MainWindow(QMainWindow):
    """ Main control window of pt """

    def __init__(self):
        super().__init__()
        self.plugins = self.find_plugins()
        self._setup_ui()


    def _setup_ui(self):
        self.setWindowTitle("PowerTime")
        self.resize(800, 600)

        # Main menu
        menubar: QMenuBar = self.menuBar()
        menufont: QFont = menubar.font()
        menufont.setPointSize(13)
        menubar.setFont(menufont)
        menubar.setMinimumHeight(40)

        # Settings
        self.menu_settings = QMenu("Настройки", self)
        menubar.addMenu(self.menu_settings)

        # Devices (plugins)
        self.menu_devices = QMenu("Устройства", self)
        self.menu_devices.addActions(self._build_devices_actions())
        menubar.addMenu(self.menu_devices)

        # Statusbar
        self.statusBar().setFont(menubar.font())
        self.statusBar().showMessage("Вeрсия: 0")


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
        """Build actions for devices menu
        :return list[QAction]"""
        actions = []
        for plugin in self.plugins:
            pname = plugin.get_info(self)["plugin_name"]
            action = QAction(QIcon("./res/icse0xxa_device.ico"), pname, self)
            action.setFont(self.menuBar().font())
            action.setCheckable(True)
            action.setChecked(True)
            action.setData(plugin) # Set reference to us plugin into menu
            action.setStatusTip("Управление модулем " + pname)
            action.triggered.connect(self.mclick)
            actions.append(action)
        return actions

    def mclick(self):
        plugin = qApp.sender().data()
        self.psettings = PluginSettings(self, plugin)
        self.psettings.show()


class PluginSettings(QDialog):
    """Settings window for current plugin"""
    def __init__(self, parent, plugin):
        super().__init__(parent)
        self.plugin = plugin
        self.setup_ui()

    def setup_ui(self):
        self.setMinimumSize(500, 500)
        self.setWindowTitle(self.plugin.get_info(self)["plugin_name"])


if __name__ == "__main__":
    import sys
    os.chdir("..")
    print(os.getcwd())

    app = QApplication([])
    mw = MainWindow()
    mw.show()

    app.exec()
