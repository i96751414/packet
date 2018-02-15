#!/usr/bin/python
# -*- coding: UTF-8 -*-

JSON_SERIALIZER = 1  # JSON serializer
AST_SERIALIZER = 2  # AST literal eval

CTR_MODE = 1  # Counter Mode
CBC_MODE = 2  # Cipher Block Chaining Mode


class UnknownPacket(Exception):
    pass


class InvalidData(Exception):
    pass


class UnknownEncryption(Exception):
    pass


class NotSerializable(Exception):
    pass
