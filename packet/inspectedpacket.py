#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys
from .basepacket import Packet
from .safepacket import SafePacket
from .utils import NotSerializable, InvalidData

PY3 = sys.version_info[0] == 3

if PY3:
    def get_items(o):
        return o.items()
else:
    def get_items(o):
        return o.iteritems()

__allowed_types = {
    "dict": "object",
    "list": "array", "tuple": "array",
    "str": "string", "unicode": "string",
    "int": "number", "long": "number",
    "float": "real",
    "bool": "boolean",
    "NoneType": "null",
}


def _is_instance_of_class(var):
    # TODO - improve this check: instances of classes with a __call__() method are also callable
    return not callable(var) and hasattr(var, "__dict__")


def _generate_dict(obj):
    _dict = {}
    for k, v in get_items(obj.__dict__):
        t = _type_string(v)
        if t in __allowed_types:
            _dict[k] = v
        elif _is_instance_of_class(v):
            _dict[k] = _generate_dict(v)
        else:
            raise NotSerializable
    return _dict


def _type_string(var):
    return var.__class__.__name__


def __check_dict(obj, data):
    if not isinstance(data, dict) or set(obj.__dict__) != set(data):
        raise Exception
    for k, v in get_items(obj.__dict__):
        type1 = _type_string(v)
        type2 = _type_string(data[k])
        if type1 in __allowed_types:
            if __allowed_types[type1] != __allowed_types[type2]:
                raise Exception
        elif _is_instance_of_class(v):
            if type2 != "dict":
                raise Exception
            __check_dict(v, data[k])
        else:
            raise Exception


def __update_dict(obj, data):
    for k, v in get_items(obj.__dict__):
        if _type_string(v) in __allowed_types:
            obj.__dict__[k] = data[k]
        else:
            _update_dict(obj.__dict__[k], data[k])


def _update_dict(obj, data):
    try:
        __check_dict(obj, data)
    except Exception:
        raise InvalidData
    __update_dict(obj, data)


class InspectedPacket(Packet):
    """
    Inspected packet class
    """


InspectedPacket._generate_dict = _generate_dict
InspectedPacket._update_dict = _update_dict


class InspectedSafePacket(InspectedPacket, SafePacket):
    """
    Inspected and safe packet class
    """
