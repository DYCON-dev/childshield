"""Main window: drag-and-drop or open dialog, processes the image, shows result."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QImage, QPixmap
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from childshield.blur import blur_faces
from childshield.detection import FaceDetector

SUPPORTED_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
DROP_HINT = "Drag and drop an image here, or click below."


class _DropZone(QLabel):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        self._owner = parent
        self.setObjectName("dropZone")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText(DROP_HINT)
        self.setMinimumSize(420, 260)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if not urls:
            return
        self._owner.process_image(Path(urls[0].toLocalFile()))


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ChildShield")
        self.setMinimumSize(560, 620)

        self._detector = FaceDetector()
        self._last_output: Path | None = None

        layout = QVBoxLayout(self)

        self._drop = _DropZone(self)
        layout.addWidget(self._drop)

        btn_row = QHBoxLayout()
        self._open_btn = QPushButton("Open image…")
        self._open_btn.clicked.connect(self._open_dialog)
        btn_row.addWidget(self._open_btn)

        self._reveal_btn = QPushButton("Show saved file")
        self._reveal_btn.setEnabled(False)
        self._reveal_btn.clicked.connect(self._reveal_output)
        btn_row.addWidget(self._reveal_btn)
        layout.addLayout(btn_row)

        self._status = QLabel("Ready.")
        self._status.setObjectName("status")
        layout.addWidget(self._status)

    # ------------------------------------------------------------------ slots

    def _open_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open image", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if path:
            self.process_image(Path(path))

    def _reveal_output(self) -> None:
        if self._last_output is None or not self._last_output.exists():
            return
        # cross-platform "show in folder" via QDesktopServices on the directory
        from PyQt6.QtCore import QUrl
        from PyQt6.QtGui import QDesktopServices

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._last_output.parent)))

    # ----------------------------------------------------------- processing

    def process_image(self, path: Path) -> None:
        if path.suffix.lower() not in SUPPORTED_EXT:
            self._error(f"Unsupported file type: {path.suffix}")
            return

        image = cv2.imread(str(path))
        if image is None:
            self._error(f"Could not read image: {path.name}")
            return

        self._status.setText(f"Processing {path.name}…")
        self.repaint()

        faces = self._detector.detect(image)
        blurred = blur_faces(image, faces)

        out_path = path.with_name(f"blurred_{path.name}")
        if not cv2.imwrite(str(out_path), blurred):
            self._error(f"Could not save: {out_path}")
            return

        self._last_output = out_path
        self._reveal_btn.setEnabled(True)
        self._display(blurred)
        self._status.setText(
            f"{len(faces)} face(s) blurred. Saved as {out_path.name}"
        )

    def _display(self, image_bgr: np.ndarray) -> None:
        rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pix = QPixmap.fromImage(qimg).scaled(
            self._drop.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._drop.setPixmap(pix)

    def _error(self, message: str) -> None:
        self._status.setText("Error.")
        QMessageBox.critical(self, "ChildShield", message)
