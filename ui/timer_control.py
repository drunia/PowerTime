#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from builtins import print

from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QFont, QPaintEvent, QPainter, QPixmap, QPalette, QColor, QPen
from PyQt5.QtWidgets import *
from configparser import ConfigParser
import datetime, enum, pt


class ControlMode(enum.Enum):
    """Enumeration for control modes"""
    # Control modes:
    # FREE - work max to 24 hours
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

    """ 
    Switch signal
    :param object - instance of TimerCashControl
    :param bool - switch state
    """
    switched = pyqtSignal(object, bool)

    """
    Change signal - Changed when time or cash added (from AddDialog())
    :param int - old time value
    :param int - new time value
    """
    changed = pyqtSignal(int, int)

    def __init__(self, parent: QWidget, num_channel: int):
        """
        Create control UI by channel
        :param parent: Parent component
        :param num_channel: Number of switchable channel (from active plugin)
        """
        super().__init__(parent)

        # current control mode
        self.mode = ControlMode.FREE
        # all time on current session for audit
        self.session_time = 0
        self.time = 0
        self.cash = 0
        self.price = 80
        self.channel = num_channel
        # can displayed time (for blinking time in pause)
        self.displayed = True
        # timer paused
        self.paused = False
        # timer stopped
        self.stopped = True
        self.timer_id = 0
        self.edit_time_mode = EditTimeMode.NO_EDIT
        # Edit peace of time
        self.tmp_edit_time = {
            "time_str": "00:00:00",
            "h_peace": "00",
            "m_peace": "00"
        }
        # Add cash/time dialog object
        self.add_dialog = None

        # Current plugin
        self.plugin = None

        # last second for indicating (blinking) control mode
        self.time_repaint_mode = datetime.datetime.now().second

        # Tariffs
        self.config: ConfigParser = self.parent().config
        if self.config.has_section(pt.TARIFFS_CONF_SECTION):
            self.tariffs = self.config[pt.TARIFFS_CONF_SECTION]
        else:
            self.tariffs = {}

        # Timer
        self.timer = QTimer()
        self.timer.timerEvent = self._timer_event
        self.timer_id = self.timer.startTimer(100, Qt.PreciseTimer)

        # Icons
        self.cash_pixmap = QPixmap("./res/cash.png")
        self.time_pixmap = QPixmap("./res/clock.png")

        # UI
        self._init_ui()
        self.set_control_tittle()
        self.display()

        # Test timeout signal
        self.switched.connect(
            lambda *x:
            print("Switch signal:", x)
        )

        # Test change signal
        self.changed.connect(
            lambda *x:
            print("Change signal:", x)
        )

    def _init_ui(self):
        # Set minimum size
        self.setMinimumSize(310, 260)
        self.setMaximumSize(480, 400)
        self.setFrameStyle(QFrame.Panel)

        # Title (Number of channel)
        self.tittle_lb = QLabel()
        f: QFont = self.tittle_lb.font()
        f.setPointSize(20)
        self.tittle_lb.setFont(f)
        self.tittle_lb.setAlignment(Qt.AlignLeft)

        # Time
        self.time_display = QLCDNumber()
        self.time_display.setDigitCount(10)
        self.time_display.setSegmentStyle(QLCDNumber.Flat)
        self.time_display.paintEvent = self._time_paint_event
        self.time_display.setAutoFillBackground(True)
        self.time_display.setFocusPolicy(Qt.ClickFocus)
        self.time_display.setCursor(Qt.IBeamCursor)

        # set background color
        p: QPalette = self.time_display.palette()
        p.setColor(QPalette.Background, QColor(204, 204, 204))
        self.time_display.setPalette(p)

        self.time_display.focusInEvent = self._time_focus_in
        self.time_display.focusOutEvent = self._time_focus_out
        self.time_display.keyPressEvent = self._time_key_pressed

        self.time_display.setMouseTracking(True)
        self.time_display.mouseMoveEvent = self._time_mouse_move
        self.time_display.mousePressEvent = self._time_mouse_pressed

        # $Cash
        self.cash_display = QLCDNumber()
        self.cash_display.setDigitCount(8)
        self.cash_display.display(self.cash)
        self.cash_display.setSegmentStyle(QLCDNumber.Flat)
        self.cash_display.paintEvent = self._cash_paint_event
        self.cash_display.setAutoFillBackground(True)
        self.cash_display.setFocusPolicy(Qt.ClickFocus)
        self.cash_display.setCursor(Qt.IBeamCursor)

        # set background color
        self.cash_display.setPalette(p)

        self.cash_display.focusInEvent = self._cash_focus_in
        self.cash_display.focusOutEvent = self._cash_focus_out
        self.cash_display.keyPressEvent = self._cash_key_pressed

        self.cash_display.setMouseTracking(True)
        self.cash_display.mouseMoveEvent = self._cash_mouse_move
        self.cash_display.mousePressEvent = self._cash_mouse_pressed

        # Get default display background color
        p: QPalette = self.cash_display.palette()
        self.default_background_display_color = p.color(QPalette.Background)

        # Tariffs combobox
        self.tariff_cb = QComboBox()
        f = self.tariff_cb.font()
        f.setPointSize(12)
        self.tariff_cb.setFont(f)
        for o, v in self.tariffs.items():
            try:
                self.tariff_cb.addItem(o, float(v))
                self.tariff_cb.setItemData(self.tariff_cb.count() - 1,
                                           " Стоимость за час: " + v + " грн.", Qt.ToolTipRole)
            except ValueError:
                pass
        # Select last select tariff
        if self.tariff_cb.count() > 0:
            index = 0
            if self.config.has_option(pt.TIMER_CONTROLS_SECTION, "tariff-channel-" + str(self.channel)):
                tariff = self.config[pt.TIMER_CONTROLS_SECTION]["tariff-channel-" + str(self.channel)]
                if self.tariff_cb.findText(tariff) >= 0:
                    index = self.tariff_cb.findText(tariff)
            self.tariff_cb.setCurrentIndex(index)
            self.change_tariff_cb(index)
        # Set slot for change events
        self.tariff_cb.currentIndexChanged.connect(self.change_tariff_cb)

        # Controls
        self.start_btn = QPushButton("Старт")
        self.start_btn.setMinimumSize(100, 20)
        self.start_btn.clicked.connect(self.start)
        self.start_btn.setAutoDefault(True)
        self.start_btn.setFont(f)

        self.stop_btn = QPushButton("Стоп")
        self.stop_btn.setMinimumSize(100, 20)
        self.stop_btn.clicked.connect(self.stop)
        self.stop_btn.setFont(f)

        # Root layout
        root_lay = QVBoxLayout(self)
        head_hbox_lay = QHBoxLayout()
        head_hbox_lay.addWidget(self.tittle_lb)
        head_hbox_lay.addWidget(self.tariff_cb)
        root_lay.addLayout(head_hbox_lay)
        root_lay.addWidget(self.time_display, stretch=1)
        root_lay.addWidget(self.cash_display, stretch=1)

        # Controls layout
        controls_lay = QHBoxLayout(self)
        controls_lay.addWidget(self.start_btn)
        controls_lay.addWidget(self.stop_btn)
        controls_lay.setContentsMargins(0, 10, 0, 5)

        root_lay.addLayout(controls_lay)

    # Set price by tariff
    def change_tariff_cb(self, index):
        print("Channel:", self.channel, "tariff changed to:", self.tariff_cb.currentText())
        self.price = self.tariff_cb.currentData()
        # Check admin tariff
        if self.price == 0:
            self.time_display.setFocusPolicy(Qt.NoFocus)
            self.cash_display.setFocusPolicy(Qt.NoFocus)
            self.cash = 0
            self.time = 0
        else:
            self.time_display.setFocusPolicy(Qt.ClickFocus)
            self.cash_display.setFocusPolicy(Qt.ClickFocus)
        # Save tariff to config
        if not self.config.has_section(pt.TIMER_CONTROLS_SECTION):
            self.config.add_section(pt.TIMER_CONTROLS_SECTION)
        self.config[pt.TIMER_CONTROLS_SECTION]["tariff-channel-" + str(self.channel)] = \
            self.tariff_cb.currentText()

        self.display()

    # Timer
    def _timer_event(self, evt):
        if self.stopped:
            self.displayed = True
            return
        if self.paused:
            self.displayed = not self.displayed
        else:
            # Audit session
            if self.time > self.session_time:
                # Send change session signal
                if self.session_time > 0 and self.mode != ControlMode.FREE:
                    self.changed.emit(self.session_time, self.time)
                self.session_time = self.time

            self.displayed = True
            if self.mode == ControlMode.FREE:
                self.time += 1
                if self.time == (24 * 3600):
                    self.stop()
            elif self.time == 0:
                # Time  is UP!
                self.time_out()
            else:
                self.time -= 1
        self.display()

    def time_out(self):
        # Close add cash/time dialog if opened
        if self.add_dialog:
            self.add_dialog.close()
        self.stop()
        QMessageBox.information(
            self.parent(), self.tittle_lb.text(),
            "Время вышло!",
            QMessageBox.Ok
        )

    # Set control tittle
    def set_control_tittle(self, tittle="Канал "):
        self.tittle_lb.setText(tittle + str(self.channel + 1))

    # Display time & cash
    def display(self):
        self.cash = round(self.time * (self.price / 3600), 2)
        # Time
        if self.displayed:
            str_time = "{:0>8}".format(str(datetime.timedelta(seconds=self.time)))
        else:
            str_time = ""
        # Cash
        str_cash = "{:.2f}".format(self.cash)
        # Display values
        self.time_display.display(str_time)
        self.time_display.update()
        self.cash_display.display(str_cash)
        self.cash_display.update()

        # print("self.session_time:", self.session_time, "self.mode =", self.mode)

    # Start / Pause timer
    def start(self):
        self.time_display.setFocusPolicy(Qt.NoFocus)
        self.cash_display.setFocusPolicy(Qt.NoFocus)

        if self.stopped:
            self.stopped = False
            self.start_btn.setText("Пауза")
            self.switched.emit(self, True)
            self.session_time = 0
            if self.cash == 0 and self.time == 0:
                self.mode = ControlMode.FREE
            self.tariff_cb.setDisabled(True)
            return

        if self.paused:
            self.start_btn.setText("Пауза")
            self.paused = False
            self.switched.emit(self, True)
        else:
            self.start_btn.setText("Возобновить")
            self.paused = True
            self.switched.emit(self, False)

        self.display()

    # Stop timer
    def stop(self):
        if self.stopped:
            return
        if (self.cash or self.time) and \
                QMessageBox.No == QMessageBox.question(
            self.parent(), self.tittle_lb.text(), "Завершить текущий сеанс?",
            QMessageBox.Yes | QMessageBox.No):
            return

        # Check admin tariff
        if self.price > 0:
            self.time_display.setFocusPolicy(Qt.ClickFocus)
            self.cash_display.setFocusPolicy(Qt.ClickFocus)

        self.start_btn.setText("Старт")

        # Set default mode to FREE
        self.mode = ControlMode.FREE

        self.displayed = True
        self.paused = False
        self.stopped = True
        self.tariff_cb.setDisabled(False)

        # Before clear self.cash & self.time we send signal
        # for calculating difference for cash back in main app
        self.switched.emit(self, False)

        self.cash = 0
        self.time = 0
        self.display()

    # Paint cash icon in QLCDNumber
    def _cash_paint_event(self, evt: QPaintEvent):
        p: QPainter = QPainter(self.cash_display)
        w, h = 0, self.cash_display.height() - (p.fontMetrics().height() / 2)
        p.drawText((p.fontMetrics().height() / 2), h, "Деньги")

        # Blinking icon to indicate control mode when cash < by 5 min for price
        if not self.stopped and not self.paused and \
                self.cash < (self.price / 3600 * (5 * 60)) and \
                self.mode != ControlMode.FREE and \
                datetime.datetime.now().second % 2:
            QLCDNumber.paintEvent(self.cash_display, evt)
            return

        if self.mode != ControlMode.TIME:
            w, h = 32, 32
            p.drawPixmap(5, 5, w, h, self.cash_pixmap)

        QLCDNumber.paintEvent(self.cash_display, evt)

    # Paint clock icon in QLCDNumber
    def _time_paint_event(self, evt: QPaintEvent):
        p: QPainter = QPainter(self.time_display)
        p.setRenderHints(p.renderHints() | QPainter.Antialiasing)
        w, h = 0, self.time_display.height() - (p.fontMetrics().height() / 2)
        p.drawText((p.fontMetrics().height() / 2), h, "Время")

        # Blinking icon to indicate control mode when 5 minutes left
        if not self.stopped and not self.paused and \
                self.time < (5 * 60) and \
                self.mode != ControlMode.FREE and \
                datetime.datetime.now().second % 2:
            QLCDNumber.paintEvent(self.time_display, evt)
            return

        if self.mode != ControlMode.CASH:
            w, h = 32, 32
            p.drawPixmap(5, 5, w, h, self.time_pixmap)

        # Edit time
        if self.edit_time_mode != EditTimeMode.NO_EDIT:
            pos_num = 0
            if self.edit_time_mode == EditTimeMode.HOURS:
                pos_num = 2
            if self.edit_time_mode == EditTimeMode.MINUTES:
                pos_num = 5
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
        palette: QPalette = self.cash_display.palette()
        palette.setColor(QPalette.Background, QColor(255, 255, 255))
        self.cash_display.setPalette(palette)
        try:
            if float(self.cash).is_integer():
                self.cash = str(int(float(self.cash)))
            else:
                self.cash = str(round(self.cash, 2))
        except Exception as e:
            print(e)
        # Set control mode by cash
        self.mode = ControlMode.CASH
        self.cash_display.display(self.cash)
        self.time_display.update()

    # Cash display lost focus
    def _cash_focus_out(self, evt):
        pallete: QPalette = self.cash_display.palette()
        pallete.setColor(QPalette.Background, self.default_background_display_color)
        self.cash_display.setPalette(pallete)

        self.cash = float(self.cash)
        if self.cash == 0:
            self.mode = ControlMode.FREE

        # Check max cash by 24 hours
        max_cash = ((24 * 3600) - 1) * (self.price / 3600)
        if self.cash > max_cash:
            self.cash = max_cash

        # Calculate time by cash
        self.time = round(self.cash / self.price * 3600)
        self.display()
        self.start_btn.setFocus()

    # Cash display key pressed
    def _cash_key_pressed(self, evt):
        # In edit mode , we work ONLY with str type self.cash
        if evt.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape):
            self.cash_display.clearFocus()
            return
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
            elif len(cash) > self.cash_display.digitCount() - 2 or \
                    "." not in cash and len(cash) >= self.cash_display.digitCount() - 4 and \
                    evt.key() != Qt.Key_Period:
                pass
            else:
                cash += evt.text()
            self.cash = cash if len(cash) > 0 else "0"
        if evt.key() == Qt.Key_Delete:
            self.cash = "0"
        self.cash_display.display(self.cash)

    # Cash display mouse move
    def _cash_mouse_move(self, evt):
        if self.mode == ControlMode.CASH and not self.stopped and \
                evt.pos().x() < 32 and evt.pos().y() < 32:
            if self.cash_display.cursor() != Qt.PointingHandCursor:
                self.cash_display.setCursor(Qt.PointingHandCursor)
                QToolTip.showText(evt.globalPos(), "Добавить деньги", self.cash_display)
        elif self.cash_display.cursor() != Qt.IBeamCursor:
            self.cash_display.setCursor(Qt.IBeamCursor)

    # Cash display mouse pressed
    def _cash_mouse_pressed(self, evt):
        if self.mode == ControlMode.CASH and not self.stopped and \
                evt.button() == Qt.LeftButton and evt.x() < 32 and evt.y() < 32:
            self.add_dialog = AddDialog(self)

    # Time display get focus
    def _time_focus_in(self, evt):
        pallete: QPalette = self.time_display.palette()
        pallete.setColor(QPalette.Background, QColor(255, 255, 255))
        self.time_display.setPalette(pallete)
        self.edit_time_mode = EditTimeMode.HOURS
        # Set control mode by time
        self.mode = ControlMode.TIME
        self.cash_display.update()

    # Time display lost focus
    def _time_focus_out(self, evt):
        palette: QPalette = self.time_display.palette()
        palette.setColor(QPalette.Background, self.default_background_display_color)
        self.time_display.setPalette(palette)
        self.edit_time_mode = EditTimeMode.NO_EDIT
        if self.time == 0:
            self.mode = ControlMode.FREE
        self.display()
        self.start_btn.setFocus()

    # Time display key pressed
    def _time_key_pressed(self, evt):
        if evt.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape):
            self.time_display.clearFocus()
        legal_keys = (Qt.Key_Left, Qt.Key_Right, Qt.Key_Plus, Qt.Key_Minus,
                      Qt.Key_Enter, Qt.Key_Return, Qt.Key_Delete, Qt.Key_Up, Qt.Key_Down)
        if not (Qt.Key_0 <= evt.key() <= Qt.Key_9) and evt.key() not in legal_keys: return

        if Qt.Key_0 <= evt.key() <= Qt.Key_9 or evt.key() == Qt.Key_Delete:
            # Time to str for edit peaces
            self.tmp_edit_time["time_str"] = "{:0>8}".format(str(datetime.timedelta(seconds=self.time)))
            self.tmp_edit_time["h_peace"] = self.tmp_edit_time["time_str"][:2]
            self.tmp_edit_time["m_peace"] = self.tmp_edit_time["time_str"][3:5]
            if self.edit_time_mode == EditTimeMode.HOURS:
                if evt.key() == Qt.Key_Delete:
                    self.tmp_edit_time["h_peace"] = "00"
                else:
                    if self.tmp_edit_time["h_peace"][-1] in "012":
                        if self.tmp_edit_time["h_peace"][-1] == "2" and evt.text() not in "0123":
                            pass
                        else:
                            self.tmp_edit_time["h_peace"] = self.tmp_edit_time["h_peace"][-1] + evt.text()
                    else:
                        self.tmp_edit_time["h_peace"] = "0" + evt.text()
            if self.edit_time_mode == EditTimeMode.MINUTES:
                if evt.key() == Qt.Key_Delete:
                    self.tmp_edit_time["m_peace"] = "00"
                else:
                    if self.tmp_edit_time["m_peace"][-1] in "012345":
                        self.tmp_edit_time["m_peace"] = self.tmp_edit_time["m_peace"][-1] + evt.text()
                    else:
                        self.tmp_edit_time["m_peace"] = "0" + evt.text()
            # Str to time, after edit
            self.time = (int(self.tmp_edit_time["h_peace"]) * 3600) + \
                        (int(self.tmp_edit_time["m_peace"]) * 60) + \
                        int(self.tmp_edit_time["time_str"][6:8])
            self.display()
        if evt.key() == Qt.Key_Left or evt.key() == Qt.Key_Right:
            if self.edit_time_mode == EditTimeMode.HOURS:
                self.edit_time_mode = EditTimeMode.MINUTES
                self.time_display.update()
                return
            elif self.edit_time_mode == EditTimeMode.MINUTES:
                self.edit_time_mode = EditTimeMode.HOURS
                self.time_display.update()
                return
        if evt.key() == Qt.Key_Plus or evt.key() == Qt.Key_Up:
            if self.edit_time_mode == EditTimeMode.HOURS:
                if self.time <= (23 * 3600) - 1:
                    self.time += 3600
                else:
                    self.edit_time_mode = EditTimeMode.MINUTES
                    self.time_display.update()
            if self.edit_time_mode == EditTimeMode.MINUTES:
                if self.time <= (24 * 3600) - 61:
                    self.time += 60
            if (24 * 3600) - self.time == 60:
                self.time += 59
            self.display()
            return
        if evt.key() == Qt.Key_Minus or evt.key() == Qt.Key_Down:
            if self.edit_time_mode == EditTimeMode.HOURS:
                if self.time >= 3600:
                    self.time -= 3600
                else:
                    self.edit_time_mode = EditTimeMode.MINUTES
                    self.time_display.update()
            if self.edit_time_mode == EditTimeMode.MINUTES:
                if self.time >= 60:
                    self.time -= 60
            if self.time < 60:
                self.time = 0
            self.display()
            return

    # Time display mouse move
    def _time_mouse_move(self, evt):
        if self.mode == ControlMode.TIME and not self.stopped and \
                evt.pos().x() < 32 and evt.pos().y() < 32:
            if self.time_display.cursor() != Qt.PointingHandCursor:
                self.time_display.setCursor(Qt.PointingHandCursor)
                QToolTip.showText(evt.globalPos(), "Добавить время", self.time_display)
        elif self.time_display.cursor() != Qt.IBeamCursor:
            self.time_display.setCursor(Qt.IBeamCursor)

    # Cash display mouse pressed
    def _time_mouse_pressed(self, evt):
        if self.mode == ControlMode.TIME and not self.stopped and \
                evt.button() == Qt.LeftButton and evt.x() < 32 and evt.y() < 32:
            self.add_dialog = AddDialog(self)


