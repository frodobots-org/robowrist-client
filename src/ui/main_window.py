import sys
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QLineEdit,
    QTextEdit,
    QGroupBox,
    QMessageBox,
    QApplication,
    QFrame,
    QTabWidget,
    QProgressDialog,
    QFileDialog,
    QStyle,
)
from PyQt5.QtGui import QFont, QIcon

from ..core import adb, time_sync
from ..core import version as version_module
from ..core import ota as ota_module
from .sdcard_panel import SdcardPanel


def _tr(s: str) -> str:
    return s


class SyncWorker(QThread):
    """Background worker to synchronize time without blocking UI."""
    finished = pyqtSignal(bool, str)

    def __init__(self, serial: str, time_service: time_sync.TimeSyncService, parent=None):
        super().__init__(parent)
        self.serial = serial
        self._time_service = time_service

    def run(self):
        ok, msg = self._time_service.sync_host_time_to_device(self.serial)
        self.finished.emit(ok, msg)


class VersionWorker(QThread):
    """Fetch device version from /userdata/version.json."""
    finished = pyqtSignal(object)  # dict or None

    def __init__(self, serial: str, parent=None):
        super().__init__(parent)
        self.serial = serial

    def run(self):
        info = version_module.get_device_version(self.serial)
        self.finished.emit(info)


