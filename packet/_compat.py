#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys

PY_VERSION = sys.version_info[0:2]
PY3 = PY_VERSION[0] == 3
PY2 = PY_VERSION[0] == 2

if PY3:
    def get_items(o):
        return o.items()
else:
    def get_items(o):
        return o.iteritems()
