#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pt

from PySide.QtGui import (QWidget, QApplication, QTabWidget, QFrame, QVBoxLayout, QHBoxLayout,
                          QCheckBox, QFormLayout, QSpinBox, QLineEdit, QMessageBox, QPushButton,
                          QSizePolicy, QStyleFactory, QComboBox)
from PySide.QtCore import Qt


class Settings(QWidget):
    def __init__(self, parent: QWidget, config):
        super().__init__(parent, Qt.Window)
        self.tabs = QTabWidget()
        self.config = config

        self.tab_names = (
            ("Общие", General),
            ("Тарификация", Tariffication),
            ("Печать квитанций", Printing)
        )
        self._setup_ui()

    def _setup_ui(self):
        self.setMinimumSize(640, 480)
        self.setWindowTitle("Настройки")

        # Tabs
        self.build_tabs()

        vbox_lay = QVBoxLayout(self)
        vbox_lay.addWidget(self.tabs)

        # Accept settings button
        self.accept_btn = QPushButton("Применить")
        self.accept_btn.clicked.connect(self.close)
        self.accept_btn.setSizePolicy(
            QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
        )
        vbox_lay.addWidget(self.accept_btn, alignment=Qt.AlignRight | Qt.AlignBottom)

    def build_tabs(self):
        for tab_name in self.tab_names:
            tab_frame = tab_name[1](self.config)
            self.tabs.addTab(tab_frame, tab_name[0])

    def __del__(self):
        print("Settings destroyed")

    def closeEvent(self, e):
        for tab_index in range(self.tabs.count()):
            self.tabs.widget(tab_index).set_config()
        pt.set_ui_settings(self.config)
        self.parent().save_config()

    def show(self, tab_index):
        super().show()
        if 0 <= tab_index < self.tabs.count():
            self.tabs.setCurrentIndex(tab_index)
        self.activateWindow()


class General(QFrame):
    """General tab settings"""
    def __init__(self, config):
        super().__init__()
        self.config = config
        self._setup_ui()
        try:
            self.load_config()
        except Exception as e:
            print(e)
            QMessageBox.critical(self, "", "Ошибка при загрузке настроек", QMessageBox.Ok)

    def _setup_ui(self):
        fm = self.fontMetrics()

        self.activate_plugin_on_start_cb = QCheckBox("Активировать загруженные плагины при старте", self)

        # Default channel name
        self.default_channel_name = QLineEdit()
        self.default_channel_name.setMaxLength(15)
        self.default_channel_name.setToolTip("Максимальная длина названия " +
                                             str(self.default_channel_name.maxLength()) + " символов")
        self.default_channel_name.setFixedWidth(fm.widthChar("0") * (self.default_channel_name.maxLength()+2))

        # Default font size
        self.default_font_size = QSpinBox(self)
        self.default_font_size.setMinimum(8)
        self.default_font_size.setMaximum(14)
        self.default_font_size.setFixedWidth(fm.widthChar("0") * 6)

        # UI style
        self.style_cb = QComboBox()
        self.style_cb.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

        # Layouts
        form_lay = QFormLayout()
        form_lay.addRow(self.activate_plugin_on_start_cb)
        form_lay.addRow("Размер шрифта по умолчанию", self.default_font_size)
        form_lay.addRow("Название канала устройства по умолчанию", self.default_channel_name)
        form_lay.addRow("Стиль интерфейса", self.style_cb)

        root_lay = QHBoxLayout(self)
        root_lay.addLayout(form_lay)

    def load_config(self):
        """Load config data into form for edit"""
        if not self.config.has_section(pt.APP_MAIN_SECTION):
            return
        self.activate_plugin_on_start_cb.setChecked(
            self.config.getboolean(pt.APP_MAIN_SECTION, "activate_plugin_on_start", fallback=False)
        )
        self.default_channel_name.setText(
            self.config.get(pt.APP_MAIN_SECTION, "default_channel_name", fallback="Канал")
        )
        self.default_font_size.setValue(
            self.config.getint(pt.APP_MAIN_SECTION, "default_font_size", fallback=12)
        )
        # Styles combobox
        excluded_styles = ['Motif', 'CDE', "Windows"]
        styles = []
        for style in QStyleFactory.keys():
            if style in excluded_styles:
                continue
            else:
                styles.append(style)
        self.style_cb.addItems(styles)
        curr_style = self.config.get(pt.APP_MAIN_SECTION, "ui_style", fallback="")
        self.style_cb.setCurrentIndex(self.style_cb.findText(curr_style))

    def set_config(self):
        """Store data into config, no save!"""
        if not self.config.has_section(pt.APP_MAIN_SECTION):
            self.config.add_section(pt.APP_MAIN_SECTION)
        self.config.set(
            pt.APP_MAIN_SECTION, "activate_plugin_on_start", str(self.activate_plugin_on_start_cb.isChecked())
        )
        self.config.set(pt.APP_MAIN_SECTION, "default_channel_name", self.default_channel_name.text())
        self.config.set(pt.APP_MAIN_SECTION, "default_font_size", str(self.default_font_size.value()))
        self.config.set(pt.APP_MAIN_SECTION, "ui_style", self.style_cb.currentText())



class Tariffication(QFrame):
    """Tariffication tab settings"""
    def __init__(self, config):
        super().__init__()
        self.config = config

    def load_config(self):
        """Load config data into form for edit"""
        pass

    def set_config(self):
        """Store data into config, no save!"""
        pass


class Printing(QFrame):
    """Printing tab settings"""
    def __init__(self, config):
        super().__init__()
        self.config = config

    def load_config(self):
        """Load config data into form for edit"""
        pass

    def set_config(self):
        """Store data into config, no save!"""
        pass


if __name__ == "__main__":
    import os

    os.chdir("..")
    config = pt.read_config()

    app = QApplication([])

    app.setStyle("")

    settings = Settings(None, config)
    settings.show(0)
    app.exec_()
