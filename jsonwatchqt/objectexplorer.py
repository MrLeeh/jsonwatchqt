"""
    Copyright (c) 2015 by Stefan Lehmann

"""
import os
import sys
import re
import logging

from qtpy.QtCore import QModelIndex, Qt, QAbstractItemModel, QMimeData, \
    QByteArray, QDataStream, QIODevice, QPoint
from qtpy.QtGui import QIcon
from qtpy.QtWidgets import QTreeView, QItemDelegate, QSpinBox, \
    QDoubleSpinBox, QMenu, QAction, QInputDialog, QDialog

from jsonwatch.abstractjsonitem import AbstractJsonItem
from jsonwatch.jsonnode import JsonNode
from jsonwatch.jsonitem import JsonItem
from jsonwatchqt.itemproperties import ItemPropertyDialog
from jsonwatchqt.utilities import pixmap
from pyqtconfig.qt import pyqtSignal


logger = logging.getLogger("jsonwatchqt.objectexplorer")


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
            if node.type in ('float', 'int'):
                editor = QDoubleSpinBox(parent)
                editor.setSuffix(node.unit or "")
                editor.setRange(node.min or -sys.maxsize,
                                node.max or sys.maxsize)
                editor.setGeometry(options.rect)
                editor.setDecimals(node.decimals or 0)
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
                try:
                    editor.setValue(node.value)
                except TypeError:
                    pass
            else:
                return super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if isinstance(editor, (QSpinBox, QDoubleSpinBox)):
            print(editor.value())
            model.setData(index, editor.value())
        else:
            super().setModelData(editor, model, index)


