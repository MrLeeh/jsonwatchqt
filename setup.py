#!/usr/bin/env python
from setuptools import setup

setup(
    name='jsonwatchqt',
    version='0.0.1',
    packages=['jsonwatchqt'],
    url='https://github.com/MrLeeh/jsonwatchqt',
    license='MIT License',
    author='Stefan Lehmann',
    author_email='Stefan.St.Lehmann@gmail.com',
    description='Qt GUI for the jsonwatch package',
    install_requires=[
        'pyqtconfig>=0.8.6',
        'jsonwatch>=0.0.1',
        'pandas'
    ],
    platforms='any',
    scripts=['run_jsonwatchqt.pyw']
)
