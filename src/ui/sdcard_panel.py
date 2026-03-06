import os
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QFileDialog,
    QHeaderView,
    QAbstractItemView,
    QInputDialog,
    QStyle,
)
from PyQt5.QtGui import QFont, QIcon

from ..core import sdcard_fs

ROOT = sdcard_fs.ROOT


def _tr(s: str) -> str:
    return s


class ListDirWorker(QThread):
    """Background worker for directory listing."""
    finished = pyqtSignal(object, str)  # (list or None, error_msg)

    def __init__(self, serial: str, path: str, parent=None):
        super().__init__(parent)
        self.serial = serial
        self.path = path

    def run(self):
        result, err = sdcard_fs.list_dir(self.serial, self.path)
        self.finished.emit(result, err)


class TransferWorker(QThread):
    """Background worker for file upload/download."""
    finished = pyqtSignal(bool, str)

    def __init__(self, serial: str, is_upload: bool, local: str, remote: str, parent=None):
        super().__init__(parent)
        self.serial = serial
        self.is_upload = is_upload
        self.local = local
        self.remote = remote

    def run(self):
        if self.is_upload:
            ok, msg = sdcard_fs.upload(self.serial, self.local, self.remote)
        else:
            ok, msg = sdcard_fs.download(self.serial, self.remote, self.local)
        self.finished.emit(ok, msg)


class MkdirWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, serial: str, path: str, parent=None):
        super().__init__(parent)
        self.serial = serial
        self.path = path

    def run(self):
        ok, msg = sdcard_fs.mkdir(self.serial, self.path)
        self.finished.emit(ok, msg)


class RmWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, serial: str, path: str, parent=None):
        super().__init__(parent)
        self.serial = serial
        self.path = path

    def run(self):
        ok, msg = sdcard_fs.rm(self.serial, self.path)
        self.finished.emit(ok, msg)


class RenameWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, serial: str, dir_path: str, old_name: str, new_name: str, parent=None):
        super().__init__(parent)
        self.serial = serial
        self.dir_path = dir_path
        self.old_name = old_name
        self.new_name = new_name

    def run(self):
        ok, msg = sdcard_fs.rename(self.serial, self.dir_path, self.old_name, self.new_name)
        self.finished.emit(ok, msg)


class FormatWorker(QThread):
    finished = pyqtSignal(bool, str)

    def __init__(self, serial: str, parent=None):
        super().__init__(parent)
        self.serial = serial

    def run(self):
        ok, msg = sdcard_fs.format_sdcard(self.serial)
        self.finished.emit(ok, msg)

