# ChildShield Desktop

Cross-platform desktop app to blur faces in photos before sharing.

## Install

```bash
cd apps/desktop
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -e .
```

Requires Python 3.10+.

## Run

```bash
childshield
```

Or:

```bash
python -m childshield
```

## How it works

1. Drag-and-drop an image into the window (or click "Open image")
2. ChildShield detects faces with [InsightFace SCRFD](https://github.com/deepinsight/insightface) (`det_10g.onnx`, ~16 MB, bundled) and estimates the age bucket of each face with a ViT-base age classifier fine-tuned on FairFace (`age_vit.onnx`, ~85 MB, int8-quantized, bundled)
3. Each face gets a colored box overlay (red = will be blurred, green = will stay clear) and a label showing the predicted age range (`3-9y`, `10-19y`, `20-29y`, …)
4. **Click any face** to flip its blur state. Use the threshold slider to auto-select buckets whose lower bound is ≤ N.
5. Press **Save blurred copy** to write `blurred_<filename>` next to the original.

## Project layout

```
apps/desktop/
├── pyproject.toml
├── childshield/
│   ├── __init__.py
│   ├── __main__.py            # CLI entry point
│   ├── analysis.py            # InsightFace SCRFD detector + genderage age regressor
│   ├── blur.py                # Gaussian blur of selected face boxes
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py     # PyQt6 main window with drag & drop
│   │   ├── canvas.py          # Interactive image canvas with face overlays
│   │   ├── main_window.py     # PyQt6 main window with drag & drop
│   │   └── style.qss
│   └── models/
│       ├── det_10g.onnx       # SCRFD face detection (~16 MB)
│       └── age_vit.onnx       # ViT-FairFace age classifier (~85 MB, int8)
├── tools/                     # Scripts to regenerate the bundled ONNX models
└── README.md
```

## License

[MIT](../../LICENSE)
