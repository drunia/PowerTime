#!/usr/bin/env python3
# --* encoding: utf-8 *--

import os
import sys
import configparser

from PyQt5.QtWidgets import QApplication, QDesktopWidget
from PyQt5.QtGui import QIcon


START_DIR = os.getcwd()
MAIN_CONF_FILE = "main.conf"
VERSION = "1.0.0"

APP_MAIN_SECTION = "Main"
PLUGINS_CONF_SECTION = "Plugins"
TARIFFS_CONF_SECTION = "Tariffs"


def read_config(filename=MAIN_CONF_FILE):
    cp = configparser.ConfigParser()
    cp.optionxform = str
    cp.read(filename)
    return cp


def write_config(c: configparser.ConfigParser, filename=MAIN_CONF_FILE):
    with open(filename, "w") as f:
        c.write(f)
    print("Config writed")


if __name__ == "__main__":
    from ui.main import MainWindow

    config = read_config(MAIN_CONF_FILE)

    # Usb device plug-in/plug-out notify
    usb_notification = None
    if os.name == "nt":
        import devices.usb_device_event_win
        usb_notification = devices.usb_device_event_win.Notification()
    elif os.name == "linux":
        import devices.usb_device_event_linux

    if usb_notification:
        pass

    app = QApplication(sys.argv)
    app.setStyle("fusion")
    app.setApplicationDisplayName("PowerTime")
    app.setApplicationVersion(VERSION)
    app.setWindowIcon(QIcon("./res/pt.ico"))
    desktop: QDesktopWidget = app.desktop()

    mw = MainWindow(config)
    mw.show()

    sys.exit(app.exec())
