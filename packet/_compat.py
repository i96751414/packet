#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys

PY_VERSION = sys.version_info[0:2]
PY3 = PY_VERSION[0] == 3
PY2 = PY_VERSION[0] == 2

if PY3:
    string_types = str,

    def get_items(o):
        return o.items()
else:
    # noinspection PyUnresolvedReferences
    string_types = basestring,  # NOQA

    def get_items(o):
        return o.iteritems()


def with_metaclass(meta, *bases):
    class Metaclass(meta):
        __call__ = type.__call__
        __init__ = type.__init__

        def __new__(cls, name, this_bases, d):
            if this_bases is None:
                return type.__new__(cls, name, (), d)
            return meta(name, bases, d)

    return Metaclass("temporary_class", None, {})
