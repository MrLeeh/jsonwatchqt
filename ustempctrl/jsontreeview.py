"""
    Copyright © 2015 by Stefan Lehmann

"""
from PyQt5.QtCore import QModelIndex, Qt, QAbstractItemModel, QMimeData, \
    QByteArray, QDataStream, QIODevice
from PyQt5.QtWidgets import QTreeView, QApplication, QItemDelegate
import sys
import re

import serial
from jsonwatch.jsonobject import JsonObject
from jsonwatch.jsonvalue import JsonValue


utf8_to_bytearray = lambda x: bytearray(x, 'utf-8')


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

    def createEditor(self, widget, options, index):
        self.update = True
        return super().createEditor(widget, options, index)

    def setEditorData(self, widget, index):
        if self.update:
            self.update = False
            return super().setEditorData(widget, index)


class JsonDataModel(QAbstractItemModel):
    def __init__(self, rootnode: JsonObject, ser: serial.Serial, parent=None):
        super().__init__(parent)
        self.root = rootnode
        self.serial = ser
        self.root.child_added_callback = self.insert_row
        self.columns = [
            Column('key'),
            Column('name'),
            Column('value')
        ]

    def index(self, row, column, parent=QModelIndex()):
        parent_node = self.node_from_index(parent)
        return self.createIndex(row, column, parent_node.child_at(row))

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

        if role in (Qt.DisplayRole, Qt.EditRole):
            item = index.internalPointer()
            column = self.columns[index.column()]
            if column.name == 'key':
                return item.key
            if column.name == 'name':
                return item.name
            elif column.name == 'value':
                if isinstance(item, JsonValue):
                    if item.value is None:
                        return "-"
                    else:
                        return item.value_str() + ' ' + item.unit

    def setData(self, index:QModelIndex, value, role=Qt.EditRole):
        if not index.isValid():
            return False

        if role == Qt.EditRole:
            node = index.internalPointer()
            if isinstance(node, JsonValue):
                if self.serial.isOpen():
                    node.value = extract_number(value)
                    s = '{"%s": %i}\n' % (node.key, node._raw_value)
                    print(s.strip())
                    self.serial.write(utf8_to_bytearray(s))
                    return True
        return False

    def flags(self, index: QModelIndex):
        flags = Qt.NoItemFlags | Qt.ItemIsDragEnabled | Qt.ItemIsSelectable
        if index.isValid():
            node = self.node_from_index(index)
            if node.latest:
                flags |= Qt.ItemIsEnabled
            if isinstance(node, JsonValue):
                if not node.readonly:
                    flags |= Qt.ItemIsEditable
        return flags

    def mimeTypes(self):
        return ["application/x-nodepath.list"]

    def mimeData(self, indexes):
        mimedata = QMimeData()
        data = QByteArray()
        stream = QDataStream(data, QIODevice.WriteOnly)

        path = lambda x: x.path
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


class JsonTreeView(QTreeView):
    def __init__(self, rootnode: JsonObject, ser: serial.Serial, parent=None):
        super().__init__(parent)
        self.setModel(JsonDataModel(rootnode, ser))
        self.setItemDelegate(MyItemDelegate())
        self.setDragDropMode(QTreeView.DragDrop)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)

    def refresh(self):
        self.model().refresh()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = JsonTreeView()
    jsonstr = '''
    {
        "item2": 3,
        "item1": 2,
        "item3": {
            "item1": 4,
            "item2": 5
        }
    }'''
    w.refresh(jsonstr)
    w.show()
    app.exec_()