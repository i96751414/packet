#!/usr/bin/python
# -*- coding: UTF-8 -*-

import json
import types

from packet._compat import string_types, get_items
from packet.evaluate import safe_eval
from packet.utils import NotSerializable, InvalidData


def _type_string(var):
    """
    Get the type of var as string.

    :param var: variable to check
    :return: str, type of var
    """
    return var.__class__.__name__


def _is_instance_of_class(obj):
    """
    Check if object is instance of class.

    :param obj: object to check
    :return: bool, is instance of class
    """
    return (hasattr(obj, "__dict__") or hasattr(obj, "__slots__")) and not isinstance(
        obj, (type, types.BuiltinFunctionType, types.FunctionType, types.MethodType, types.ModuleType))


def _can_be_reduced(obj):
    """
    Check if object can be reduced and used in InspectedPacket.

    :param obj: object to check
    :return: bool, can be reduced
    """
    try:
        reduced = obj.__reduce__()
    except AttributeError:
        return False
    return (isinstance(reduced, tuple) and 2 <= len(reduced) <= 5 and
            reduced[0] == obj.__class__)


def _get_reduced(obj):
    """
    Get result of __reduced__() method from obj converting generators
    to tuples.

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
    must be a dictionary and it will be added to the object’s __dict__
    attribute.

    :param list_items: A sequence of successive items. These items will be
    appended to the object using obj.append(item). This is primarily used for
    list subclasses, but may be used by other classes as long as they have the
    append() method with the appropriate signature.

    :param dict_items: A sequence of successive key-value pairs. These items
    will be stored to the object using obj[key] = value. This is primarily
    used for dictionary subclasses, but may be used by other classes as long
    as they implement __setitem__().

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


class _Serializable(object):
    __slots__ = ["_packet_lock", "_packet_initialised", "_packet_serializer"]


def _get_attributes(obj):
    """
    Get all the attributes of a given object as a set.

    :param obj: object to check attributes
    :type obj: object
    :return: tuple, attributes
    """
    attributes = {slot for cls in (getattr(obj.__class__, "__mro__", ()))
                  for slot in getattr(cls, "__slots__", ()) if hasattr(obj, slot)}
    attributes.update(getattr(obj, "__dict__", {}))
    if isinstance(obj, _Serializable):
        for a in _Serializable.__slots__:
            if a in attributes:
                attributes.remove(a)
    return attributes


class _Serializer(object):
    def __init__(self, allowed_types):
        self._allowed_types = allowed_types

    def dumps(self, data):
        raise NotImplementedError("abstract methods must be implemented")

    def loads(self, data):
        raise NotImplementedError("abstract methods must be implemented")

    def is_serializable(self, data_type):
        return data_type in self._allowed_types

    def verify_data_types(self, expected, data_type):
        raise NotImplementedError("abstract methods must be implemented")

    def serialize_object(self, obj):
        _dict = {}
        for attribute in _get_attributes(obj):
            value = getattr(obj, attribute)
            t = _type_string(value)
            if self.is_serializable(t):
                _dict[attribute] = value
            elif _is_instance_of_class(value):
                _dict[attribute] = self.serialize_object(value)
            elif _can_be_reduced(value):
                _dict[attribute] = _get_reduced(value)[1:]
            else:
                raise NotSerializable("Attribute type not supported: '{}'".format(t))
        return _dict

    def deserialize_object(self, obj, data):
        self._is_deserializable(obj, data)
        self._deserialize_object(obj, data)

    def _is_deserializable(self, obj, data):
        if not isinstance(data, dict):
            raise InvalidData("Expected dictionary data")
        attributes = _get_attributes(obj)
        if attributes != set(data):
            raise InvalidData("Attributes do not match")
        for attribute in attributes:
            value = getattr(obj, attribute)
            type1 = _type_string(value)
            type2 = _type_string(data[attribute])

            if self.verify_data_types(type1, type2):
                continue

            elif _is_instance_of_class(value):
                if type2 != "dict":
                    raise InvalidData("Expected dictionary data for attribute '{}'".format(attribute))
                self._is_deserializable(value, data[attribute])

            elif _can_be_reduced(value):
                if type2 != "list" and type2 != "tuple":
                    raise InvalidData("Expected list/tuple for attribute '{}'".format(attribute))
                try:
                    _obj_from_reduce(value.__class__, *data[attribute])
                except Exception as e:
                    raise InvalidData(e)

            else:
                raise InvalidData("Attribute type not supported: '{}'".format(type1))

    def _deserialize_object(self, obj, data):
        _setattr = object.__setattr__ if isinstance(obj, _Serializable) else setattr

        for attribute in _get_attributes(obj):
            value = getattr(obj, attribute)
            t = _type_string(value)

            if self.is_serializable(t):
                _setattr(obj, attribute, data[attribute])
            elif _is_instance_of_class(value):
                self._deserialize_object(value, data[attribute])
            else:
                _setattr(obj, attribute, _obj_from_reduce(value.__class__, *data[attribute]))


class _AstSerializer(_Serializer):
    def dumps(self, data):
        try:
            data = repr(data)
            safe_eval(data)
        except ValueError as e:
            raise NotSerializable(e)
        return data.encode()

    def loads(self, data):
        if isinstance(data, bytes):
            data = data.decode()
        return safe_eval(data)

    def verify_data_types(self, expected, data_type):
        if expected in self._allowed_types:
            if expected != data_type:
                raise InvalidData("AST types not matching. Got '{}' but expected '{}'".format(data_type, expected))
            return True
        return False


class _JsonSerializer(_Serializer):
    def dumps(self, data):
        try:
            self._check_dict_keys(data)
            data = json.dumps(data)
        except TypeError as e:
            raise NotSerializable(e)
        return data.encode()

    def loads(self, data):
        if isinstance(data, bytes):
            data = data.decode()
        return json.loads(data)

    def verify_data_types(self, expected, data_type):
        if expected in self._allowed_types:
            if data_type not in self._allowed_types or self._allowed_types[expected] != self._allowed_types[data_type]:
                raise InvalidData("JSON types not matching. Got '{}' but expected '{}'".format(data_type, expected))
            return True
        return False

    def _check_dict_keys(self, obj):
        """
        Check if all obj keys are strings, so it can be json serialized.
        If one of the keys is not string, raise TypeError.

        :param obj: dict, Dict to verify
        :return: None
        """

        for k, v in get_items(obj):
            if not isinstance(k, string_types):
                raise TypeError("Only string keys are allowed in Packet dicts")
            if isinstance(v, dict):
                self._check_dict_keys(v)


ast_serializer = _AstSerializer([
    "dict",
    "list", "tuple",
    "set",
    "str", "unicode",
    "bytes",
    "int", "long",
    "float",
    "complex",
    "bool",
    "NoneType",  # NoneType can't be updated. Avoid using it
])

json_serializer = _JsonSerializer({
    "dict": "object",
    "list": "array", "tuple": "array",
    "str": "string", "unicode": "string",
    "int": "number", "long": "number",
    "float": "real",
    "bool": "boolean",
    "NoneType": "null",  # NoneType can't be updated. Avoid using it
})
