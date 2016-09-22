"""
    Module for recording json data to csv

    Copyright (c) 2015 by Stefan Lehmann

"""


import pandas as pd
from datetime import datetime

from qtpy.QtWidgets import QTableView
from qtpy.QtCore import QAbstractTableModel, QModelIndex, Qt
from jsonwatch.jsonnode import JsonNode, JsonItem


def tabulate(starttime, time, rootnode: JsonNode):

    def iter_children(node: JsonNode):
        for key, child in node.items:
            if isinstance(child, JsonItem):
                yield child
            elif isinstance(child, JsonNode):
                yield from iter_children(child)

    delta = time - starttime
    data = {'.'.join(child.path[1:]): child.value
            for i, child in enumerate(iter_children(rootnode))}
    df = pd.DataFrame(data=data, index=[time])
    df.insert(0, "seconds", delta.total_seconds())
    return df


class RecordModel(QAbstractTableModel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dataframe = pd.DataFrame()

    def rowCount(self, parent=QModelIndex()):
        return len(self.dataframe.index)

    def columnCount(self, parent=QModelIndex()):
        return len(self.dataframe.columns)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            val = self.dataframe.iloc[index.row(), index.column()]
            if index.column() == 0:
                return "{:3f}".format(val)
            return str(val)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                    return self.dataframe.columns[section]
            elif orientation == Qt.Vertical:
                dt = self.dataframe.index[section]
                return "{:%H:%M:%S}.{:03d}".format(
                    dt, round(dt.microsecond / 1000)
                )


class RecordWidget(QTableView):

    def __init__(self, rootnode, parent=None):
        super().__init__(parent)
        self.setModel(RecordModel())
        self.starttime = None

    def add_data(self, time, rootnode):
        if self.starttime is None:
            self.starttime = time
        df = tabulate(self.starttime, time, rootnode)
        if self.dataframe is None:
            self.dataframe = df
        else:
            self.dataframe = self.dataframe.append(df)
        self.scrollToBottom()

    def clear(self):
        self.dataframe = pd.DataFrame()
        self.starttime = None

    # dataframe property
    @property
    def dataframe(self):
        return self.model().dataframe

    @dataframe.setter
    def dataframe(self, value):
        self.model().beginResetModel()
        self.model().dataframe = value
        self.model().endResetModel()
