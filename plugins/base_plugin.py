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
        self._activated = False

    @abstractmethod
    def get_info(self):
        """Main info about plugin

        :return: dict {author: str, plugin_name: str, version: str, description: str, activated: bool}
        :raises Exception"""
        return {}

    @abstractmethod
    def get_channels_count(self):
        """Return count of swichable chanels"""
        return 0

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
        :raises Exception
        """
        return False

    @abstractmethod
    def build_settings(self, widget: QWidget):
        """Build plugin setting ui on plugin page

        :raises Exception
        """
        pass


