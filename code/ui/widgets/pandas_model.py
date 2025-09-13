# code/ui/widgets/pandas_model.py
# Editable DataFrame model for QTableView.
# Fixed for PySide6 (Qt6) → no QVariant needed.

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
import pandas as pd


class PandasModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self._df = df

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._df.index)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._df.columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None

        value = self._df.iat[index.row(), index.column()]

        if role in (Qt.DisplayRole, Qt.EditRole):
            return "" if pd.isna(value) else str(value)

        if role == Qt.TextAlignmentRole:
            col_name = self._df.columns[index.column()]
            if col_name.lower() in {"id", "value", "count"}:
                return int(Qt.AlignRight | Qt.AlignVCenter)
            return int(Qt.AlignLeft | Qt.AlignVCenter)

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return str(self._df.columns[section])
        return str(self._df.index[section]) if section < len(self._df.index) else None

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable

    def setData(self, index: QModelIndex, value, role: int = Qt.EditRole):
        if role != Qt.EditRole or not index.isValid():
            return False
        col = self._df.columns[index.column()]
        if col.lower() in {"id", "value", "count"}:
            try:
                self._df.iat[index.row(), index.column()] = int(float(value))
            except Exception:
                self._df.iat[index.row(), index.column()] = value
        else:
            self._df.iat[index.row(), index.column()] = value
        self.dataChanged.emit(index, index, [Qt.DisplayRole, Qt.EditRole])
        return True

    def dataframe(self) -> pd.DataFrame:
        return self._df

    def insert_empty_row(self, default_row: dict | None = None):
        self.beginInsertRows(QModelIndex(), len(self._df), len(self._df))
        if default_row is None:
            default_row = {c: "" for c in self._df.columns}
        self._df.loc[len(self._df)] = default_row
        self.endInsertRows()

    def remove_rows(self, rows: list[int]):
        for r in sorted(rows, reverse=True):
            self.beginRemoveRows(QModelIndex(), r, r)
            self._df.drop(self._df.index[r], inplace=True)
            self._df.reset_index(drop=True, inplace=True)
            self.endRemoveRows()