#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

requires = ['mido',
]

setup(
    name='color_organist',
    install_requires=requires,
    license='GPL2',
)