"""Entry point for the standalone ACAMP desktop interface."""

from __future__ import annotations

import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from acamp.ui.main_window import MainWindow
from acamp.ui.theme import APP_STYLESHEET


def create_application() -> tuple[QApplication, MainWindow]:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setApplicationName("ACAMP WBSDAC 2026")
    app.setOrganizationName("WBSDAC")
    app.setStyleSheet(APP_STYLESHEET)

    window = MainWindow()
    return app, window


def main() -> int:
    app, window = create_application()
    window.show()

    # A non-interactive startup check used by development verification.
    if "--smoke-test" in sys.argv:
        QTimer.singleShot(250, app.quit)

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
