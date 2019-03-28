#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from devices.icse0xxa import ICSE0XXADevice
from plugins.base_plugin import PTBasePlugin, ActivateException, SwitchException, NoDevicesException
from PySide.QtGui import (QFrame, QHBoxLayout, QVBoxLayout, QListView, QStandardItemModel, QStandardItem,
                          QPushButton, QLabel, QIcon, QApplication, QMessageBox, QPixmap)
from PySide.QtCore import QSize, QModelIndex, Qt

# Windows PortStateNotificatorWin
from ctypes import *
from PySide.QtCore import QObject, Signal
from win32.lib import win32con
from win32 import win32gui
from win32 import win32api

# Linux PortStateNotificatorWin
import os
if os.name == "linux":
    import pyudev

"""
Classes for listen enable/disable ports to re-init icse00xa module 
"""


# ICSE0XXAPlugin #######################################################################################################

class ICSE0XXAPlugin(PTBasePlugin):
    """Plugin for control ICSE0XXA devices"""

    def __init__(self):
        super().__init__()
        # Structure of __channels : {global number of channel: [device, local number of channel], ...}
        self.__channels = {}
        self.__activated = False
        self.settings = None
        self.__dev_list = self.load_devs_from_config()

    def load_devs_from_config(self):
        """
        Loading devices from config file
        :return list of loaded ICSE0XXADevice's
        """
        # Load devices from config file
        self.__dev_list = ICSE0XXADevice.load_devices_from_config()
        return self.__dev_list

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
        """Return current loaded devices"""
        return self.__dev_list

    def build_settings(self, parent_widget):
        self.settings = Settings(self, parent=parent_widget)
        return self.settings


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

        self.parent().setFixedSize(550, 450)

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
            # Set data : tuple (id, port)
            item.setData((d.id(), d.port()))
            item.setEditable(False)
            item.setIcon(QIcon("./res/icse0xxa_device.ico"))
            self.qlist_model.appendRow(item)
        self.st_lb.setText("Загружено устройств: {} ".format(len(devs)))

    def qlist_sel_changed(self, item1, item2):
        if item1.row() != item2.row() and item2.row() > 0:
            self.qlist.clicked[QModelIndex].emit(item1)

    # Search devices on serial bus
    def find_devices(self):
        self.st_lb.setText("Выполняется поиск...")
        QApplication.processEvents()
        devs = ICSE0XXADevice.find_devices()
        if len(devs) == 0:
            self.st_lb.setText("Устройств не найдено")
            QMessageBox.warning(
                self, "Поиск устройств",
                (
                    "Устройства не найдены!\n\n"
                    "Попробуйте выключить/включить устройство(ва) и выполнить поиск снова.\n"
                ), QMessageBox.Ok)
            return
        self.st_lb.setText("Найдено утсройств: {} ".format(len(devs)))
        self.qlist_model.clear()

        # Add find + loaded devices
        ports = list(map(lambda dev: dev.port(), self.plugin.devices()))
        devs = list(filter(lambda dev: dev.port() not in ports, devs))
        devs.extend(self.plugin.devices())

        # Build list from find_devices()
        self.build_dev_list(devs)

    def save_settings(self):
        devs = self.plugin.devices()
        checked_items_ports = []
        m = self.qlist_model
        for i in range(0, m.rowCount()):
            item = m.item(i)
            if item.checkState():
                checked_items_ports.append(item.data()[1])
        devs = list(filter(lambda dev: dev.port() in checked_items_ports, devs))
        if m.rowCount() > 0 and len(devs) == 0:
            if QMessageBox.question(self, "Запись в файл",
                                    "Не отмечена ни одна запись в списке.\n"
                                    "Все ранее сохраненые устройства будут отчищены, все верно?",
                                    QMessageBox.Yes, QMessageBox.Cancel) == QMessageBox.Cancel:
                return
        ICSE0XXADevice.save_devices_to_config(devs)
        # Re-load devices into plugin
        self.plugin.load_devs_from_config()
        devs = self.plugin.devices()
        if len(devs) > 0:
            QMessageBox.information(self, "Запись в файл",
                                    "Записано {} устройств".format(len(devs)), QMessageBox.Ok)
        m.clear()
        self.build_dev_list(devs)

    def qlist_item_clicked(self, item: QModelIndex):
        try:
            id = self.qlist_model.item(item.row()).data()[0]
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


