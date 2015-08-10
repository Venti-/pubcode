# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
from codecs import open
from os import path
import pubcode

here = path.abspath(path.dirname(__file__))

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='PubCode',
    version=pubcode.__version__,
    description='A simple module for creating barcodes.',
    long_description=long_description,
    url='https://github.com/Venti-/pubcode',

    author='Ari Koivula',
    author_email='ari@koivu.la',

    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Multimedia :: Graphics',
        'License :: OSI Approved :: MIT License',

        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.4',
    ],

    install_requires=[
        "future",  # For Python3 like builtins in Python2.
    ],

    packages=find_packages(exclude=['tests']),
)
