"""Main window: load an image, show face overlays, let the user toggle blur per face."""

from __future__ import annotations

from pathlib import Path

import cv2
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtWidgets import (
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
from childshield.gui.canvas import ImageCanvas

SUPPORTED_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}
DEFAULT_AGE_THRESHOLD = 12


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ChildShield")
        self.setMinimumSize(700, 820)

        self._analyzer = FaceAnalyzer()
        self._current_path: Path | None = None
        self._current_faces: list[Face] = []
        self._last_output: Path | None = None

        layout = QVBoxLayout(self)

        # Image canvas with face overlays
        self._canvas = ImageCanvas(
            on_drop=self._on_drop,
            on_state_change=self._on_canvas_changed,
        )
        layout.addWidget(self._canvas, stretch=1)

        # Live counter showing blur vs. keep
        self._counter = QLabel("")
        self._counter.setObjectName("counter")
        self._counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._counter)

        # Help line
        self._help = QLabel(
            "Red boxes will be blurred. Green ones will stay clear. Click any face to toggle."
        )
        self._help.setObjectName("help")
        self._help.setWordWrap(True)
        layout.addWidget(self._help)

        # Auto-select threshold
        slider_row = QHBoxLayout()
        slider_row.addWidget(QLabel("Auto-select faces estimated ≤"))
        self._threshold_label = QLabel(f"{DEFAULT_AGE_THRESHOLD}y")
        self._threshold_label.setObjectName("thresholdValue")
        self._threshold_label.setMinimumWidth(40)
        self._threshold = QSlider(Qt.Orientation.Horizontal)
        self._threshold.setMinimum(0)
        self._threshold.setMaximum(30)
        self._threshold.setValue(DEFAULT_AGE_THRESHOLD)
        self._threshold.valueChanged.connect(self._on_threshold_changed)
        slider_row.addWidget(self._threshold)
        slider_row.addWidget(self._threshold_label)
        layout.addLayout(slider_row)

        # Bulk-select buttons
        bulk_row = QHBoxLayout()
        self._blur_all_btn = QPushButton("Blur all")
        self._blur_all_btn.setObjectName("secondary")
        self._blur_all_btn.clicked.connect(lambda: self._canvas.set_all(True))
        bulk_row.addWidget(self._blur_all_btn)

        self._keep_all_btn = QPushButton("Blur none")
        self._keep_all_btn.setObjectName("secondary")
        self._keep_all_btn.clicked.connect(lambda: self._canvas.set_all(False))
        bulk_row.addWidget(self._keep_all_btn)

        self._reapply_btn = QPushButton("Re-apply auto-select")
        self._reapply_btn.setObjectName("secondary")
        self._reapply_btn.clicked.connect(self._apply_auto_selection)
        bulk_row.addWidget(self._reapply_btn)
        layout.addLayout(bulk_row)

        # Action buttons
        action_row = QHBoxLayout()
        self._open_btn = QPushButton("Open image…")
        self._open_btn.clicked.connect(self._open_dialog)
        action_row.addWidget(self._open_btn)

        self._save_btn = QPushButton("Save blurred copy")
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._save)
        action_row.addWidget(self._save_btn)

        self._reveal_btn = QPushButton("Show saved file")
        self._reveal_btn.setObjectName("secondary")
        self._reveal_btn.setEnabled(False)
        self._reveal_btn.clicked.connect(self._reveal_output)
        action_row.addWidget(self._reveal_btn)
        layout.addLayout(action_row)

        self._status = QLabel("Ready.")
        self._status.setObjectName("status")
        self._status.setWordWrap(True)
        layout.addWidget(self._status)

    # ---------------------------------------------------------- slots

    def _on_drop(self, path: str) -> None:
        if path:
            self.process_image(Path(path))

    def _open_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open image", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)"
        )
        if path:
            self.process_image(Path(path))

    def _reveal_output(self) -> None:
        if self._last_output is None or not self._last_output.exists():
            return
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._last_output.parent)))

    def _on_threshold_changed(self, value: int) -> None:
        self._threshold_label.setText(f"{value}y")
        # We do NOT re-apply automatically here — the user might have manual
        # selections they don't want clobbered. The "Re-apply" button does it explicitly.

    def _on_canvas_changed(self) -> None:
        """Update the live counter every time the user toggles a face."""
        total = self._canvas.get_face_count()
        to_blur = self._canvas.get_blur_count()
        keep = total - to_blur
        if total == 0:
            self._counter.setText("")
            return
        self._counter.setText(
            f"🔴 {to_blur} blurred   •   🟢 {keep} clear   •   {total} total"
        )

    # ------------------------------------------------------ processing

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
        self._current_path = path
        self._current_faces = faces
        self._save_btn.setEnabled(True)

        threshold = self._threshold.value()
        flags = [f.age <= threshold for f in faces]
        self._canvas.set_image(image, faces, flags)

        if not faces:
            self._status.setText(f"No faces detected in {path.name}.")
        else:
            age_summary = ", ".join(f"~{f.age}y" for f in faces)
            to_blur = sum(flags)
            self._status.setText(
                f"{len(faces)} face(s) detected ({age_summary}). "
                f"Auto-selected {to_blur} for blur. Click any face to override."
            )

    def _apply_auto_selection(self) -> None:
        if not self._current_faces:
            return
        threshold = self._threshold.value()
        flags = [f.age <= threshold for f in self._current_faces]
        self._canvas.set_image(self._canvas.get_source(), self._current_faces, flags)

    def _save(self) -> None:
        if self._current_path is None or not self._current_faces:
            src = self._canvas.get_source()
            if src is None:
                return
            # No faces — just save a copy
            out_path = self._current_path.with_name(f"blurred_{self._current_path.name}")
            cv2.imwrite(str(out_path), src)
            self._after_save(out_path, blurred_count=0)
            return

        flags = self._canvas.get_blur_flags()
        faces_to_blur = [f for f, b in zip(self._current_faces, flags) if b]
        src = self._canvas.get_source()
        assert src is not None
        result = blur_faces(src, faces_to_blur)

        out_path = self._current_path.with_name(f"blurred_{self._current_path.name}")
        if not cv2.imwrite(str(out_path), result):
            self._error(f"Could not save: {out_path}")
            return
        self._after_save(out_path, blurred_count=len(faces_to_blur))

    def _after_save(self, out_path: Path, blurred_count: int) -> None:
        self._last_output = out_path
        self._reveal_btn.setEnabled(True)
        self._status.setText(f"Saved {out_path.name} ({blurred_count} face(s) blurred).")

    def _error(self, message: str) -> None:
        self._status.setText("Error.")
        QMessageBox.critical(self, "ChildShield", message)
