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
        'appdirs>=1.4.3',
        'blinker>=1.4'
        'cycler>=0.10.0',
        'jsonpickle>=0.9.4',
        'matplotlib>=2.0.0',
        'numpy>=1.12.1',
        'packaging>=16.8',
        'pandas>=0.19.2',
        'pyparsing>=2.2.0',
        'pyqt5>=5.8.2',
        'pyserial>=3.3',
        'python-dateutil>=2.6.0',
        'pytz>=2017.2',
        'qtpy>=1.2.1',
        'six>=1.10.0',
        'jsonwatch>=1.0.1',
        'pyqtconfig>=0.8.6',
    ],
    dependency_links=[
        'git+https://github.com/MrLeeh/jsonwatch#egg=jsonwatch',
        'git+https://github.com/MrLeeh/pyqtconfig#egg=pyqtconfig',
    ],
    platforms='any',
    scripts=['run_jsonwatchqt.pyw'],
    cmdclass=versioneer.get_cmdclass()
)
