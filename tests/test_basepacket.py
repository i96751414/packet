#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import sys
import math
import pytest
import threading

sys.path.insert(0, os.path.dirname((os.path.dirname(__file__))))

import packet

try:
    from utils import *
except ImportError:
    from .utils import *


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


def test_undefined_attribute():
    packet1 = JSONTestPacket()
    with pytest.raises(AttributeError):
        packet1.abc = "abc"


class DummyConnection:
    def __init__(self):
        self.__data = None

    def send(self, data):
        self.__data = data
        return len(data)

    def recv(self, buffer_size):
        return self.__data[:buffer_size]


def test_send_to_and_receive_from():
    # Create a dummy connection just for tests
    connection = DummyConnection()

    packet1 = JSONTestPacket()
    packet2 = JSONTestPacket()

    # Modify values
    modify_json_test_packet(packet1)

    # Send packet1 data to packet2
    # Same as packet2.loads(packet1.dumps())
    packet1.send_to(connection)
    packet2.receive_from(connection)

    check_json_test_packets(packet1, packet2)


def test_delattr():
    packet1 = JSONTestPacket()
    with pytest.raises(AttributeError):
        del packet1.tuple


def test_lock_acquire_and_release():
    packet1 = JSONTestPacket()

    # Get lock so we can change values first
    packet1.lock_acquire()

    # Launch thread
    thread = threading.Thread(target=modify_json_test_packet, args=(packet1,))
    thread.start()

    # Modify values
    packet1.str = "one two three"

    # Release lock
    packet1.lock_release()

    # Wait for thread to finish
    thread.join()

    assert packet1.str == "123"


if __name__ == "__main__":
    pytest.main(sys.argv)
