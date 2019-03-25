#!/usb/bin/env python3
# -*- coding: utf-8 -*-

from ctypes import *
import win32.win32api as win32api
import win32.win32console as win32con
import win32.win32gui as win32gui

from PySide.QtCore import QObject, Signal

"""
Module for listen enable/disable ports to re-init icse00xa module 
"""

#
# Device change events (WM_DEVICECHANGE wParam)
#
DBT_DEVICEARRIVAL = 0x8000
DBT_DEVICEREMOVECOMPLETE = 0x8004

#
# type of device in DEV_BROADCAST_HDR
#
DBT_DEVTYPE_PORT = 0x00000003

# c types
WORD = c_ushort
DWORD = c_ulong


class DEV_BROADCAST_HDR(Structure):
    _fields_ = [
        ("dbch_size", DWORD),
        ("dbch_devicetype", DWORD),
        ("dbch_reserved", DWORD)
    ]


class DEV_BROADCAST_PORT(Structure):
    _fields_ = [
        ("dbcp_size", DWORD),
        ("dbcp_devicetype", DWORD),
        ("dbcp_reserved", DWORD),
        ("dbcp_name", ARRAY(c_wchar, 255))
    ]


class PortStateNotificator(QObject):
    """
    Signal emit when ports state changed
    :param str - port name
    :param bool - connect state
    """
    state_changed = Signal(str, bool)

    def __init__(self):
        super().__init__()
        message_map = {
            win32con.WM_DEVICECHANGE: self.onDeviceChange
        }

        wc = win32gui.WNDCLASS()
        hinst = wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "pt_port_state_listener"
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32con.COLOR_WINDOW
        wc.lpfnWndProc = message_map
        classAtom = win32gui.RegisterClass(wc)
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(
            classAtom,
            "pt_port_state_listener",
            style,
            0, 0,
            win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT,
            0, 0,
            hinst, None
        )

    def onDeviceChange(self, hwnd, msg, wparam, lparam):
        #
        # WM_DEVICECHANGE:
        #  wParam - type of change: arrival, removal etc.
        #  lParam - what's changed?
        #    if it's a volume then...
        #  lParam - what's changed more exactly
        #
        dev_broadcast_hdr = DEV_BROADCAST_HDR.from_address(lparam)

        # print("hwnd = {}, msg = {}, wparam = {}, lparam = {}".format(hwnd, msg, wparam, lparam))

        if wparam == DBT_DEVICEARRIVAL or wparam == DBT_DEVICEREMOVECOMPLETE and \
                dev_broadcast_hdr.dbch_devicetype == DBT_DEVTYPE_PORT:
            dev_broadcast_port = DEV_BROADCAST_PORT.from_address(lparam)
            port_name = dev_broadcast_port.dbcp_name
            if wparam == DBT_DEVICEARRIVAL:
                # print(__name__, ": Port {} connected".format(port_name))
                self.state_changed.emit(port_name, True)
            if wparam == DBT_DEVICEREMOVECOMPLETE:
                # print(__name__, ": Port {} disconnected".format(dev_broadcast_port.dbcp_name))
                self.state_changed.emit(port_name, False)
        return 1


if __name__ == '__main__':
    w = PortStateNotificator()
    win32gui.PumpMessages()
