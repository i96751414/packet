#!/usr/bin/python
# -*- coding: UTF-8 -*-

import math
import sys
import threading

import pytest

import packet
from tests import utils


def test_packet_safe_eval():
    assert packet.safe_eval(repr(dict())) == dict()
    assert packet.safe_eval(repr(list())) == list()
    assert packet.safe_eval(repr(tuple())) == tuple()
    assert packet.safe_eval(repr(set())) == set()
    assert packet.safe_eval(repr(str())) == str()
    assert packet.safe_eval(repr(utils.Unicode())) == utils.Unicode()
    assert packet.safe_eval(repr(bytes())) == bytes()
    assert packet.safe_eval(repr(int())) == int()
    assert packet.safe_eval(repr(utils.Long())) == utils.Long()
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


def test_ast_packet():
    packet1 = utils.ASTTestPacket()
    packet2 = utils.ASTTestPacket()

    # Modify values
    utils.modify_ast_test_packet(packet1)

    packet2.loads(packet1.dumps())

    utils.check_ast_test_packet(packet1, packet2)


def test_json_packet():
    packet1 = utils.JSONTestPacket()
    packet2 = utils.JSONTestPacket()

    # Modify values
    utils.modify_json_test_packet(packet1)

    packet2.loads(packet1.dumps())

    utils.check_json_test_packets(packet1, packet2)


def test_undefined_attribute():
    packet1 = utils.JSONTestPacket()
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

    packet1 = utils.JSONTestPacket()
    packet2 = utils.JSONTestPacket()

    # Modify values
    utils.modify_json_test_packet(packet1)

    # Send packet1 data to packet2
    # Same as packet2.loads(packet1.dumps())
    packet1.send_to(connection)
    packet2.receive_from(connection)

    utils.check_json_test_packets(packet1, packet2)


def test_delattr():
    packet1 = utils.JSONTestPacket()
    with pytest.raises(AttributeError):
        del packet1.tuple


def test_lock_acquire_and_release():
    packet1 = utils.JSONTestPacket()

    # Get lock so we can change values first
    # noinspection PyProtectedMember
    packet1._packet_lock.acquire()

    # Launch thread
    thread = threading.Thread(target=utils.modify_json_test_packet, args=(packet1,))
    thread.start()

    # Modify values
    packet1.str = "one two three"

    # Release lock
    # noinspection PyProtectedMember
    packet1._packet_lock.release()

    # Wait for thread to finish
    thread.join()

    assert packet1.str == "123"


if __name__ == "__main__":
    pytest.main(sys.argv)
