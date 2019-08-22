#!/usr/bin/python
# -*- coding: UTF-8 -*-

import json
import threading
from ast import Str, Num, Tuple, List, Set, Dict, Name, UnaryOp, UAdd, \
    USub, BinOp, Add, Sub, Call
# AST necessary imports
from ast import parse, Expression

from packet._compat import get_items, string_types, with_metaclass
from packet.utils import JSON_SERIALIZER, AST_SERIALIZER
from packet.utils import UnknownPacket, InvalidData, NotSerializable

try:
    from ast import Constant
except ImportError:
    class Constant(object):
        value = None

try:
    from ast import NameConstant
except ImportError:
    class NameConstant(object):
        value = None

try:
    from ast import Bytes
except ImportError:
    class Bytes(object):
        s = None

_NUM_TYPES = (int, float, complex)

# None, True and False are treated as Names in Python 2+
_SAFE_NAMES = {
    "None": None, "True": True, "False": False,
    "inf": float("inf"), "nan": float("nan"),
    "infj": complex("infj"), "nanj": complex("nanj"),
}

_SAFE_CALLS = {
    "set": set,
}


def safe_eval(node_or_string):
    """
    Safely evaluate an expression node or a string containing a Python
    expression. The string or node provided may only consist of the following
    Python literal structures: strings, bytes, numbers, tuples, lists, dicts,
    sets, booleans, and None.

    Note: This is a modified version of the ast.literal_eval function from
    Python 3.6

    :type node_or_string: str, node
    :param node_or_string: expression string or node
    :return: evaluated
    """
    if isinstance(node_or_string, string_types):
        node_or_string = parse(node_or_string, mode="eval")
    if isinstance(node_or_string, Expression):
        node_or_string = node_or_string.body

    def _convert(node):
        if isinstance(node, Constant):
            return node.value
        elif isinstance(node, (Str, Bytes)):
            return node.s
        elif isinstance(node, Num):
            return node.n
        elif isinstance(node, Tuple):
            return tuple(map(_convert, node.elts))
        elif isinstance(node, List):
            return list(map(_convert, node.elts))
        elif isinstance(node, Set):
            return set(map(_convert, node.elts))
        elif isinstance(node, Dict):
            return dict((_convert(k), _convert(v)) for k, v
                        in zip(node.keys, node.values))
        elif isinstance(node, Name):
            if node.id in _SAFE_NAMES:
                return _SAFE_NAMES[node.id]
        elif isinstance(node, NameConstant):
            return node.value
        elif isinstance(node, Call):
            if node.func.id in _SAFE_CALLS:
                args = [_convert(arg) for arg in node.args]
                return _SAFE_CALLS[node.func.id](*args)
        elif isinstance(node, UnaryOp) and isinstance(node.op, (UAdd, USub)):
            operand = _convert(node.operand)
            if isinstance(operand, _NUM_TYPES):
                if isinstance(node.op, UAdd):
                    return + operand
                else:
                    return - operand
        elif isinstance(node, BinOp) and isinstance(node.op, (Add, Sub)):
            left = _convert(node.left)
            right = _convert(node.right)
            if isinstance(left, _NUM_TYPES) and isinstance(right, _NUM_TYPES):
                if isinstance(node.op, Add):
                    return left + right
                else:
                    return left - right
        raise ValueError("malformed node or string: {}".format(repr(node)))

    return _convert(node_or_string)


def set_json_serializer():
    """
    Set JSON_SERIALIZER as the serializer to be used in all packets.
    Same as set_packet_serializer(JSON_SERIALIZER).

    :return: None
    """
    Packet.packet_serializer = JSON_SERIALIZER


def set_ast_serializer():
    """
    Set AST_SERIALIZER as the serializer to be used in all packets.
    Same as set_packet_serializer(AST_SERIALIZER).

    :return: None
    """
    Packet.packet_serializer = AST_SERIALIZER


def set_packet_serializer(serializer):
    """
    Set serializer to be used in all packets.
    Serializer must be either JSON_SERIALIZER or AST_SERIALIZER.

    :param serializer: int, Serializer to use
    :return: None
    """
    if not isinstance(serializer, int) or (
            serializer != JSON_SERIALIZER and serializer != AST_SERIALIZER):
        raise ValueError("Unknown serializer")
    Packet.packet_serializer = serializer


def _check_dict_keys(obj):
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
            _check_dict_keys(v)


class _PacketMetaClass(type):
    """
    MetaClass to be used in Packet in order to set _INITIALISED flag
    after __init__ is called
    """

    def __call__(cls, *args, **kwargs):
        self = super(_PacketMetaClass, cls).__call__(*args, **kwargs)
        object.__setattr__(self, "_packet_initialised", True)
        return self


