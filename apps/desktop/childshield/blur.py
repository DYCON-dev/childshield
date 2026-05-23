"""Elliptical, feathered face blur.

Each detected face is blurred inside a soft-edged ellipse rather than a
hard rectangle. We work in three steps per face:

1. Crop a padded box around the face (extra room for the fade)
2. Apply a strong Gaussian blur to that crop
3. Build an elliptical alpha mask, blur the mask itself to feather its
   edges, then alpha-blend the blurred crop back into the original

The result is a round, smoothly dissolving blur instead of a sharp
rectangular tile.
"""

from __future__ import annotations

import cv2
import numpy as np

from childshield.analysis import Face


# How much extra space to keep around each face for the fade. 25% on
# every side is enough for a visibly soft transition without bleeding
# into neighbouring faces.
_PADDING_RATIO = 0.30

# Ellipse axes relative to the detected face box. Most face crops are a
# bit narrower than tall — we widen the X axis less than the Y axis so
# the ellipse hugs the head shape.
_AX_RATIO = 0.55
_AY_RATIO = 0.65

# Feather kernel as a fraction of the cropped region's shortest side.
_FEATHER_RATIO = 0.18


def _odd(n: int, minimum: int = 3) -> int:
    n = max(n, minimum)
    return n if n % 2 == 1 else n + 1


def blur_faces(image: np.ndarray, faces: list[Face], strength: float = 1.0) -> np.ndarray:
    """Return a copy of ``image`` with each face blurred in a soft ellipse."""
    if not faces:
        return image.copy()

    out = image.astype(np.float32, copy=True)
    img_h, img_w = image.shape[:2]

    for face in faces:
        pad = int(max(face.w, face.h) * _PADDING_RATIO)
        x1 = max(0, face.x - pad)
        y1 = max(0, face.y - pad)
        x2 = min(img_w, face.x + face.w + pad)
        y2 = min(img_h, face.y + face.h + pad)
        if x2 <= x1 or y2 <= y1:
            continue

        crop_h = y2 - y1
        crop_w = x2 - x1
        roi = out[y1:y2, x1:x2]

        # Strong blur — kernel scaled to face size so big and small faces
        # both get a thoroughly anonymised look.
        kw = _odd(int(face.w / 3 * strength))
        kh = _odd(int(face.h / 3 * strength))
        blurred_roi = cv2.GaussianBlur(roi, (kw, kh), 0)

        # Elliptical alpha mask centred on the original face box.
        mask = np.zeros((crop_h, crop_w), dtype=np.float32)
        cx = int(round((face.x + face.w / 2) - x1))
        cy = int(round((face.y + face.h / 2) - y1))
        ax = max(1, int(face.w * _AX_RATIO))
        ay = max(1, int(face.h * _AY_RATIO))
        cv2.ellipse(mask, (cx, cy), (ax, ay), 0, 0, 360, 1.0, thickness=-1)

        # Feather the mask edge by Gaussian-blurring the mask itself.
        feather = _odd(int(min(crop_h, crop_w) * _FEATHER_RATIO))
        mask = cv2.GaussianBlur(mask, (feather, feather), 0)
        mask = np.clip(mask, 0.0, 1.0)

        alpha = mask[..., None]  # (h, w, 1) broadcasts over 3 channels
        out[y1:y2, x1:x2] = alpha * blurred_roi + (1.0 - alpha) * roi

    return np.clip(out, 0, 255).astype(np.uint8)
