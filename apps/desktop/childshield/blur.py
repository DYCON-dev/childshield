"""Elliptical face blur with a long, smoothly-dissolving outer fade.

Each detected face is blurred inside an elliptical region whose alpha
falls off using a *smoothstep* curve. The curve has two knobs:

- ``_FADE_INNER`` — fraction of the ellipse axes inside which the blur
  is at full strength.
- ``_FADE_OUTER`` — fraction at which the blur has fully faded out.

Between those two, the alpha follows ``smoothstep`` (3t² − 2t³), which
gives a noticeably softer falloff than a Gaussian-blurred binary mask
and avoids any visible "edge" on the photo. The crop around each face
is padded enough to hold the entire fade so we never clip it.
"""

from __future__ import annotations

import cv2
import numpy as np

from childshield.analysis import Face


# Inner radius (in axis-fraction units) where blur is full strength.
_FADE_INNER = 0.65
# Outer radius where blur has completely faded to zero.
_FADE_OUTER = 1.55
# Ellipse semi-axes relative to the face bounding box.
_AX_RATIO = 0.55
_AY_RATIO = 0.65
# How much extra room to keep around each face for the fade. Must be
# big enough to cover ``_FADE_OUTER`` times the axis without clipping.
_PADDING_RATIO = 0.55


def _odd(n: int, minimum: int = 3) -> int:
    n = max(n, minimum)
    return n if n % 2 == 1 else n + 1


def _smoothstep(t: np.ndarray) -> np.ndarray:
    """Classic 3t² − 2t³ ease curve, applied element-wise to t in [0, 1]."""
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def blur_faces(image: np.ndarray, faces: list[Face], strength: float = 1.0) -> np.ndarray:
    """Return a copy of ``image`` with each face blurred and softly faded."""
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

        # Strong Gaussian blur scaled to the face size.
        kw = _odd(int(face.w / 3 * strength))
        kh = _odd(int(face.h / 3 * strength))
        blurred_roi = cv2.GaussianBlur(roi, (kw, kh), 0)

        # Radial distance in axis-fraction units centred on the face.
        cx = (face.x + face.w / 2.0) - x1
        cy = (face.y + face.h / 2.0) - y1
        ax = max(1.0, face.w * _AX_RATIO)
        ay = max(1.0, face.h * _AY_RATIO)
        yy, xx = np.indices((crop_h, crop_w), dtype=np.float32)
        d = np.sqrt(((xx - cx) / ax) ** 2 + ((yy - cy) / ay) ** 2)

        # Alpha = 1 inside _FADE_INNER, smoothly drops to 0 by _FADE_OUTER.
        t = (_FADE_OUTER - d) / (_FADE_OUTER - _FADE_INNER)
        alpha = _smoothstep(t)[..., None]  # (h, w, 1) broadcasts over BGR

        out[y1:y2, x1:x2] = alpha * blurred_roi + (1.0 - alpha) * roi

    return np.clip(out, 0, 255).astype(np.uint8)