# noinspection PyCallByClass
class Packet(with_metaclass(_PacketMetaClass, object)):
    """
    General packet class. This is the main "Packet" class.
    Every packet classes should inherit from this one.
    """

    packet_serializer = JSON_SERIALIZER

    __slots__ = ["_packet_lock", "_packet_initialised"]

    def __new__(cls, *args, **kwargs):
        self = super(Packet, cls).__new__(cls, *args, **kwargs)
        object.__setattr__(self, "_packet_lock", threading.RLock())
        object.__setattr__(self, "_packet_initialised", False)
        return self

    @property
    def __tag__(self):
        """
        Tag of current packet. This must be equal for all instances
        sharing data.

        :return: str
        """
        return self.__class__.__name__

    @staticmethod
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
        if isinstance(obj, Packet):
            for a in Packet.__slots__:
                if a in attributes:
                    attributes.remove(a)
        return attributes

    def _generate_dict(self):
        """
        Return packet as a dictionary

        :return: dict
        """
        return {attribute: getattr(self, attribute) for attribute in self._get_attributes(self)}

    def dump(self, fp):
        """
        Serialize packet object to fp (a .write()-supporting file-like object).
        Raises NotSerializable if the packet is not serializable.

        :param fp: file-like object
        :return: None
        """
        fp.write(self.dumps())

    def dumps(self):
        """
        Serialize packet object to string using the packet name as the tag.
        Raises NotSerializable if the packet is not serializable.

        :return: bytes
        """

        with self._packet_lock:
            _data = self._generate_dict()

        if self.packet_serializer == AST_SERIALIZER:
            try:
                data = repr({self.__tag__: _data})
                safe_eval(data)
            except ValueError as e:
                raise NotSerializable(e)
        else:
            try:
                _check_dict_keys(_data)
                data = json.dumps({self.__tag__: _data})
            except TypeError as e:
                raise NotSerializable(e)
        return data.encode()

    def _update_dict(self, data):
        """
        Update packet dictionary with the given data.

        :param data: dict, new data
        :return: None
        """
        if not isinstance(data, dict):
            raise InvalidData("Expected dictionary data")
        if set(data) != self._get_attributes(self):
            raise InvalidData("Attributes do not match")
        for k, v in get_items(data):
            object.__setattr__(self, k, v)

    def load(self, fp):
        """
        Deserialize data from fp (a .read()-supporting file-like object) and
        update packet object.
        Raises UnknownPacket or InvalidData if the data is not deserializable.

        :param fp: file-like object
        :return: None
        """
        self.loads(fp.read())

    def loads(self, data):
        """
        Deserialize data and update packet object.
        Raises UnknownPacket or InvalidData if the data is not deserializable.

        :param data: bytes/str
        :return: None
        """
        with self._packet_lock:
            tag = self.__tag__
            try:
                if isinstance(data, bytes):
                    data = data.decode()
                if self.packet_serializer == AST_SERIALIZER:
                    _data = safe_eval(data)
                else:
                    _data = json.loads(data)
            except Exception as e:
                raise UnknownPacket(e)
            if not isinstance(_data, dict):
                raise UnknownPacket("Expected dictionary data")
            if tag not in _data:
                raise InvalidData("Expected data with tag '{}'".format(tag))

            self._update_dict(_data[tag])

    def receive_from(self, conn, buffer_size=512):
        """
        Receive data from a connection conn (typically a socket connection)
        by doing conn.recv(buffer_size) and loads the received data into the
        packet. If there is an error loading data or no data is obtained,
        returns False, otherwise returns True.

        :param conn: Socket connection
        :param buffer_size: int, Socket buffer size
        :return: bool, Success
        """
        if conn is None:
            return False
        data = conn.recv(buffer_size)
        if not data:
            return False
        try:
            self.loads(data)
        except (UnknownPacket, InvalidData):
            return False
        return True

    def send_to(self, conn):
        """
        Send data to a connection conn (typically a socket connection).
        If no connection, returns None, otherwise returns the same as
        conn.send(data).

        :param conn: Socket connection
        :return: int, Bytes sent
        """
        if conn is None:
            return None
        return conn.send(self.dumps())

    def __setattr__(self, name, value):
        """
        Set attribute in a Packet instance.

        :param name: str, name of attribute to set
        :param value: obj, value of attribute to set
        :return: None
        """
        if name in Packet.__slots__:
            raise AttributeError("'{}' is not a valid attribute name")

        if (self._packet_initialised and name not in self._get_attributes(self) and
                not isinstance(getattr(self.__class__, name, None), property)):
            raise AttributeError("'{}' is not an attribute of '{}' packet".format(name, self.__class__.__name__))

        with self._packet_lock:
            object.__setattr__(self, name, value)

    def __delattr__(self, item):
        raise AttributeError("Can't delete {}".format(item))
