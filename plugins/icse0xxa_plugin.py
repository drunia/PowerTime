#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from drivers.icse0xxa import *
from plugins.base_plugin import *


class ICSE0XXA_Plugin(PTBasePlugin):
    """Plugin for control ICSE0XXA devices"""
    def __init__(self):
        super().__init__()

    def __check_activated(self):
        if not self.__activated:
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
        self.__dev_lists[self.__channels[channel]].switch_relay(channel-1, state)

    def activate(self):
        self.__dev_lists = find_devices()
        self.__channels = {}
        
        self.__activated = True
        return True
