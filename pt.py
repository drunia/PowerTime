#!/usr/bin/env python3
# --* encoding: utf-8 *--

import os
import sys
import configparser

from PySide.QtGui import QApplication, QIcon


START_DIR = os.getcwd()
MAIN_CONF_FILE = "main.conf"
VERSION = "1.0.0"

APP_MAIN_SECTION = "Main"
PLUGINS_CONF_SECTION = "Plugins"
TARIFFS_CONF_SECTION = "Tariffs"
TIMER_CONTROLS_SECTION = "TimerControls"


def read_config(filename=MAIN_CONF_FILE):
    cp = configparser.ConfigParser()
    cp.optionxform = str
    cp.read(filename, "utf-8")
    return cp


def write_config(c: configparser.ConfigParser, filename=MAIN_CONF_FILE):
    with open(filename, "w", encoding="utf-8") as f:
        c.write(f)
    print("Config writen")


if __name__ == "__main__":
    from ui.main import MainWindow

    config = read_config(MAIN_CONF_FILE)

    app = QApplication(sys.argv)
    app.setStyle("fusion")

    # Set default app font size
    f = app.font()
    if config.has_option(APP_MAIN_SECTION, "default_font_size"):
        f.setPointSize(config.getint(APP_MAIN_SECTION, "default_font_size", fallback=12))
    else:
        f.setPointSize(12)
    app.setFont(f)

    app.setApplicationName("PowerTime")
    app.setApplicationVersion(VERSION)
    app.setWindowIcon(QIcon("./res/pt.ico"))

    mw = MainWindow(config)

    # Usb device plug-in/plug-out notify
    port_notification = None
    if os.name == "nt":
        import devices.icsex00a_port_state_notificator_win

        port_notification = devices.icsex00a_port_state_notificator_win.PortStateNotificator()
    elif os.name == "linux":
        import devices.icsex00a_port_state_notificator_linux

    # Called when ports (Serial/Parallel/etc...) connected or disconnected
    def port_state_changed(port, state):
        print("Port [{}] connected state changed to: {}".format(port, state))

    if port_notification:
        print("port_notification created")
        port_notification.state_changed.connect(port_state_changed)

    sys.exit(app.exec_())
