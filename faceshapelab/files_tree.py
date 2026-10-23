from PySide6.QtCore import (
    QAbstractProxyModel,
    QFileInfo,
    QModelIndex,
    QPersistentModelIndex,
)
from PySide6.QtWidgets import QFileSystemModel


class FilesTreeModel(QAbstractProxyModel):
    """Keep shortcut branches in the tree while browsing their target directories."""

    def __init__(self, parent=None):
        super().__init__(parent)
        source = QFileSystemModel(self)
        source.setResolveSymlinks(False)
        self.setSourceModel(source)
        self.nodes = {}
        source.rowsAboutToBeInserted.connect(self.layout_about_to_change)
        source.rowsAboutToBeRemoved.connect(self.layout_about_to_change)
        source.layoutAboutToBeChanged.connect(self.layout_about_to_change)
        source.rowsInserted.connect(self.layout_changed)
        source.rowsRemoved.connect(self.layout_changed)
        source.layoutChanged.connect(self.layout_changed)
        source.dataChanged.connect(self.data_changed)

    def layout_about_to_change(self, *args):
        self.layoutAboutToBeChanged.emit()
        self.old_indexes = self.persistentIndexList()

    def layout_changed(self, *args):
        self.changePersistentIndexList(
            self.old_indexes,
            [
                self.node_index(index.internalPointer(), index.column())
                for index in self.old_indexes
            ],
        )
        self.layoutChanged.emit()

    def data_changed(self, first, last, roles):
        for node in list(self.nodes.values()):
            source = node[0]
            if (
                source.parent() == first.parent()
                and first.row() <= source.row() <= last.row()
            ):
                self.dataChanged.emit(
                    self.node_index(node, first.column()),
                    self.node_index(node, last.column()),
                    roles,
                )

    def node_index(self, node, column=0):
        if not node[0].isValid() or (
            node[1] is not None and not self.node_index(node[1]).isValid()
        ):
            return QModelIndex()
        return self.createIndex(node[0].row(), column, node)

    def branch_index(self, index):
        if not index.isValid():
            return QModelIndex()
        source = self.mapToSource(index)
        info = self.sourceModel().fileInfo(source)
        if info.isShortcut():
            target = info.symLinkTarget()
            if QFileInfo(target).isDir():
                return self.sourceModel().index(target)
        return source

    def mapToSource(self, index):
        if not index.isValid():
            return QModelIndex()
        return QModelIndex(index.internalPointer()[0]).siblingAtColumn(index.column())

    def mapFromSource(self, index):
        if not index.isValid():
            return QModelIndex()
        parent = self.mapFromSource(index.parent())
        return self.index(index.row(), index.column(), parent)

    def index(self, row, column=0, parent=QModelIndex()):  # noqa: B008 - immutable Qt index
        if isinstance(row, str):
            return self.mapFromSource(self.sourceModel().index(row, column))
        source = self.sourceModel().index(row, column, self.branch_index(parent))
        if not source.isValid():
            return QModelIndex()
        source = source.siblingAtColumn(0)
        parent_node = parent.internalPointer() if parent.isValid() else None
        key = (id(parent_node), QPersistentModelIndex(source))
        if key not in self.nodes:
            self.nodes[key] = (QPersistentModelIndex(source), parent_node)
        return self.node_index(self.nodes[key], column)

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()
        node = index.internalPointer()[1]
        return self.node_index(node) if node is not None else QModelIndex()

    def rowCount(self, parent=QModelIndex()):  # noqa: B008 - immutable Qt index
        if parent.column() > 0:
            return 0
        return self.sourceModel().rowCount(self.branch_index(parent))

    def columnCount(self, parent=QModelIndex()):  # noqa: B008 - immutable Qt index
        return self.sourceModel().columnCount(self.mapToSource(parent))

    def hasChildren(self, parent=QModelIndex()):  # noqa: B008 - immutable Qt index
        return parent.column() <= 0 and self.sourceModel().hasChildren(
            self.branch_index(parent)
        )

    def canFetchMore(self, parent):
        return self.sourceModel().canFetchMore(self.branch_index(parent))

    def fetchMore(self, parent):
        self.sourceModel().fetchMore(self.branch_index(parent))

    def data(self, index, role):
        return self.sourceModel().data(self.mapToSource(index), role)

    def flags(self, index):
        return self.sourceModel().flags(self.mapToSource(index))

    def sort(self, column, order):
        self.sourceModel().sort(column, order)

    def mimeData(self, indexes):
        return self.sourceModel().mimeData(
            [self.mapToSource(index) for index in indexes]
        )

    def filePath(self, index):
        return self.sourceModel().filePath(self.mapToSource(index))

    def setRootPath(self, path):
        return self.mapFromSource(self.sourceModel().setRootPath(path))
