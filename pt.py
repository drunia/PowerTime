#!/usr/bin/env python3
#--* encoding: utf-8 *--

import os
from drivers.icse0xxa import *
from  plugins.icse0xxa_plugin import ICSE0XXA_Plugin

print("Working directory:", os.getcwd())

plugin = ICSE0XXA_Plugin()
print(plugin.get_info())
print(plugin.get_channels_count())

try:
    plugin.switch(1,True)
except Exception as e:
    print("Error happend:", e)




