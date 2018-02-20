#!/usr/bin/python
# -*- coding: UTF-8 -*-

import types
import inspect
from .basepacket import Packet
from .safepacket import SafePacket
from .utils import NotSerializable, InvalidData, JSON_SERIALIZER, AST_SERIALIZER
from ._compat import PY_VERSION

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
    "str", "unicode",
    "bytes",
    "int", "long",
    "float",
    "complex",
    "bool",
    "NoneType",  # NoneType can't be updated. Avoid using it
]

if PY_VERSION >= (3, 2):
    # Empty sets are not allowed. Sets are allowed since Python 3.2
    _ast_allowed_types.append("set")

FLOAT_P_INF = "Infinity"
FLOAT_N_INF = "-Infinity"
FLOAT_NAN = "NaN"


def _is_instance_of_class(obj):
    """
    Check if object is instance of class.

    :param obj: object to check
    :return: bool, is instance of class
    """
    return (hasattr(obj, "__dict__") or hasattr(obj, "__slots__")) and not inspect.isroutine(
        obj) and not inspect.isclass(obj) and not inspect.ismodule(obj)


def _can_be_reduced(obj):
    """
    Check if object can be reduced and used in InspectedPacket.

    :param obj: object to check
    :return: bool, can be reduced
    """
    try:
        reduce = obj.__reduce__()
    except AttributeError:
        return False
    return isinstance(reduce, tuple) and 2 <= len(reduce) <= 5 and reduce[0] == obj.__class__


def _get_reduced(obj):
    """
    Get result of __reduced__() method from obj converting generators to tuples.

    :param obj: object to get __reduced__() from
    :return: tuple
    """
    reduced = list(obj.__reduce__())
    for i in range(3, len(reduced)):
        if isinstance(reduced[i], types.GeneratorType):
            reduced[i] = tuple(reduced[i])
    return tuple(reduced)


def _obj_from_reduce(cls, args, state=None, list_items=None, dict_items=None):
    """
    Get instance of cls with specified parameters.

    :param cls: A callable object that will be called to create the initial
    version of the object.

    :param args: A tuple of arguments for the callable object. An empty tuple
    must be given if the callable does not accept any argument.

    :param state: The object’s state, which will be passed to the object’s
    __setstate__() method. If the object has no such method then, the value
    must be a dictionary and it will be added to the object’s __dict__ attribute.

    :param list_items: A sequence of successive items. These items will be
    appended to the object using obj.append(item). This is primarily used for
    list subclasses, but may be used by other classes as long as they have the
    append() method with the appropriate signature.

    :param dict_items: A sequence of successive key-value pairs. These items will
    be stored to the object using obj[key] = value. This is primarily used for
    dictionary subclasses, but may be used by other classes as long as they
    implement __setitem__().

    :return: object
    """
    obj = cls(*args)

    if state is not None:
        if hasattr(obj, "__setstate__"):
            obj.__setstate__(state)
        else:
            obj.__dict__.update(state)

    if list_items is not None:
        for item in list_items:
            obj.append(item)

    if dict_items is not None:
        for k, v in dict_items:
            obj[k] = v

    return obj


def _type_string(var):
    """
    Get the type of var as string.

    :param var: variable to check
    :return: str, type of var
    """
    return var.__class__.__name__


def _encode_ast_float(value):
    if value == float("inf"):
        return FLOAT_P_INF
    elif value == float("-inf"):
        return FLOAT_N_INF
    elif value == float("nan"):
        return FLOAT_NAN
    else:
        return value


def _decode_ast_float(value):
    if isinstance(value, str):
        if value == FLOAT_P_INF:
            return float("inf")
        elif value == FLOAT_N_INF:
            return float("-inf")
        else:
            return float("nan")
    return value


def _check_ast_float(attribute, value):
    if isinstance(value, float) or (isinstance(value, str) and value in [FLOAT_P_INF, FLOAT_N_INF, FLOAT_NAN]):
        return
    raise InvalidData("AST types not matching. Got '%s' but expected 'float' for attribute %s" % (
        _type_string(value), attribute))


class InspectedPacket(Packet):
    """
    Inspected packet class
    """

    def __generate_dict(self, obj):
        _dict = {}
        for attribute in self._get_attributes(obj):
            value = getattr(obj, attribute)
            t = _type_string(value)

            if self.packet_serializer == JSON_SERIALIZER and t in _json_allowed_types:
                _dict[attribute] = value

            elif self.packet_serializer == AST_SERIALIZER and t in _ast_allowed_types:
                if t == "float":
                    _dict[attribute] = _encode_ast_float(value)
                else:
                    _dict[attribute] = value

            elif _is_instance_of_class(value):
                _dict[attribute] = self.__generate_dict(value)

            elif _can_be_reduced(value):
                _dict[attribute] = _get_reduced(value)[1:]

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
                    raise InvalidData("JSON types not matching. Got '%s' but expected '%s' for attribute %s" % (
                        type2, type1, attribute))

            elif self.packet_serializer == AST_SERIALIZER and type1 in _ast_allowed_types:
                if type1 == "float":
                    _check_ast_float(attribute, data[attribute])
                elif type1 != type2:
                    raise InvalidData("AST types not matching. Got '%s' but expected '%s' for attribute %s" % (
                        type2, type1, attribute))

            elif _is_instance_of_class(value):
                if type2 != "dict":
                    raise InvalidData("Expected dictionary data for attribute '%s'" % attribute)
                self.__check_dict(value, data[attribute])

            elif _can_be_reduced(value):
                if type2 != "list" and type2 != "tuple":
                    raise InvalidData("Expected list/tuple for attribute '%s'" % attribute)
                try:
                    _obj_from_reduce(value.__class__, *data[attribute])
                except Exception as e:
                    raise InvalidData(e)

            else:
                raise InvalidData("Type of attribute '%s' is not supported: '%s'" % (attribute, type1))

    def __update_dict(self, obj, data):
        for attribute in self._get_attributes(obj):
            value = getattr(obj, attribute)
            t = _type_string(value)

            if self.packet_serializer == JSON_SERIALIZER and t in _json_allowed_types:
                setattr(obj, attribute, data[attribute])
            elif self.packet_serializer == AST_SERIALIZER and t in _ast_allowed_types:
                if t == "float":
                    setattr(obj, attribute, _decode_ast_float(data[attribute]))
                else:
                    setattr(obj, attribute, data[attribute])
            elif _is_instance_of_class(value):
                self.__update_dict(value, data[attribute])
            else:
                setattr(obj, attribute, _obj_from_reduce(value.__class__, *data[attribute]))

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
