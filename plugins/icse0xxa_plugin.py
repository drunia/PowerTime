#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from drivers.icse0xxa import *
from plugins.base_plugin import PTBasePlugin

class SwitchException(Exception):
    """Exception raises on problem in switch"""
    pass


class ICSE0XXA_Plugin(PTBasePlugin):
    """Plugin for control ICSE0XXA devices"""
    def __init__(self):
        super().__init__()
        self.__dev_lists = find_devices()

    def get_info(self):
        return {"author": "drunia",
                "plugin_name": "ICSE0XXA control",
                "version": 1.0,
                "description": "Test"}

    def get_channels_count(self):
        count = 0
        for d in self.__dev_lists:
            count += d.relays_count()
        return count

    def switch(self, channel, state):
        if channel > self.get_channels_count():
            raise SwitchException(
                "Num {} channel biggest of channels {} "
                "on connected devices.".format(channel, self.get_channels_count())
            )
        all_channels = {num_device: channels for num_device, channels in self.__dev_lists}
        pass

