#!/usr/bin/python
# -*- coding: UTF-8 -*-

import inspect
from .basepacket import Packet
from .safepacket import SafePacket
from .utils import NotSerializable, InvalidData, JSON_SERIALIZER, AST_SERIALIZER

_json_allowed_types = {
    "dict": "object",
    "list": "array", "tuple": "array",
    "str": "string", "unicode": "string",
    "int": "number", "long": "number",
    "float": "real",
    "bool": "boolean",
    "NoneType": "null",  # NoneType can't be updated. Avoid using it
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
    "NoneType",  # NoneType can't be updated. Avoid using it
]


def _is_instance_of_class(var):
    return (hasattr(var, "__dict__") or hasattr(var, "__slots__")) and \
           not inspect.isroutine(var) and \
           not inspect.isclass(var) and \
           not inspect.ismodule(var)


def _type_string(var):
    return var.__class__.__name__


class InspectedPacket(Packet):
    """
    Inspected packet class
    """

    def __generate_dict(self, obj):
        _dict = {}
        for attribute in self._get_attributes(obj):
            value = getattr(obj, attribute)
            t = _type_string(value)
            if (self.packet_serializer == JSON_SERIALIZER and t in _json_allowed_types) or (
                    self.packet_serializer == AST_SERIALIZER and t in _ast_allowed_types):
                _dict[attribute] = value
            elif _is_instance_of_class(value):
                _dict[attribute] = self.__generate_dict(value)
            else:
                raise NotSerializable("Attribute type not supported: '%s'" % t)
        return _dict

    def _generate_dict(self):
        """
        Return packet as a dictionary

        :return: dict
        """
        return self.__generate_dict(self)

    def __check_dict(self, obj, data):
        if not isinstance(data, dict):
            raise InvalidData("Expected dictionary data")
        attributes = self._get_attributes(obj)
        if attributes != set(data):
            raise InvalidData("Attributes do not match")
        for attribute in attributes:
            value = getattr(obj, attribute)
            type1 = _type_string(value)
            type2 = _type_string(data[attribute])
            if self.packet_serializer == JSON_SERIALIZER and type1 in _json_allowed_types:
                if type2 not in _json_allowed_types or _json_allowed_types[type1] != _json_allowed_types[type2]:
                    raise InvalidData("JSON types not matching. Got '%s' but expected '%s'" % (type2, type1))
            elif self.packet_serializer == AST_SERIALIZER and type1 in _ast_allowed_types:
                if type1 != type2:
                    raise InvalidData("AST types not matching. Got '%s' but expected '%s'" % (type2, type1))
            elif _is_instance_of_class(value):
                if type2 != "dict":
                    raise InvalidData("Expected dictionary data for attribute '%s'" % attribute)
                self.__check_dict(value, data[attribute])
            else:
                raise InvalidData("Attribute type not supported: '%s'" % type1)

    def __update_dict(self, obj, data):
        for attribute in self._get_attributes(obj):
            value = getattr(obj, attribute)
            t = _type_string(value)
            if (self.packet_serializer == JSON_SERIALIZER and t in _json_allowed_types) or (
                    self.packet_serializer == AST_SERIALIZER and t in _ast_allowed_types):
                obj.__setattr__(attribute, data[attribute])
            else:
                self.__update_dict(value, data[attribute])

    def _update_dict(self, data):
        """
        Update packet dictionary with the given data.

        :param data: dict, new data
        :return: None
        """
        self.__check_dict(self, data)
        self.__update_dict(self, data)


class InspectedSafePacket(InspectedPacket, SafePacket):
    """
    Inspected and safe packet class
    """