class JsonDataModel(QAbstractItemModel):

    def __init__(self, rootnode: JsonNode, mainwindow, parent=None):
        super().__init__(parent)
        self.mainwindow = mainwindow
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
                        if node.type != 'bool':
                            return "-"
                    else:
                        if node.type in ('int', 'float'):
                            return node.value_str() + ' ' + node.unit

        elif role == Qt.CheckStateRole:
            if column.name == 'value':
                if isinstance(node, JsonItem):
                    if node.type == 'bool':
                        return Qt.Checked if node.value else Qt.Unchecked

        elif role == Qt.DecorationRole:
            if column.name == 'key':
                if node.up_to_date and self.mainwindow.connected:
                    return pixmap("emblem_uptodate.png")
                else:
                    return pixmap("emblem_outofdate.png")

    def setData(self, index: QModelIndex, value, role=Qt.EditRole):
        if not index.isValid():
            return False

        node = index.internalPointer()

        if role == Qt.EditRole:
            if isinstance(node, JsonItem):
                if node.type in ('float', 'int', None):
                    node.value = value
                try:  # PyQt5
                    self.dataChanged.emit(index, index, [Qt.EditRole])
                except TypeError:  # PyQt4, PySide
                    self.dataChanged.emit(index, index)

        elif role == Qt.CheckStateRole:
            if isinstance(node, JsonItem):
                if node.type == 'bool':
                    node.value = value == Qt.Checked
                    try:  # PyQt5
                        self.dataChanged.emit(
                            index, index, [Qt.CheckStateRole])
                    except TypeError:  # PyQt4, PySide
                        self.dataChanged.emit(index, index)
                    return True
        return False

    def flags(self, index: QModelIndex):
        flags = (Qt.NoItemFlags | Qt.ItemIsDragEnabled | Qt.ItemIsSelectable |
                 Qt.ItemIsEnabled)

        if index.isValid():
            node = self.node_from_index(index)
            column = self.columns[index.column()].name

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
        def path(x):
            return "/".join(x.path)

        def node(x):
            return self.node_from_index(x)

        mimedata = QMimeData()
        data = QByteArray()
        stream = QDataStream(data, QIODevice.WriteOnly)

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
        try:  # PyQt5
            self.dataChanged.emit(
                QModelIndex(), QModelIndex(), [Qt.DisplayRole])
        except TypeError:  # PyQt4, PySide
            self.dataChanged.emit(QModelIndex(), QModelIndex())

    def node_from_index(self, index):
        return index.internalPointer() if index.isValid() else self.root

    def index_from_node(self, node):
        def iter_model(parent):
            if parent.internalPointer() == node:
                return parent

            for row in range(self.rowCount(parent)):
                index = self.index(row, 0, parent)

                if (index is not None and index.isValid() and
                        index.internalPointer() == node):
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
    nodeproperty_changed = pyqtSignal(AbstractJsonItem)

    def __init__(self, rootnode: JsonNode, parent):
        super().__init__(parent)
        self.mainwindow = parent
        self.setModel(JsonDataModel(rootnode, self.mainwindow))
        self.model().dataChanged.connect(self.data_changed)
        self.setItemDelegate(MyItemDelegate())
        self.setDragDropMode(QTreeView.DragDrop)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.doubleClicked.connect(self.double_clicked)

        # context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_contextmenu)

        # actions
        # properties action
        self.propertiesAction = QAction(self.tr("properties"), self)
        self.propertiesAction.setIcon(QIcon(pixmap("document_properties.png")))
        self.propertiesAction.triggered.connect(self.show_properties)

        # edit action
        self.editAction = QAction(self.tr("edit value"), self)
        self.editAction.setShortcut("F2")
        self.editAction.setIcon(QIcon(pixmap("edit.png")))
        self.editAction.triggered.connect(self.edit_value)

        # edit key action
        self.editkeyAction = QAction(self.tr("edit key"), self)
        self.editkeyAction.setIcon(QIcon(pixmap("kgpg_key1_kgpg.png")))
        self.editkeyAction.triggered.connect(self.edit_key)

        # insert item action
        self.insertitemAction = QAction(self.tr("insert item"), self)
        self.insertitemAction.setIcon(QIcon(pixmap("list_add.png")))
        self.insertitemAction.triggered.connect(self.insert_item)

        # insert node action
        self.insertnodeAction = QAction(self.tr("insert node"), self)
        self.insertnodeAction.setIcon(QIcon(pixmap("list_add.png")))
        self.insertnodeAction.triggered.connect(self.insert_node)

        # remove item action
        self.removeitemAction = QAction(self.tr("remove"), self)
        self.removeitemAction.setIcon(QIcon(pixmap("list_remove")))
        self.removeitemAction.triggered.connect(self.remove_item)

    def data_changed(self, topleft, bottomright, *args):
        node = topleft.internalPointer()
        if node is not None and isinstance(node, JsonItem):
            self.nodevalue_changed.emit(node)

    def double_clicked(self, *args, **kwargs):
        index = self.currentIndex()

        if not index.isValid():
            return

        column = self.model().columns[index.column()]
        if column.name == "value":
            self.edit_value()
        else:
            self.show_properties()

    def edit_key(self):
        index = self.currentIndex()
        if index.isValid():
            node = index.internalPointer()
            key, b = QInputDialog.getText(
                self, "Edit Json item", "Insert new key for item:",
                text=node.key
            )

            if not b:
                return

            node.key = key

            try:  # PyQt5
                self.model().dataChanged.emit(index, index, [Qt.DisplayRole])
            except TypeError:  # PyQt4, PySide
                self.model().dataChanged.emit(index, index)

    def edit_value(self):
        index = self.currentIndex()
        if not index.isValid():
            return

        i = self.model().index(index.row(), 2, index.parent())
        self.edit(i)

    def insert_item(self):
        index = self.currentIndex()

        if index.isValid():
            node = index.internalPointer()
        else:
            node = self.model().root

        key, b = QInputDialog.getText(
            self, "Insert Json item", "Insert key for new item:")

        if not b:
            return

        item = JsonItem(key)
        node.add(item)
        row = node.index(item)
        self.model().beginInsertRows(index, row, row)
        self.model().endInsertRows()

    def insert_node(self):
        index = self.currentIndex()
        parentnode = index.internalPointer() or self.model().root

        key, b = QInputDialog.getText(
            self, "Insert Json node", "Insert key for new node:")
        if not b:
            return
        node = JsonNode(key)
        parentnode.add(node)
        row = parentnode.index(node)
        self.model().beginInsertRows(index, row, row)
        self.model().endInsertRows()

    def mousePressEvent(self, event):
        index = self.indexAt(event.pos())
        if not index.isValid():
            self.setCurrentIndex(QModelIndex())
        super().mousePressEvent(event)

    def refresh(self):
        self.model().refresh()

    def remove_item(self):
        index = self.currentIndex()
        self.model().beginRemoveRows(index.parent(), index.row(), index.row())

        if index.isValid():
            node = index.internalPointer()
            if node.parent is not None:
                node.parent.remove(node.key)

        self.model().refresh()
        self.model().endRemoveRows()

    def show_contextmenu(self, pos: QPoint):
        menu = QMenu(self)
        index = self.currentIndex()
        node = index.internalPointer()

        # insert item and node
        menu.addAction(self.insertitemAction)
        menu.addAction(self.insertnodeAction)

        # edit key
        if isinstance(node, (JsonNode, JsonItem)):
            menu.addSeparator()
            menu.addAction(self.editkeyAction)
            if isinstance(node, JsonItem):
                menu.addAction(self.editAction)
                self.editAction.setEnabled(not node.readonly)

        # remove
        if isinstance(node, (JsonNode, JsonItem)):
            menu.addSeparator()
            menu.addAction(self.removeitemAction)

        # properties
        if isinstance(node, JsonItem):
            menu.addSeparator()
            menu.addAction(self.propertiesAction)
            menu.setDefaultAction(self.propertiesAction)

        menu.popup(self.viewport().mapToGlobal(pos), self.editAction)

    def show_properties(self):
        index = self.currentIndex()
        node = index.internalPointer()
        if not (index.isValid() and isinstance(node, JsonItem)):
            return

        dlg = ItemPropertyDialog(node, self.parent())
        if dlg.exec_() == QDialog.Accepted:
            self.nodeproperty_changed.emit(node)
