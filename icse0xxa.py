#!/usr/bin/env python3

import time, sys

from serial import Serial, SerialException, SerialTimeoutException
from serial.tools import list_ports

import serial

devices = {0xAB: "ICSE012A", 0xAD: "ICSE013A", 0xAC: "ICSE014A"}

class ICSE0XXADevice:
    """Class for controlling ICSE0XXA device"""

    # State of device initializing
    initialized = False

    _port = None
    _id = None

    _relays = {0xAB: 4, 0xAD: 2, 0xAC: 8}

    def __init__(self, port, id):
        super().__init__()
        self._port = port
        self._id = id

    def relays_count(self):
        return self._relays[self._id]

    def info(self):
        return "{}@{} with {} relays".format(devices[self._id], self._port, self.relays_count())

    def switch_relay(relay_num, enable):
        """Switching relay on device
        relay_num - Number of relay
        enable - switch state True - ON, False - OFF """
        pass

    def init_device(self):
        pass

def find_devices():
    """Find ICSE0XXA devices on ports
    Return: dev_list[ICSE0XXADevice, ...]"""
    id_c = bytearray([0x50])
    dev_list = []
    for port in list_ports.comports():
        p = Serial()
        p.port = port.device
        p.timeout = 1
        try:
            p.open()
        except SerialException:
            _eprint("find_devices(): Error in open {} port".format(p.port))
            continue
        try:
            print("write to {}".format(p.port))
            p.write(id_c)
            time.sleep(0.5)
            answer = p.read()
            if (len(answer) > 0) and (answer[0] in devices.keys()):
                dev_list.append(ICSE0XXADevice(p.port, answer[0]))
        except SerialTimeoutException:
            _eprint("find_devices(): Read/Write timeout on {}".format(p.port))
        finally:
            p.close()
    return dev_list


def _eprint(err):
    print(err, file=sys.stderr)


if __name__ == "__main__":
    dev_list = find_devices()
    for d in dev_list: print(d.info())
