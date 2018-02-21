#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys

PY3 = sys.version_info[0] == 3
PY2 = sys.version_info[0] == 2

if PY3:
    def get_items(o):
        return o.items()
else:
    def get_items(o):
        return o.iteritems()
