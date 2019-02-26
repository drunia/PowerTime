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
        self.qlist.setModel(self.qlist_model)
        f = self.qlist.font(); f.setPointSize(12)
        self.qlist.setFont(f)
        self.qlist.clicked.connect(self.qlist_item_clicked)
        self.vboxl.addWidget(self.qlist)

        # Search button
        self.find_button = QPushButton(QIcon("./res/search.ico"), "Поиск устройств")
        self.find_button.setIconSize(QSize(24,24))
        self.find_button.clicked.connect(self.find_devices)

        # Save Button
        self.save_button = QPushButton(QIcon("./res/lock.ico"), "Записать")
        self.save_button.setIconSize(QSize(24, 24))
        self.save_button.clicked.connect(self.save_settings)

        # Buttons H layout
        butt_lay = QHBoxLayout()
        butt_lay.addWidget(self.find_button)
        butt_lay.addWidget(self.save_button)
        self.vboxl.addLayout(butt_lay)

        # Info label
        self.info_lb = QLabel()
        self.info_lb.setWordWrap(True)
        self.info_lb.setFont(f)
        self.vboxr.addWidget(self.info_lb)

        # Image label
        self.img_lb = QLabel()
        self.img_lb.setFixedWidth(self.width() // 2)
        self.img_lb.setFixedHeight(self.height() // 3)
        self.vboxr.addWidget(self.img_lb)

        # Status label
        self.st_lb = QLabel()
        self.st_lb.setFont(f)
        self.st_lb.setFixedHeight(30)
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

    # Search devices on serial bus
    def find_devices(self):
        self.st_lb.setText("Выполняется поиск...")
        QApplication.processEvents()
        devs = find_devices()
        if len(devs) == 0:
            self.st_lb.setText("")
            r = QMessageBox.warning(
                    self,"Поиск устройств", (
                    "Устройства не найдены!\n\n" 
                    "Попробуйте выключить/включить устройство(ва) и выполнить поиск снова.\n"
                    "Удалить сохраненные устройства?"
                ), QMessageBox.Yes | QMessageBox.No)
            if r == QMessageBox.Yes: self.qlist_model.clear()
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
            if item.checkState(): devs.append(item.data())
        if len(devs) > 0:
            save_divices_to_config(devs)
            QMessageBox.information(self, "Запись в файл",
                                    "Записано {} устройств".format(len(devs)), QMessageBox.Ok)
        elif m.rowCount() > 0:
            QMessageBox.warning(self, "Запись в файл",
                                "Отметьте устройство для сохранения", QMessageBox.Ok)

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
            self.img_lb.setPixmap(QPixmap.fromImage(QImage("./res/" + img_name)))
        except Exception as e:
            print(e)


if __name__ == "__main__":
    app = QApplication([])
    s = Settings(ICSE0XXA_Plugin(), )
    s.show()
    app.exec()
    print("Settings DEBUG")
    pass