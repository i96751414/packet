#!/usr/bin/python
# -*- coding: UTF-8 -*-

"""
Example 2 - SafePacket:
    Use SafePacket to send/receive encrypted data.
    For this example, json serializer will be used, therefore
    we can only use JSON allowed types.

    As well as Packet, the attributes are not inspected so,
    the attributes will be updated as long as their name are
    the same.
"""

from packet import SafePacket, set_cbc_mode, set_packet_encryption_key

# Set Cipher Block Chaining mode
set_cbc_mode()
# Set encryption key
set_packet_encryption_key("just-a-key")


class DummyPacket(SafePacket):
    def __init__(self):
        # This is not necessary, as json_serializer is the default serializer
        self.set_json_serializer()

        self.a = None
        self.b = None
        self.c = None


def example2():
    # Create packet instances
    packet1 = DummyPacket()
    packet2 = DummyPacket()

    # Change some values so we can see they will be loaded
    packet1.a = 3
    packet1.b = 2
    packet1.c = 1

    # Send packet1 data to packet2
    packet2.loads(packet1.dumps())

    print("packet 2 a: {}, b: {}, c: {}".format(
        packet2.a, packet2.b, packet2.c))
    print("packet 2 dump: {}".format(packet2.dumps()))


if __name__ == "__main__":
    example2()
