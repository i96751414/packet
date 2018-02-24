#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
import pytest
import datetime

sys.path.insert(0, os.path.dirname((os.path.dirname(__file__))))

import packet

try:
    from utils import *
except ImportError:
    from .utils import *


class ASTTestInspectedPacket2(packet.InspectedPacket):
    def __init__(self):
        self.a = "a"
        self.b = "b"
        self.c = "c"


class ASTTestInspectedPacket1(ASTTestPacket, packet.InspectedPacket):
    def __init__(self):
        super(ASTTestInspectedPacket1, self).__init__()
        self.inner = ASTTestInspectedPacket2()
        self.datetime = datetime.datetime(2000, 1, 1)


def modify_inspected_ast_test_packets(packet1):
    modify_ast_test_packet(packet1)

    packet1.inner.a = "A"
    packet1.inner.b = "B"
    packet1.inner.c = "C"

    packet1.datetime = datetime.datetime.now()


def check_inspected_ast_test_packets(packet1, packet2):
    check_ast_test_packet(packet1, packet2)

    assert packet1.inner.a == packet2.inner.a
    assert packet1.inner.b == packet2.inner.b
    assert packet1.inner.c == packet2.inner.c

    assert packet1.datetime == packet2.datetime


def test_inspected_packet():
    packet1 = ASTTestInspectedPacket1()
    packet2 = ASTTestInspectedPacket1()

    # Modify values
    modify_inspected_ast_test_packets(packet1)

    packet2.loads(packet1.dumps())

    check_inspected_ast_test_packets(packet1, packet2)


class ASTTestInspectedSafePacket(ASTTestInspectedPacket1, packet.InspectedSafePacket):
    pass


def test_inspected_safe_packet():
    packet.set_packet_encryption_key("key")

    packet1 = ASTTestInspectedSafePacket()
    packet2 = ASTTestInspectedSafePacket()

    # Modify values
    modify_inspected_ast_test_packets(packet1)

    dump = packet1.dumps()
    assert is_encrypted(dump)
    packet2.loads(dump)

    check_inspected_ast_test_packets(packet1, packet2)


if __name__ == "__main__":
    pytest.main(sys.argv)
