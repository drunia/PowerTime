#!/usr/bin/env python3
# --* encoding: utf-8 *--

import os
import sys
import configparser

from PyQt5.QtWidgets import QApplication, QDesktopWidget
from ui.main import MainWindow


START_DIR = os.getcwd()
MAIN_CONF_FILE = "main.conf"
PLUGINS_CONF_SECTION = "Plugins"

def read_config(filename=MAIN_CONF_FILE):
    cp = configparser.ConfigParser()
    cp.optionxform = str
    cp.read(filename)
    return cp

def write_config(filename=MAIN_CONF_FILE):
    with open(filename, "w") as f:
        config.write(f)
    print("Config writed")

if __name__ == "__main__":
    config = read_config(MAIN_CONF_FILE)
    print("On COM1 attached:", config.get("ICSE0XXA_devices", "COM1", fallback=""))


    app = QApplication(sys.argv)
    desktop: QDesktopWidget = app.desktop()

    mw = MainWindow(config)
    mw.show()

    # Usb device plug-in/plug-out notify
    usb_notofication = None
    if os.name == "nt":
        import devices.usb_device_event_win
        usb_notofication = devices.usb_device_event_win.Notification()
    elif os.name == "linux":
        import  devices.usb_device_event_linux

    if usb_notofication:
        pass


    #app.setStyle("fusion")
    sys.exit(app.exec())
