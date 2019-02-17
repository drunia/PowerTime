#!/usr/bin/env python3

import time, sys

from serial import Serial, SerialException, SerialTimeoutException
from serial.tools import list_ports
from configparser import ConfigParser

devices = {0xAB: "ICSE012A", 0xAD: "ICSE013A", 0xAC: "ICSE014A"}
MAIN_CFG_SECTION = "devices"

# Error log file, set for logging icse0xxa errors
err_file = None

class ICSE0XXADevice:
    """Class for controlling ICSE0XXA device"""

    ID_COMMAND = bytes([0x50])
    READY_COMMAND = bytes([0x51])

    # State of device initializing
    initialized = False

    _port = None
    _id = None
    _connection = None
    _relays_register = 0

    _relays = {0xAB: 4, 0xAD: 2, 0xAC: 8}

    def __init__(self, port, id):
        """Create ICSE0XXADevice object
        :arg port  Device port
        :arg id  Device id"""

        super().__init__()
        self._port = port
        self._id = id

    def __del__(self):
        if self._connection != None: self._connection.close()

    def relays_count(self):
        self._chek_init()
        return self._relays[self._id]

    def info(self):
        self._chek_init()
        return "{}@{} with {} relays".format(devices[self._id], self._port, self.relays_count())


    def port(self): return self._port
    def id(self): return self._id

    def name(self):
        if self._id in devices:
            return "{}@{}".format(devices[self._id], self._port)
        else: return "Unknown_Device@{}".format(self.port())

    def switch_relay(self, relay_num, enable):
        """Switching relay on device
        :arg relay_num  Number of relay
        :arg enable Switch state True - ON, False - OFF
        NOTICE:
        ON - diode on PCB is off, OFF - diodes lights!"""
        self._chek_init()
        if relay_num >= self.relays_count():
            raise Exception("Relay num mast be less than {}".format(self._relays[self._id]))
        if enable:
            self._relays_register = self._relays_register | (1 << relay_num)
        else:
            self._relays_register = self._relays_register & ~(1 << relay_num)
        time.sleep(0.01)
        self._connection.write(bytes([self._relays_register]))

    def init_device(self):
        """Turn device to listening mode
        NOTICE:
        In listening mode device not responding for identification
        For disable listening mode need turn off or reset device!
        :return Result of initialize (bool)
        :except SerialTimeoutException, SerialException
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
        except Exception as e:
            icse0xxa_eprint("ICSE0XXADevice.init_device(): {}".format(e))
            return self.initialized

        # no errors - good
        self.initialized = True
        return self.initialized

    def _chek_init(self):
        if not self._id in devices:
            raise Exception("Unknow_device: {}".format(self.name()))
        if not self.initialized:
            raise Exception("Device {} not initialized.".format(self.name()))


def load_devices_from_config(file="icse0xxa.conf"):
    """Load ICSE0XXA devices from config file
    :return: dev_list[ICSE0XXADevice, ...]"""

    dev_list = []
    c = ConfigParser()
    c.optionxform = str
    c.read(file)
    if not MAIN_CFG_SECTION in c.sections(): return dev_list
    for k in c[MAIN_CFG_SECTION]:
        dev_list.append(ICSE0XXADevice(k, int(c[MAIN_CFG_SECTION][k], 16)))
    return dev_list

def save_divices_to_config(dev_list, file="icse0xxa.conf"):
    c = ConfigParser()
    c.optionxform = str
    c.read(file)
    c[MAIN_CFG_SECTION] = {}
    for d in dev_list:
        c[MAIN_CFG_SECTION][d.port()] = hex(d.id())
    c.write(open(file, "w"))


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
        except SerialException as e:
            icse0xxa_eprint("find_devices(): {}".format(e))
            continue
        try:
            time.sleep(0.5)
            p.write(ICSE0XXADevice.ID_COMMAND)
            time.sleep(0.5)
            answer = p.read(1)
            if (len(answer) > 0) and (answer[0] in devices):
                dev_list.append(ICSE0XXADevice(p.port, answer[0]))
        except SerialTimeoutException as e:
            icse0xxa_eprint("find_devices(): {}".format(e))
        finally:
            p.close()
    return dev_list


def icse0xxa_eprint(err):
    print(err, file=sys.stderr)
    if err_file:
        print("{} ERR: {}".format(time.asctime(), err), file=err_file)


def test():
    # Set error file, for simply logging
    global err_file
    err_file = open(file="ICSE0XXA.errors", mode="a", encoding="windows-1251")

    _dev_list = load_devices_from_config()
    if len(_dev_list) == 0:
        print("No devices in config file, try autosearch device on serial ports")
        _dev_list = find_devices()

        if len(_dev_list) == 0:
            print("No device(s) finded on serial ports. " \
                  "If device connected - try reset him")
            sys.exit(1)
        else:
            # Save devices in config
            save_divices_to_config(_dev_list)

    _d = _dev_list[0]
    if _d.init_device():
        print("Device {} initialized".format(_d.info()))
    else:
        print("Can't init device: {}".format(_d.name()))
        sys.exit(1)

    print("Finded {} device(s)".format(len(_dev_list)))
    for _d in _dev_list: print(_d.info())

    while True:
        r = input("Try switch relay, format: [numstate], where num - num of relay, state - switch state[0/1]:")
        try:
            if r == "": sys.exit(0)
            n, s = r[0], r[1]
            _d.switch_relay(int(n), bool(int(s)))
        except Exception as ex:
            print("Error input format, try again...", )

if __name__ == "__main__":
    test()