class SdcardPanel(QWidget):
    """Device storage tab: browse /mnt/sdcard like a USB drive."""

    def __init__(self, get_serial_callback, parent=None):
        super().__init__(parent)
        self._get_serial = get_serial_callback
        self._current_path = ROOT
        self._list_worker = None
        self._transfer_worker = None
        self._op_worker = None  # mkdir/rm/rename/format
        self._upload_queue = []  # multiple files upload queue
        self._progress_total = 0
        self._progress_done = 0
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)

        # Path bar + go up
        path_row = QHBoxLayout()
        self._back_btn = QPushButton(_tr("Go up"))
        self._back_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowUp))
        self._back_btn.clicked.connect(self._on_back)
        path_row.addWidget(self._back_btn)
        self._path_edit = QLineEdit()
        self._path_edit.setPlaceholderText(_tr("Browse device storage path"))
        self._path_edit.returnPressed.connect(self._on_path_go)
        path_row.addWidget(self._path_edit, 1)
        self._refresh_btn = QPushButton(_tr("Refresh"))
        self._refresh_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self._refresh_btn.clicked.connect(self._on_refresh)
        path_row.addWidget(self._refresh_btn)
        layout.addLayout(path_row)

        # Toolbar
        tool_row = QHBoxLayout()
        self._new_dir_btn = QPushButton(_tr("New folder"))
        self._new_dir_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        self._new_dir_btn.clicked.connect(self._on_new_dir)
        self._upload_btn = QPushButton(_tr("Upload"))
        self._upload_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowUp))
        self._upload_btn.clicked.connect(self._on_upload)
        self._download_btn = QPushButton(_tr("Download"))
        self._download_btn.setIcon(self.style().standardIcon(QStyle.SP_ArrowDown))
        self._download_btn.clicked.connect(self._on_download)
        self._delete_btn = QPushButton(_tr("Delete"))
        self._delete_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        self._delete_btn.clicked.connect(self._on_delete)
        self._rename_btn = QPushButton(_tr("Rename"))
        self._rename_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        self._rename_btn.clicked.connect(self._on_rename)
        self._format_btn = QPushButton(_tr("Format SD card"))
        self._format_btn.setProperty("cssClass", "danger")
        self._format_btn.clicked.connect(self._on_format)
        for btn in (
            self._new_dir_btn,
            self._upload_btn,
            self._download_btn,
            self._delete_btn,
            self._rename_btn,
            self._format_btn,
        ):
            tool_row.addWidget(btn)
        tool_row.addStretch(1)
        layout.addLayout(tool_row)

        # File list
        self._table = QTableWidget()
        self._table.setColumnCount(4)
        self._table.setHorizontalHeaderLabels([_tr("Name"), _tr("Type"), _tr("Size"), _tr("Modified at")])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.doubleClicked.connect(self._on_double_click)
        layout.addWidget(self._table)

        self._path_edit.setText(self._current_path)
        self._update_back_state()

        # Progress label
        self._progress_label = QLabel("")
        layout.addWidget(self._progress_label)

    def _update_back_state(self):
        self._back_btn.setEnabled(self._current_path != ROOT and self._current_path.rstrip("/") != ROOT)

    def set_serial(self, serial):
        """Optionally called by parent when current device changes."""
        self._refresh_list()

    def _refresh_list(self):
        serial = self._get_serial()
        if not serial:
            self._table.setRowCount(0)
            return
        self._table.setRowCount(0)
        self._refresh_btn.setEnabled(False)
        self._list_worker = ListDirWorker(serial, self._current_path, self)
        self._list_worker.finished.connect(self._on_list_finished)
        self._list_worker.start()

    def _on_list_finished(self, result, err):
        self._list_worker = None
        self._refresh_btn.setEnabled(True)
        if err:
            QMessageBox.warning(self, _tr("列表失败"), err)
            return
        self._table.setRowCount(len(result) if result else 0)
        if not result:
            return
        for i, (name, is_dir, size_str, mtime_str) in enumerate(result):
            self._table.setItem(i, 0, QTableWidgetItem(name))
            self._table.setItem(i, 1, QTableWidgetItem(_tr("文件夹") if is_dir else _tr("文件")))
            self._table.setItem(i, 2, QTableWidgetItem(size_str))
            self._table.setItem(i, 3, QTableWidgetItem(mtime_str))
            self._table.item(i, 0).setData(Qt.UserRole, (name, is_dir))

    def _on_back(self):
        if self._current_path == ROOT or self._current_path.rstrip("/") == ROOT:
            return
        self._current_path = os.path.dirname(self._current_path.rstrip("/")) or ROOT
        self._path_edit.setText(self._current_path)
        self._update_back_state()
        self._refresh_list()

    def _on_path_go(self):
        path = self._path_edit.text().strip().replace("\\", "/") or ROOT
        if not path.startswith("/"):
            path = ROOT + "/" + path
        if not path.startswith(ROOT):
            path = ROOT
        self._current_path = path
        self._path_edit.setText(self._current_path)
        self._update_back_state()
        self._refresh_list()

    def _on_refresh(self):
        self._current_path = self._path_edit.text().strip().replace("\\", "/") or ROOT
        if not self._current_path.startswith(ROOT):
            self._current_path = ROOT
        self._path_edit.setText(self._current_path)
        self._refresh_list()

    def _on_double_click(self, index):
        row = index.row()
        item = self._table.item(row, 0)
        if not item:
            return
        data = item.data(Qt.UserRole)
        if not data:
            return
        name, is_dir = data
        if not is_dir:
            return
        self._current_path = (self._current_path.rstrip("/") + "/" + name).replace("//", "/")
        self._path_edit.setText(self._current_path)
        self._update_back_state()
        self._refresh_list()

    def _get_selected_names(self):
        """Return list of selected (name, is_dir) items in current directory."""
        rows = set(index.row() for index in self._table.selectionModel().selectedRows())
        out = []
        for r in rows:
            item = self._table.item(r, 0)
            if item and item.data(Qt.UserRole):
                out.append(item.data(Qt.UserRole))
        return out

    def _on_new_dir(self):
        serial = self._get_serial()
        if not serial:
            QMessageBox.warning(self, _tr("Notice"), _tr("Please select a device first."))
            return
        name, ok = QInputDialog.getText(self, _tr("New folder"), _tr("Folder name:"))
        if not ok or not name or not name.strip():
            return
        name = name.strip()
        if "/" in name or "\\" in name:
            QMessageBox.warning(self, _tr("Error"), _tr("Folder name must not contain path separators."))
            return
        path = (self._current_path.rstrip("/") + "/" + name).replace("//", "/")
        self._new_dir_btn.setEnabled(False)
        self._op_worker = MkdirWorker(serial, path, self)
        self._op_worker.finished.connect(self._on_mkdir_finished)
        self._op_worker.start()

    def _on_mkdir_finished(self, ok, msg):
        self._op_worker = None
        self._new_dir_btn.setEnabled(True)
        if ok:
            self._refresh_list()
        else:
            QMessageBox.warning(self, _tr("Failed to create folder"), msg)

    def _on_upload(self):
        serial = self._get_serial()
        if not serial:
            QMessageBox.warning(self, _tr("Notice"), _tr("Please select a device first."))
            return
        paths, _ = QFileDialog.getOpenFileNames(self, _tr("Choose files to upload"))
        if not paths:
            return
        self._upload_queue = list(paths)
        # compute total bytes
        total = 0
        for p in self._upload_queue:
            try:
                total += os.path.getsize(p)
            except OSError:
                continue
        self._progress_total = max(total, 1)
        self._progress_done = 0
        self._update_progress_label(_tr("Uploading"), self._progress_done, self._progress_total)
        self._do_upload_next(serial)

    def _do_upload_next(self, serial):
        if not self._upload_queue:
            self._upload_btn.setEnabled(True)
            self._download_btn.setEnabled(True)
            self._refresh_list()
            self._update_progress_label(_tr("Upload completed"), self._progress_total, self._progress_total)
            QMessageBox.information(self, _tr("Done"), _tr("Upload completed."))
            return
        self._upload_btn.setEnabled(False)
        local = self._upload_queue.pop(0)
        remote = self._current_path
        self._transfer_worker = TransferWorker(serial, True, local, remote, self)
        self._transfer_worker.finished.connect(self._on_transfer_finished)
        self._transfer_worker.start()

    def _on_transfer_finished(self, ok, msg):
        self._transfer_worker = None
        serial = self._get_serial()
        if not ok:
            self._upload_btn.setEnabled(True)
            self._download_btn.setEnabled(True)
            QMessageBox.warning(self, _tr("Transfer failed"), msg)
            self._upload_queue.clear()
            self._update_progress_label(_tr("Transfer failed"), self._progress_done, self._progress_total)
            return
        # update progress after one file
        try:
            if self._transfer_worker and self._transfer_worker.is_upload:
                self._progress_done += os.path.getsize(self._transfer_worker.local)
        except Exception:
            pass
        self._update_progress_label(_tr("Transferring"), self._progress_done, self._progress_total)
        if self._upload_queue:
            self._do_upload_next(serial)
        else:
            self._upload_btn.setEnabled(True)
            self._download_btn.setEnabled(True)
            self._refresh_list()
            self._update_progress_label(_tr("Transfer completed"), self._progress_total, self._progress_total)
            QMessageBox.information(self, _tr("Done"), msg)

    def _on_download(self):
        serial = self._get_serial()
        if not serial:
            QMessageBox.warning(self, _tr("Notice"), _tr("Please select a device first."))
            return
        selected = self._get_selected_names()
        if not selected:
            QMessageBox.warning(self, _tr("Notice"), _tr("Please select at least one file or folder."))
            return
        dest = QFileDialog.getExistingDirectory(self, _tr("Choose download destination"))
        if not dest:
            return
        name, is_dir = selected[0]
        remote = (self._current_path.rstrip("/") + "/" + name).replace("//", "/")
        # compute remote size
        total = sdcard_fs.get_path_size(serial, remote)
        self._progress_total = max(total, 1)
        self._progress_done = 0
        self._update_progress_label(_tr("Downloading"), self._progress_done, self._progress_total)
        self._download_btn.setEnabled(False)
        self._transfer_worker = TransferWorker(serial, False, dest, remote, self)
        self._transfer_worker.finished.connect(self._on_transfer_finished)
        self._transfer_worker.start()

    def _on_delete(self):
        serial = self._get_serial()
        if not serial:
            QMessageBox.warning(self, _tr("Notice"), _tr("Please select a device first."))
            return
        selected = self._get_selected_names()
        if not selected:
            QMessageBox.warning(self, _tr("Notice"), _tr("Please select at least one item to delete."))
            return
        names = [n for n, _ in selected]
        ok = QMessageBox.question(
            self, _tr("Confirm delete"),
            _tr("Delete the following items?\n\n%s") % "\n".join(names),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        ) == QMessageBox.Yes
        if not ok:
            return
        path = (self._current_path.rstrip("/") + "/" + names[0]).replace("//", "/")
        self._delete_btn.setEnabled(False)
        self._op_worker = RmWorker(serial, path, self)
        self._op_worker.finished.connect(self._on_rm_finished)
        self._op_worker.start()

    def _on_rm_finished(self, ok, msg):
        self._op_worker = None
        self._delete_btn.setEnabled(True)
        if ok:
            self._refresh_list()
        else:
            QMessageBox.warning(self, _tr("Delete failed"), msg)

    def _on_rename(self):
        serial = self._get_serial()
        if not serial:
            QMessageBox.warning(self, _tr("Notice"), _tr("Please select a device first."))
            return
        selected = self._get_selected_names()
        if not selected or len(selected) != 1:
            QMessageBox.warning(self, _tr("Notice"), _tr("Please select a single item to rename."))
            return
        old_name = selected[0][0]
        new_name, ok = QInputDialog.getText(self, _tr("Rename"), _tr("New name:"), text=old_name)
        if not ok or not new_name or new_name.strip() == old_name:
            return
        new_name = new_name.strip()
        if "/" in new_name or "\\" in new_name:
            QMessageBox.warning(self, _tr("Error"), _tr("Name must not contain path separators."))
            return
        self._rename_btn.setEnabled(False)
        self._op_worker = RenameWorker(serial, self._current_path, old_name, new_name, self)
        self._op_worker.finished.connect(self._on_rename_finished)
        self._op_worker.start()

    def _on_rename_finished(self, ok, msg):
        self._op_worker = None
        self._rename_btn.setEnabled(True)
        if ok:
            self._refresh_list()
        else:
            QMessageBox.warning(self, _tr("Rename failed"), msg)

    def _on_format(self):
        serial = self._get_serial()
        if not serial:
            QMessageBox.warning(self, _tr("Notice"), _tr("Please select a device first."))
            return
        msg = _tr(
            "This will format the SD card (/dev/mmcblk0p1)\n"
            "and erase all data under /mnt/sdcard permanently.\n\n"
            "Make sure you have backed up important data. Continue?"
        )
        ok = QMessageBox.question(
            self,
            _tr("Confirm SD card format"),
            msg,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        ) == QMessageBox.Yes
        if not ok:
            return
        self._format_btn.setEnabled(False)
        self._op_worker = FormatWorker(serial, self)
        self._op_worker.finished.connect(self._on_format_finished)
        self._op_worker.start()

    def _on_format_finished(self, ok, msg):
        self._op_worker = None
        self._format_btn.setEnabled(True)
        if ok:
            self._current_path = ROOT
            self._path_edit.setText(self._current_path)
            self._update_back_state()
            self._refresh_list()
            QMessageBox.information(self, _tr("Done"), msg)
        else:
            QMessageBox.warning(self, _tr("Format failed"), msg)

    def _update_progress_label(self, prefix: str, done: int, total: int) -> None:
        if total <= 0:
            self._progress_label.setText("")
            return
        percent = int(done * 100 / total)
        self._progress_label.setText(
            f"{prefix}: {done}/{total} bytes ({percent}%)"
        )
