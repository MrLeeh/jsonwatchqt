"""
    Copyright © 2015 by Stefan Lehmann

"""
from PyQt5.QtCore import QModelIndex, Qt, QAbstractItemModel, QMimeData, \
    QByteArray, QDataStream, QIODevice
from PyQt5.QtWidgets import QTreeView, QApplication
import sys
from jsonwatch.jsonobject import JsonObject
from jsonwatch.jsonvalue import JsonValue


class Column():
    def __init__(self, name, label=None):
        self.name = name
        self.label = label or name


class JsonDataModel(QAbstractItemModel):
    def __init__(self, rootnode: JsonObject, parent=None):
        super().__init__(parent)
        self.root = rootnode
        self.root.child_added_callback = self.insert_row
        self.columns = [
            Column('key'),
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

        if role == Qt.DisplayRole:
            parent_node = self.node_from_index(index.parent())
            item = parent_node.child_at(index.row())
            column = index.column()
            if self.columns[column].name == 'key':
                return item.key
            elif self.columns[column].name == 'value':
                if isinstance(item, JsonValue):
                    return item.value

    def flags(self, index: QModelIndex):
        flags = Qt.NoItemFlags | Qt.ItemIsDragEnabled | Qt.ItemIsSelectable
        if index.isValid():
            node = self.node_from_index(index)
            if node.latest:
                flags |= Qt.ItemIsEnabled
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
        return 2

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
    def __init__(self, rootnode: JsonObject, parent=None):
        super().__init__(parent)
        self.setModel(JsonDataModel(rootnode))
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