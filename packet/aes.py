#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import pyaes
import hashlib


def random_iv():
    return os.urandom(16)


class CTRCipher:
    def __init__(self, key):
        if isinstance(key, str):
            key = key.encode()
        self.__key = hashlib.sha3_256(key).digest()

    def encrypt(self, raw):
        return pyaes.AESModeOfOperationCTR(self.__key).encrypt(raw)

    def decrypt(self, enc):
        return pyaes.AESModeOfOperationCTR(self.__key).decrypt(enc)


class CBCCipher:
    def __init__(self, key, block_size=16):
        if isinstance(key, str):
            key = key.encode()
        self.__key = hashlib.sha3_256(key).digest()
        self.__block_size = block_size

    def encrypt(self, raw):
        iv = random_iv()
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
