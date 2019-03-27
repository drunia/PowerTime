#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os

from PySide.QtGui import *
from PySide.QtCore import Qt, QSize
from ui.timer_control import *
from ui.settings import Settings


class MainWindow(QMainWindow):
    """ Main control window of pt """

    def __init__(self, config: ConfigParser):
        super().__init__()

        self.config = config
        self.loaded_plugins = []
        self.plugin_controls = []
        self.settings = None

        self.plugins = self.find_plugins()
        self._load_plugins()

        self._setup_ui()
        self._activate_plugins_on_start()
        self.add_plugin_controls()

    def _setup_ui(self):
        self.setWindowTitle("PowerTime")
        # Size from config
        if self.config.has_section(pt.APP_MAIN_SECTION):
            width, height = 1024, 768
            try:
                width = self.config.getint(pt.APP_MAIN_SECTION, "width", fallback=1024)
                height = self.config.getint(pt.APP_MAIN_SECTION, "height", fallback=768)
            except ValueError:
                pass
            self.resize(width, height)
            if self.config.getboolean(pt.APP_MAIN_SECTION, "maximized", fallback=False):
                self.showMaximized()
        else:
            # Default: show maximized
            self.showMaximized()

        # Main menu
        menubar = self.menuBar()
        menubar.setMinimumHeight(40)

        # Settings menu
        self.menu_settings = QMenu("Настройки", self)
        self.menu_settings.aboutToShow.connect(self._init_settings)
        menubar.addMenu(self.menu_settings)

        # Devices menu (plugins)
        self.menu_devices = QMenu("Модули устройств", self)
        self.menu_devices.addActions(self._build_devices_actions())
        self.menu_devices.aboutToShow.connect(self.devices_menu_show)
        menubar.addMenu(self.menu_devices)

        # Central widget
        self.control_frame = QFrame()
        self.control_frame.setLayout(QGridLayout())

        self.scroll_area = QScrollArea(self.centralWidget())
        self.scroll_area.setWidgetResizable(True)

        scroll_vbox_lay = QVBoxLayout(self.scroll_area.viewport())
        scroll_vbox_lay.addWidget(self.control_frame, alignment=Qt.AlignCenter)
        self.setCentralWidget(self.scroll_area)

        # Statusbar
        self.statusBar().showMessage("Вeрсия: " + QApplication.applicationVersion())
        self.statusBar()

        self.show()

    def add_plugin_controls(self):
        """Add switchable controls for controlling active plugin"""
        all_channels_info = {}
        for plugin in self._get_activated_plugins():
            for k, v in plugin.get_channels_info().items():
                info = v.copy()
                info.append(plugin)
                all_channels_info[k] = info
        channels = len(all_channels_info)

        # DEBUG
        #channels = 4

        cols = 4 if (channels // 5) > 0 else 2
        print("total channels:", channels)

        # Delete all old controls
        for c in self.plugin_controls:
            c.close()
        self.plugin_controls.clear()

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
                if self.config.has_option(pt.APP_MAIN_SECTION, "default_channel_name"):
                    control.set_control_tittle(self.config.get(pt.APP_MAIN_SECTION, "default_channel_name"))
        self.scroll_area.setWidget(self.control_frame)

    def switch_event(self, control, state: bool):
        try:
            plugin = self.loaded_plugins[0]
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
        if not self.isMaximized():
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
        # Save settings, when main window close
        self.save_config()

    def devices_menu_show(self):
        for action in self.menu_devices.actions():
            plugin = action.data()
            if plugin.get_info()["activated"]:
                action.setIcon(QIcon("./res/on.ico"))
            else:
                action.setIcon(QIcon("./res/off.ico"))

    def find_plugins(self, plugins_dir="./plugins"):
        """Search device-plugins in modules dir
        :return list[Plugin_Class...,]"""
        import pkgutil
        import inspect
        plugins = []
        # Find modules with classes inherited from PTBasePlugin
        mod_info_list = list(pkgutil.iter_modules([plugins_dir]))
        for module in mod_info_list:
            m = __import__("plugins." + module[1], fromlist=['object'])
            clslist = inspect.getmembers(m, inspect.isclass)
            for cls in clslist:
                bases = cls[1].__mro__
                for b in bases:
                    if b.__name__ == "PTBasePlugin" and not cls[1].__name__ == "PTBasePlugin":
                        print("{}(): Plugin class finded: {}".format(inspect.stack()[0][3], cls[1].__name__))
                        plugins.append(cls[1])
                        break
        del pkgutil
        del inspect
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
                    errors = []
                    for p in self.loaded_plugins:
                        if p.get_info()["plugin_name"] == plugin:
                            try:
                                print("_activate_plugins_on_start():", plugin)
                                p.activate()
                            except Exception as e:
                                errors.append(e)
                    # Show errors
                    if errors:
                        err_str = ""
                        for e in errors:
                            err_str += plugin + ": " + str(e) + "\n"
                        err_str = err_str[:-1]
                        QMessageBox.critical(self, "Активация " + plugin, err_str, QMessageBox.Ok)
                        print("ERR: _activate_plugins_on_start():", err_str)
        del pt

    def _build_devices_actions(self):
        """
        Build actions for devices menu
        :return list[QAction,...]
        """
        actions = []
        for plugin in self.loaded_plugins:
            pname = plugin.get_info()["plugin_name"]
            action = QAction(pname, self)
            action.setCheckable(True)
            action.setChecked(True)
            action.setData(plugin)  # Set reference to us plugin into menu
            action.setStatusTip("Управление модулем " + pname)
            action.triggered.connect(self.mclick)
            actions.append(action)
        return actions

    def _init_settings(self):
        """
        Create settings instance,
        when menu Settings clicked first time
        """
        if not self.settings:
            self.settings = Settings(self, self.config)
            print("Settings created")

        self.menu_settings.clear()
        self.menu_settings.addActions(self._build_settings_actions())

    def _build_settings_actions(self):
        """
        Build actions for settings menu
        :return list[QAction,...]
        """
        actions = []
        for item in self.settings.tab_names:
            action = QAction(item[0], self)
            action.setStatusTip("Открыть настройки: " + item[0])
            action.setData(len(actions))
            action.triggered.connect(self.menu_open_settings_tab)
            actions.append(action)
        return actions

    def menu_open_settings_tab(self):
        index = QApplication.sender(self).data()
        self.settings.show(index)

    def mclick(self):
        """ Mouse click from devices menu """
        plugin = QApplication.sender(self).data()
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

        # Integrate plugin settings
        self.plugin.build_settings(plugin_frame)

        self.activate_btn.setFixedSize(180, 30)
        self.activate_btn.setCheckable(True)
        if self.plugin.get_info()["activated"]:
            self.activate_btn.setIcon(QIcon("./res/on.ico"))
            self.activate_btn.setText("Деактивировать")
        else:
            self.activate_btn.setIcon(QIcon("./res/off.ico"))
        self.activate_btn.setIconSize(QSize(24, 24))

        self.activate_btn.clicked.connect(self.activate_plugin)

        self.plugin_info_lb.setWordWrap(True)
        self.plugin_info_lb.setFixedWidth(plugin_frame.width() - 180)
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
            self.plugin
            if not self.plugin.get_info()["activated"]:
                self.plugin.activate()
                self.activate_btn.setIcon(QIcon("./res/on.ico"))
                self.activate_btn.setText("Деактивировать")
                print("Activate successfully, plugin with ", self.plugin.get_channels_count(), "relays")
            else:
                # Check if plugin used in this time
                for p_control in self.parent().plugin_controls:
                    if not p_control.stopped:
                        if QMessageBox.warning(
                                self, "Внимание!",
                                "В данный момент плагина находится в использовании.\n"
                                "Деактивация плагина приведет к утрате результатов работы\n"
                                "Все равно продолжить ?",
                                QMessageBox.Yes | QMessageBox.No
                                ) == QMessageBox.No:
                            return
                self.plugin.deactivate()
                self.activate_btn.setIcon(QIcon("./res/off.ico"))
                self.activate_btn.setText("Активировать")
                print(self.plugin, "deactivated")
            # Rebuild timer controls
            print("Rebuild timer controls")
            self.parent().add_plugin_controls()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка активации", str(e), QMessageBox.Ok)

    def closeEvent(self, e):
        """On plugin settings close"""
        pass


if __name__ == "__main__":
    import sys

    os.chdir("..")
    print(os.getcwd())

    app = QApplication([])
    mw = MainWindow(ConfigParser())
    mw.show()
    app.exec_()
