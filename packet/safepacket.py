#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import pyaes
import hashlib
from .basepacket import Packet
from .utils import CTR_MODE, CBC_MODE, UnknownEncryption


def _random_iv():
    """
    Generate a random initialization vector (suitable for cryptographic use).

    :return: bytes, iv
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

    :return: None
    """
    SafePacket.encryption_mode = CBC_MODE


def set_ctr_mode():
    """
    Set CTR_MODE as the encryption mode to be used when serializing packets.
    Same as set_packet_encryption_mode(CTR_MODE).

    :return: None
    """
    SafePacket.encryption_mode = CTR_MODE


def set_packet_encryption_key(key):
    """
    Set encryption key to be used when serializing packets.
    Encryption key must be a string.

    :param key: str, Encryption key
    :return: None
    """
    if not isinstance(key, str):
        raise ValueError("Key must be a string")
    SafePacket.encryption_key = key


def set_packet_encryption_mode(mode):
    """
    Set encryption mode to be used when serializing packets.
    Encryption mode must be either CBC_MODE or CTR_MODE.

    :param mode: int, Encryption mode
    :return: None
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
        Serialize packet object and encrypt it using the specified encryption_key and encryption_mode.

        :return: bytes
        """
        cipher = self.__get_cipher()
        return cipher.encrypt(super(SafePacket, self).dumps())

    def loads(self, data):
        """
        Deserialize encrypted data using the specified encryption_key and encryption_mode and update packet object.
        Raises UnknownEncryption if not possible to decrypt the data.
        Raises UnknownPacket or InvalidData if the data is not deserializable.

        :param data: bytes, Encrypted data
        :return: None
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
