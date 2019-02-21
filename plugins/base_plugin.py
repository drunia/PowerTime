#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod


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

        :return: dict {author: str, plugin_name: str, version: str, description: str}"""
        return {}

    @abstractmethod
    def get_channels_count(self):
        """Return count of swichable chanels"""
        return 0

    @abstractmethod
    def switch(self, channel, state):
        """Switch channel on/off

        :param: channel Channel to switch int
        :param: state State of chanel bool"""
        pass

    @abstractmethod
    def activate(self):
        """
        Activating plugin

        This method activate / initialize plugin

        :return: Activation result (bool)
        """
        pass

