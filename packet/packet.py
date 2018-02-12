#!/usr/bin/python
# -*- coding: UTF-8 -*-

import json
from packet.utils import UnknownPacket, InvalidData, NotSerializable


class Packet:
    """
    General packet class
    """

    def dumps(self):
        """
        Serialize packet object to a JSON formatted string using the packet name as the tag.

        :return: bytes, JSON
        """
        try:
            data = json.dumps({self.__class__.__name__: self.__dict__}).encode()
        except TypeError as e:
            raise NotSerializable(e)
        return data

    def loads(self, data):
        """
        Deserialize data (instance containing a JSON document) and update packet object.
        Raises UnknownPacket or InvalidData if the data is not deserializable.

        :param data: bytes/str, JSON
        :return: None
        """
        tag = self.__class__.__name__
        try:
            _data = json.loads(data)
        except Exception:
            raise UnknownPacket
        if tag not in _data or not isinstance(_data[tag], dict) or set(_data[tag]) != set(self.__dict__):
            raise InvalidData
        self.__dict__.update(_data[tag])

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
