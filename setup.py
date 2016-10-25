#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

requires = ['mido', 'dill', 'husl'
]

setup(
    name='color_organist',
    install_requires=requires,
    license='GPL2',
)