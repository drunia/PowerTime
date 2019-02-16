#!/usr/bin/env python3

import time
from serial import Serial, SerialException
from serial.tools import list_ports

id_c = bytearray([0x50])
devices = {0xAB: "ICSE012A", 0xAD: "ICSE013A" , 0xAC: "ICSE014A"}

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
            print("find_devices(): Error in port.open()")
        p.write(id_c)
        time.sleep(0.5)
        answer = p.read()
        try:
            dev_list[port.device] = devices[answer[0]]
        except KeyError:
            print("find_devices(): Unknown device answer {}".format(answer))
        except IndexError:
            # if device on port not responding (empty port)
            pass
        finally:
            p.close()
    return dev_list


if __name__ == "__main__":
    dev_list = find_devices()
    print(dev_list.values())











