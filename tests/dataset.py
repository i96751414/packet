#!/usr/bin/python
# -*- coding: UTF-8 -*-

import packet
from packet._compat import PY2

__all__ = ["ASTTestPacket", "JSONTestPacket", "check_json_test_packets", "check_ast_test_packet",
           "modify_ast_test_packet", "modify_json_test_packet"]

if not PY2:
    unicode = str
    long = int
    __all__.extend(["unicode", "long"])


class ASTTestPacket(packet.Packet):
    packet_serializer = packet.AST_SERIALIZER

    def __init__(self):
        self.dict = dict()
        self.list = list()
        self.tuple = tuple()
        self.set = set()
        self.str = str()
        self.unicode = unicode()
        self.bytes = bytes()
        self.int = int()
        self.long = long()
        self.float = float()
        self.complex = complex()
        self.bool = bool()
        self.none = None


def check_ast_test_packet(packet1, packet2):
    assert packet1.dict == packet2.dict
    assert packet1.list == packet2.list
    assert packet1.tuple == packet2.tuple
    assert packet1.set == packet2.set
    assert packet1.str == packet2.str
    assert packet1.unicode == packet2.unicode
    assert packet1.bytes == packet2.bytes
    assert packet1.int == packet2.int
    assert packet1.long == packet2.long
    assert packet1.float == packet2.float
    assert packet1.complex == packet2.complex
    assert packet1.bool == packet2.bool
    assert packet1.none == packet2.none


def modify_ast_test_packet(packet1):
    packet1.dict = {"key": "value"}
    packet1.list = [1, 2, 3]
    packet1.tuple = (1, 2, 3)
    packet1.set = {1, 2, 3}
    packet1.str = "123"
    packet1.unicode = unicode("123")
    packet1.bytes = b"123"
    packet1.int = 123
    packet1.long = long(123)
    packet1.float = float(1.23)
    packet1.complex = 1 + 23j
    packet1.bool = True
    packet1.none = None


class JSONTestPacket(packet.Packet):
    packet_serializer = packet.JSON_SERIALIZER

    def __init__(self):
        self.dict = dict()
        self.list = list()
        self.tuple = tuple()
        self.str = str()
        self.unicode = unicode()
        self.int = int()
        self.long = long()
        self.float = float()
        self.bool = bool()
        self.none = None


def check_json_test_packets(packet1, packet2):
    assert packet1.dict == packet2.dict
    assert packet1.list == packet2.list
    assert list(packet1.tuple) == packet2.tuple
    assert packet1.str == packet2.str
    assert packet1.unicode == packet2.unicode
    assert packet1.int == packet2.int
    assert packet1.long == packet2.long
    assert packet1.float == packet2.float
    assert packet1.bool == packet2.bool
    assert packet1.none == packet2.none


def modify_json_test_packet(packet1):
    packet1.dict = {"key": "value"}
    packet1.list = [1, 2, 3]
    packet1.tuple = (1, 2, 3)
    packet1.str = "123"
    packet1.unicode = unicode("123")
    packet1.int = 123
    packet1.long = long(123)
    packet1.float = float(1.23)
    packet1.bool = True
    packet1.none = None
