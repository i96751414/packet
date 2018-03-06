#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys
import packet
import pytest
from tests import utils


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


class ASTTestSafePacket(utils.ASTTestPacket, packet.SafePacket):
    pass


def test_safe_packet():
    packet.set_packet_encryption_key("key")
    for mode in [packet.CBC_MODE, packet.CTR_MODE]:
        packet.set_packet_encryption_mode(mode)

        packet1 = ASTTestSafePacket()
        packet2 = ASTTestSafePacket()

        # Modify values
        utils.modify_ast_test_packet(packet1)

        dump = packet1.dumps()
        for key in packet1.__dict__.keys():
            assert key.encode() not in dump
        utils.check_encrypted(dump)
        packet2.loads(dump)

        utils.check_ast_test_packet(packet1, packet2)


def test_fail_decryption():
    packet1 = ASTTestSafePacket()
    packet2 = ASTTestSafePacket()

    # Modify values
    utils.modify_ast_test_packet(packet1)

    packet.set_packet_encryption_key("key1")
    dump = packet1.dumps()

    packet.set_packet_encryption_key("key2")
    with pytest.raises(packet.UnknownPacket):
        packet2.loads(dump)


if __name__ == "__main__":
    pytest.main(sys.argv)
