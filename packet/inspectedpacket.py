#!/usr/bin/python
# -*- coding: UTF-8 -*-

from packet.basepacket import Packet
from packet.safepacket import SafePacket
from packet.utils import NotSerializable, InvalidData

__allowed_types = ["dict",
                   "list", "tuple",
                   "str", "unicode",
                   "int", "long", "float",
                   "bool",
                   "NoneType"]


def _is_instance_of_class(var):
    # TODO - improve this check: instances of classes with a __call__() method are also callable
    return not callable(var) and hasattr(var, "__dict__")


def _generate_dict(obj):
    _dict = {}
    for k, v in obj.__dict__.items():
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
    for k, v in obj.__dict__.items():
        t = _type_string(v)
        if t in __allowed_types:
            if t != _type_string(data[k]):
                raise Exception
        elif _is_instance_of_class(v):
            if _type_string(data[k]) != "dict":
                raise Exception
            __check_dict(v, data[k])
        else:
            raise Exception


def __update_dict(obj, data):
    for k, v in obj.__dict__.items():
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
