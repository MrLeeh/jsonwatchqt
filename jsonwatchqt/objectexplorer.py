"""
    Copyright © 2015 by Stefan Lehmann

"""

import sys
import re

from PyQt5.QtCore import QModelIndex, Qt, QAbstractItemModel, QMimeData, \
    QByteArray, QDataStream, QIODevice
from PyQt5.QtWidgets import QTreeView, QItemDelegate, QSpinBox, \
    QDoubleSpinBox

from jsonwatch.abstractjsonitem import AbstractJsonItem
from jsonwatch.jsonnode import JsonNode
from jsonwatch.jsonitem import JsonItem
from pyqtconfig.qt import pyqtSignal


def extract_number(s: str):
    return float(re.findall('([-+]?[\d.]+)', s)[0])


class Column():
    def __init__(self, name, label=None):
        self.name = name
        self.label = label or name


class MyItemDelegate(QItemDelegate):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update = False

    def createEditor(self, parent, options, index):
        self.update = True
        node = index.internalPointer()
        if isinstance(node, JsonItem):
            if node.type == 'int':
                editor = QSpinBox(parent)
                editor.setSuffix(node.unit or "")
                editor.setRange(node.min or -sys.maxsize,
                                node.max or sys.maxsize)
                editor.setGeometry(options.rect)
                editor.show()
                return editor
            elif node.type == 'float':
                editor = QDoubleSpinBox(parent)
                editor.setSuffix(node.unit or "")
                editor.setRange(node.min or -sys.maxsize,
                                node.max or sys.maxsize)
                editor.setGeometry(options.rect)
                editor.show()
                return editor
            else:
                return super().createEditor(parent, options, index)

    def destroyEditor(self, editor, index):
        self.update = True
        super().destroyEditor(editor, index)

    def setEditorData(self, editor, index):
        if self.update:
            self.update = False
            node = index.internalPointer()
            if node.type in ('int', 'float'):
                editor.setValue(node.value)
            else:
                return super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, (QSpinBox, QDoubleSpinBox)):
            print(editor.value())
            model.setData(index, editor.value())
        else:
            super().setModelData(editor, model, index)


class JsonDataModel(QAbstractItemModel):
    def __init__(self, rootnode: JsonNode, parent=None):
        super().__init__(parent)
        self.root = rootnode
        self.root.child_added_callback = self.insert_row
        self.columns = [
            Column('key'),
            Column('name'),
            Column('value')
        ]

    def index(self, row, column, parent=QModelIndex()):
        parent_node = self.node_from_index(parent)
        return self.createIndex(row, column, parent_node.item_at(row))

    def parent(self, index=QModelIndex()):
        node = self.node_from_index(index)
        if node is None:
            return QModelIndex()
        parent = node.parent
        if parent is None:
            return QModelIndex()
        grandparent = parent.parent
        if grandparent is None:
            return QModelIndex()
        row = grandparent.index(parent)
        assert row != -1
        return self.createIndex(row, 0, parent)

    def data(self, index=QModelIndex(), role=Qt.DisplayRole):
        if not index.isValid():
            return

        node = index.internalPointer()
        column = self.columns[index.column()]

        if role in (Qt.DisplayRole, Qt.EditRole):

            if column.name == 'key':
                return node.key
            if column.name == 'name':
                return node.name
            elif column.name == 'value':
                if isinstance(node, JsonItem):
                    if node.value is None:
                        return "-"
                    else:
                        if node.type in ('int', 'float'):
                            return node.value_str() + ' ' + node.unit

        elif role == Qt.CheckStateRole:
            if column.name == 'value':
                if isinstance(node, JsonItem):
                    if node.type == 'bool':
                        return Qt.Checked if node.value else Qt.Unchecked

    def setData(self, index:QModelIndex, value, role=Qt.EditRole):
        if not index.isValid():
            return False

        node = index.internalPointer()

        if role == Qt.EditRole:
            if isinstance(node, JsonItem):
                if node.type in ('float', 'int', None):
                    node.value = value
                self.dataChanged.emit(index, index, [Qt.EditRole])
                return True

        elif role == Qt.CheckStateRole:
            if isinstance(node, JsonItem):
                if node.type == 'bool':
                    node.value = value == Qt.Checked
                    self.dataChanged.emit(index, index, [Qt.CheckStateRole])
                    return True
        return False

    def flags(self, index: QModelIndex):
        flags = Qt.NoItemFlags | Qt.ItemIsDragEnabled | Qt.ItemIsSelectable
        if index.isValid():
            node = self.node_from_index(index)
            column = self.columns[index.column()].name

            if node.latest:
                flags |= Qt.ItemIsEnabled
            if isinstance(node, JsonItem):
                if column == 'value' and not node.readonly:
                   if not node.type == 'bool':
                        flags |= Qt.ItemIsEditable
                   else:
                        flags |= Qt.ItemIsUserCheckable
        return flags

    def mimeTypes(self):
        return ["application/x-nodepath.list"]

    def mimeData(self, indexes):
        mimedata = QMimeData()
        data = QByteArray()
        stream = QDataStream(data, QIODevice.WriteOnly)

        path = lambda x: '/'.join(x.path)
        node = lambda x: self.node_from_index(x)
        for path in set(path(node(index)) for index
                        in indexes if index.isValid()):
            stream.writeQString(path)

        mimedata.setData("application/x_nodepath.list", data)
        return mimedata

    def columnCount(self, parent=QModelIndex()):
        return len(self.columns)

    def rowCount(self, parent=QModelIndex()):
        node = self.node_from_index(parent)
        return len(node)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return self.columns[section].label
            else:
                return str(section)

    def supportedDragActions(self):
        return Qt.CopyAction | Qt.MoveAction

    def refresh(self):
        self.dataChanged.emit(QModelIndex(), QModelIndex(), [Qt.DisplayRole])

    def node_from_index(self, index):
        return index.internalPointer() if index.isValid() else self.root

    def index_from_node(self, node):
        def iter_model(parent):
            if parent.internalPointer() == node:
                return parent
            for row in range(self.rowCount(parent)):
                index = self.index(row, 0, parent)
                if index is not None and index.isValid() and index.internalPointer() == node:
                    return index
                res = iter_model(index)
                if res is not None:
                    return res
        return iter_model(QModelIndex())

    def insert_row(self, jsonitem):
        parent_node = jsonitem.parent
        row = parent_node.index(jsonitem)
        parent = self.index_from_node(parent_node)

        if parent is None:
            parent = QModelIndex()

        self.beginInsertRows(parent, row, row)
        self.endInsertRows()


class ObjectExplorer(QTreeView):
    nodevalue_changed = pyqtSignal(AbstractJsonItem)

    def __init__(self, rootnode: JsonNode, parent=None):
        super().__init__(parent)
        self.setModel(JsonDataModel(rootnode))
        self.model().dataChanged.connect(self.data_changed)
        self.setItemDelegate(MyItemDelegate())
        self.setDragDropMode(QTreeView.DragDrop)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

    def data_changed(self, topleft, bottomright, roles):
        node = topleft.internalPointer()
        if node is not None and isinstance(node, JsonItem):
            self.nodevalue_changed.emit(node)

    def refresh(self):
        self.model().refresh()