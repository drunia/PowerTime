#!/usr/bin/env python3
# --* encoding: utf-8 *--

import os
import sys
import configparser

from PyQt5.QtWidgets import QDesktopWidget, QApplication
from ui.main import MainWindow


START_DIR = os.getcwd()
MAIN_CONF_FILE = "main.conf"

def read_config(filename=MAIN_CONF_FILE):
    cp = configparser.ConfigParser()
    cp.optionxform = str
    cp.read(filename)
    return cp

def write_config(filename=MAIN_CONF_FILE):
    config.write(filename)

config = read_config("icse0xxa.conf")
print(config.get("DEFAULT", "option", "123"))


sys.exit(0)

app = QApplication(sys.argv)
desktop: QDesktopWidget = app.desktop()

mw = MainWindow()
mw.show()

app.setStyle("fusion")
sys.exit(app.exec())
