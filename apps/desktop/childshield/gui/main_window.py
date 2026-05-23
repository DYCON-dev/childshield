"""Main window: drag-and-drop or open dialog, process the image, show result."""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QImage, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from childshield.analysis import Face, FaceAnalyzer
from childshield.blur import blur_faces

SUPPORTED_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
DROP_HINT = "Drag and drop an image here, or click below."


class _DropZone(QLabel):
    def __init__(self, parent: "MainWindow") -> None:
        super().__init__(parent)
        self._owner = parent
        self.setObjectName("dropZone")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText(DROP_HINT)
        self.setMinimumSize(420, 280)
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
        self.setMinimumSize(600, 760)

        self._analyzer = FaceAnalyzer()

        # Cache the last loaded image + faces so the user can re-blur with
        # different settings without re-running detection.
        self._current_image: np.ndarray | None = None
        self._current_path: Path | None = None
        self._current_faces: list[Face] = []
        self._last_output: Path | None = None

        layout = QVBoxLayout(self)

        self._drop = _DropZone(self)
        layout.addWidget(self._drop)

        # Threshold slider
        slider_row = QHBoxLayout()
        slider_row.addWidget(QLabel("Blur if estimated age ≤"))
        self._threshold_label = QLabel("12")
        self._threshold_label.setObjectName("thresholdValue")
        self._threshold_label.setMinimumWidth(30)
        self._threshold = QSlider(Qt.Orientation.Horizontal)
        self._threshold.setMinimum(0)
        self._threshold.setMaximum(30)
        self._threshold.setValue(12)
        self._threshold.valueChanged.connect(self._on_threshold_changed)
        slider_row.addWidget(self._threshold)
        slider_row.addWidget(self._threshold_label)
        layout.addLayout(slider_row)

        # "Blur all" override
        self._blur_all = QCheckBox("Blur all detected faces (override)")
        self._blur_all.toggled.connect(self._reprocess_current)
        layout.addWidget(self._blur_all)

        # Action buttons
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
        self._status.setWordWrap(True)
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
        from PyQt6.QtCore import QUrl
        from PyQt6.QtGui import QDesktopServices

        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._last_output.parent)))

    def _on_threshold_changed(self, value: int) -> None:
        self._threshold_label.setText(str(value))
        self._reprocess_current()

    # ----------------------------------------------------------- processing

    def process_image(self, path: Path) -> None:
        if path.suffix.lower() not in SUPPORTED_EXT:
            self._error(f"Unsupported file type: {path.suffix}")
            return

        image = cv2.imread(str(path))
        if image is None:
            self._error(f"Could not read image: {path.name}")
            return

        self._status.setText(f"Analyzing {path.name}…")
        self.repaint()

        faces = self._analyzer.analyze(image)

        self._current_image = image
        self._current_path = path
        self._current_faces = faces

        self._save_and_display()

    def _reprocess_current(self) -> None:
        if self._current_image is not None:
            self._save_and_display()

    def _save_and_display(self) -> None:
        assert self._current_image is not None
        assert self._current_path is not None

        threshold = self._threshold.value()
        blur_all = self._blur_all.isChecked()

        if blur_all:
            faces_to_blur = self._current_faces
        else:
            faces_to_blur = [f for f in self._current_faces if f.age <= threshold]

        blurred = blur_faces(self._current_image, faces_to_blur)

        out_path = self._current_path.with_name(f"blurred_{self._current_path.name}")
        if not cv2.imwrite(str(out_path), blurred):
            self._error(f"Could not save: {out_path}")
            return

        self._last_output = out_path
        self._reveal_btn.setEnabled(True)
        self._display(blurred)

        total = len(self._current_faces)
        blurred_count = len(faces_to_blur)
        if total == 0:
            msg = "No faces detected."
        else:
            age_summary = ", ".join(f"~{f.age}y" for f in self._current_faces)
            msg = (
                f"{total} face(s) detected ({age_summary}). "
                f"Blurred {blurred_count}. Saved as {out_path.name}"
            )
        self._status.setText(msg)

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
