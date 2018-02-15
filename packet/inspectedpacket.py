#!/usr/bin/python
# -*- coding: UTF-8 -*-

from .basepacket import Packet
from .safepacket import SafePacket
from .utils import NotSerializable, InvalidData, JSON_SERIALIZER, AST_SERIALIZER
from ._compat import get_items

_json_allowed_types = {
    "dict": "object",
    "list": "array", "tuple": "array",
    "str": "string", "unicode": "string",
    "int": "number", "long": "number",
    "float": "real",
    "bool": "boolean",
    # "NoneType": "null", # NoneType is not allowed
}

_ast_allowed_types = [
    "dict",
    "list", "tuple",
    "set",  # Empty sets are not allowed. Sets are allowed since Python 3.2
    "str", "unicode",
    "bytes",
    "int", "long",
    "float",
    "complex",
    "bool",
    # "NoneType", # NoneType is not allowed
]


def _is_instance_of_class(var):
    # TODO - improve this check: instances of classes with a __call__() method are also callable
    return not callable(var) and hasattr(var, "__dict__")


def _type_string(var):
    return var.__class__.__name__


class InspectedPacket(Packet):
    """
    Inspected packet class
    """

    def __generate_dict(self, obj):
        _dict = {}
        for k, v in get_items(obj.__dict__):
            t = _type_string(v)
            if (self.packet_serializer == JSON_SERIALIZER and t in _json_allowed_types) or (
                    self.packet_serializer == AST_SERIALIZER and t in _ast_allowed_types):
                _dict[k] = v
            elif _is_instance_of_class(v):
                _dict[k] = self.__generate_dict(v)
            else:
                raise NotSerializable
        return _dict

    def _generate_dict(self):
        return self.__generate_dict(self)

    def __check_dict(self, obj, data):
        # TODO - improve exception raising
        if not isinstance(data, dict) or set(obj.__dict__) != set(data):
            raise Exception
        for k, v in get_items(obj.__dict__):
            type1 = _type_string(v)
            type2 = _type_string(data[k])
            if self.packet_serializer == JSON_SERIALIZER and type1 in _json_allowed_types:
                if _json_allowed_types[type1] != _json_allowed_types[type2]:
                    raise Exception
            elif self.packet_serializer == AST_SERIALIZER and type1 in _ast_allowed_types:
                if type1 != type2:
                    raise Exception
            elif _is_instance_of_class(v):
                if type2 != "dict":
                    raise Exception
                self.__check_dict(v, data[k])
            else:
                raise Exception

    def __update_dict(self, obj, data):
        for k, v in get_items(obj.__dict__):
            t = _type_string(v)
            if (self.packet_serializer == JSON_SERIALIZER and t in _json_allowed_types) or (
                    self.packet_serializer == AST_SERIALIZER and t in _ast_allowed_types):
                # obj.__dict__[k] = obj.__dict__[k].__class__(data[k])
                obj.__dict__[k] = data[k]
            else:
                self.__update_dict(obj.__dict__[k], data[k])

    def _update_dict(self, data):
        try:
            self.__check_dict(self, data)
        except Exception:
            raise InvalidData
        self.__update_dict(self, data)


class InspectedSafePacket(InspectedPacket, SafePacket):
    """
    Inspected and safe packet class
    """
