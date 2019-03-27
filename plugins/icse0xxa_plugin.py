#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from devices.icse0xxa import load_devices_from_config, save_devices_to_config, find_devices
from plugins.base_plugin import PTBasePlugin, ActivateException, SwitchException, NoDevicesException
from PySide.QtGui import (QFrame, QWidget, QHBoxLayout, QVBoxLayout, QListView, QStandardItemModel, QStandardItem,
                          QPushButton, QLabel, QIcon, QApplication, QMessageBox, QPixmap)
from PySide.QtCore import QSize, QModelIndex, Qt


class ICSE0XXAPlugin(PTBasePlugin):
    """Plugin for control ICSE0XXA devices"""

    def __init__(self):
        super().__init__()
        # Structure of __channels : {global number of channel: [device, local number of channel], ...}
        self.__channels = {}
        self.__activated = False
        self.__dev_list = []
        self.settings = None

    def __check_activated(self):
        if not self.__activated:
            raise ActivateException("Need activate first!")

    def get_info(self):
        return {"author": "Andrunin Dmitry",
                "plugin_name": "ICSE0XXA control",
                "version": 1.0,
                "description": "Плагин для управления релейными модулями типа ICSE0XXA",
                "activated": self.__activated}

    def get_channels_count(self):
        self.__check_activated()
        count = 0
        for d in self.__dev_list:
            count += d.relays_count()
        return count

    def get_channels_info(self):
        return self.__channels

    def switch(self, channel, state):
        self.__check_activated()
        if channel + 1 > len(self.__channels):
            raise SwitchException(
                "Channel {}  biggest of total channels {} "
                "on connected devices.".format(channel + 1, len(self.__channels))
            )
        dev, ch = self.__channels[channel]
        dev.switch_relay(ch, state)

    def activate(self):
        # Load from config file first
        self.__dev_list = load_devices_from_config()
        if len(self.__dev_list) == 0:
            raise NoDevicesException("Activation error: No devices!")

        # Init devices
        for d in self.__dev_list:
            d.init_device()
            print("ICSE0XXAPlugin.activate():", d, "initialized")
            # DEBUG. Delete this below and uncomment above
            # d._ICSE0XXADevice__initialized = True

        relay = 0
        for d in self.__dev_list:
            for r in range(0, d.relays_count()):
                self.__channels[r + relay] = [d, r]
            relay += r + 1
        self.__activated = len(self.__dev_list) > 0
        return self.__activated

    def deactivate(self):
        # del devices & close ports
        self.__dev_list = []
        self.__channels = {}
        self.__activated = False

    def devices(self):
        """Return current initialized devices"""
        return self.__dev_list

    def build_settings(self, widget: QWidget):
        self.settings = Settings(self, widget)


