#!/usr/bin/env python3

import time
from serial import Serial, SerialException, SerialTimeoutException
from serial.tools import list_ports

import serial

id_c = bytearray([0x50])
devices = {0xAB: "ICSE012A", 0xAD: "ICSE013A", 0xAC: "ICSE014A"}


def find_devices():
    """Find ICSE0XXA devices on ports
    Return: dev_list{} PORT:DEVICE_NAME"""
    dev_list = {}
    for port in list_ports.comports():
        p = Serial()
        p.port = port.device
        p.timeout = 1
        try:
            p.open()
        except SerialException:
            print("find_devices(): Error in port.open({})".format(p.port))
            continue
        try:
            print("write to {}".format(p.port))
            p.write(id_c)
            time.sleep(0.5)
            answer = p.read()
            if len(answer) > 0:
                dev_list[port.device] = devices[answer[0]]
        except SerialTimeoutException:
            print("find_devices(): Read/Write timeout on {}".format(p.port))
        except KeyError:
            print("find_devices(): Unknown device answer {}".format(answer))
        finally:
            p.close()
    return dev_list


if __name__ == "__main__":
    dev_list = find_devices()
    print(dev_list)
