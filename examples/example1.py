#!/usr/bin/python
# -*- coding: UTF-8 -*-


"""
Example 1 - Packet:
    Use Packet and a dummy connection to send/receive data.
    For this example, ast serializer will be used, allowing us
    to send bytes/tuple/complex types among others.

    Since we are using Packet, the attributes are not inspected
    so, the attributes will be updated as long as their name are
    the same. This is the reason that Packet only allows basic types.
"""

from packet import Packet, set_ast_serializer

# Set ast serializer as the serializer to be used in all packets from now on
set_ast_serializer()


class DummyPacket(Packet):
    def __init__(self):
        self.bytes = b"123"
        self.complex = 123j
        self.tuple = (123,)


class DummyConnection:
    def __init__(self):
        self.__data = None

    def send(self, data):
        self.__data = data
        return len(data)

    def recv(self, buffer_size):
        return self.__data[:buffer_size]


def example1():
    # Create a dummy connection just for tests
    connection = DummyConnection()
    # Create packet instances
    packet1 = DummyPacket()
    packet2 = DummyPacket()

    # Change some values so we can see they will be loaded
    packet1.bytes = b"321"
    packet1.complex = 321j
    packet1.tuple = (321,)

    # Send packet1 data to packet2
    # Same as packet2.loads(packet1.dumps())
    packet1.send_to(connection)
    packet2.receive_from(connection)

    print("Packet 2 dump: %s" % packet2.dumps())


if __name__ == "__main__":
    example1()
