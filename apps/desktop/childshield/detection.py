"""Face detection using YuNet (OpenCV Zoo)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

_MODEL_FILENAME = "face_detection_yunet_2023mar.onnx"


@dataclass(frozen=True)
class Face:
    """A detected face. x, y are top-left coords; w, h are width/height in pixels."""

    x: int
    y: int
    w: int
    h: int
    confidence: float


class FaceDetector:
    """YuNet-based face detector. Single instance — the model loads once."""

    def __init__(self, score_threshold: float = 0.6, nms_threshold: float = 0.3) -> None:
        model_path = Path(__file__).parent / "models" / _MODEL_FILENAME
        if not model_path.exists():
            raise FileNotFoundError(
                f"YuNet model not found at {model_path}. "
                "Re-install the package or download the model from "
                "https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet"
            )

        # input_size is (0, 0) here — we resize per image in detect()
        self._detector = cv2.FaceDetectorYN_create(
            model=str(model_path),
            config="",
            input_size=(320, 320),
            score_threshold=score_threshold,
            nms_threshold=nms_threshold,
            top_k=5000,
        )

    def detect(self, image: np.ndarray) -> list[Face]:
        """Detect faces in a BGR image. Returns a list of Face boxes."""
        height, width = image.shape[:2]
        self._detector.setInputSize((width, height))

        _, raw = self._detector.detect(image)
        if raw is None:
            return []

        # raw shape: (N, 15) — [x, y, w, h, 5 landmark pairs, confidence]
        faces: list[Face] = []
        for row in raw:
            x, y, w, h = (int(v) for v in row[:4])
            confidence = float(row[14])
            # Clamp to image bounds (YuNet can return slightly out-of-frame boxes)
            x = max(0, x)
            y = max(0, y)
            w = min(w, width - x)
            h = min(h, height - y)
            if w <= 0 or h <= 0:
                continue
            faces.append(Face(x=x, y=y, w=w, h=h, confidence=confidence))
        return faces
