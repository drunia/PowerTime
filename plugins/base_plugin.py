#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from abc import ABCMeta, abstractmethod

class PTBasePlugin(metaclass=ABCMeta):
    """Base Power Time plugin"""

    @abstractmethod
    def get_info(self):
        """Main info about plugin
        :return {author: author, plugin_name: plugin_name, version: version, description}"""
        pass

