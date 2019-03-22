#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod, abstractproperty
from PyQt5.QtWidgets import QWidget


class SwitchException(Exception):
    """Exception raises on problem in switch"""
    pass

class ActivateException(Exception):
    """Exception raises with non activated plugin state"""
    pass


class PTBasePlugin(metaclass=ABCMeta):
    """Base Power Time plugin"""
    def __init__(self):
        super().__init__()
        self.__activated = False

    @abstractmethod
    def get_info(self):
        """Main info about plugin

        :return: dict {author: str, plugin_name: str, version: str, description: str, activated: bool}
        :raises Exception"""

        info = {
            "author" : "Andrunin Dmitry",
            "plugin_name": "Test plugin",
            "version": "1.0.0",
            "description": "This is example plugin description",
            "activated": False
        }
        return info

    @abstractmethod
    def get_channels_count(self):
        """Return count of swichable chanels"""
        return 0

    @abstractmethod
    def get_channels_info(self):
        """
        Returned dict {global_channel_num: [dev, local_channel_num], ...}
        Like:
        {
            0: [dev1, 0],
            1: [dev1, 1],
            2: [dev2, 0],
            3: [dev2, 1]
        }
        """
        return {}

    @abstractmethod
    def switch(self, channel, state):
        """Switch channel on/off
        :param: channel Channel to switch int
        :param: state State of chanel bool
        :raises SwitchException, Exception"""
        pass

    @abstractmethod
    def activate(self):
        """
        Activating plugin
        This method activate / initialize plugin
        :return: Activation result (bool)
        :raise Exception
        """
        return False

    @abstractmethod
    def deactivate(self):
        """
        Deactivating plugin
        Method deactivate plugin
        :raises Exception
        """

    @abstractmethod
    def build_settings(self, widget: QWidget):
        """Build plugin setting ui on plugin page

        :raises Exception
        """
        pass


