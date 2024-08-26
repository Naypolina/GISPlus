# Модель для отображения таблиц

from PyQt6.QtCore import QAbstractTableModel, Qt, QModelIndex
from PyQt6 import QtWidgets, QtCore, QtGui

class PandasModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self._data = data

    def rowCount(self, index):
        return self._data.shape[0]

    def columnCount(self, parent=None):
        return self._data.shape[1]

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid():
            if role == Qt.ItemDataRole.DisplayRole:
                value = self._data.iloc[index.row(), index.column()]
                return str(value)
            elif role == Qt.ItemDataRole.BackgroundRole:
                if index.row() % 2 == 0:
                    return QtGui.QColor('#f5f5f5')
                else:
                    return QtGui.QColor('#e3e3e3')

    # def setData(self, index, value, role):
    #     if role == Qt.ItemDataRole.CheckStateRole:
    #         checked = value == Qt.CheckState.Checked
    #         self._checked[index.row()] = checked
    #         return True

    def headerData(self, col, orientation, role):
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                return str(self._data.columns[col])
            if orientation == Qt.Orientation.Vertical:
                return str(self._data.index[col])
        else:
            if role == Qt.ItemDataRole.FontRole:
                font = QtGui.QFont('Montserrat', 14)
                font.setBold(True)
                return font



    def flags(self, index):
        # if index.column() == 1:
        #     return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable
        # else:
        #     return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        return Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
