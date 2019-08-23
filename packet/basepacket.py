#!/usr/bin/python
# -*- coding: UTF-8 -*-

import hashlib
import os
import threading
from typing import BinaryIO  # noqa

import pyaes

from packet._compat import get_items, with_metaclass
from packet.serializers import json_serializer, ast_serializer, _get_attributes, _Serializable, _Serializer
from packet.utils import CTR_MODE, CBC_MODE, UnknownEncryption
from packet.utils import UnknownPacket, InvalidData


class _PacketMetaClass(type):
    """
    MetaClass to be used in Packet in order to set _INITIALISED flag
    after __init__ is called
    """

    def __call__(cls, *args, **kwargs):
        self = super(_PacketMetaClass, cls).__call__(*args, **kwargs)
        object.__setattr__(self, "_packet_initialised", True)
        return self


# noinspection PyCallByClass
class Packet(with_metaclass(_PacketMetaClass, _Serializable)):
    """
    General packet class. This is the main "Packet" class.
    Every packet classes should inherit from this one.
    """

    def __new__(cls, *args, **kwargs):
        self = super(Packet, cls).__new__(cls, *args, **kwargs)
        object.__setattr__(self, "_packet_serializer", json_serializer)
        object.__setattr__(self, "_packet_lock", threading.RLock())
        object.__setattr__(self, "_packet_initialised", False)
        return self

    def set_json_serializer(self):
        """
       Set json_serializer as the serializer to be used.
       Same as self.set_packet_serializer(json_serializer).
       """
        self.set_serializer(json_serializer)

    def set_ast_serializer(self):
        """
       Set ast_serializer as the serializer to be used.
       Same as self.set_packet_serializer(ast_serializer).
       """
        self.set_serializer(ast_serializer)

    def set_serializer(self, serializer):
        """
        Set serializer to be used.
        Serializer must be either json_serializer or ast_serializer.
        :param serializer: Serializer to use
        :type serializer: _Serializer
        """
        if not isinstance(serializer, _Serializer):
            raise TypeError("Invalid serializer")
        object.__setattr__(self, "_packet_serializer", serializer)

    @property
    def __tag__(self):
        """
        Tag of current packet. This must be equal for all instances
        sharing data.
        :rtype: str
        """
        return self.__class__.__name__

    def _generate_dict(self):
        """
        Return packet as a dictionary
        :rtype: dict
        """
        return {attribute: getattr(self, attribute) for attribute in _get_attributes(self)}

    def dump(self, fp):
        """
        Serialize packet object to fp (a .write()-supporting file-like object).
        Raises NotSerializable if the packet is not serializable.
        :param fp: file-like object
        :type fp: BinaryIO
        """
        fp.write(self.dumps())

    def dumps(self):
        """
        Serialize packet object to string using the packet name as the tag.
        Raises NotSerializable if the packet is not serializable.
        :rtype: bytes
        """
        with self._packet_lock:
            _data = self._generate_dict()

        return self._packet_serializer.dumps({self.__tag__: _data})

    def _update_dict(self, data):
        """
        Update packet dictionary with the given data.
        :param data: new data
        :type data: dict
        """
        if not isinstance(data, dict):
            raise InvalidData("Expected dictionary data")
        if set(data) != _get_attributes(self):
            raise InvalidData("Attributes do not match")
        for k, v in get_items(data):
            object.__setattr__(self, k, v)

    def load(self, fp):
        """
        Deserialize data from fp (a .read()-supporting file-like object) and
        update packet object.
        Raises UnknownPacket or InvalidData if the data is not deserializable.
        :param fp: file-like object
        :type fp: BinaryIO
        """
        self.loads(fp.read())

    def loads(self, data):
        """
        Deserialize data and update packet object.
        Raises UnknownPacket or InvalidData if the data is not deserializable.
        :type data: bytes or str
        """
        with self._packet_lock:
            tag = self.__tag__
            try:
                _data = self._packet_serializer.loads(data)
            except Exception as e:
                raise UnknownPacket(e)
            if not isinstance(_data, dict):
                raise UnknownPacket("Expected dictionary data")
            if tag not in _data:
                raise InvalidData("Expected data with tag '{}'".format(tag))

            self._update_dict(_data[tag])

    def receive_from(self, conn, buffer_size=512):
        """
        Receive data from a connection conn (typically a socket connection)
        by doing conn.recv(buffer_size) and loads the received data into the
        packet. If there is an error loading data or no data is obtained,
        returns False, otherwise returns True.
        :param conn: Socket connection
        :param buffer_size: Socket buffer size
        :type buffer_size: int
        :return: Success
        :rtype: bool
        """
        if conn is None:
            return False
        data = conn.recv(buffer_size)
        if not data:
            return False
        try:
            self.loads(data)
        except (UnknownPacket, InvalidData):
            return False
        return True

    def send_to(self, conn):
        """
        Send data to a connection conn (typically a socket connection).
        If no connection, returns None, otherwise returns the same as
        conn.send(data).
        :param conn: Socket connection
        :rtype: int
        :return: Bytes sent
        """
        if conn is None:
            return None
        return conn.send(self.dumps())

    def __setattr__(self, name, value):
        """
        Set attribute in a Packet instance.
        :param name: name of attribute to set
        :type name: str
        :param value: value of attribute to set
        """
        if name in _Serializable.__slots__:
            raise AttributeError("'{}' is not a valid attribute name")

        if (self._packet_initialised and name not in _get_attributes(self) and
                not isinstance(getattr(self.__class__, name, None), property)):
            raise AttributeError("'{}' is not an attribute of '{}' packet".format(name, self.__class__.__name__))

        with self._packet_lock:
            object.__setattr__(self, name, value)

    def __delattr__(self, item):
        raise AttributeError("Can't delete {}".format(item))


