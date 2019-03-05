#!/usb/bin/env python3
#-*- coding: utf-8 -*-


from PyQt5.QtCore import Qt, QTimer, QTimerEvent
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import *
import time


class TimerControl(QFrame):
    """ Control for channel"""
    
    def __init__(self):
        super().__init__()
        self.time = 0
        self.cash = 0

        self.timer = QTimer()
        self.timer.timerEvent = self._timerEvent
        self.timer.startTimer(1000)

        self._init_ui()

    # Timer timeout
    def _timerEvent(self, evt):
        self.time += 1
        self.time_display.display(0)
        #print(time.strftime("%H:%M:%S", self.time))
        print(time.strftime("%H:%M:%S", self.time))


    def _init_ui(self):
        # Set minimum size
        self.setMinimumSize(300, 300)
        self.setFrameStyle(QFrame.Box)
        self.resize(400, 300)

        # Title (Number of channel)
        self.tittle_lb = QLabel()
        self.tittle_lb.setText("Канал 1")
        f: QFont = self.tittle_lb.font()
        f.setPointSize(20)
        self.tittle_lb.setFont(f)
        self.tittle_lb.setAlignment(Qt.AlignVCenter | Qt.AlignHCenter)

        # Time
        self.time_display = QLCDNumber()
        self.time_display.setDigitCount(8)
        self.time_display.display("12:34:56")

        # $Cash
        self.cash_display = QLCDNumber()
        self.cash_display.setDigitCount(6)
        self.cash_display.display("123.00")

        # Controls
        self.start_btn = QPushButton("Старт")
        self.start_btn.setMinimumSize(100, 20)

        self.stop_btn = QPushButton("Стоп")
        self.start_btn.setMinimumSize(100, 20)

        # Root layout
        root_lay = QVBoxLayout(self)
        root_lay.addWidget(self.tittle_lb, stretch=0)
        root_lay.addWidget(self.time_display, stretch=1)
        root_lay.addWidget(self.cash_display, stretch=1)

        # Controls layout
        controls_lay = QHBoxLayout(self)
        controls_lay.addWidget(self.start_btn)
        controls_lay.addWidget(self.stop_btn)
        controls_lay.setContentsMargins(0, 10, 0, 5)

        root_lay.addLayout(controls_lay)





if __name__ == "__main__":


    app = QApplication([])
    w = TimerControl()
    w.show()
    app.exec()
        






