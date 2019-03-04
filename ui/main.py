#!/usb/bin/env python3
#-*- coding: utf-8 -*-

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import QSize, Qt
from configparser import ConfigParser
from plugins.icse0xxa_plugin import ICSE0XXA_Plugin
import os



class MainWindow(QMainWindow):
    """ Main control window of pt """

    def __init__(self, config: ConfigParser):
        super().__init__()

        self.config = config
        self.plugins = self.find_plugins()
        self.loaded_plugins = []

        self._load_plugins()
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
        self.menu_devices.aboutToShow.connect(self.devices_menu_show)
        menubar.addMenu(self.menu_devices)

        # Statusbar
        self.statusBar().setFont(menubar.font())
        self.statusBar().showMessage("Вeрсия: 0")

    def save_config(self):
        import pt

        # Plugins
        for plugin in self.loaded_plugins:
            try:
                if not self.config.has_section(pt.PLUGINS_CONF_SECTION):
                   self.config.add_section(pt.PLUGINS_CONF_SECTION)
                self.config[pt.PLUGINS_CONF_SECTION][plugin.get_info()["plugin_name"]] = \
                    str(plugin.get_info()["activated"])
            except Exception as e:
                print(e)
        try:
            pt.write_config(self.config)
        except Exception as e:
            print(e)
        del pt

    def closeEvent(self, e):
        self.save_config()

    def devices_menu_show(self):
        for action in self.menu_devices.actions():
            plugin: ICSE0XXA_Plugin = action.data()
            if plugin.get_info()["activated"]:
                action.setIcon(QIcon("./res/on.ico"))
            else:
                action.setIcon(QIcon("./res/off.ico"))

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

    def _load_plugins(self):
        for plugin, plug_num in zip(self.plugins, range(len(self.plugins))):
            print("load plugin:", plug_num, plugin.__name__)
            self.loaded_plugins.append(plugin())


    def _build_devices_actions(self):
        """Build actions for devices menu
        :return list[QAction]"""
        actions = []
        for plugin in self.loaded_plugins:
            pname = plugin.get_info()["plugin_name"]
            action = QAction(pname, self)
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
        psettings = PluginSettings(self, plugin)
        psettings.show()


class PluginSettings(QDialog):
    """Settings window for current plugin"""
    def __init__(self, main_win, plugin):
        self.plugin = plugin
        super().__init__(main_win)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowModality(Qt.WindowModal)
        self.setWindowTitle(self.plugin.get_info()["plugin_name"])

        plugin_frame = QFrame()
        plugin_frame.setMaximumSize(1280, 1024)
        plugin_frame.setMinimumSize(400, 200)
        self.plugin.build_settings(plugin_frame)

        self.activate_btn = QPushButton("Активировать")
        self.activate_btn.setFixedHeight(30)
        self.activate_btn.setCheckable(True)
        if self.plugin.get_info()["activated"]:
            self.activate_btn.setIcon(QIcon("./res/on.ico"))
            self.activate_btn.setText("Деактивировать")
        else:
            self.activate_btn.setIcon(QIcon("./res/off.ico"))
        self.activate_btn.setIconSize(QSize(24, 24))

        self.activate_btn.clicked.connect(self.activate_plugin)

        self.plugin_info_lb = QLabel("Plugin info")
        self.plugin_info_lb.setWordWrap(True)
        self.plugin_info_lb.setFixedWidth(plugin_frame.width()-100)
        self.plugin_info_lb.setText(
            "<b>{}</b> - {} <br>Автор: <b>{}</b>, Версия: <b>{}</b>".format(
                self.plugin.get_info()["plugin_name"],
                self.plugin.get_info()["description"],
                self.plugin.get_info()["author"],
                self.plugin.get_info()["version"]
            )
        )

        vboxlay = QVBoxLayout()
        vboxlay.addWidget(plugin_frame, alignment=Qt.AlignCenter | Qt.AlignTop)

        plugin_info_lay = QHBoxLayout()
        plugin_info_lay.addWidget(self.plugin_info_lb)
        plugin_info_lay.addWidget(self.activate_btn, alignment=Qt.AlignBottom | Qt.AlignRight)

        vboxlay.addItem(plugin_info_lay)
        self.setLayout(vboxlay)

    def activate_plugin(self):
        try:
            self.plugin : ICSE0XXA_Plugin
            if not self.plugin.get_info()["activated"]:
                self.plugin.activate()
                self.activate_btn.setText("Деактивировать")
                print("Activate successfully, plugin with ", self.plugin.get_channels_count(), "relays")
            else: print(self.plugin, "already activated")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка активации", str(e), QMessageBox.Ok)


if __name__ == "__main__":
    import sys
    os.chdir("..")
    print(os.getcwd())

    app = QApplication([])
    mw = MainWindow()
    mw.show()

    app.exec()