class Settings(QFrame):
    def __init__(self, plugin, parent=None):
        super().__init__(parent)
        self.st_lb = QLabel()
        self.img_lb = QLabel()
        self.info_lb = QLabel()
        self.vboxl, self.vboxr = QVBoxLayout(), QVBoxLayout()
        self.hbox = QHBoxLayout()
        self.find_button = QPushButton(QIcon("./res/search.ico"), "Поиск устройств")
        self.save_button = QPushButton(QIcon("./res/save.ico"), "Записать")

        self.qlist = QListView()
        self.qlist_model = QStandardItemModel(self.qlist)
        # For fix run-time error: Internal C++ object (PySide.QtGui.QItemSelectionModel) already deleted.
        self.qlist_sel_model = None

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
        f = self.qlist.font()
        f.setPointSize(12)
        self.qlist.setFont(f)
        self.qlist.clicked.connect(self.qlist_item_clicked)
        self.qlist_sel_model = self.qlist.selectionModel()
        self.qlist_sel_model.currentChanged.connect(self.qlist_sel_changed)
        self.vboxl.addWidget(self.qlist)

        # Search button
        self.find_button.setIconSize(QSize(20, 20))
        self.find_button.clicked.connect(self.find_devices)
        self.find_button.setFont(f)

        # Save Button
        self.save_button.setIconSize(QSize(20, 20))
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setFont(f)

        # Buttons H layout
        butt_lay = QHBoxLayout()
        butt_lay.addWidget(self.find_button)
        butt_lay.addWidget(self.save_button)
        self.vboxl.addLayout(butt_lay)

        # Info label
        self.info_lb.setWordWrap(True)
        self.info_lb.setFont(f)
        self.info_lb.setText(
            "Подсказка:\nДля удаления устройства\nсо списка "
            "нужно снять галочку\nи затем нажать кнопку Записать"
        )
        self.vboxr.addWidget(self.info_lb, alignment=Qt.AlignTop)

        # Image label
        self.img_lb.setFixedWidth(self.width() // 2)
        self.vboxr.addWidget(self.img_lb)

        # Status label
        self.st_lb.setFont(f)
        self.st_lb.setAlignment(Qt.AlignRight | Qt.AlignBottom)
        self.st_lb.setText("Status text")
        self.vboxr.addWidget(self.st_lb, alignment=Qt.AlignBottom)

        # Display devices
        devs = self.plugin.devices()
        self.build_dev_list(devs)

        self.show()

    def build_dev_list(self, devs):
        """Create list in QListView from devs[]"""
        self.qlist_model.clear()
        for d in devs:
            item = QStandardItem(d.name())
            item.setCheckable(True)
            item.setCheckState(Qt.Checked)
            item.setData(d.id())
            item.setEditable(False)
            item.setIcon(QIcon("./res/icse0xxa_device.ico"))
            self.qlist_model.appendRow(item)
        self.st_lb.setText("Загружено утсройств: {} ".format(len(devs)))

    def qlist_sel_changed(self, item1, item2):
        if item1.row() != item2.row() and item2.row() > 0:
            self.qlist.clicked[QModelIndex].emit(item1)

    # Search devices on serial bus
    def find_devices(self):
        self.st_lb.setText("Выполняется поиск...")
        QApplication.processEvents()
        devs = find_devices()
        if len(devs) == 0:
            self.st_lb.setText("Устройств не найдено")
            QMessageBox.warning(
                self, "Поиск устройств",
                (
                    "Устройства не найдены!\n\n"
                    "Попробуйте выключить/включить устройство(ва) и выполнить поиск снова.\n"
                ), QMessageBox.Ok)
            return
        self.qlist_model.clear()
        # Add active devices
        if self.plugin.get_info()["activated"]:
            for d in self.plugin.devices():
                print("Save active device:", d)
                devs.append(d)
        # Build list from find_devices()
        self.build_dev_list(devs)
        self.st_lb.setText("Найдено утсройств: {} ".format(len(devs)))

    def save_settings(self):
        devs = []
        m = self.qlist_model
        for i in range(0, m.rowCount()):
            item = m.item(i)
            if item.checkState():
                devs.append(item.data())
        if m.rowCount() > 0 and len(devs) == 0:
            if QMessageBox.question(self, "Запись в файл",
                                    "Не отмечена ни одна запись в списке.\n"
                                    "Все ранее сохраненые устройства будут отчищены, все верно?",
                                    QMessageBox.Yes, QMessageBox.Cancel) == QMessageBox.Cancel:
                return
        save_devices_to_config(devs)
        if len(devs) > 0:
            QMessageBox.information(self, "Запись в файл",
                                    "Записано {} устройств".format(len(devs)), QMessageBox.Ok)
        m.clear()
        self.build_dev_list(devs)

    def qlist_item_clicked(self, item: QModelIndex):
        try:
            id = self.qlist_model.item(item.row()).data()
            devs = {
                0xAB: ["ICSE012A - 4х канальный модуль без дополнительного питания", "icse012A.jpg"],
                0xAD: ["ICSE013A - 2х канальный модуль без дополнительного питания", "icse013A.jpg"],
                0xAC: ["ICSE014A - 8х канальный модуль с дополнительным питанием", "icse014A.jpg"]
            }
            info_text = devs[id][0]
            img_name = devs[id][1]
            self.info_lb.setText(info_text)
            self.img_lb.setPixmap(QPixmap("./res/" + img_name))
        except Exception as e:
            print(e)
