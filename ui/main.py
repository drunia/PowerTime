#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import QSize, Qt
from configparser import ConfigParser
from plugins.icse0xxa_plugin import PTBasePlugin
from ui.timer_control import *
import os


class MainWindow(QMainWindow):
    """ Main control window of pt """

    def __init__(self, config: ConfigParser):
        super().__init__()

        self.config = config
        self.loaded_plugins = []
        self.plugin_controls = []

        self.plugins = self.find_plugins()
        self._load_plugins()

        self._setup_ui()
        self._activate_plugins_on_start()
        self.add_plugin_controls()

    def _setup_ui(self):
        self.setWindowTitle("PowerTime")
        self.resize(800, 600)

        # Main menu
        menubar: QMenuBar = self.menuBar()
        menufont: QFont = menubar.font()
        menufont.setPointSize(13)
        menubar.setFont(menufont)
        menubar.setMinimumHeight(40)

        # Settings menu
        self.menu_settings = QMenu("Настройки", self)
        menubar.addMenu(self.menu_settings)

        # Devices menu (plugins)
        self.menu_devices = QMenu("Модули устройств", self)
        self.menu_devices.addActions(self._build_devices_actions())
        self.menu_devices.aboutToShow.connect(self.devices_menu_show)
        menubar.addMenu(self.menu_devices)

        # Central widget
        self.control_frame = QFrame()

        self.scroll_area = QScrollArea(self.centralWidget())
        self.scroll_area.setWidgetResizable(True)

        scroll_vbox_lay = QVBoxLayout(self.scroll_area.viewport())
        scroll_vbox_lay.addWidget(self.control_frame, alignment=Qt.AlignCenter)
        self.setCentralWidget(self.scroll_area)

        # Statusbar
        self.statusBar().setFont(menubar.font())
        self.statusBar().showMessage("Вeрсия: " + qApp.applicationVersion())
        self.statusBar()

        self.show()

    def add_plugin_controls(self):
        """Add switchable controls for controlling active plugin"""
        all_channels_info = {}
        for plugin in self._get_activated_plugins():
            for k, v in plugin.get_channels_info().items():
                v.append(plugin)
                all_channels_info[k] = v
        channels = len(all_channels_info)

        # delete this
        #channels = 4

        cols = 4 if (channels // 5) > 0 else 2
        print("total channels:", channels)

        # Delete old controls
        for pc in self.plugin_controls:
            del pc
        self.control_frame.setLayout(QGridLayout())

        for channel in range(channels):
            control = TimerCashControl(self, channel)
            self.control_frame.layout().addWidget(control, (channel // cols), channel % cols)
            self.plugin_controls.append(control)
            control.switched.connect(self.switch_event)
            if all_channels_info:
                # Set the plugin info on tittle
                ch_info = all_channels_info[channel]
                plugin_info = ch_info[2].get_info()["plugin_name"] + \
                              " - " + str(ch_info[0]) + " - channel: " + str(ch_info[1])
                control.tittle_lb.setToolTip(plugin_info)
        self.scroll_area.setWidget(self.control_frame)

    def switch_event(self, control, state: bool):
        try:
            plugin: PTBasePlugin = self.loaded_plugins[0]
            plugin.switch(control.channel, state)
        except Exception as e:
            print(e)

    def _get_activated_plugins(self):
        """Returned activated plugins list"""
        l = []
        for p in self.loaded_plugins:
            if p.get_info()["activated"]:
                l.append(p)
        return l

    def save_config(self):
        import pt
        # Main
        if not self.config.has_section(pt.APP_MAIN_SECTION):
            self.config.add_section(pt.APP_MAIN_SECTION)
        self.config[pt.APP_MAIN_SECTION]["maximized"] = str(int(self.isMaximized()))
        self.config[pt.APP_MAIN_SECTION]["height"] = str(self.height())
        self.config[pt.APP_MAIN_SECTION]["width"] = str(self.width())
        # Plugins
        for plugin in self.loaded_plugins:
            if not self.config.has_section(pt.PLUGINS_CONF_SECTION):
                self.config.add_section(pt.PLUGINS_CONF_SECTION)
            self.config[pt.PLUGINS_CONF_SECTION][plugin.get_info()["plugin_name"]] = \
                str(int(plugin.get_info()["activated"]))
        try:
            pt.write_config(self.config)
        except Exception as e:
            print(e)
        del pt

    def closeEvent(self, e):
        self.save_config()

    def devices_menu_show(self):
        for action in self.menu_devices.actions():
            plugin: PTBasePlugin = action.data()
            if plugin.get_info()["activated"]:
                action.setIcon(QIcon("./res/on.ico"))
            else:
                action.setIcon(QIcon("./res/off.ico"))

    def find_plugins(self, plugins_dir="./plugins"):
        """Search device-plugins in modules dir
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
        print("find_plugins():", len(plugins))
        return plugins

    def _load_plugins(self):
        for plugin, plug_num in zip(self.plugins, range(len(self.plugins))):
            print("load plugin:", plug_num, plugin.__name__)
            self.loaded_plugins.append(plugin())

    # Activates plugin from main.conf file
    def _activate_plugins_on_start(self):
        import pt
        if self.config.has_section(pt.PLUGINS_CONF_SECTION):
            for plugin, active_state in self.config[pt.PLUGINS_CONF_SECTION].items():
                if int(bool(active_state)):
                    for p in self.loaded_plugins:
                        errors = []
                        if p.get_info()["plugin_name"] == plugin:
                            try:
                                print("_activate_plugins_on_start():", plugin)
                                p.activate()
                                p._ICSE0XXAPlugin__activated = True
                            except Exception as e:
                                errors.append(e)
                        # Show errors
                        if errors:
                            err_str = ""
                            for e in errors:
                                err_str += str(e) + "\n"
                            err_str = err_str[:-1]
                            #QMessageBox.critical(self, "Активация " + plugin, err_str, QMessageBox.Ok)
                            print(err_str)
        del pt

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
            action.setData(plugin)  # Set reference to us plugin into menu
            action.setStatusTip("Управление модулем " + pname)
            action.triggered.connect(self.mclick)
            actions.append(action)
        return actions

    def mclick(self):
        """ Mouse click from devices menu """
        plugin = qApp.sender().data()
        try:
            psettings = PluginSettings(self, plugin)
            psettings.show()
        except Exception as e:
            print(e)


class PluginSettings(QDialog):
    """Settings window for current plugin"""

    def __init__(self, parent, plugin):
        self.plugin_info_lb = QLabel("Plugin info")
        self.activate_btn = QPushButton("Активировать")
        self.plugin = plugin
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        self.setWindowModality(Qt.WindowModal)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        self.setWindowTitle(self.plugin.get_info()["plugin_name"])
        self.setMaximumSize(800, 600)

        plugin_frame = QFrame()
        plugin_frame.setMinimumSize(400, 200)
        self.plugin.build_settings(plugin_frame)

        self.activate_btn.setFixedSize(150, 30)
        self.activate_btn.setCheckable(True)
        if self.plugin.get_info()["activated"]:
            self.activate_btn.setIcon(QIcon("./res/on.ico"))
            self.activate_btn.setText("Деактивировать")
        else:
            self.activate_btn.setIcon(QIcon("./res/off.ico"))
        self.activate_btn.setIconSize(QSize(24, 24))

        self.activate_btn.clicked.connect(self.activate_plugin)

        self.plugin_info_lb.setWordWrap(True)
        self.plugin_info_lb.setFixedWidth(plugin_frame.width() - 150)
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
            self.plugin: PTBasePlugin
            if not self.plugin.get_info()["activated"]:
                # self.plugin.activate()
                self.plugin.__activated = True
                self.activate_btn.setIcon(QIcon("./res/on.ico"))
                self.activate_btn.setText("Деактивировать")
                print("Activate successfully, plugin with ", self.plugin.get_channels_count(), "relays")
            else:
                self.plugin.deactivate()
                self.activate_btn.setIcon(QIcon("./res/off.ico"))
                self.activate_btn.setText("Активировать")
                print(self.plugin, "deactivated")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка активации", str(e), QMessageBox.Ok)

    def closeEvent(self, e):
        """On plugin settings close"""
        # Rebuild timer controls
        print("Rebuild timer controls")
        self.parent().add_plugin_controls()


if __name__ == "__main__":
    import sys

    os.chdir("..")
    print(os.getcwd())

    app = QApplication([])
    mw = MainWindow(ConfigParser())
    mw.show()
    app.exec()
