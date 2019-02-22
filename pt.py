#!/usr/bin/env python3
#--* encoding: utf-8 *--

import os, sys, time
from devices.icse0xxa import *
from  plugins.icse0xxa_plugin import ICSE0XXA_Plugin
from PyQt5.QtWidgets import *

print("Working directory:", os.getcwd())

plugin = ICSE0XXA_Plugin()
print(plugin.get_info())
#print(plugin.activate())

qapp = QApplication(sys.argv)
mw = QMainWindow()
mw.setGeometry(0,0,500,500)
mw.setWindowTitle("Main Window")
mw.show()

pb = QPushButton("Я кнопка главного окна", mw)
pb.setGeometry(100,100, 150, 30)
pb.clicked.connect(lambda : print("Я кнопка главного окна"))
pb.show()


plugin.build_settings(mw)

sys.exit(qapp.exec())






