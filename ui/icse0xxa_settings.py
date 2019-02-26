#!/usb/bin/env python3
#-*- coding: utf-8 -*-

from plugins.icse0xxa_plugin import *
from PyQt5.Qt import *
from PyQt5.QtCore import *

class Settings(QFrame):
    def __init__(self, plugin: ICSE0XXA_Plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.setup_ui()

    def setup_ui(self):
        self.setFrameStyle(QFrame.Panel)
        self.setMinimumSize(320, 480)
        # Set size = container size
        self.resize(self.parent().size())

        # layouts
        self.hbox = QHBoxLayout()
        self.vboxl, self.vboxr = QVBoxLayout(), QVBoxLayout()
        self.hbox.addLayout(self.vboxl)
        self.hbox.addLayout(self.vboxr, 1)
        self.setLayout(self.hbox)

        # QListView to view connected/saved devices
        self.qlist = QListView()
        self.qlist_model = QStandardItemModel(self.qlist)
        for d in load_devices_from_config():
            item = QStandardItem(d.name())
            item.setCheckable(True)
            item.setEditable(False)
            item.setIcon(QIcon("./res/icse0xxa_device.ico"))
            self.qlist_model.appendRow(item)
        self.qlist.setModel(self.qlist_model)
        f = self.qlist.font(); f.setPointSize(14)
        self.qlist.setFont(f)
        self.vboxl.addWidget(self.qlist)

        # Search button
        self.find_button = QPushButton(QIcon("./res/search.ico"), "Поиск устройств")
        self.find_button.setIconSize(QSize(24,24))
        self.find_button.clicked.connect(self.find_devices)
        # Save Button
        self.save_button = QPushButton(QIcon("./res/lock.ico"), "Применить")
        self.save_button.setIconSize(QSize(24, 24))
        self.save_button.clicked.connect(self.save_settings)
        # Buttons H layout
        butt_lay = QHBoxLayout()
        butt_lay.addWidget(self.find_button)
        butt_lay.addWidget(self.save_button)
        self.vboxl.addLayout(butt_lay)

        self.show()

    # Search devices on serial bus
    def find_devices(self):
        devs = find_devices()
        if len(devs) == 0:
            QMessageBox.warning(
                self,"Поиск устройств", (
                    "Устройства не найдены!\n\n" 
                    "Попробуйте выключить - включить устройство(а) и выполнить поиск снова."
                ), QMessageBox.Ok)
            return
        # find ...
        self.qlist_model.clear()
        for d in devs:
            item = QStandardItem(d.name())
            item.setCheckable(True)
            item.setIcon(QIcon("./res/icse0xxa_device.ico"))
            self.qlist_model.appendRow(item)

    def save_settings(self):
        m = self.qlist_model
        print(m.rowCount())
        print()





if __name__ == "__main__":
    app = QApplication([])
    s = Settings(ICSE0XXA_Plugin())
    s.show()
    app.exec()
    print("Settings DEBUG")
    pass