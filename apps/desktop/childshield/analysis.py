"""Face detection (InsightFace SCRFD) + age estimation (ViT-FairFace).

We use two ONNX models, both bundled under ``models/`` and loaded
directly from disk via ``onnxruntime`` — no runtime download.

- ``det_10g.onnx``  — InsightFace SCRFD-10G face detector (~16 MB)
- ``age_vit.onnx``  — ViT-base age classifier trained on FairFace, exported
  from ``nateraw/vit-age-classifier``, MatMul-quantized to int8 (~85 MB).

ViT-FairFace was chosen because:
- FairFace is a demographically balanced dataset — much less of the
  "overestimates children" bias that plagues IMDB-WIKI / Adience models
- 9 coarse age buckets work better than continuous regression for the
  "minor vs. adult" decision we actually care about
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

warnings.filterwarnings("ignore", category=UserWarning, module="onnxruntime")

import onnxruntime as ort  # noqa: E402
from insightface.app.common import Face as _IFace  # noqa: E402
from insightface.model_zoo import model_zoo  # noqa: E402

_DET_INPUT_SIZE = (640, 640)

# Order must match nateraw/vit-age-classifier's config.json id2label
AGE_BUCKETS: list[tuple[str, int, int]] = [
    ("0-2", 0, 2),
    ("3-9", 3, 9),
    ("10-19", 10, 19),
    ("20-29", 20, 29),
    ("30-39", 30, 39),
    ("40-49", 40, 49),
    ("50-59", 50, 59),
    ("60-69", 60, 69),
    ("70+", 70, 100),
]

# ImageNet/ViT preprocessing
_VIT_MEAN = np.array([0.5, 0.5, 0.5], dtype=np.float32).reshape(1, 3, 1, 1)
_VIT_STD = np.array([0.5, 0.5, 0.5], dtype=np.float32).reshape(1, 3, 1, 1)
_VIT_SIZE = 224


@dataclass(frozen=True)
class Face:
    """A detected face with estimated age bucket."""

    x: int
    y: int
    w: int
    h: int
    age_label: str       # e.g. "3-9", "20-29"
    age_min: int         # inclusive lower bound of the bucket
    age_max: int         # inclusive upper bound of the bucket
    age_confidence: float  # softmax probability of the chosen bucket (0..1)
    confidence: float    # face detection confidence


class FaceAnalyzer:
    """Combined face detection + age estimation."""

    def __init__(self) -> None:
        models_dir = Path(__file__).parent / "models"
        det_path = models_dir / "det_10g.onnx"
        age_path = models_dir / "age_vit.onnx"
        for path in (det_path, age_path):
            if not path.exists():
                raise FileNotFoundError(
                    f"Required model file missing: {path}. Re-install the package."
                )

        self._detector = model_zoo.get_model(str(det_path))
        self._detector.prepare(ctx_id=-1, input_size=_DET_INPUT_SIZE)

        self._age = ort.InferenceSession(
            str(age_path), providers=["CPUExecutionProvider"]
        )
        self._age_input_name = self._age.get_inputs()[0].name

    def analyze(self, image: np.ndarray) -> list[Face]:
        """Detect every face in `image` (BGR) and return Face boxes with age."""
        bboxes, _ = self._detector.detect(image, max_num=0, metric="default")
        if bboxes is None or len(bboxes) == 0:
            return []

        height, width = image.shape[:2]
        faces: list[Face] = []
        for row in bboxes:
            x1, y1, x2, y2, score = row
            x = max(0, int(x1))
            y = max(0, int(y1))
            w = min(int(x2) - x, width - x)
            h = min(int(y2) - y, height - y)
            if w <= 0 or h <= 0:
                continue

            crop = image[y : y + h, x : x + w]
            if crop.size == 0:
                continue
            bucket_idx, conf = self._predict_age_bucket(crop)
            label, age_min, age_max = AGE_BUCKETS[bucket_idx]

            faces.append(
                Face(
                    x=x,
                    y=y,
                    w=w,
                    h=h,
                    age_label=label,
                    age_min=age_min,
                    age_max=age_max,
                    age_confidence=conf,
                    confidence=float(score),
                )
            )
        return faces

    # ----------------------------------------------------------- internals

    def _predict_age_bucket(self, face_bgr: np.ndarray) -> tuple[int, float]:
        rgb = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2RGB)
        resized = cv2.resize(rgb, (_VIT_SIZE, _VIT_SIZE))
        x = resized.astype(np.float32) / 255.0
        x = x.transpose(2, 0, 1)[None]  # (1, 3, 224, 224)
        x = (x - _VIT_MEAN) / _VIT_STD

        logits = self._age.run(None, {self._age_input_name: x})[0][0]
        # softmax for confidence
        e = np.exp(logits - logits.max())
        probs = e / e.sum()
        idx = int(np.argmax(probs))
        return idx, float(probs[idx])
