#!/usr/bin/python
# -*- coding: UTF-8 -*-

from setuptools import setup
from packet import __author__, __email__, __version__


setup(
    name="packet",
    version=__version__,
    description="A simple object serializer which can be used in socket communications",
    license="GPLv3",
    author=__author__,
    author_email=__email__,
    packages=["packet"],
    install_requires=["pyaes"],
    include_package_data=True
)
