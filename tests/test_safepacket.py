#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys

sys.path.insert(0, os.path.dirname((os.path.dirname(__file__))))

import math
import pytest
import packet
import collections
from packet._compat import PY2

if not PY2:
    unicode = str
    long = int


def test_set_cbc_mode():
    packet.SafePacket.encryption_mode = None
    packet.set_cbc_mode()
    assert packet.SafePacket.encryption_mode == packet.CBC_MODE

    packet.SafePacket.encryption_mode = None
    packet.set_packet_encryption_mode(packet.CBC_MODE)
    assert packet.SafePacket.encryption_mode == packet.CBC_MODE


def test_set_ctr_mode():
    packet.SafePacket.encryption_mode = None
    packet.set_ctr_mode()
    assert packet.SafePacket.encryption_mode == packet.CTR_MODE

    packet.SafePacket.encryption_mode = None
    packet.set_packet_encryption_mode(packet.CTR_MODE)
    assert packet.SafePacket.encryption_mode == packet.CTR_MODE


def test_set_packet_encryption_key():
    key = "key"
    packet.SafePacket.encryption_key = None
    packet.set_packet_encryption_key(key)
    assert packet.SafePacket.encryption_key == key


class ASTTestSafePacket(packet.SafePacket):
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


def is_encrypted(text):
    scores = collections.defaultdict(lambda: 0)
    for letter in text:
        scores[letter] += 1
    largest = max(scores.values())
    average = len(text) / 256.0
    return largest < average + 5 * math.sqrt(average)


def test_safe_packet():
    packet.set_packet_encryption_key("key")
    for mode in [packet.CBC_MODE, packet.CTR_MODE]:
        packet.set_packet_encryption_mode(mode)

        packet1 = ASTTestSafePacket()
        packet2 = ASTTestSafePacket()

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

        dump = packet1.dumps()
        for key in packet1.__dict__.keys():
            assert key.encode() not in dump
        assert is_encrypted(dump)
        packet2.loads(dump)

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


if __name__ == "__main__":
    pytest.main(sys.argv)
