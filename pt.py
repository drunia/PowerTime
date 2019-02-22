#!/usr/bin/env python3
#--* encoding: utf-8 *--

import os, sys, time
from drivers.icse0xxa import *
from  plugins.icse0xxa_plugin import ICSE0XXA_Plugin
from PyQt5.QtWidgets import QMainWindow, QWidget, QApplication

print("Working directory:", os.getcwd())

plugin = ICSE0XXA_Plugin()
print(plugin.get_info())
#print(plugin.activate())

qapp = QApplication(sys.argv)
mw = QMainWindow()
mw.setGeometry(0,0,500,500)
mw.setWindowTitle("Main Window")
mw.show()

sys.exit(qapp.exec())








