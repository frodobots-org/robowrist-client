import sys
import os

# Ensure we can import from project root when running as module or frozen.
if getattr(sys, "frozen", False):
    _root = os.path.dirname(sys.executable)
else:
    _root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _root not in sys.path:
    sys.path.insert(0, _root)

if getattr(sys, "frozen", False):
    _resource_base = getattr(sys, "_MEIPASS", _root)
else:
    _resource_base = _root

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from src.ui.main_window import MainWindow
from src.ui.style import nordic_stylesheet


def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    app.setApplicationName("Robowrist-client")
    app.setStyleSheet(nordic_stylesheet())
    icon_path = os.path.join(_resource_base, "assets", "icon.png")
    if os.path.isfile(icon_path):
        icon = QIcon(icon_path)
        app.setWindowIcon(icon)
    win = MainWindow()
    if os.path.isfile(icon_path):
        win.setWindowIcon(icon)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