class InspectedPacket(Packet):
    """
    Inspected packet class
    """

    def _generate_dict(self):
        return self._packet_serializer.serialize_object(self)

    def _update_dict(self, data):
        self._packet_serializer.deserialize_object(self, data)


def _random_iv():
    """
    Generate a random initialization vector (suitable for cryptographic use).
    :return: iv
    :rtype: bytes
    """
    return os.urandom(16)


class _CTRCipher:
    """
    Counter (CTR) Cipher mode
    """

    def __init__(self, key):
        if isinstance(key, str):
            key = key.encode()
        self.__key = hashlib.sha256(key).digest()

    def encrypt(self, raw):
        return pyaes.AESModeOfOperationCTR(self.__key).encrypt(raw)

    def decrypt(self, enc):
        return pyaes.AESModeOfOperationCTR(self.__key).decrypt(enc)


class _CBCCipher:
    """
    Cipher Block Chaining (CBC) mode
    """

    def __init__(self, key, block_size=16):
        if isinstance(key, str):
            key = key.encode()
        self.__key = hashlib.sha256(key).digest()
        self.__block_size = block_size

    def encrypt(self, raw):
        iv = _random_iv()
        aes = pyaes.Encrypter(pyaes.AESModeOfOperationCBC(self.__key, iv=iv))
        data = aes.feed(raw)
        data += aes.feed()
        return iv + data

    def decrypt(self, enc):
        iv = enc[:16]
        aes = pyaes.Decrypter(pyaes.AESModeOfOperationCBC(self.__key, iv=iv))
        data = aes.feed(enc[16:])
        data += aes.feed()
        return data


def set_cbc_mode():
    """
    Set CBC_MODE as the encryption mode to be used when serializing packets.
    Same as set_packet_encryption_mode(CBC_MODE).
    """
    SafePacket.encryption_mode = CBC_MODE


def set_ctr_mode():
    """
    Set CTR_MODE as the encryption mode to be used when serializing packets.
    Same as set_packet_encryption_mode(CTR_MODE).
    """
    SafePacket.encryption_mode = CTR_MODE


def set_packet_encryption_key(key):
    """
    Set encryption key to be used when serializing packets.
    Encryption key must be a string.
    :param key: Encryption key
    :type key: str
    """
    if not isinstance(key, str):
        raise ValueError("Key must be a string")
    SafePacket.encryption_key = key


def set_packet_encryption_mode(mode):
    """
    Set encryption mode to be used when serializing packets.
    Encryption mode must be either CBC_MODE or CTR_MODE.
    :param mode: Encryption mode
    :type mode: int
    """
    if not isinstance(mode, int) or (mode != CBC_MODE and mode != CTR_MODE):
        raise ValueError("Unknown mode")
    SafePacket.encryption_mode = mode


class SafePacket(Packet):
    """
    General SafePacket class
    """

    encryption_key = ""
    encryption_mode = CTR_MODE

    def dumps(self):
        """
        Serialize packet object and encrypt it using the specified
        encryption_key and encryption_mode.
        :rtype: bytes
        """
        cipher = self.__get_cipher()
        return cipher.encrypt(super(SafePacket, self).dumps())

    def loads(self, data):
        """
        Deserialize encrypted data using the specified encryption_key and
        encryption_mode and update packet object.
        Raises UnknownEncryption if not possible to decrypt the data.
        Raises UnknownPacket or InvalidData if the data is not deserializable.
        :param data: Encrypted data
        :type data: bytes
        """
        cipher = self.__get_cipher()
        try:
            decoded = cipher.decrypt(data)
        except Exception as e:
            raise UnknownEncryption(e)
        return super(SafePacket, self).loads(decoded)

    def __get_cipher(self):
        """
        Get the cipher as specified by encryption_mode.
        If no cipher is specified, return the default cipher (CTR).
        :return: cipher
        """
        if self.encryption_mode == CBC_MODE:
            return _CBCCipher(self.encryption_key)
        return _CTRCipher(self.encryption_key)


class InspectedSafePacket(InspectedPacket, SafePacket):
    """
    Inspected and safe packet class
    """
