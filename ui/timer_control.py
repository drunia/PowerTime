#!/usb/bin/env python3
#-*- coding: utf-8 -*-


from PyQt5.QtCore import Qt, QTimer, QTimerEvent, QRectF
from PyQt5.QtGui import QFont, QPaintEvent, QPainter, QPixmap, QFocusEvent, QKeyEvent, QPalette, QColor, QPen
from PyQt5.QtWidgets import *
from decimal import Decimal
from configparser import  ConfigParser
import datetime, math, enum, pt


class ControlMode(enum.Enum):
    """Enumeration for control modes"""
    # Control modes:
    # FREE - work infinity
    # CASH - calculate time by taked cash
    # TIME - calculating time
    TIME = 0
    CASH = 1
    FREE = 2

class EditTimeMode(enum.Enum):
    """Enumeration for edit mode in time display"""
    NO_EDIT = 0
    HOURS = 1
    MINUTES = 2


class TimerCashControl(QFrame):
    """ Control for channel"""

    def __init__(self, parent):
        super().__init__(parent)

        # current control mode
        self.mode = ControlMode.FREE
        self.time = 22*3600
        self.cash = 123.50
        self.price = 80
        # can displayed time
        self.displayed = True
        # timer paused
        self.paused = False
        # timer stopped
        self.stopped = True
        self.timer_id = 0
        self.edit_time_mode = EditTimeMode.NO_EDIT

        # Tariffs
        self.config: ConfigParser = self.parent().config
        if self.config.has_section(pt.TARIFFS_CONF_SECTION):
            self.tariffs = self.config[pt.TARIFFS_CONF_SECTION]
        else:
            self.tariffs = {}

        #print(self.config.options(pt.TARIFFS_CONF_SECTION))

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
        if self.stopped:
            self.displayed = True
            return
        if self.paused:
            self.displayed = not self.displayed
        else:
            self.displayed = True
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

    # Start / Pause timer
    def start(self):
        self.time_display.setFocusPolicy(Qt.NoFocus)
        self.cash_display.setFocusPolicy(Qt.NoFocus)

        if self.stopped:
            self.stopped = False
            self.start_btn.setText("Пауза")
            return

        if self.paused:
            self.start_btn.setText("Пауза")
            self.paused = False
        else:
            self.start_btn.setText("Возобновить")
            self.paused = True

    # Stop timer
    def stop(self):
        self.time_display.setFocusPolicy(Qt.ClickFocus)
        self.cash_display.setFocusPolicy(Qt.ClickFocus)

        self.start_btn.setText("Старт")

        self.paused = False
        self.stopped = True

    def _init_ui(self):
        # Set minimum size
        self.setMinimumSize(330, 300)
        self.setFrameStyle(QFrame.Box)
        self.resize(400,400)

        # Title (Number of channel)
        self.tittle_lb = QLabel()
        self.tittle_lb.setText("Канал 1")
        f: QFont = self.tittle_lb.font()
        f.setPointSize(20)
        self.tittle_lb.setFont(f)
        self.tittle_lb.setAlignment(Qt.AlignLeft)

        # Time
        self.time_display = QLCDNumber()
        self.time_display.setDigitCount(10)
        self.time_display.setSegmentStyle(QLCDNumber.Flat)
        self.time_display.paintEvent = self._time_paintEvent
        self.time_display.setAutoFillBackground(True)
        self.time_display.setFocusPolicy(Qt.ClickFocus)

        # set background color
        p: QPalette = self.time_display.palette()
        p.setColor(QPalette.Background, QColor(204, 204, 204))
        self.time_display.setPalette(p)

        self.time_display.focusInEvent = self._time_focus_in
        self.time_display.focusOutEvent = self._time_focus_out
        self.time_display.keyPressEvent = self._time_key_pressed

        # $Cash
        self.cash_display = QLCDNumber()
        self.cash_display.setDigitCount(8)
        self.cash_display.display(self.cash)
        self.cash_display.setSegmentStyle(QLCDNumber.Flat)
        self.cash_display.paintEvent = self._cash_paintEvent
        self.cash_display.setAutoFillBackground(True)
        self.cash_display.setFocusPolicy(Qt.ClickFocus)

        # set background color
        self.cash_display.setPalette(p)

        self.cash_display.focusInEvent = self._cash_focus_in
        self.cash_display.focusOutEvent = self._cash_focus_out
        self.cash_display.keyPressEvent = self._cash_key_pressed

        # Get default display background color
        p: QPalette = self.cash_display.palette()
        self.default_background_display_color = p.color(QPalette.Background)

        # Controls
        self.start_btn = QPushButton("Старт")
        self.start_btn.setMinimumSize(100, 20)
        self.start_btn.clicked.connect(self.start)

        self.stop_btn = QPushButton("Стоп")
        self.stop_btn.setMinimumSize(100, 20)
        self.stop_btn.clicked.connect(self.stop)

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

        # Edit time
        if self.edit_time_mode != EditTimeMode.NO_EDIT:
            pos_num = 0
            if self.edit_time_mode == EditTimeMode.HOURS: pos_num = 2
            if self.edit_time_mode == EditTimeMode.MINUTES: pos_num = 5
            pen: QPen = p.pen()
            pen.setWidth(2)
            pen.setCapStyle(Qt.FlatCap)
            pen.setJoinStyle(Qt.RoundJoin)
            p.setPen(pen)
            dig_width = self.time_display.width() / self.time_display.digitCount()
            dig_height = self.time_display.height() / 2
            margin = dig_width / 4
            x1 = (dig_width * pos_num) - margin
            y1 = (dig_height / 2) - margin
            x2 = (dig_width * 2) + margin * 2
            y2 = dig_height + margin * 2
            p.drawRoundedRect(x1, y1, x2, y2, 5.0, 5.0)

        QLCDNumber.paintEvent(self.time_display, evt)

    # Cash display get focus
    def _cash_focus_in(self, evt):
        print("cash_focus_in")
        pallete: QPalette = self.cash_display.palette()
        pallete.setColor(QPalette.Background, QColor(255, 255, 255))
        self.cash_display.setPalette(pallete)

        print(self.cash)
        self.cash = str(int(float(self.cash))) if float(self.cash).is_integer() else str(round(self.cash, 2))
        self.cash_display.display(self.cash)

    # Cash display lost focus
    def _cash_focus_out(self, evt):
        print("cash_focus_out")
        pallete: QPalette = self.cash_display.palette()
        pallete.setColor(QPalette.Background, self.default_background_display_color)
        self.cash_display.setPalette(pallete)

        self.cash = round(float(self.cash), 2)
        self.cash_display.display(self.cash)

    # Cash display key pressed
    def _cash_key_pressed(self, evt):
        # in edit mode , we work ONLY with str type self.cash
        if evt.key() == Qt.Key_Enter or evt.key() == Qt.Key_Return:
            self.cash_display.clearFocus()
        if (Qt.Key_0 <= evt.key() <= Qt.Key_9) or \
                (evt.key() == Qt.Key_Period or evt.key() == Qt.Key_Backspace):
            cash = str(self.cash)
            if evt.key() == Qt.Key_Backspace and len(cash) > 0:
                cash = cash[:-1]
            elif len(cash) == 1 and cash[0] == "0" and \
                    evt.key() != Qt.Key_Period and Qt.Key_1 <= evt.key() <= Qt.Key_9:
                cash = evt.text()
            elif evt.key() == Qt.Key_0 and len(cash) == 1 and cash[0] == "0":
                pass
            elif evt.key() == Qt.Key_Period and "." in cash:
                pass
            elif "." in cash and len(cash) - cash.index(".") == 3:
                pass
            elif len(cash) > self.cash_display.digitCount()-2 or \
                    "." not in cash and len(cash) >= self.cash_display.digitCount()-4 and \
                    evt.key() != Qt.Key_Period:
                pass
            else:
                cash += evt.text()
            self.cash = cash if len(cash) > 0 else "0"
            self.cash_display.display(self.cash)

    # Time display get focus
    def _time_focus_in(self, evt):
        print("time_focus_in")
        pallete: QPalette = self.time_display.palette()
        pallete.setColor(QPalette.Background, QColor(255, 255, 255))
        self.time_display.setPalette(pallete)
        self.edit_time_mode = EditTimeMode.HOURS

    # Time display lost focus
    def _time_focus_out(self, evt):
        print("time_focus_out")
        palette: QPalette = self.time_display.palette()
        palette.setColor(QPalette.Background, self.default_background_display_color)
        self.time_display.setPalette(palette)
        self.edit_time_mode = EditTimeMode.NO_EDIT

    # Time display key pressed
    def _time_key_pressed(self, evt):
        print("time_key_pressed")
        if evt.key() == Qt.Key_Enter or evt.key() == Qt.Key_Return:
            self.time_display.clearFocus()
        legal_keys = (Qt.Key_Left, Qt.Key_Right, Qt.Key_Plus, Qt.Key_Minus, Qt.Key_Enter, Qt.Key_Return)
        if not (Qt.Key_0 <= evt.key() <= Qt.Key_9) and evt.key() not in legal_keys: return
        if evt.key() == Qt.Key_Left or evt.key() == Qt.Key_Right:
            if self.edit_time_mode == EditTimeMode.HOURS:
                self.edit_time_mode = EditTimeMode.MINUTES
                self.time_display.repaint()
                return
            elif self.edit_time_mode == EditTimeMode.MINUTES:
                self.edit_time_mode = EditTimeMode.HOURS
                self.time_display.repaint()
                return







if __name__ == "__main__":
    import os, pt
    os.chdir("..")
    app = QApplication([])
    mw = QWidget()
    mw.config = pt.read_config()
    w = TimerCashControl(mw)
    mw.show()
    app.exec()
        






