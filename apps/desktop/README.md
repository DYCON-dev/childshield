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
2. ChildShield detects faces with [InsightFace SCRFD](https://github.com/deepinsight/insightface) (`det_10g.onnx`, ~16 MB, bundled) and estimates the age of each face with `genderage.onnx` (~1.3 MB, bundled)
3. A gaussian blur is applied to every face whose estimated age is below the threshold (default ≤ 12 years)
4. The blurred image is saved next to the original as `blurred_<filename>`
5. You can adjust the age threshold or toggle "Blur all" without re-opening the file

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
│   │   └── style.qss
│   └── models/
│       ├── det_10g.onnx       # SCRFD face detection (~16 MB)
│       └── genderage.onnx     # Age / gender regressor (~1.3 MB)
└── README.md
```

## License

[MIT](../../LICENSE)
