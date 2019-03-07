#!/usb/bin/env python3
#-*- coding: utf-8 -*-


from PyQt5.QtCore import Qt, QTimer, QTimerEvent
from PyQt5.QtGui import QFont, QPaintEvent, QPainter, QPixmap, QPalette, QColor
from PyQt5.QtWidgets import *
from decimal import Decimal
from configparser import  ConfigParser
import datetime, math, enum, pt


class ControlMode(enum.Enum):
    TIME = 0
    CASH = 1
    FREE = 2


class TimerCashControl(QFrame):
    """ Control for channel"""

    CONFIG_FILENAME = "tariffs.conf"
    
    def __init__(self, parent):
        super().__init__(parent)

        self.mode = ControlMode.FREE
        self.time = 22*3600
        self.cash = 0
        self.price = 80
        self.displayed = True
        self.paused = False
        self.timer_id = 0

        # Tariffs
        self.config: ConfigParser = self.parent().config
        if self.config.has_section(pt.TARIFFS_CONF_SECTION):
            self.tariffs = self.config[pt.TARIFFS_CONF_SECTION]
        else:
            self.tariffs = {}

        print(self.config.options(pt.TARIFFS_CONF_SECTION))

        # Timer
        self.timer = QTimer()
        self.timer.timerEvent = self._timerEvent
        self.timer_id = self.timer.startTimer(1000, Qt.PreciseTimer)

        # Icons
        self.cash_pixmap = QPixmap("./res/cash.png")
        self.time_pixmap = QPixmap("./res/clock.png")

        # UI
        self._init_ui()

    # Timer
    def _timerEvent(self, evt: QTimerEvent):
        if self.paused:
            self.displayed = not self.displayed
        else:
            if self.mode == ControlMode.FREE:
                self.time += 1
            else:
                self.time -= 1

        self.cash = Decimal(self.time) * Decimal(self.price/3600)

        # Time
        if self.displayed:
            str_time = str(datetime.timedelta(seconds=self.time))
        else:
            str_time = ""
        # Cash
        str_cash = "{:.2f}".format(self.cash)
        # Display values
        self.time_display.display(str_time)
        self.cash_display.display(str_cash)

    def _init_ui(self):
        # Set minimum size
        self.setMinimumSize(330, 300)
        self.setFrameStyle(QFrame.Box)
        self.resize(self.minimumSize())

        # Title (Number of channel)
        self.tittle_lb = QLabel()
        self.tittle_lb.setText("Канал 1")
        f: QFont = self.tittle_lb.font()
        f.setPointSize(20)
        self.tittle_lb.setFont(f)
        self.tittle_lb.setAlignment(Qt.AlignLeft)

        # Time
        self.time_display = QLCDNumber()
        self.time_display.setDigitCount(9)
        self.time_display.display("00:00:00")
        self.time_display.setSegmentStyle(QLCDNumber.Flat)
        self.time_display.paintEvent = self._time_paintEvent
        self.time_display.mouseMoveEvent = None

        # $Cash
        self.cash_display = QLCDNumber()
        self.cash_display.setDigitCount(8)
        self.cash_display.display("0.00")
        self.cash_display.setSegmentStyle(QLCDNumber.Flat)
        self.cash_display.paintEvent = self._cash_paintEvent

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

    # Paint cash icon in QLCDNumber
    def _cash_paintEvent(self, evt: QPaintEvent):
        p: QPainter = QPainter(self.cash_display)
        w, h = 32, 32
        p.drawPixmap(5, 5, w, h, self.cash_pixmap)
        QLCDNumber.paintEvent(self.cash_display, evt)

    # Paint clock icon in QLCDNumber
    def _time_paintEvent(self, evt: QPaintEvent):
        p: QPainter = QPainter(self.time_display)
        w, h = 32, 32
        p.drawPixmap(5, 5, w, h, self.time_pixmap)
        QLCDNumber.paintEvent(self.time_display, evt)



if __name__ == "__main__":
    import os, pt
    os.chdir("..")
    app = QApplication([])
    mw = QWidget()
    mw.config = pt.read_config()
    w = TimerCashControl(mw)
    mw.show()
    app.exec()
        






