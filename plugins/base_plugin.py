#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod

class PTBasePlugin(metaclass=ABCMeta):
    """Base Power Time plugin"""

    @abstractmethod
    def get_info(self):
        """Main info about plugin

        :return {author: author, plugin_name: plugin_name, version: version, description}"""
        return {}

    @abstractmethod
    def get_channels_count(self):
        """Return count of swichable chanels"""
        return 0

    def switch(self, channel, state):
        """Switch channel on/off

        :param channel Channel to switch int
        :param state State of chanel bool"""

        return 0

