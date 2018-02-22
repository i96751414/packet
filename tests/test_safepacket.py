#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys

sys.path.insert(0, os.path.dirname((os.path.dirname(__file__))))

import math
import pytest
import packet
import collections

try:
    from dataset import *
except ImportError:
    from .dataset import *


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


class ASTTestSafePacket(ASTTestPacket, packet.SafePacket):
    pass


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
        modify_ast_test_packet(packet1)

        dump = packet1.dumps()
        for key in packet1.__dict__.keys():
            assert key.encode() not in dump
        assert is_encrypted(dump)
        packet2.loads(dump)

        check_ast_test_packet(packet1, packet2)


if __name__ == "__main__":
    pytest.main(sys.argv)
