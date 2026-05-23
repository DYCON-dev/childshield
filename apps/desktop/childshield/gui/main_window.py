"""Main window: header + image canvas + faces panel + controls."""

from __future__ import annotations

from pathlib import Path

import cv2
from PyQt6.QtCore import QSize, Qt, QUrl
from PyQt6.QtGui import QDesktopServices, QIcon, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtSvgWidgets import QSvgWidget
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSlider,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from childshield.analysis import Face, FaceAnalyzer
from childshield.blur import blur_faces
from childshield.gui.canvas import ImageCanvas
from childshield.gui.faces_panel import FacesPanel

SUPPORTED_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".webp"}

# By default we blur anyone potentially under 18 — buckets whose lower
# bound is ≤ 17 (so 0-2, 3-9, 10-19 all get auto-flagged).
DEFAULT_AGE_THRESHOLD = 17


def _logo_path() -> Path:
    return Path(__file__).parent.parent / "assets" / "logo.svg"


def _logo_pixmap(size: int) -> QPixmap:
    """Render the SVG logo into a QPixmap of the requested edge size."""
    from PyQt6.QtCore import QSize as _QSize
    from PyQt6.QtGui import QPainter

    renderer = QSvgRenderer(str(_logo_path()))
    pix = QPixmap(_QSize(size, size))
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    renderer.render(painter)
    painter.end()
    return pix


class MainWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ChildShield")
        self.setWindowIcon(QIcon(_logo_pixmap(256)))
        self.setMinimumSize(960, 720)

        self._analyzer = FaceAnalyzer()
        self._current_path: Path | None = None
        self._current_faces: list[Face] = []
        self._last_output: Path | None = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        outer.addWidget(self._build_header())
        outer.addWidget(self._build_body(), stretch=1)
        outer.addWidget(self._build_controls())

    # ----------------------------------------------------------- layout

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("header")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(20, 14, 20, 14)
        h_layout.setSpacing(12)

        logo = QSvgWidget(str(_logo_path()))
        logo.setFixedSize(QSize(36, 36))
        h_layout.addWidget(logo)

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        title = QLabel("ChildShield")
        title.setObjectName("appTitle")
        subtitle = QLabel("Blur faces before sharing")
        subtitle.setObjectName("appSubtitle")
        title_col.addWidget(title)
        title_col.addWidget(subtitle)
        h_layout.addLayout(title_col)
        h_layout.addStretch()

        return header

    def _build_body(self) -> QWidget:
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setObjectName("body")
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(1)

        self._canvas = ImageCanvas(
            on_drop=self._on_drop,
            on_state_change=self._on_canvas_changed,
        )
        splitter.addWidget(self._canvas)

        self._faces_panel = FacesPanel(on_toggle=self._on_panel_toggle)
        splitter.addWidget(self._faces_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        splitter.setSizes([700, 280])
        return splitter

    def _build_controls(self) -> QWidget:
        wrapper = QWidget()
        wrapper.setObjectName("controls")
        col = QVBoxLayout(wrapper)
        col.setContentsMargins(20, 12, 20, 16)
        col.setSpacing(10)

        # Threshold row
        slider_row = QHBoxLayout()
        slider_row.setSpacing(10)
        label = QLabel("Auto-blur if age range may include")
        label.setObjectName("controlLabel")
        slider_row.addWidget(label)

        self._threshold = QSlider(Qt.Orientation.Horizontal)
        self._threshold.setMinimum(0)
        self._threshold.setMaximum(30)
        self._threshold.setValue(DEFAULT_AGE_THRESHOLD)
        self._threshold.valueChanged.connect(self._on_threshold_changed)
        slider_row.addWidget(self._threshold, stretch=1)

        self._threshold_label = QLabel(f"≤ {DEFAULT_AGE_THRESHOLD}y")
        self._threshold_label.setObjectName("thresholdValue")
        self._threshold_label.setMinimumWidth(50)
        slider_row.addWidget(self._threshold_label)
        col.addLayout(slider_row)

        # Bulk + action row
        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self._blur_all_btn = QPushButton("Blur all")
        self._blur_all_btn.setObjectName("secondary")
        self._blur_all_btn.clicked.connect(lambda: self._canvas.set_all(True))
        action_row.addWidget(self._blur_all_btn)

        self._keep_all_btn = QPushButton("Blur none")
        self._keep_all_btn.setObjectName("secondary")
        self._keep_all_btn.clicked.connect(lambda: self._canvas.set_all(False))
        action_row.addWidget(self._keep_all_btn)

        self._reapply_btn = QPushButton("Re-apply auto")
        self._reapply_btn.setObjectName("secondary")
        self._reapply_btn.clicked.connect(self._apply_auto_selection)
        action_row.addWidget(self._reapply_btn)

        action_row.addStretch()

        self._open_btn = QPushButton("Open image…")
        self._open_btn.clicked.connect(self._open_dialog)
        action_row.addWidget(self._open_btn)

        self._save_btn = QPushButton("Save blurred copy")
        self._save_btn.setEnabled(False)
        self._save_btn.clicked.connect(self._save)
        action_row.addWidget(self._save_btn)

        self._reveal_btn = QPushButton("Show saved")
        self._reveal_btn.setObjectName("secondary")
        self._reveal_btn.setEnabled(False)
        self._reveal_btn.clicked.connect(self._reveal_output)
        action_row.addWidget(self._reveal_btn)

        col.addLayout(action_row)

        # Status footer
        self._counter = QLabel("")
        self._counter.setObjectName("counter")
        self._counter.setAlignment(Qt.AlignmentFlag.AlignCenter)
        col.addWidget(self._counter)

        self._status = QLabel("Ready.")
        self._status.setObjectName("status")
        self._status.setWordWrap(True)
        col.addWidget(self._status)

        return wrapper

    # --------------------------------------------------------- slots

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
        self._threshold_label.setText(f"≤ {value}y")

    def _on_canvas_changed(self) -> None:
        total = self._canvas.get_face_count()
        to_blur = self._canvas.get_blur_count()
        keep = total - to_blur
        if total == 0:
            self._counter.setText("")
        else:
            self._counter.setText(
                f"🔴 {to_blur} blurred   •   🟢 {keep} clear   •   {total} total"
            )
        # Sync the side panel to the canvas state
        self._faces_panel.set_blur_flags(self._canvas.get_blur_flags())

    def _on_panel_toggle(self, face_idx: int) -> None:
        """A click on a row in the side panel toggles that face."""
        self._canvas.toggle_face(face_idx)

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
        flags = [f.age_min <= threshold for f in faces]
        self._canvas.set_image(image, faces, flags)
        self._faces_panel.populate(image, faces, flags)

        if not faces:
            self._status.setText(f"No faces detected in {path.name}.")
        else:
            self._status.setText(
                f"{len(faces)} face(s) detected. "
                "Click any face on the image — or any row on the right — to toggle blur."
            )

    def _apply_auto_selection(self) -> None:
        if not self._current_faces:
            return
        threshold = self._threshold.value()
        flags = [f.age_min <= threshold for f in self._current_faces]
        self._canvas.set_image(
            self._canvas.get_source(), self._current_faces, flags
        )

    def _save(self) -> None:
        src = self._canvas.get_source()
        if src is None or self._current_path is None:
            return

        flags = self._canvas.get_blur_flags()
        faces_to_blur = [f for f, b in zip(self._current_faces, flags) if b]
        result = blur_faces(src, faces_to_blur)

        out_path = self._current_path.with_name(f"blurred_{self._current_path.name}")
        if not cv2.imwrite(str(out_path), result):
            self._error(f"Could not save: {out_path}")
            return

        self._last_output = out_path
        self._reveal_btn.setEnabled(True)
        self._status.setText(
            f"Saved {out_path.name} ({len(faces_to_blur)} face(s) blurred)."
        )

    def _error(self, message: str) -> None:
        self._status.setText("Error.")
        QMessageBox.critical(self, "ChildShield", message)
