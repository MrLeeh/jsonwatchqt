#!/usr/bin/env python

from setuptools import setup
import versioneer

setup(
    name='jsonwatchqt',
    version=versioneer.get_version(),
    packages=['jsonwatchqt'],
    url='https://github.com/MrLeeh/jsonwatchqt',
    license='MIT License',
    author='Stefan Lehmann',
    author_email='Stefan.St.Lehmann@gmail.com',
    description='Qt GUI for the jsonwatch package',
    install_requires=[
        'pyqtconfig>=0.8.6',
        'jsonwatch>=0.0.1',
        'pandas',
        'matplotlib',
        'pyserial',
        'qtpy'
    ],
    platforms='any',
    scripts=['run_jsonwatchqt.pyw'],
    cmdclass=versioneer.get_cmdclass()
)
