"""Side panel listing every detected face with its age and blur state."""

from __future__ import annotations

from typing import Callable

import cv2
import numpy as np
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from childshield.analysis import Face


THUMB_SIZE = 48


class _FaceRow(QFrame):
    """A single row in the faces panel."""

    def __init__(
        self,
        index: int,
        face: Face,
        thumb: QPixmap,
        blurred: bool,
        on_click: Callable[[int], None],
    ) -> None:
        super().__init__()
        self._index = index
        self._on_click = on_click
        self.setObjectName("faceRow")
        self.setProperty("blurred", blurred)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(10)

        self._thumb_label = QLabel()
        self._thumb_label.setFixedSize(THUMB_SIZE, THUMB_SIZE)
        self._thumb_label.setPixmap(thumb)
        self._thumb_label.setScaledContents(True)
        self._thumb_label.setObjectName("faceThumb")
        layout.addWidget(self._thumb_label)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        self._title = QLabel(f"Face #{index + 1}")
        self._title.setObjectName("faceTitle")
        text_col.addWidget(self._title)

        self._age_label = QLabel(
            f"{face.age_label} years  ·  {int(face.age_confidence * 100)}%"
        )
        self._age_label.setObjectName("faceAge")
        text_col.addWidget(self._age_label)

        layout.addLayout(text_col, stretch=1)

        self._status = QLabel("BLUR" if blurred else "CLEAR")
        self._status.setObjectName("faceStatus")
        self._status.setProperty("blurred", blurred)
        layout.addWidget(self._status)

    def set_blurred(self, blurred: bool) -> None:
        self.setProperty("blurred", blurred)
        self._status.setProperty("blurred", blurred)
        self._status.setText("BLUR" if blurred else "CLEAR")
        # Force style re-evaluation
        self.style().unpolish(self)
        self.style().polish(self)
        self._status.style().unpolish(self._status)
        self._status.style().polish(self._status)

    def mousePressEvent(self, event) -> None:
        self._on_click(self._index)


class FacesPanel(QWidget):
    """Vertical list of detected faces with their blur state."""

    def __init__(self, on_toggle: Callable[[int], None]) -> None:
        super().__init__()
        self.setObjectName("facesPanel")
        self.setMinimumWidth(260)
        self.setMaximumWidth(320)

        self._on_toggle = on_toggle
        self._rows: list[_FaceRow] = []

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        header = QLabel("Detected faces")
        header.setObjectName("panelHeader")
        outer.addWidget(header)

        self._list = QListWidget()
        self._list.setObjectName("facesList")
        self._list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        self._list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        outer.addWidget(self._list, stretch=1)

        self._empty_label = QLabel("Load an image to see detected faces here.")
        self._empty_label.setObjectName("panelEmpty")
        self._empty_label.setWordWrap(True)
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        outer.addWidget(self._empty_label)
        outer.addStretch()

        self._show_empty()

    # ---------------------------------------------------- public API

    def populate(
        self, source_bgr: np.ndarray, faces: list[Face], blur_flags: list[bool]
    ) -> None:
        self._list.clear()
        self._rows = []

        if not faces:
            self._show_empty()
            return

        self._empty_label.hide()
        self._list.show()

        for i, (face, blurred) in enumerate(zip(faces, blur_flags)):
            thumb = self._make_thumb(source_bgr, face)
            row = _FaceRow(i, face, thumb, blurred, self._on_toggle)
            item = QListWidgetItem(self._list)
            item.setSizeHint(row.sizeHint())
            self._list.addItem(item)
            self._list.setItemWidget(item, row)
            self._rows.append(row)

    def set_blur_flags(self, blur_flags: list[bool]) -> None:
        for row, blurred in zip(self._rows, blur_flags):
            row.set_blurred(blurred)

    def clear(self) -> None:
        self._list.clear()
        self._rows = []
        self._show_empty()

    # ---------------------------------------------------- internals

    def _show_empty(self) -> None:
        self._empty_label.show()
        self._list.hide()

    @staticmethod
    def _make_thumb(image_bgr: np.ndarray, face: Face) -> QPixmap:
        crop = image_bgr[face.y : face.y + face.h, face.x : face.x + face.w]
        if crop.size == 0:
            return QPixmap(THUMB_SIZE, THUMB_SIZE)
        rgb = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        rgb = cv2.resize(rgb, (THUMB_SIZE, THUMB_SIZE))
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888).copy()
        return QPixmap.fromImage(qimg)
