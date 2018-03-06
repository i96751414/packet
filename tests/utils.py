#!/usr/bin/python
# -*- coding: UTF-8 -*-

import packet
# noinspection PyProtectedMember
from packet._compat import PY2

if PY2:
    # noinspection PyUnresolvedReferences
    Unicode = unicode  # NOQA
    # noinspection PyUnresolvedReferences
    Long = long  # NOQA
else:
    Unicode = str
    Long = int


def check_encrypted(data):
    assert b"dict" not in data
    assert b"list" not in data
    assert b"tuple" not in data
    assert b"str" not in data
    assert b"unicode" not in data
    assert b"int" not in data
    assert b"long" not in data
    assert b"float" not in data
    assert b"bool" not in data
    assert b"none" not in data
    assert b"_protected" not in data
    assert b"__private" not in data
    assert b"set" not in data
    assert b"bytes" not in data
    assert b"complex" not in data


class JSONTestPacket(packet.Packet):
    packet_serializer = packet.JSON_SERIALIZER

    def __init__(self):
        self.dict = dict()
        self.list = list()
        self.tuple = tuple()
        self.str = str()
        self.unicode = Unicode()
        self.int = int()
        self.long = Long()
        self.float = float()
        self.bool = bool()
        self.none = None
        self._protected = int()
        self.__private = int()

    @property
    def protected(self):
        return self._protected

    @protected.setter
    def protected(self, value):
        self._protected = value

    @property
    def private(self):
        return self.__private

    @private.setter
    def private(self, value):
        self.__private = value


def check_json_test_packets(packet1, packet2):
    assert packet1.dict == packet2.dict
    assert packet1.list == packet2.list
    assert list(packet1.tuple) == list(packet2.tuple)
    assert packet1.str == packet2.str
    assert packet1.unicode == packet2.unicode
    assert packet1.int == packet2.int
    assert packet1.long == packet2.long
    assert packet1.float == packet2.float
    assert packet1.bool == packet2.bool
    assert packet1.none == packet2.none
    assert packet1.protected == packet2.protected
    assert packet1.private == packet2.private


def modify_json_test_packet(packet1):
    packet1.dict = {"key": "value"}
    packet1.list = [1, 2, 3]
    packet1.tuple = (1, 2, 3)
    packet1.str = "123"
    packet1.unicode = Unicode("123")
    packet1.int = 123
    packet1.long = Long(123)
    packet1.float = float(1.23)
    packet1.bool = True
    packet1.none = None
    packet1.protected = 456
    packet1.private = 789


class ASTTestPacket(JSONTestPacket):
    packet_serializer = packet.AST_SERIALIZER

    def __init__(self):
        super(ASTTestPacket, self).__init__()

        self.set = set()
        self.bytes = bytes()
        self.complex = complex()


def check_ast_test_packet(packet1, packet2):
    check_json_test_packets(packet1, packet2)

    assert packet1.tuple == packet2.tuple
    assert packet1.set == packet2.set
    assert packet1.bytes == packet2.bytes
    assert packet1.complex == packet2.complex


def modify_ast_test_packet(packet1):
    modify_json_test_packet(packet1)

    packet1.set = {1, 2, 3}
    packet1.bytes = b"123"
    packet1.complex = 1 + 23j
