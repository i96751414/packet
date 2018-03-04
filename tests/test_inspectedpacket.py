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


class ASTTestInspectedPacket(ASTTestPacket, packet.InspectedPacket):
    def __init__(self):
        super(ASTTestInspectedPacket, self).__init__()

        self.inner = ASTTestPacket()
        self.datetime = datetime.datetime(2000, 1, 1)


def modify_inspected_ast_test_packets(packet1):
    modify_ast_test_packet(packet1)
    modify_ast_test_packet(packet1.inner)

    packet1.datetime = datetime.datetime.now()


def check_inspected_ast_test_packets(packet1, packet2):
    check_ast_test_packet(packet1, packet2)
    check_ast_test_packet(packet1.inner, packet2.inner)

    assert packet1.datetime == packet2.datetime


def test_inspected_packet():
    packet1 = ASTTestInspectedPacket()
    packet2 = ASTTestInspectedPacket()

    # Modify values
    modify_inspected_ast_test_packets(packet1)

    packet2.loads(packet1.dumps())

    check_inspected_ast_test_packets(packet1, packet2)


class ASTTestInspectedSafePacket(ASTTestInspectedPacket, packet.InspectedSafePacket):
    pass


def test_inspected_safe_packet():
    packet.set_packet_encryption_key("key")

    packet1 = ASTTestInspectedSafePacket()
    packet2 = ASTTestInspectedSafePacket()

    # Modify values
    modify_inspected_ast_test_packets(packet1)

    dump = packet1.dumps()
    check_encrypted(dump)
    packet2.loads(dump)

    check_inspected_ast_test_packets(packet1, packet2)


if __name__ == "__main__":
    pytest.main(sys.argv)
