#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from devices.icse0xxa import ICSE0XXADevice, load_devices_from_config, save_devices_to_config, find_devices
from plugins.base_plugin import PTBasePlugin, ActivateException, SwitchException
from PyQt5.Qt import (QFrame, QWidget, QHBoxLayout, QVBoxLayout, QListView, QStandardItemModel, QStandardItem,
                      QPushButton, QLabel, QIcon, QApplication, QMessageBox, QPixmap)
from PyQt5.QtCore import QSize, QModelIndex, Qt


class ICSE0XXA_Plugin(PTBasePlugin):
    """Plugin for control ICSE0XXA devices"""

    def __init__(self):
        super().__init__()
        # Structure of __channels : {global number of channel: [device, local number of channel], ...}
        self.__channels = {}
        self._activated = False
        self.__dev_list = []

    def __check_activated(self):
        if not self._activated:
            raise ActivateException("Need activate first!")

    def get_info(self):
        return {"author": "Andrunin Dmitry",
                "plugin_name": "ICSE0XXA control",
                "version": 1.0,
                "description": "Плагин для управления релейными модулями типа ICSE0XXA",
                "activated": self._activated}

    def get_channels_count(self):
        self.__check_activated()
        count = 0
        for d in self.__dev_list:
            count += d.relays_count()
        return count

    def switch(self, channel, state):
        self.__check_activated()
        if channel > len(self.__channels):
            raise SwitchException(
                "Num {} channel biggest of channels {} "
                "on connected devices.".format(channel, len(self.__channels))
            )
        dev, ch = self.__channels[channel]
        dev.switch_relay(ch, state)

    def activate(self):
        # Load from config file first
        self.__dev_list = load_devices_from_config()
        if len(self.__dev_list) == 0:
            print("Try find devices on serial ports...")
            self.__dev_list = find_devices()
            if len(self.__dev_list) > 0:
                save_devices_to_config(self.__dev_list)
            else:
                print("No devices!")

        for d in self.__dev_list:
            d.init_device(not self._activated)
            print(d, "initialized")

        relay = 0
        for d in self.__dev_list:
            for r in range(0, 8):
                self.__channels[r + relay] = [d, r]
            relay += r + 1

        self._activated = True
        return self._activated

    def build_settings(self, widget: QWidget):
        Settings(self, widget)


class Settings(QFrame):
    def __init__(self, plugin: ICSE0XXA_Plugin, parent=None):
        super().__init__(parent)
        self.st_lb = QLabel()
        self.img_lb = QLabel()
        self.info_lb = QLabel()
        self.vboxl, self.vboxr = QVBoxLayout(), QVBoxLayout()
        self.hbox = QHBoxLayout()
        self.qlist = QListView()
        self.qlist_model = QStandardItemModel(self.qlist)
        self.find_button = QPushButton(QIcon("./res/search.ico"), "Поиск устройств")
        self.save_button = QPushButton(QIcon("./res/save.ico"), "Записать")
        self.plugin = plugin
        self.setup_ui()

    def setup_ui(self):
        # Set size = container size
        self.setMinimumSize(500, 400)
        self.setMaximumSize(600, 500)
        self.parent().setFixedSize(530, 400)

        # layouts
        self.hbox.addLayout(self.vboxl)
        self.hbox.addLayout(self.vboxr, 1)
        self.setLayout(self.hbox)

        # QListView to view connected/saved devices
        self.qlist.setModel(self.qlist_model)
        f = self.qlist.font();
        f.setPointSize(12)
        self.qlist.setFont(f)
        self.qlist.clicked.connect(self.qlist_item_clicked)
        self.qlist.selectionModel().currentChanged.connect(self.qlist_sel_changed)
        self.vboxl.addWidget(self.qlist)

        # Search button
        self.find_button.setIconSize(QSize(20, 20))
        self.find_button.clicked.connect(self.find_devices)

        # Save Button
        self.save_button.setIconSize(QSize(20, 20))
        self.save_button.clicked.connect(self.save_settings)

        # Buttons H layout
        butt_lay = QHBoxLayout()
        butt_lay.addWidget(self.find_button)
        butt_lay.addWidget(self.save_button)
        self.vboxl.addLayout(butt_lay)

        # Info label
        self.info_lb.setWordWrap(True)
        self.info_lb.setFont(f)
        self.vboxr.addWidget(self.info_lb, alignment=Qt.AlignTop)

        # Image label
        self.img_lb.setFixedWidth(self.width() // 2)
        self.vboxr.addWidget(self.img_lb)

        # Status label
        self.st_lb.setFont(f)
        self.st_lb.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.st_lb.setText("Status text")
        self.vboxr.addWidget(self.st_lb, alignment=Qt.AlignBottom)

        # Load devices
        devs = load_devices_from_config()
        for d in devs:
            item = QStandardItem(d.name())
            item.setCheckable(True)
            item.setCheckState(Qt.Checked)
            item.setEditable(False)
            item.setData(d)
            item.setIcon(QIcon("./res/icse0xxa_device.ico"))
            self.qlist_model.appendRow(item)
        self.st_lb.setText("Загружено утсройств: {} ".format(len(devs)))
        self.show()

    def qlist_sel_changed(self, item1, item2):
        if item1.row() != item2.row():
            self.qlist.clicked[QModelIndex].emit(item1)

    # Search devices on serial bus
    def find_devices(self):
        self.st_lb.setText("Выполняется поиск...")
        QApplication.processEvents()
        devs = find_devices()
        if len(devs) == 0:
            self.st_lb.setText("")
            r = QMessageBox.warning(
                self, "Поиск устройств",
                (
                    "Устройства не найдены!\n\n"
                    "Попробуйте выключить/включить устройство(ва) и выполнить поиск снова.\n"
                    "Удалить сохраненные устройства?"
                ), QMessageBox.Yes | QMessageBox.No)
            if r == QMessageBox.Yes:
                self.qlist_model.clear()
            return
        # Add from find_devices()
        self.qlist_model.clear()
        for d in devs:
            item = QStandardItem(d.name())
            item.setCheckable(True)
            item.setData(d)
            item.setIcon(QIcon("./res/icse0xxa_device.ico"))
            self.qlist_model.appendRow(item)
        self.st_lb.setText("Найдено утсройств: {} ".format(len(devs)))

    def save_settings(self):
        devs = []
        m = self.qlist_model
        for i in range(0, m.rowCount()):
            item: QStandardItem = m.item(i)
            if item.checkState():
                devs.append(item.data())
        if len(devs) > 0:
            save_devices_to_config(devs)
            QMessageBox.information(self, "Запись в файл",
                                    "Записано {} устройств".format(len(devs)), QMessageBox.Ok)
        elif m.rowCount() > 0:
            QMessageBox.warning(self,
                                "Запись в файл", "Отметьте устройство для сохранения", QMessageBox.Ok)

    def qlist_item_clicked(self, item: QModelIndex):
        try:
            dev: ICSE0XXADevice = self.qlist_model.item(item.row()).data()
            devs = {
                0xAB: ["ICSE012A - 4х канальный модуль без дополнительного питания", "icse012A.jpg"],
                0xAD: ["ICSE013A - 2х канальный модуль без дополнительного питания", "icse013A.jpg"],
                0xAC: ["ICSE014A - 8х канальный модуль с дополнительным питанием", "icse014A.jpg"]
            }
            info_text = devs[dev.id()][0]
            img_name = devs[dev.id()][1]
            self.info_lb.setText(info_text)
            self.img_lb.setPixmap(QPixmap("./res/" + img_name))
        except Exception as e:
            print(e)
