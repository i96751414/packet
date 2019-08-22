#!/usr/bin/python
# -*- coding: UTF-8 -*-

from setuptools import setup

__author__ = "i96751414"
__email__ = "i96751414@gmail.com"
__version__ = "0.0.1"

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="packet",
    version=__version__,
    description="A simple object serializer which can be used in socket communications",
    long_description=long_description,
    license="GPLv3",
    author=__author__,
    author_email=__email__,
    packages=["packet"],
    install_requires=["pyaes"],
    tests_require=["pytest"],
    python_requires=">=2.7",
)
