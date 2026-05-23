"""Face detection + age estimation, both powered by InsightFace.

We use InsightFace's SCRFD detector (`det_10g.onnx`, ~16 MB) and its
genderage regressor (`genderage.onnx`, ~1.3 MB), both shipped inside the
package under `models/`. The two models are loaded directly from disk
via `insightface.model_zoo.get_model` so no network download happens at
runtime.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

# InsightFace warns about CUDAExecutionProvider not being available on
# CPU-only setups; that's expected and noisy in the GUI status bar.
warnings.filterwarnings("ignore", category=UserWarning, module="onnxruntime")

from insightface.model_zoo import model_zoo  # noqa: E402

_DET_INPUT_SIZE = (640, 640)


@dataclass(frozen=True)
class Face:
    """A detected face with estimated age."""

    x: int
    y: int
    w: int
    h: int
    age: int
    confidence: float


class FaceAnalyzer:
    """Combined face detection + age estimation."""

    def __init__(self) -> None:
        models_dir = Path(__file__).parent / "models"
        det_path = models_dir / "det_10g.onnx"
        age_path = models_dir / "genderage.onnx"
        for path in (det_path, age_path):
            if not path.exists():
                raise FileNotFoundError(
                    f"Required model file missing: {path}. Re-install the package."
                )

        self._detector = model_zoo.get_model(str(det_path))
        self._detector.prepare(ctx_id=-1, input_size=_DET_INPUT_SIZE)

        self._age = model_zoo.get_model(str(age_path))
        self._age.prepare(ctx_id=-1)

    def analyze(self, image: np.ndarray) -> list[Face]:
        """Detect every face in `image` (BGR) and return Face boxes with age."""
        bboxes, kps = self._detector.detect(image, max_num=0, metric="default")
        if bboxes is None or len(bboxes) == 0:
            return []

        height, width = image.shape[:2]
        faces: list[Face] = []
        for i in range(len(bboxes)):
            x1, y1, x2, y2, score = bboxes[i]
            x = max(0, int(x1))
            y = max(0, int(y1))
            w = min(int(x2) - x, width - x)
            h = min(int(y2) - y, height - y)
            if w <= 0 or h <= 0:
                continue

            # The genderage model needs an insightface "Face" object with
            # bbox + kps; we mimic it with a small ad-hoc wrapper.
            face_obj = _AgeInput(bbox=bboxes[i][:4], kps=kps[i] if kps is not None else None)
            self._age.get(image, face_obj)
            age = int(round(float(face_obj.age)))

            faces.append(
                Face(x=x, y=y, w=w, h=h, age=age, confidence=float(score))
            )
        return faces


class _AgeInput:
    """Minimal duck-typed Face object that genderage.get() expects."""

    __slots__ = ("bbox", "kps", "age", "gender", "sex")

    def __init__(self, bbox: np.ndarray, kps: np.ndarray | None) -> None:
        self.bbox = bbox
        self.kps = kps
        self.age = 0.0
        self.gender = 0
        self.sex = "?"
