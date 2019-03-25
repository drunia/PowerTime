#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pt

from PySide.QtGui import (QWidget, QApplication, QTabWidget, QFrame, QVBoxLayout, QHBoxLayout,
                          QCheckBox, QFormLayout, QSpinBox)
from PySide.QtCore import Qt


class Settings(QWidget):
    def __init__(self, parent: QWidget, config):
        super().__init__(parent, Qt.Window)
        self.config = config

        self.tab_names = {
            "Общие": General,
            "Тарификация": Tariffication,
            "Печать квитанций": Printing
        }
        self.setup_ui()

    def setup_ui(self):
        self.setMinimumSize(640, 480)
        self.setWindowTitle("Настройки")
        # Tabs
        self.tabs = QTabWidget()
        self.build_tabs()

        vbox_lay = QVBoxLayout(self)
        vbox_lay.addWidget(self.tabs)

    def build_tabs(self):
        for tab_name in self.tab_names.keys():
            tab_frame = self.tab_names[tab_name]()
            self.tabs.addTab(tab_frame, tab_name)

    def __del__(self):
        print("Settings destroyed")

    def closeEvent(self, e):
        self.parent().save_config()

    def show(self, tab_index):
        super().show()
        if 0 <= tab_index < self.tabs.count():
            self.tabs.setCurrentIndex(tab_index)
        self.activateWindow()


class General(QFrame):
    """General tab settings"""
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        fm = self.fontMetrics()

        self.save_window_geometry_cb = QCheckBox("Сохранять размеры и положение главного окна", self)
        self.activate_plugin_on_start_cb = QCheckBox("Активировать загруженные плагины при старте", self)

        # Default font size
        self.default_font_size = QSpinBox(self)
        self.default_font_size.setMinimum(8)
        self.default_font_size.setMaximum(14)
        self.default_font_size.setFixedWidth(fm.widthChar("0") * 6)

        # Layouts
        form_lay = QFormLayout()
        form_lay.addRow(self.save_window_geometry_cb)
        form_lay.addRow(self.activate_plugin_on_start_cb)
        form_lay.addRow("Размер шрифта по умолчанию", self.default_font_size)

        root_lay = QHBoxLayout(self)
        root_lay.addLayout(form_lay)


class Tariffication(QFrame):
    """Tariffication tab settings"""
    def __init__(self):
        super().__init__()


class Printing(QFrame):
    """Printing tab settings"""
    def __init__(self):
        super().__init__()


if __name__ == "__main__":
    import os

    os.chdir("..")
    config = pt.read_config()

    app = QApplication([])
    settings = Settings(None, config)
    settings.show(0)
    app.exec_()
