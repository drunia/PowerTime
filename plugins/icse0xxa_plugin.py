#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from drivers.icse0xxa import *
from plugins.base_plugin import *


class ICSE0XXA_Plugin(PTBasePlugin):
    """Plugin for control ICSE0XXA devices"""
    def __init__(self):
        super().__init__()
        self.__dev_list = []

    def __check_activated(self):
        if not self._activated:
            raise ActivateException("Need activate first!")

    def get_info(self):
        return {"author": "drunia",
                "plugin_name": "ICSE0XXA control",
                "version": 1.0,
                "description": "Test"}

    def get_channels_count(self):
        self.__check_activated()
        count = 0
        for d in self.__dev_lists:
            count += d.relays_count()
        return count

    def switch(self, channel, state):
        self.__check_activated()
        if channel > len(self.__channels):
            raise SwitchException(
                "Num {} channel biggest of channels {} "
                "on connected devices.".format(channel, len(self.__channels))
            )
        dev, ch = self.__channels[channel-1]
        dev.switch_relay(ch, state)


    def activate(self):
        if self._activated: return self._activated

        #self.__dev_lists = find_devices()

        self.__dev_list = load_devices_from_config()
        for d in self.__dev_list:
            d.init_device()

        relay = 0
        # Structure of __channels : {global number of channel: [device, local number of channel], ...}
        self.__channels = {}
        for d in self.__dev_list:
            for r in range(0, 8):
                self.__channels[r+relay] = [d, r]
            relay += r+1
        
        self._activated = True
        return self._activated

    def build_settings(self, qwidget):

        pass
