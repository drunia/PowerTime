#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import drivers.icse0xxa
from plugins.base_plugin import PTBasePlugin

class ICSE0XXA_Plugin(PTBasePlugin):
    """Plugin for control ICSE0XXA devices"""
    def __init__(self):
        super().__init__()

    def get_info(self):
        return {"author": "drunia",
                "plugin_name": "ICSE0XXA control",
                "version": 1.0,
                "description": "Test"}




