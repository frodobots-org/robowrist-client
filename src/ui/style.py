"""Nordic minimal style for Robowrist-client."""


def nordic_stylesheet() -> str:
    """Return a Qt stylesheet implementing a light Nordic look."""
    return """
    QWidget {
        background-color: #F5F5F7;
        color: #1F2933;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        font-size: 10pt;
    }

    QGroupBox {
        border: 1px solid #E1E4EA;
        border-radius: 8px;
        margin-top: 12px;
        padding: 8px;
        background-color: #FFFFFF;
    }

    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 4px;
        color: #4B5563;
        font-weight: 600;
    }

    QTabWidget::pane {
        border-top: 1px solid #E1E4EA;
        margin-top: 4px;
    }

    QTabBar::tab {
        padding: 6px 18px;
        border: 1px solid transparent;
        border-bottom: none;
        background: #E5E7EB;
        color: #4B5563;
        border-top-left-radius: 8px;
        border-top-right-radius: 8px;
        margin-right: 4px;
    }

    QTabBar::tab:selected {
        background: #FFFFFF;
        border-color: #D1D5DB;
        color: #111827;
    }

    QPushButton {
        border-radius: 6px;
        padding: 6px 14px;
        border: 1px solid #D1D5DB;
        background-color: #FFFFFF;
        color: #111827;
    }

    QPushButton:hover {
        background-color: #E5F0FF;
        border-color: #5C7CFA;
    }

    QPushButton:pressed {
        background-color: #D0E0FF;
    }

    QPushButton:disabled {
        background-color: #F3F4F6;
        color: #9CA3AF;
        border-color: #E5E7EB;
    }

    QLineEdit, QComboBox, QTextEdit {
        border-radius: 6px;
        border: 1px solid #D1D5DB;
        padding: 4px 6px;
        background-color: #FFFFFF;
    }

    QLineEdit:focus, QComboBox:focus, QTextEdit:focus {
        border-color: #5C7CFA;
        outline: none;
    }

    QTableWidget {
        background-color: #FFFFFF;
        border: 1px solid #E5E7EB;
        border-radius: 8px;
        gridline-color: #E5E7EB;
    }

    QHeaderView::section {
        background-color: #F3F4F6;
        border: none;
        border-bottom: 1px solid #E5E7EB;
        padding: 6px 8px;
        font-weight: 600;
        color: #4B5563;
    }

    QTableWidget::item:selected {
        background-color: #E5F0FF;
        color: #111827;
    }

    QStatusBar {
        background-color: #F9FAFB;
        border-top: 1px solid #E5E7EB;
    }
    """

