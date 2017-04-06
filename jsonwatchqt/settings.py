# -*- coding: utf-8 -*-
# @Author: Stefan Lehmann
# @Date:   2016
# @Last Modified by:   MrLeeh
# @Last Modified time: 2016
from collections import namedtuple
from qtpy.QtCore import QSettings


class Setting:
    def __init__(self, name, type_=None, default=None):
        self.name = name
        self.type = type_
        self.default = default
        self.value = default


class SettingsManager:
    def __init__(self):
        self._settings = []

    def load_settings(self):
        qt_settings = QSettings()
        for setting in self.settings:
            setting.value = qt_settings.value(setting.name, setting.type,
                                              settings.default)
    def save_settings(self):
        qt_settings = QSettings()
        for setting in self.settings:
            qt_settings.setValue(setting.name, setting.value)


class Settings:
    def __init__(self):
        self.settings = dict(
            window_state=Setting('mainwindow/windowstate'),
            window_geometry=Setting('mainwindow/geometry'),
            filename=Setting('mainwindow/filename', str)
        )