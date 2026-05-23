"""Entry point: `childshield` or `python -m childshield`."""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication

from childshield.gui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)

    style_path = Path(__file__).parent / "gui" / "style.qss"
    if style_path.exists():
        app.setStyleSheet(style_path.read_text())

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
