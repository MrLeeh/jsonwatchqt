"""
    Module for recording json data to csv

    Copyright (c) 2015 by Stefan Lehmann

"""


import pandas as pd
from datetime import datetime

from qtpy.QtWidgets import QTableView
from qtpy.QtCore import QAbstractTableModel, QModelIndex, Qt
from jsonwatch.jsonnode import JsonNode, JsonItem


def tabulate(rootnode: JsonNode):

    def iter_children(node: JsonNode):
        for key, child in node.items:
            if isinstance(child, JsonItem):
                yield child
            elif isinstance(child, JsonNode):
                yield from iter_children(child)

    data = (('.'.join(child.path[1:]), child.value)
            for i, child in enumerate(iter_children(rootnode)))
    values = {d[0]: d[1] for d in data}
    return pd.DataFrame(data=values, index=[datetime.now()])


class RecordModel(QAbstractTableModel):

    def __init__(self, dataframe, parent=None):
        super().__init__(parent)
        self.dataframe = dataframe

    def rowCount(self, parent=QModelIndex()):
        return len(self.dataframe.index)

    def columnCount(self, parent=QModelIndex()):
        return len(self.dataframe.columns)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            return str(self.dataframe.iloc[index.row(), index.column()])

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.dataframe.columns[section]
            elif orientation == Qt.Vertical:
                return str(self.dataframe.index[section])


class RecordWidget(QTableView):

    def __init__(self, rootnode, parent=None):
        super().__init__(parent)
        self.dataframe = pd.DataFrame()
        self.setModel(RecordModel(self.dataframe))

    def add_data(self, rootnode):
        df = tabulate(rootnode)
        if self.dataframe is None:
            self.dataframe = df
        else:
            self.dataframe = self.dataframe.append(df)

        self.model().dataframe = self.dataframe
        self.model().beginResetModel()
        self.model().endResetModel()
        self.scrollToBottom()