class AddDialog(QDialog):
    """ Adding time or cash dialog """

    def __init__(self, parent):
        super().__init__(parent)
        self.icon = None
        self.inputted_value = 0
        self.add_cash = 0
        self.edit_time_mode = EditTimeMode.HOURS
        if parent.mode == ControlMode.TIME:
            self.icon = QPixmap("./res/clock.png")
        else:
            self.icon = QPixmap("./res/cash.png")
        # Minimum time to add
        self.min_add_time = 5 * 60
        self._init_ui()

    def _init_ui(self):
        self.setWindowTitle(self.parent().tittle_lb.text())
        self.setFixedSize(380, 220)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint)
        self.setModal(True)

        # Root layout
        vbox_lay = QVBoxLayout(self)
        vbox_lay.setContentsMargins(10, 10, 10, 10)

        # Add button
        self.add_btn = QPushButton("Добавить")
        self.add_btn.setFixedSize(120, 30)
        self.add_btn.clicked.connect(self._add_btn_click)
        self.add_btn.setDefault(True)

        self.input_lcd = QLCDNumber(self)
        self.input_lcd.setStyleSheet("background: silver;")
        self.input_lcd.setFixedSize(self.width() - 20, (self.height() // 10) * 5)
        self.input_lcd.paintEvent = self._input_lcd_paint
        self.input_lcd.setDigitCount(9)
        self.input_lcd.setFocusPolicy(Qt.ClickFocus)
        self.input_lcd.setFocus()
        self.input_lcd.focusInEvent = lambda x: self.input_lcd.setStyleSheet("background: white;")
        self.input_lcd.focusOutEvent = lambda x: self.input_lcd.setStyleSheet("background: silver;")
        self.input_lcd.keyPressEvent = self._input_key_press

        self.title_lb = QLabel()
        f: QFont = self.title_lb.font()
        f.setPointSize(16)
        self.title_lb.setFont(f)
        self.title_lb.setWordWrap(True)

        self.res_lb = QLabel()
        self.res_lb.setFont(f)

        subh_lay = QHBoxLayout(self)
        subh_lay.addWidget(self.res_lb, alignment=Qt.AlignLeft)
        subh_lay.addWidget(self.add_btn, alignment=Qt.AlignRight)
        vbox_lay.addLayout(subh_lay)

        vbox_lay.insertWidget(0, self.input_lcd, alignment=Qt.AlignBottom)
        vbox_lay.insertWidget(0, self.title_lb, alignment=Qt.AlignCenter)

        if self.parent().mode == ControlMode.TIME:
            self.title_lb.setText("Больше времени? та не вопрос!")
            self.res_lb.setText("Введите время...")
        else:
            self.title_lb.setText("Кто платит - тот и заказывает музыку!")
            self.res_lb.setText("Введите деньги...")
        self._display()
        self.show()

    def _display(self):
        display_str = "Err"
        if self.parent().mode == ControlMode.TIME:
            display_str = "{:0>8}".format(str(datetime.timedelta(seconds=self.inputted_value)))
            self.add_cash = str(round((self.inputted_value / 3600) * self.parent().price, 2))
            self.res_lb.setText("Деньги: " + self.add_cash)
        elif self.parent().mode == ControlMode.CASH:
            self.add_cash = self.inputted_value
            self.res_lb.setText("Время: {:0>8}".format(
                str(datetime.timedelta(seconds=round(float(self.inputted_value) / self.parent().price * 3600)))
            ))
            display_str = self.inputted_value
        self.input_lcd.display(display_str)

    def _input_key_press(self, evt):
        # Esc
        if evt.key() == Qt.Key_Escape:
            self.close()
        # Enter
        if evt.key() == Qt.Key_Enter or evt.key() == Qt.Key_Return:
            self.add_btn.click()
        # Time
        if self.parent().mode == ControlMode.TIME:
            # Delete
            if evt.key() == Qt.Key_Delete:
                if self.edit_time_mode == EditTimeMode.HOURS:
                    self.inputted_value = self.inputted_value % 3600
                if self.edit_time_mode == EditTimeMode.MINUTES:
                    self.inputted_value = self.inputted_value - (self.inputted_value % 3600)
            # <- ->
            if evt.key() == Qt.Key_Left or evt.key() == Qt.Key_Right:
                if self.edit_time_mode == EditTimeMode.HOURS:
                    self.edit_time_mode = EditTimeMode.MINUTES
                    self.input_lcd.update()
                else:
                    self.edit_time_mode = EditTimeMode.HOURS
                    self.input_lcd.update()
            # Plus
            if evt.key() == Qt.Key_Plus or evt.key() == Qt.Key_Up:
                if self.edit_time_mode == EditTimeMode.HOURS:
                    if (self.inputted_value + self.parent().time) <= (23 * 3600 - 1):
                        self.inputted_value += 3600
                elif self.edit_time_mode == EditTimeMode.MINUTES:
                    if (self.inputted_value + self.parent().time) <= (24 * 3600 - 61):
                        self.inputted_value += 60
            # Minus
            if evt.key() == Qt.Key_Minus or evt.key() == Qt.Key_Down:
                if self.edit_time_mode == EditTimeMode.HOURS:
                    if self.inputted_value >= 3600:
                        self.inputted_value -= 3600
                elif self.edit_time_mode == EditTimeMode.MINUTES:
                    if self.inputted_value >= 60:
                        self.inputted_value -= 60
            # 0 - 9
            if Qt.Key_0 <= evt.key() <= Qt.Key_9:
                if self.edit_time_mode == EditTimeMode.HOURS:
                    hours = "{:0>2}".format(str(self.inputted_value // 3600))
                    if int(hours + evt.text()) < 24:
                        hours = hours[-1] + evt.text()
                    else:
                        hours = "00"
                    self.inputted_value = (self.inputted_value % 3600) + (int(hours) * 3600)
                if self.edit_time_mode == EditTimeMode.MINUTES:
                    minutes = "{:0>2}".format(str(self.inputted_value % 3600 // 60))
                    if int(minutes + evt.text()) < 59:
                        minutes = minutes[-1] + evt.text()
                    else:
                        minutes = "00"
                    self.inputted_value = (self.inputted_value // 3600) * 3600 + int(minutes) * 60
            # Check time overflow
            if self.inputted_value + self.parent().time > 24 * 3600:
                self.inputted_value = 24 * 3600 - self.parent().time

        # Cash
        elif self.parent().mode == ControlMode.CASH:
            self.inputted_value = str(self.inputted_value)
            # 0..9
            if Qt.Key_0 <= evt.key() <= Qt.Key_9 or evt.key() == Qt.Key_Period:
                if "." in self.inputted_value and evt.key() == Qt.Key_Period:
                    return
                if len(self.inputted_value) == 0 or self.inputted_value == "0":
                    if evt.key() == Qt.Key_Period:
                        self.inputted_value = "0."
                    else:
                        self.inputted_value = evt.text()
                else:
                    if "." in self.inputted_value and \
                            len(self.inputted_value) - self.inputted_value.index(".") > 2:
                        return
                    self.inputted_value = self.inputted_value + evt.text()
                if self.parent().cash + float(self.inputted_value) > 24 * self.parent().price:
                    self.inputted_value = str(round((24 * self.parent().price) - self.parent().cash, 2))
            # Backspace
            if evt.key() == Qt.Key_Backspace and len(self.inputted_value) > 0:
                self.inputted_value = self.inputted_value[:-1]
            # Delete
            if evt.key() == Qt.Key_Delete:
                self.inputted_value = "0"
            if len(self.inputted_value) == 0:
                self.inputted_value = "0"
        self._display()

    def _input_lcd_paint(self, evt):
        p = QPainter(self.input_lcd)
        p.setRenderHints(p.renderHints() | QPainter.Antialiasing)
        p.drawPixmap(10, (self.input_lcd.height() - self.icon.height()) // 2, self.icon)
        pen: QPen = p.pen()
        pen.setWidth = 2
        pen.setCapStyle(Qt.RoundCap)

        if self.parent().mode == ControlMode.TIME:
            h = (self.input_lcd.height() // 10) * 8.5
            w = self.input_lcd.width() // self.input_lcd.digitCount()
            if self.edit_time_mode == EditTimeMode.HOURS:
                offset_x, offset_y = w + 5, 8
            else:
                offset_x, offset_y = (w * 4) - 2, 8
            p.drawRoundedRect(offset_x, offset_y, w * 2, h, 5.0, 5.0)

        QLCDNumber.paintEvent(self.input_lcd, evt)

    def _add_btn_click(self):
        if self.parent().mode == ControlMode.CASH:
            self.time = round(float(self.inputted_value) / self.parent().price * 3600)
            if self.time < self.min_add_time:
                QMessageBox.warning(self, "Добавить деньги",
                                    "Минимальная сумма для добавления: " + str(round(self.parent().price / 60 * 5, 2)))
                return
        else:
            self.time = self.inputted_value
            if self.time < self.min_add_time:
                QMessageBox.warning(self, "Добавить время",
                                    "Минимальное время для добавления: 5 минут")
                return
        if QMessageBox.question(self, "Оплата",
                                "Доплата в размере " + self.add_cash + " грн получена?",
                                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.parent().time += self.time
        self.close()


if __name__ == "__main__":
    import os, pt

    os.chdir("..")
    app = QApplication([])
    mw = QWidget()
    mw.config = pt.read_config()
    w = TimerCashControl(mw, 1)
    mw.show()
    app.exec()
