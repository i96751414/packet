#!/usr/bin/python
# -*- coding: UTF-8 -*-

from packet.packet import Packet
from packet.utils import CTR_MODE, CBC_MODE, UnknownEncryption
from packet.aes import CBCCipher, CTRCipher


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
        return cipher.encrypt(Packet.dumps(self))

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
        except Exception:
            raise UnknownEncryption
        return Packet.loads(self, decoded)

    def __get_cipher(self):
        """
        Get the cipher as specified by encryption_mode.
        If no cipher is specified, return the default cipher (CTR).

        :return: cipher
        """
        if self.encryption_mode is CBC_MODE:
            return CBCCipher(self.encryption_key)
        return CTRCipher(self.encryption_key)
