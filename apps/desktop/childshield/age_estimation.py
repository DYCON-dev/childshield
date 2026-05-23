"""Age estimation using the Gil Levi & Hassner Caffe model (2015).

This is a coarse, biased model. We use it as an *assistive* signal to
pre-select likely-children for blurring — the user can always override.
Future versions will move to MiVOLO (2024) for better accuracy and
reduced bias on darker skin tones and Asian features.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np

from childshield.detection import Face

# Bucket centers used as the estimated age (in years).
_BUCKET_LABELS = ["(0-2)", "(4-6)", "(8-12)", "(15-20)", "(25-32)", "(38-43)", "(48-53)", "(60-100)"]
_BUCKET_CENTERS = [1, 5, 10, 17, 28, 40, 50, 80]

_MEAN = (78.4263377603, 87.7689143744, 114.895847746)
_INPUT_SIZE = (227, 227)


class AgeEstimator:
    """Caffe-based age estimator. Loads the model once."""

    def __init__(self) -> None:
        models_dir = Path(__file__).parent / "models"
        proto = models_dir / "age_deploy.prototxt"
        weights = models_dir / "age_net.caffemodel"
        if not proto.exists() or not weights.exists():
            raise FileNotFoundError(
                f"Age model files not found in {models_dir}. "
                "Re-install the package."
            )
        self._net = cv2.dnn.readNetFromCaffe(str(proto), str(weights))

    def estimate(self, image: np.ndarray, face: Face) -> int:
        """Return an estimated age in years for the given face crop.

        The model returns probabilities over 8 buckets; we return the
        center of the most-likely bucket.
        """
        roi = image[face.y : face.y + face.h, face.x : face.x + face.w]
        if roi.size == 0:
            return 0
        blob = cv2.dnn.blobFromImage(roi, 1.0, _INPUT_SIZE, _MEAN, swapRB=False)
        self._net.setInput(blob)
        preds = self._net.forward()
        idx = int(np.argmax(preds[0]))
        return _BUCKET_CENTERS[idx]

    def estimate_many(self, image: np.ndarray, faces: list[Face]) -> list[int]:
        return [self.estimate(image, f) for f in faces]
