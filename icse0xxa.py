#!/usr/bin/env python3

import time, sys

from serial import Serial, SerialException, SerialTimeoutException
from serial.tools import list_ports
from configparser import ConfigParser

devices = {0xAB: "ICSE012A", 0xAD: "ICSE013A", 0xAC: "ICSE014A"}

class ICSE0XXADevice:
    """Class for controlling ICSE0XXA device"""

    ID_COMMAND = bytes([0x50])
    READY_COMMAND = bytes([0x51])

    # State of device initializing
    initialized = False

    _port = None
    _id = None
    _connection = None

    _relays = {0xAB: 4, 0xAD: 2, 0xAC: 8}

    def __init__(self, port, id):
        super().__init__()
        self._port = port
        self._id = id

    def relays_count(self):
        return self._relays[self._id]

    def info(self):
        return "{}@{} with {} relays".format(devices[self._id], self._port, self.relays_count())

    def switch_relay(self, relay_num, enable):
        """Switching relay on device
        :arg relay_num - Number of relay
        :arg enable - switch state True - ON, False - OFF """

        if relay_num > 7: raise Exception("Relay num mast be less than 8")
        self._connection.write(bytes([int(enable)<<relay_num]))


    def init_device(self):
        """Turn device to listening mode
        NOTICE:
        In listening mode device not responding for identification
        For disable listening mode need turn off or reset device!
        :return Result of initialize (bool)
        """

        self.initialized = False

        self._connection = Serial()
        self._connection.port = self._port
        self._connection.timeout = 1
        try:
            self._connection.open()
            self._connection.write(ICSE0XXADevice.ID_COMMAND)
            time.sleep(0.5)
            self._connection.write(ICSE0XXADevice.READY_COMMAND)
            self._connection.close()
            time.sleep(0.5)
            self._connection.open()
            time.sleep(0.5)
        except SerialException:
            _eprint("ICSE0XXADevice.init_device(): Error open port {}".format(self._port))
            return self.initialized
        except SerialTimeoutException:
            _eprint("ICSE0XXADevice.init_device(): Error write to port {}".format(self._port))
            return self.initialized

        # no errors - good
        self.initialized = True
        return self.initialized


def load_devices_from_config(file="icse0xxa.conf"):
    """Load ICSE0XXA devices from config file
    :return: dev_list[ICSE0XXADevice, ...]"""

    MAIN_SECTION = "devices"

    dev_list = []
    config = ConfigParser()
    config.read(file)
    if not MAIN_SECTION in config.sections(): return dev_list
    for k in config[MAIN_SECTION]:
        dev_list.append(ICSE0XXADevice(k, int(config[MAIN_SECTION][k], 16)))
    return dev_list


def find_devices():
    """Find ICSE0XXA devices on ports
    :return: dev_list[ICSE0XXADevice, ...]"""
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
            p.write(ICSE0XXADevice.ID_COMMAND)
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
    #dev_list = find_devices()
    dev_list = load_devices_from_config()
    print("Finded {} device(s)".format(len(dev_list)))
    for d in dev_list: print(d.info())

    d = dev_list[0]
    if d.init_device():
        print("Device {} initialized successfully".format(d.info()))
    d.switch_relay(2, True)
    input()
