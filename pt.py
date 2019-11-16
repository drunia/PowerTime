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


def set_ui_settings(config):
    """Set some UI settings (font, style, etc, ...)"""
    # Style
    QApplication.setStyle(config.get(APP_MAIN_SECTION, "ui_style", fallback=""))
    # Font
    f = QApplication.font()
    f.setPointSize(config.getint(APP_MAIN_SECTION, "default_font_size", fallback=f.pointSize()))
    QApplication.setFont(f)


if __name__ == "__main__":
    from ui.main import MainWindow

    config = read_config(MAIN_CONF_FILE)
    app = QApplication(sys.argv)

    # Set some UI settings
    set_ui_settings(config)

    app.setApplicationName("PowerTime")
    app.setApplicationVersion(VERSION)
    app.setWindowIcon(QIcon("./res/pt.ico"))

    mw = MainWindow(config)

    sys.exit(app.exec_())
