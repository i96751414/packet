#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys

sys.path.insert(0, os.path.dirname((os.path.dirname(__file__))))

import pytest
import packet
import math
from packet._compat import PY2

if not PY2:
    unicode = str
    long = int


def test_packet_safe_eval():
    assert packet.safe_eval(repr(dict())) == dict()
    assert packet.safe_eval(repr(list())) == list()
    assert packet.safe_eval(repr(tuple())) == tuple()
    assert packet.safe_eval(repr(set())) == set()
    assert packet.safe_eval(repr(str())) == str()
    assert packet.safe_eval(repr(unicode())) == unicode()
    assert packet.safe_eval(repr(bytes())) == bytes()
    assert packet.safe_eval(repr(int())) == int()
    assert packet.safe_eval(repr(long())) == long()
    assert packet.safe_eval(repr(float())) == float()
    assert packet.safe_eval(repr(complex())) == complex()
    assert packet.safe_eval(repr(bool())) == bool()
    assert packet.safe_eval(repr(None)) is None

    # Test corner cases
    assert packet.safe_eval(repr(float("inf"))) == float("inf")
    assert packet.safe_eval(repr(float("-inf"))) == float("-inf")
    assert math.isnan(packet.safe_eval(repr(float("nan"))))
    assert packet.safe_eval(repr(complex("inf+infj"))) == complex("inf+infj")
    assert packet.safe_eval(repr(complex("inf-infj"))) == complex("inf-infj")


def test_set_json_serializer():
    packet.Packet.packet_serializer = None
    packet.set_json_serializer()
    assert packet.Packet.packet_serializer == packet.JSON_SERIALIZER

    packet.Packet.packet_serializer = None
    packet.set_packet_serializer(packet.JSON_SERIALIZER)
    assert packet.Packet.packet_serializer == packet.JSON_SERIALIZER


def test_set_ast_serializer():
    packet.Packet.packet_serializer = None
    packet.set_ast_serializer()
    assert packet.Packet.packet_serializer == packet.AST_SERIALIZER

    packet.Packet.packet_serializer = None
    packet.set_packet_serializer(packet.AST_SERIALIZER)
    assert packet.Packet.packet_serializer == packet.AST_SERIALIZER


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


def test_ast_packet():
    packet1 = ASTTestPacket()
    packet2 = ASTTestPacket()

    # Modify values
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

    packet2.loads(packet1.dumps())

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


def test_json_packet():
    packet1 = JSONTestPacket()
    packet2 = JSONTestPacket()

    # Modify values
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

    packet2.loads(packet1.dumps())

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


if __name__ == "__main__":
    pytest.main(sys.argv)
