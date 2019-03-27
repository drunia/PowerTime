#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import sys

from serial import Serial, SerialException, SerialTimeoutException
from serial.tools import list_ports
from configparser import ConfigParser


class ICSE0XXADevice:
    """Class for controlling ICSE0XXA device"""

    # Command for identification device
    ID_COMMAND = bytes([0x50])
    # Command for switching device to listening mode
    READY_COMMAND = bytes([0x51])
    # Name of main device config section
    MAIN_CFG_SECTION = "ICSE0XXA_devices"
    # Known device types
    MODELS = {0xAB: "ICSE012A", 0xAD: "ICSE013A", 0xAC: "ICSE014A"}
    # Relays count by device id
    RELAYS = {0xAB: 4, 0xAD: 2, 0xAC: 8}

    def __init__(self, port, id):
        """Create ICSE0XXADevice object
        :arg port  Device port
        :arg id  Device id"""

        super().__init__()

        self.__port = port
        self.__id = id
        self.__initialized = False
        self.__connection = None
        self.__relays_register = 0

        print("Created:", self)

    def __del__(self):
        print("ICSE0XXADevice.__del__()")
        # ICSE0XXADevice.__del__()
        # TypeError: 'NoneType' object is not callable
        #
        # if self.__connection:
        #    self.__connection.close()

    def relays_count(self):
        self.__chek_init()
        return ICSE0XXADevice.RELAYS[self.__id]

    def info(self):
        self.__chek_init()
        return "{} with {} relays".format(self.name(), self.relays_count())

    def port(self):
        return self.__port

    def id(self):
        return self.__id

    def name(self):
        if self.__id in ICSE0XXADevice.MODELS:
            return "{}@{}".format(ICSE0XXADevice.MODELS[self.__id], self.__port)
        else:
            return "Unknown_Device@{}".format(self.port())

    def switch_relay(self, relay_num, enable):
        """Switching relay on device
        :arg relay_num  Number of relay
        :arg enable Switch state True - ON, False - OFF
        NOTICE:
        ON - diode on PCB is off, OFF - diodes lights!"""
        self.__chek_init()
        if relay_num >= self.relays_count():
            raise Exception("Relay num mast be less than {}".format(ICSE0XXADevice.RELAYS[self.__id]))
        if enable:
            self.__relays_register = self.__relays_register | (1 << relay_num)
        else:
            self.__relays_register = self.__relays_register & ~(1 << relay_num)
        time.sleep(0.01)
        self.__connection.write(bytes([self.__relays_register]))

    def init_device(self):
        """Turn device to listening mode
        NOTICE:
        In listening mode device not responding for identification
        For disable listening mode need turn off or reset device!
        :except SerialTimeoutException, SerialException"""
        self.__initialized = False
        self.__connection = Serial()
        self.__connection.port = self.__port
        self.__connection.timeout = 1
        try:
            self.__connection.open()
            self.__connection.write(ICSE0XXADevice.ID_COMMAND)
            time.sleep(0.5)
            answer = self.__connection.read(1)
            if len(answer) > 0 and answer[0] not in ICSE0XXADevice.MODELS:
                raise Exception("Unknown device '" + hex(answer[0]) + "'")
            # Port opened, but no answer
            if len(answer) == 0:
                print("ICSE0XXADevice.init_device():",
                      "CAUTION: Port " + self.__port + " opened, but device not responding.",
                      "Device may be already initialized...", file=sys.stderr)
            else:
                self.__connection.write(ICSE0XXADevice.READY_COMMAND)
            time.sleep(0.5)
        except Exception as e:
            icse0xxa_eprint("ICSE0XXADevice.init_device(): {}".format(e))
            raise e
        # no errors - good
        self.__initialized = True

    def __chek_init(self):
        if self.__id not in ICSE0XXADevice.MODELS:
            raise Exception("Unknown_device: {}".format(self.name()))
        if not self.__initialized:
            raise Exception("Device {} not initialized.".format(self.name()))

    def __str__(self):
        return self.name()


def load_devices_from_config(file="icse0xxa.conf"):
    """Load ICSE0XXA devices from config file
    :return: dev_list[ICSE0XXADevice, ...]
    Returned objects device not initialized!"""
    dev_list = []
    c = ConfigParser()
    c.optionxform = str
    c.read(file)
    if ICSE0XXADevice.MAIN_CFG_SECTION not in c.sections():
        return dev_list
    for k in c[ICSE0XXADevice.MAIN_CFG_SECTION]:
        dev_list.append(ICSE0XXADevice(k, int(c[ICSE0XXADevice.MAIN_CFG_SECTION][k], 16)))
    return dev_list


def save_devices_to_config(dev_list, file="icse0xxa.conf"):
    c = ConfigParser()
    c.optionxform = str
    c.read(file)
    c[ICSE0XXADevice.MAIN_CFG_SECTION] = {}
    for d in dev_list:
        c[ICSE0XXADevice.MAIN_CFG_SECTION][d.port()] = hex(d.id())
    with open(file, "w") as f:
        c.write(f)


def find_devices():
    """Find ICSE0XXA devices on ports
    :return: dev_list[ICSE0XXADevice, ...]
    Returned objects device not initialized!"""
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
            if (len(answer) > 0) and (answer[0] in ICSE0XXADevice.MODELS):
                dev_list.append(ICSE0XXADevice(p.port, answer[0]))
        except SerialTimeoutException as e:
            icse0xxa_eprint("find_devices(): {}".format(e))
        finally:
            p.close()
    return dev_list


def icse0xxa_eprint(err):
    print(err, file=sys.stderr)


def test():
    dev_list = load_devices_from_config()
    if len(dev_list) == 0:
        print("No devices in config file, try autosearch device on serial ports")
        dev_list = find_devices()

        if len(dev_list) == 0:
            print("No device(s) finded on serial ports. " 
                  "If device connected - try reset him")
            sys.exit(1)
        else:
            # Save devices in config
            save_devices_to_config(dev_list)
            print("Finded {} device(s)".format(len(dev_list)))
    else:
        print("Loaded {} device(s)".format(len(dev_list)))

    # Print loaded/finded devices
    for d in dev_list: print("Device: {}".format(d.name()))

    d = dev_list[0]
    try:
        d.init_device()
    except SerialException as e:
        print(e)
        sys.exit(1)

    print("Device initialized: {}".format(d.info()))

    while True:
        r = input("Try switch relay, format: [numstate], where num - num of relay, state - switch state[0/1]:")
        try:
            if r == "":
                sys.exit(0)
            n, s = r[0], r[1]
            d.switch_relay(int(n), bool(int(s)))
        except Exception as e:
            print("Error input format, try again...", )


if __name__ == "__main__":
    test()
