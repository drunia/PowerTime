#!/usr/bin/env python3
#--* encoding: utf-8 *--

import os, sys, time
from devices.icse0xxa import *
from  plugins.icse0xxa_plugin import ICSE0XXA_Plugin
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QObject


def button_clk():
    sender = mw.sender()
    try:
        plugin.switch(1, sender.text().startswith("Вкл"))
    except Exception as e:
        print("Exception", e)

print("Working directory:", os.getcwd())

plugin = ICSE0XXA_Plugin()
print(plugin.get_info())
#print(plugin.activate())

qapp = QApplication(sys.argv)
mw = QMainWindow()
mw.setGeometry(0,0,500,500)
mw.setWindowTitle("Main Window")
mw.setMinimumSize(200,200)
mw.show()

pb = QPushButton("Включить", mw)
pb.setGeometry(100,100, 150, 30)
pb.clicked.connect(button_clk)
pb.show()

pb2 = QPushButton("Выключить", mw)
pb2.clicked.connect(button_clk)
pb2.setGeometry(100,130, 150, 30)
pb2.show()

try:
    plugin.activate()
except Exception:
    pass
plugin.build_settings(mw)

desktop: QDesktopWidget = qApp.desktop()

qapp.setStyle("fusion")

sys.exit(qapp.exec())






