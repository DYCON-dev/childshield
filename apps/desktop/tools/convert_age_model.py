"""Re-create ``childshield/models/age_vit.onnx`` from scratch.

Run this from inside a venv that has ``optimum[onnxruntime]`` installed.
The script:

1. Exports ``nateraw/vit-age-classifier`` (HuggingFace, MIT) to ONNX fp32
   (~328 MB).
2. Quantizes the ``MatMul`` ops to int8 to shrink the file to ~85 MB
   while keeping the same predictions on every test image we tried.
3. Drops the quantized file into ``childshield/models/age_vit.onnx``.

Why this model? ``vit-age-classifier`` was fine-tuned on **FairFace**,
which is demographically balanced — so it avoids the "overestimates
children" bias that haunts IMDB-WIKI / Adience-trained models like
InsightFace's ``genderage``.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from onnxruntime.quantization import QuantType, quantize_dynamic

ROOT = Path(__file__).resolve().parent.parent
EXPORT_DIR = ROOT / "tools" / "_export"
TARGET = ROOT / "childshield" / "models" / "age_vit.onnx"


def main() -> int:
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    fp32_path = EXPORT_DIR / "model.onnx"

    print("Step 1/2: exporting nateraw/vit-age-classifier to ONNX fp32…")
    subprocess.check_call(
        [
            sys.executable,
            "-m",
            "optimum.exporters.onnx",
            "--model",
            "nateraw/vit-age-classifier",
            "--task",
            "image-classification",
            str(EXPORT_DIR),
        ]
    )

    print("Step 2/2: int8-quantizing MatMul ops…")
    quantize_dynamic(
        str(fp32_path),
        str(TARGET),
        weight_type=QuantType.QInt8,
        op_types_to_quantize=["MatMul"],
    )

    print(f"Done. Wrote {TARGET} ({TARGET.stat().st_size / 1_048_576:.1f} MB)")
    shutil.rmtree(EXPORT_DIR, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
