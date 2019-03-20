#!/usb/bin/env python3
#-*- coding: utf-8 -*-
import struct
import win32api, win32con, win32gui
from ctypes import *

#
# Device change events (WM_DEVICECHANGE wParam)
#
import pywintypes

DBT_DEVICEARRIVAL = 0x8000
DBT_DEVICEQUERYREMOVE = 0x8001
DBT_DEVICEQUERYREMOVEFAILED = 0x8002
DBT_DEVICEMOVEPENDING = 0x8003
DBT_DEVICEREMOVECOMPLETE = 0x8004
DBT_DEVICETYPESSPECIFIC = 0x8005
DBT_CONFIGCHANGED = 0x0018

#
# type of device in DEV_BROADCAST_HDR
#
DBT_DEVTYP_OEM = 0x00000000
DBT_DEVTYP_DEVNODE = 0x00000001
DBT_DEVTYP_VOLUME = 0x00000002
DBT_DEVTYPE_PORT = 0x00000003
DBT_DEVTYPE_NET = 0x00000004

#
# media types in DBT_DEVTYP_VOLUME
#
DBTF_MEDIA = 0x0001
DBTF_NET = 0x0002

WORD = c_ushort
DWORD = c_ulong
CHAR = c_char


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
        ("dbcp_name", CHAR)
    ]


class Notification:
    def __init__(self):
        message_map = {
            win32con.WM_DEVICECHANGE: self.onDeviceChange
        }

        wc = win32gui.WNDCLASS()
        hinst = wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = "usb_change_device_listener"
        wc.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
        wc.hbrBackground = win32con.COLOR_WINDOW
        wc.lpfnWndProc = message_map
        classAtom = win32gui.RegisterClass(wc)
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(
            classAtom,
            "usb_change_device_listener",
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
        #print("hwnd = {}, msg = {}, wparam = {}, lparam = {}".format(hwnd, msg, wparam, lparam))

        if wparam == DBT_DEVICEARRIVAL and dev_broadcast_hdr.dbch_devicetype == DBT_DEVTYPE_PORT:
            print("USB-PORT CONNECT ")
            dev_broadcast_port = DEV_BROADCAST_PORT.from_address(lparam)
            print(dev_broadcast_port.dbcp_name)
            print(dev_broadcast_port.dbcp_devicetype)
        if wparam == DBT_DEVICEREMOVECOMPLETE and dev_broadcast_hdr.dbch_devicetype == DBT_DEVTYPE_PORT:
            print("USB-PORT DISCONNECT ")
        return 1




if __name__ == '__main__':
    w = Notification()
    win32gui.PumpMessages()





