#!/usr/bin/python
# -*- coding: UTF-8 -*-

import json
import types

from packet._compat import string_types, get_items
from packet.evaluate import safe_eval
from packet.utils import NotSerializable, InvalidData


def _is_instance_of_class(obj):
    """
    Check if object is instance of class.
    :param obj: object to check
    :return: is instance of class
    :rtype bool
    """
    return (hasattr(obj, "__dict__") or hasattr(obj, "__slots__")) and not isinstance(
        obj, (type, types.BuiltinFunctionType, types.FunctionType, types.MethodType, types.ModuleType))


def _can_be_reduced(obj):
    """
    Check if object can be reduced and used in InspectedPacket.
    :param obj: object to check
    :return: can be reduced
    :rtype bool
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
    :rtype: list
    """
    reduced = list(obj.__reduce__())
    for i in range(3, len(reduced)):
        if isinstance(reduced[i], types.GeneratorType):
            reduced[i] = tuple(reduced[i])
    return reduced


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
    :return: attributes
    :rtype: set
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
        self._simple_type = 1
        self._class_type = 2
        self._reduce_type = 3

    def dumps(self, data):
        raise NotImplementedError("abstract methods must be implemented")

    def loads(self, data):
        raise NotImplementedError("abstract methods must be implemented")

    def verify_data_types(self, expected, data_type):
        raise NotImplementedError("abstract methods must be implemented")

    def serialize_object(self, obj):
        if self._is_serializable(obj):
            return {self._simple_type: obj}
        elif _is_instance_of_class(obj):
            return {self._class_type: {attribute: self.serialize_object(getattr(obj, attribute))
                                       for attribute in _get_attributes(obj)}}
        elif _can_be_reduced(obj):
            return {self._reduce_type: _get_reduced(obj)[1:]}

        raise NotSerializable("Attribute type not supported: '{}'".format(obj.__class__.__name__))

    def deserialize_object(self, obj, data):
        self._validate_data(obj, data)
        return self._deserialize_object(obj, data)

    def _is_serializable(self, obj):
        return obj.__class__.__name__ in self._allowed_types

    def _validate_data(self, obj, data):
        if not isinstance(data, dict):
            raise InvalidData("Expected dictionary for data")
        if len(data) != 1:
            raise InvalidData("Malformed dictionary")
        for s_type, serialized in get_items(data):
            if s_type == self._simple_type:
                self.verify_data_types(obj.__class__.__name__, serialized.__class__.__name__)
            elif s_type == self._class_type:
                if not _is_instance_of_class(obj):
                    raise InvalidData("Expected instance of class")
                if not isinstance(serialized, dict):
                    raise InvalidData("Expected dictionary for class")
                attributes = _get_attributes(obj)
                if attributes != set(serialized):
                    raise InvalidData("Attributes do not match")
                for attribute in attributes:
                    self._validate_data(getattr(obj, attribute), serialized[attribute])
            elif s_type == self._reduce_type:
                if not _can_be_reduced(obj):
                    raise InvalidData("Object can not be reduced")
                if not isinstance(serialized, (list, tuple)):
                    raise InvalidData("Expected list/tuple for attribute")
                try:
                    _obj_from_reduce(obj.__class__, *serialized)
                except Exception as e:
                    raise InvalidData(e)
            else:
                raise InvalidData("Unknown serialization type: '{}'".format(s_type))

    def _deserialize_object(self, obj, data):
        for s_type, serialized in get_items(data):
            if s_type == self._simple_type:
                return None if obj is None else obj.__class__(serialized)
            elif s_type == self._class_type:
                _setattr = object.__setattr__ if isinstance(obj, _Serializable) else setattr
                for attribute in _get_attributes(obj):
                    _setattr(obj, attribute, self._deserialize_object(getattr(obj, attribute), serialized[attribute]))
                return obj
            else:
                return _obj_from_reduce(obj.__class__, *serialized)


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
        if expected not in self._allowed_types or expected != data_type:
            raise InvalidData("AST types not matching. Got '{}' but expected '{}'".format(data_type, expected))


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
        if (expected not in self._allowed_types or data_type not in self._allowed_types or
                self._allowed_types[expected] != self._allowed_types[data_type]):
            raise InvalidData("JSON types not matching. Got '{}' but expected '{}'".format(data_type, expected))

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
