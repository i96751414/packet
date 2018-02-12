#!/usr/bin/python
# -*- coding: UTF-8 -*-

from packet import Packet, SafePacket, CBC_MODE, InvalidData

"""
    Packet Example
"""


class Packet1(Packet):
    def __init__(self, a=0, b=0, c=0):
        self.a = a
        self.b = b
        self.c = c


def example1():
    a = Packet1(1, 2, 3)
    data = a.dumps()
    print("Data: %s" % a.__dict__)

    b = Packet1()
    b.loads(data)
    print("Loaded data: %s" % b.__dict__)


"""
    SafePacket Example
"""

SafePacket.encryption_key = "my_key"
SafePacket.encryption_mode = CBC_MODE


class SafePacket1(SafePacket):
    def __init__(self):
        self.integer = int()
        self.string = str()
        self.float = float()
        self.bool = bool()


class SafePacket2(SafePacket):
    def __init__(self):
        self.integer = int()


def example2():
    a = SafePacket1()
    print("Data:", a.__dict__)
    encrypted = a.dumps()
    print("Encrypted data: %s" % encrypted)

    b = SafePacket1()
    b.loads(encrypted)
    print("Decrypted data: %s" % b.__dict__)

    print("\nWhat happens if we try to use a different packet?")
    try:
        c = SafePacket2()
        c.loads(encrypted)
    except InvalidData:
        print("Invalid Data error!")


"""
    Using a connection to send/receive data
"""


class DumbConnection:
    def __init__(self):
        self.__data = None

    def send(self, data):
        self.__data = data
        return len(data)

    def recv(self, buffer_size):
        return self.__data[:buffer_size]


def example3():
    conn = DumbConnection()

    a = SafePacket1()
    a.string = "Not just an empty string"
    print("Data: %s" % a.__dict__)
    print("%s bytes were sent" % a.send_to(conn))

    b = SafePacket1()
    b.receive_from(conn)
    print("Received data: %s" % b.__dict__)


if __name__ == "__main__":
    print("1 - Packet example:")
    example1()
    print("\n2 - SafePacket example:")
    example2()
    print("\n3 - Using a connection to send/receive data:")
    example3()