class OtaWorker(QThread):
    """Upload OTA package and reboot recovery."""
    finished = pyqtSignal(bool, str)

    def __init__(self, serial: str, local_path: str, parent=None):
        super().__init__(parent)
        self.serial = serial
        self.local_path = local_path

    def run(self):
        ok, msg = ota_module.upload_ota(self.serial, self.local_path)
        self.finished.emit(ok, msg)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(_tr("Robowrist-client"))
        self.setMinimumSize(640, 480)
        self.resize(720, 520)

        self._worker = None
        self._sdcard_panel = None
        self._time_service = time_sync.TimeSyncService()
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Device area
        dev_group = QGroupBox(_tr("Device"))
        dev_layout = QVBoxLayout(dev_group)

        dev_row = QHBoxLayout()
        dev_row.addWidget(QLabel(_tr("Connected devices:")))
        self._dev_combo = QComboBox()
        self._dev_combo.setMinimumWidth(260)
        dev_row.addWidget(self._dev_combo, 1)
        self._refresh_btn = QPushButton(_tr("Refresh"))
        self._refresh_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self._refresh_btn.clicked.connect(self._on_refresh_devices)
        dev_row.addWidget(self._refresh_btn)
        dev_layout.addLayout(dev_row)

        id_row = QHBoxLayout()
        id_row.addWidget(QLabel(_tr("Device ID:")))
        self._device_id_edit = QLineEdit()
        self._device_id_edit.setReadOnly(True)
        id_row.addWidget(self._device_id_edit, 1)
        id_row.addWidget(QLabel(_tr("HW ver:")))
        self._hw_ver_label = QLabel("-")
        id_row.addWidget(self._hw_ver_label)
        id_row.addWidget(QLabel(_tr("PCB ver:")))
        self._pcb_ver_label = QLabel("-")
        id_row.addWidget(self._pcb_ver_label)
        dev_layout.addLayout(id_row)

        layout.addWidget(dev_group)

        # Tabs: time sync | device storage | OTA
        self._tabs = QTabWidget()
        tab_time = QWidget()
        layout_time = QVBoxLayout(tab_time)
        # Time sync tab
        sync_group = QGroupBox(_tr("Sync time to RV1106 RTC"))
        sync_layout = QVBoxLayout(sync_group)
        sync_desc = QLabel(_tr("Use host network time (NTP or system time) to update the device hardware RTC."))
        sync_desc.setWordWrap(True)
        sync_layout.addWidget(sync_desc)
        self._sync_btn = QPushButton(_tr("Sync time to RTC"))
        self._sync_btn.setMinimumHeight(40)
        self._sync_btn.setProperty("cssClass", "primary")
        self._sync_btn.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self._sync_btn.clicked.connect(self._on_sync_time)
        sync_layout.addWidget(self._sync_btn)
        layout_time.addWidget(sync_group)

        # Log area
        log_group = QGroupBox(_tr("Log"))
        log_layout = QVBoxLayout(log_group)
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMinimumHeight(120)
        self._log.setFont(QFont("Consolas" if sys.platform == "win32" else "Monospace", 9))
        log_layout.addWidget(self._log)
        layout_time.addWidget(log_group)

        self._tabs.addTab(tab_time, _tr("Time sync"))
        self._sdcard_panel = SdcardPanel(self._current_serial)
        self._tabs.addTab(
            self._sdcard_panel,
            self.style().standardIcon(QStyle.SP_DirHomeIcon),
            _tr("Device storage"),
        )
        # OTA tab
        tab_ota = QWidget()
        layout_ota = QVBoxLayout(tab_ota)
        ota_desc = QLabel(
            _tr("Choose a firmware file, then click \"Start OTA\" to upload and update the device.")
        )
        ota_desc.setWordWrap(True)
        layout_ota.addWidget(ota_desc)
        ota_row = QHBoxLayout()
        self._ota_path_edit = QLineEdit()
        self._ota_path_edit.setReadOnly(True)
        self._ota_path_edit.setPlaceholderText(_tr("Choose an OTA package to upload"))
        ota_row.addWidget(self._ota_path_edit, 1)
        self._ota_browse_btn = QPushButton(_tr("Choose OTA file"))
        self._ota_browse_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogOpenButton))
        self._ota_browse_btn.clicked.connect(self._on_choose_ota)
        ota_row.addWidget(self._ota_browse_btn)
        self._ota_start_btn = QPushButton(_tr("Start OTA"))
        self._ota_start_btn.setProperty("cssClass", "primary")
        self._ota_start_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self._ota_start_btn.clicked.connect(self._on_start_ota)
        ota_row.addWidget(self._ota_start_btn)
        layout_ota.addLayout(ota_row)
        self._tabs.addTab(
            tab_ota,
            self.style().standardIcon(QStyle.SP_ArrowUp),
            _tr("OTA"),
        )
        self._tabs.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self._tabs)

        self._log_append(_tr("Connect Robowrist and click \"Refresh devices\"."))

        self._on_refresh_devices()

    def _log_append(self, text: str):
        self._log.append(text)
        self._log.verticalScrollBar().setValue(self._log.verticalScrollBar().maximum())

    def _on_tab_changed(self, index):
        if index == 1 and self._sdcard_panel:
            self._sdcard_panel._refresh_list()

    def _on_refresh_devices(self):
        self._refresh_btn.setEnabled(False)
        self._log_append(_tr("Refreshing device list..."))
        devices = adb.get_devices()
        self._dev_combo.clear()
        if not devices:
            self._dev_combo.addItem(_tr("(no device)"), None)
            self._log_append(_tr("No device detected. Check USB cable or network ADB."))
            self._device_id_edit.setText("")
            self._hw_ver_label.setText("-")
            self._pcb_ver_label.setText("-")
        else:
            for serial, status in devices:
                self._dev_combo.addItem(f"{serial}  ({status})", serial)
            self._log_append(_tr("Detected %d device(s).") % len(devices))
            # show first device info
            first_serial = devices[0][0]
            self._device_id_edit.setText(first_serial)
            self._fetch_and_show_version(first_serial)
        self._refresh_btn.setEnabled(True)
        self._update_sync_button_state()
        if self._sdcard_panel and self._tabs.currentIndex() == 1:
            self._sdcard_panel._refresh_list()

    def _fetch_and_show_version(self, serial: str):
        worker = VersionWorker(serial, self)
        worker.finished.connect(self._on_version_ready)
        worker.start()
        # keep reference to avoid GC
        self._version_worker = worker

    def _on_version_ready(self, info):
        if not info:
            self._hw_ver_label.setText("-")
            self._pcb_ver_label.setText("-")
            return
        self._hw_ver_label.setText(str(info.get("hardware_version") or "-"))
        self._pcb_ver_label.setText(str(info.get("pcb_version") or "-"))

    def _current_serial(self):
        idx = self._dev_combo.currentIndex()
        if idx < 0:
            return None
        return self._dev_combo.itemData(idx)

    def _update_sync_button_state(self):
        self._sync_btn.setEnabled(self._current_serial() is not None and self._worker is None)

    def _on_sync_time(self):
        serial = self._current_serial()
        if not serial:
            QMessageBox.warning(self, _tr("Notice"), _tr("Please connect a device and select it first."))
            return
        self._sync_btn.setEnabled(False)
        self._refresh_btn.setEnabled(False)
        self._log_append(_tr("Syncing time to device %s ...") % serial)
        self._worker = SyncWorker(serial, self._time_service, self)
        self._worker.finished.connect(self._on_sync_finished)
        self._worker.start()

    def _on_sync_finished(self, ok: bool, msg: str):
        self._worker = None
        self._sync_btn.setEnabled(True)
        self._refresh_btn.setEnabled(True)
        self._update_sync_button_state()
        self._log_append(msg)
        if ok:
            QMessageBox.information(self, _tr("Success"), _tr("Time has been synchronized and written to device RTC."))
        else:
            QMessageBox.warning(self, _tr("Time sync failed"), msg)

    # OTA tab handlers
    def _on_choose_ota(self):
        path, _ = QFileDialog.getOpenFileName(self, _tr("Choose OTA package"))
        if not path:
            return
        self._ota_path_edit.setText(path)

    def _on_start_ota(self):
        serial = self._current_serial()
        if not serial:
            QMessageBox.warning(self, _tr("Notice"), _tr("Please connect a device and select it first."))
            return
        path = self._ota_path_edit.text().strip()
        if not path:
            QMessageBox.warning(self, _tr("Notice"), _tr("Please choose an OTA package first."))
            return
        ok = QMessageBox.question(
            self,
            _tr("Confirm OTA"),
            _tr("Upload OTA package and reboot device into recovery?\n\nFile:\n%s") % path,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        ) == QMessageBox.Yes
        if not ok:
            return
        self._ota_start_btn.setEnabled(False)
        self._ota_browse_btn.setEnabled(False)
        self._log_append(_tr("Uploading OTA package for device %s ...") % serial)
        self._ota_worker = OtaWorker(serial, path, self)
        self._ota_worker.finished.connect(self._on_ota_finished)
        self._ota_worker.start()

    def _on_ota_finished(self, ok: bool, msg: str):
        self._ota_start_btn.setEnabled(True)
        self._ota_browse_btn.setEnabled(True)
        self._log_append(msg)
        if ok:
            QMessageBox.information(self, _tr("OTA"), msg)
        else:
            QMessageBox.warning(self, _tr("OTA failed"), msg)
