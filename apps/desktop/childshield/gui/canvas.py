"""Interactive image canvas: shows the photo with clickable face overlays."""

from __future__ import annotations

from typing import Callable

import cv2
import numpy as np
from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import (
    QColor,
    QDragEnterEvent,
    QDropEvent,
    QImage,
    QMouseEvent,
    QPainter,
    QPen,
    QPixmap,
)
from PyQt6.QtWidgets import QLabel

from childshield.analysis import Face
from childshield.blur import blur_faces


class ImageCanvas(QLabel):
    """Displays an image with face overlays. Click a face to toggle blur."""

    BLUR_COLOR = QColor(220, 38, 38, 220)      # red
    KEEP_COLOR = QColor(34, 197, 94, 220)      # green
    BLUR_FILL = QColor(220, 38, 38, 60)
    KEEP_FILL = QColor(34, 197, 94, 50)

    def __init__(self, on_drop: Callable[[str], None]) -> None:
        super().__init__()
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setObjectName("dropZone")
        self.setMinimumSize(420, 320)
        self.setAcceptDrops(True)
        self.setMouseTracking(True)
        self.setText("Drag and drop an image here, or click below.")

        self._on_drop = on_drop
        self._source: np.ndarray | None = None
        self._faces: list[Face] = []
        self._blur_flags: list[bool] = []
        self._displayed_pixmap_rect: QRect | None = None  # where the pixmap sits in the widget

    # ---------------------------------------------------------- public API

    def show_message(self, text: str) -> None:
        self._source = None
        self._faces = []
        self._blur_flags = []
        self.setText(text)
        self.setPixmap(QPixmap())

    def set_image(
        self, image_bgr: np.ndarray, faces: list[Face], blur_flags: list[bool]
    ) -> None:
        self._source = image_bgr
        self._faces = faces
        self._blur_flags = list(blur_flags)
        self._render()

    def toggle_face(self, face_idx: int) -> None:
        if 0 <= face_idx < len(self._blur_flags):
            self._blur_flags[face_idx] = not self._blur_flags[face_idx]
            self._render()

    def set_all(self, blur: bool) -> None:
        self._blur_flags = [blur] * len(self._faces)
        self._render()

    def get_blur_flags(self) -> list[bool]:
        return list(self._blur_flags)

    def get_source(self) -> np.ndarray | None:
        return self._source

    # --------------------------------------------------------- Qt events

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if not urls:
            return
        self._on_drop(urls[0].toLocalFile())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._source is None or self._displayed_pixmap_rect is None:
            return
        # Map widget coordinates to source-image coordinates
        pt = event.position().toPoint()
        if not self._displayed_pixmap_rect.contains(pt):
            return

        src_h, src_w = self._source.shape[:2]
        rect = self._displayed_pixmap_rect
        rel_x = (pt.x() - rect.x()) / rect.width()
        rel_y = (pt.y() - rect.y()) / rect.height()
        src_x = rel_x * src_w
        src_y = rel_y * src_h

        # Find a face containing this point (last one drawn wins on overlap)
        for i, face in reversed(list(enumerate(self._faces))):
            if face.x <= src_x <= face.x + face.w and face.y <= src_y <= face.y + face.h:
                self.toggle_face(i)
                return

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        if self._source is not None:
            self._render()

    # -------------------------------------------------------- rendering

    def _render(self) -> None:
        if self._source is None:
            return

        # Apply blurs based on current flags
        faces_to_blur = [f for f, b in zip(self._faces, self._blur_flags) if b]
        composed = blur_faces(self._source, faces_to_blur)

        # Convert BGR -> RGB for Qt
        rgb = cv2.cvtColor(composed, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape
        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)

        # Scale to fit the widget while keeping the aspect ratio
        pix = QPixmap.fromImage(qimg).scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        # Draw bounding boxes on top of the scaled pixmap
        scale_x = pix.width() / w
        scale_y = pix.height() / h
        painter = QPainter(pix)
        font = painter.font()
        font.setBold(True)
        font.setPointSize(11)
        painter.setFont(font)

        for face, blur_flag in zip(self._faces, self._blur_flags):
            x = int(face.x * scale_x)
            y = int(face.y * scale_y)
            box_w = int(face.w * scale_x)
            box_h = int(face.h * scale_y)
            border = self.BLUR_COLOR if blur_flag else self.KEEP_COLOR
            fill = self.BLUR_FILL if blur_flag else self.KEEP_FILL

            painter.setPen(Qt.PenStyle.NoPen)
            painter.fillRect(QRect(x, y, box_w, box_h), fill)
            pen = QPen(border)
            pen.setWidth(3)
            painter.setPen(pen)
            painter.drawRect(QRect(x, y, box_w, box_h))

            # Age label
            label = f"~{face.age}y"
            label_w = painter.fontMetrics().horizontalAdvance(label) + 12
            label_h = painter.fontMetrics().height() + 4
            label_rect = QRect(x, max(0, y - label_h - 2), label_w, label_h)
            painter.fillRect(label_rect, border)
            painter.setPen(QColor(255, 255, 255))
            painter.drawText(
                label_rect, Qt.AlignmentFlag.AlignCenter, label
            )

        painter.end()

        # Center the pixmap inside the widget and remember its position
        self.setPixmap(pix)
        widget_w, widget_h = self.width(), self.height()
        x = (widget_w - pix.width()) // 2
        y = (widget_h - pix.height()) // 2
        self._displayed_pixmap_rect = QRect(x, y, pix.width(), pix.height())
