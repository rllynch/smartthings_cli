#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Setup for smartthings_cli'''

import ez_setup

ez_setup.use_setuptools()

from setuptools import setup

with open('README.md') as readme_file:
    README = readme_file.read()

setup(
    name="smartthings_cli",
    version="1.0",
    author="Richard L. Lynch",
    author_email="rich@richlynch.com",
    description=("Command line interface to query and control SmartThings devices"),
    long_description=README,
    license="Apache 2.0",
    keywords="smartthings cli automation",
    url="https://github.com/rllynch/smartthings_cli",
    packages=['smartthings_cli'],
    include_package_data=True,
    entry_points={
        'console_scripts': ['smartthings_cli = smartthings_cli.smartthings_cli:main'],
    },
    install_requires=[
        'twisted',
        'requests',
        'future'
    ]
)
