#!/usr/bin/python
# -*- coding: UTF-8 -*-

import json
from .utils import UnknownPacket, InvalidData, NotSerializable


class Packet:
    """
    General packet class. This is the main "Packet" class.
    Every packet classes should inherit from this one.
    """

    @property
    def __tag__(self):
        """
        Tag of current packet. This must be equal for all instances sharing data.

        :return: str
        """
        return self.__class__.__name__

    def _generate_dict(self):
        """
        Return packet as a dictionary

        :return: dict
        """
        return self.__dict__

    def dumps(self):
        """
        Serialize packet object to a JSON formatted string using the packet name as the tag.

        :return: bytes, JSON
        """
        try:
            data = json.dumps({self.__tag__: self._generate_dict()}).encode()
        except TypeError as e:
            raise NotSerializable(e)
        return data

    def _update_dict(self, data):
        """
        Update packet dictionary with the given data.

        :param data: dict, new data
        :return: None
        """
        if not isinstance(data, dict) or set(self.__dict__) != set(data):
            raise InvalidData
        self.__dict__.update(data)

    def loads(self, data):
        """
        Deserialize data (instance containing a JSON document) and update packet object.
        Raises UnknownPacket or InvalidData if the data is not deserializable.

        :param data: bytes/str, JSON
        :return: None
        """
        tag = self.__tag__
        try:
            _data = json.loads(data)
        except Exception:
            raise UnknownPacket
        if tag not in _data:
            raise InvalidData
        self._update_dict(_data[tag])

    def receive_from(self, conn, buffer_size=512):
        """
        Receive data from a connection and load it to the packet.
        If there is an error loading data or no data is obtained, return False.

        :param conn: Socket connection
        :param buffer_size: int, Socket buffer size
        :return: bool, Success
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
        Send data to connection.
        If no connection, return None.

        :param conn: Socket connection
        :return: int, Bytes sent
        """
        if conn is None:
            return None
        return conn.send(self.dumps())
