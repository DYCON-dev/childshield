"""Apply gaussian blur to face regions."""

from __future__ import annotations

import cv2
import numpy as np

from childshield.detection import Face


def _odd(n: int, minimum: int = 3) -> int:
    n = max(n, minimum)
    return n if n % 2 == 1 else n + 1


def blur_faces(image: np.ndarray, faces: list[Face], strength: float = 1.0) -> np.ndarray:
    """Return a copy of `image` with each face region blurred.

    `strength` scales the kernel size: 1.0 ≈ kernel = face_size / 3.
    """
    out = image.copy()
    for face in faces:
        x, y, w, h = face.x, face.y, face.w, face.h
        roi = out[y : y + h, x : x + w]
        if roi.size == 0:
            continue
        kw = _odd(int(w / 3 * strength))
        kh = _odd(int(h / 3 * strength))
        out[y : y + h, x : x + w] = cv2.GaussianBlur(roi, (kw, kh), 0)
    return out
