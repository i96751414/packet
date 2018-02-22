#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys

sys.path.insert(0, os.path.dirname((os.path.dirname(__file__))))

import pytest
import packet
import math

try:
    from dataset import *
except ImportError:
    from .dataset import *


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


def test_ast_packet():
    packet1 = ASTTestPacket()
    packet2 = ASTTestPacket()

    # Modify values
    modify_ast_test_packet(packet1)

    packet2.loads(packet1.dumps())

    check_ast_test_packet(packet1, packet2)


def test_json_packet():
    packet1 = JSONTestPacket()
    packet2 = JSONTestPacket()

    # Modify values
    modify_json_test_packet(packet1)

    packet2.loads(packet1.dumps())

    check_json_test_packets(packet1, packet2)


if __name__ == "__main__":
    pytest.main(sys.argv)
