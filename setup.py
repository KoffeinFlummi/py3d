#!/usr/bin/env python3

import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "py3d",
    version = "1.0.0",
    packages = ["py3d"],
    install_requires = [],
    author = 'Felix "KoffeinFlummi" Wiegand',
    author_email = "koffeinflummi@protonmail.com",
    description = "A library for reading and writing Arma P3D files.",
    long_description = read("README.md"),
    license = "MIT",
    keywords = "arma 3d p3d mlod",
    url = "https://github.com/KoffeinFlummi/py3d",
    classifiers = [
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6"
    ]
)