# PortStateNotificator #################################################################################################

# Windows

# Device change events (WM_DEVICECHANGE wParam)
#
DBT_DEVICEARRIVAL = 0x8000
DBT_DEVICEREMOVECOMPLETE = 0x8004

#
# type of device in DEV_BROADCAST_HDR
#
DBT_DEVTYPE_PORT = 0x00000003

# c types
WORD = c_ushort
DWORD = c_ulong


class DEV_BROADCAST_HDR(Structure):
    _fields_ = [
        ("dbch_size", DWORD),
        ("dbch_devicetype", DWORD),
        ("dbch_reserved", DWORD)
    ]


class DEV_BROADCAST_PORT(Structure):
    _fields_ = [
        ("dbcp_size", DWORD),
        ("dbcp_devicetype", DWORD),
        ("dbcp_reserved", DWORD),
        ("dbcp_name", ARRAY(c_wchar, 255))
    ]


class PortStateNotificatorWin(QObject):
    """
    Signal emit when ports state changed
    :param str - port name
    :param bool - connect state
    """
    state_changed = Signal(str, bool)

    def __init__(self):
        super().__init__()
        message_map = {
            win32con.WM_DEVICECHANGE: self.onDeviceChange
        }

        wc = win32gui.WNDCLASS()
        hinst = wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "pt_port_state_listener"
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32con.COLOR_WINDOW
        wc.lpfnWndProc = message_map
        classAtom = win32gui.RegisterClass(wc)
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(
            classAtom,
            "pt_port_state_listener",
            style,
            0, 0,
            win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT,
            0, 0,
            hinst, None
        )

    def onDeviceChange(self, hwnd, msg, wparam, lparam):
        #
        # WM_DEVICECHANGE:
        #  wParam - type of change: arrival, removal etc.
        #  lParam - what's changed?
        #    if it's a volume then...
        #  lParam - what's changed more exactly
        #
        dev_broadcast_hdr = DEV_BROADCAST_HDR.from_address(lparam)

        # print("hwnd = {}, msg = {}, wparam = {}, lparam = {}".format(hwnd, msg, wparam, lparam))

        if wparam == DBT_DEVICEARRIVAL or wparam == DBT_DEVICEREMOVECOMPLETE and \
                dev_broadcast_hdr.dbch_devicetype == DBT_DEVTYPE_PORT:
            dev_broadcast_port = DEV_BROADCAST_PORT.from_address(lparam)
            port_name = dev_broadcast_port.dbcp_name
            if wparam == DBT_DEVICEARRIVAL:
                # print(__name__, ": Port {} connected".format(port_name))
                self.state_changed.emit(port_name, True)
            if wparam == DBT_DEVICEREMOVECOMPLETE:
                # print(__name__, ": Port {} disconnected".format(dev_broadcast_port.dbcp_name))
                self.state_changed.emit(port_name, False)
        return 1


# Linux
class PortStateNotificatorLinux(QObject):
    """
    Signal emit when ports state changed
    :param str - port name
    :param bool - connect state
    """
    state_changed = Signal(str, bool)

    def __init__(self):
        super().__init__()

        self.context = pyudev.Context()
        self.monitor = pyudev.Monitor.from_netlink(context)
        self.monitor.filter_by(subsystem='usb')

        self.listen_state()

    def listen_state(self):
        for device in iter(self.monitor.poll, None):
            if device.action == 'add':
                print('{} connected'.format(device))
                # do something very interesting here.
                self.state_changed.emit(device, True)
            elif device.action == 'del':
                self.state_changed.emit(device, False)
                print('{} disconnected'.format(device))