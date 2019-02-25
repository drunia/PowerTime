#!/usb/bin/env python3
#-*- coding: utf-8 -*-

from plugins.icse0xxa_plugin import *

class Settings(QFrame):
    def __init__(self, plugin: ICSE0XXA_Plugin, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.setup_ui()

    def setup_ui(self):
        self.setFrameStyle(QFrame.Panel)
        self.setMinimumSize(320, 480)
        self.resize(self.parent().size())

        b = QPushButton("Test button", self)
        b.move(150, 150)
        b.clicked.connect(lambda : QMessageBox.question(self, "Settings", "Settings text", QMessageBox.Ok ))

        lbl = QLabel(str(self.plugin.get_info()))
        lbl.setParent(self)
        self.show()






if __name__ == "__main__":
    app = QApplication([])
    s = Settings(ICSE0XXA_Plugin())
    s.show()
    app.exec()
    print("Settings DEBUG")
    pass