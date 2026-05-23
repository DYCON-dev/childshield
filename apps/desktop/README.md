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
2. ChildShield detects faces with [YuNet](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet) (an ONNX model bundled in `childshield/models/`)
3. A gaussian blur is applied to every detected face
4. The blurred image is saved next to the original as `blurred_<filename>`

## Project layout

```
apps/desktop/
├── pyproject.toml
├── childshield/
│   ├── __init__.py
│   ├── __main__.py            # CLI entry point
│   ├── detection.py           # YuNet face detector
│   ├── blur.py                # Gaussian blur of detected boxes
│   ├── gui/
│   │   ├── __init__.py
│   │   ├── main_window.py     # PyQt6 main window with drag & drop
│   │   └── style.qss
│   └── models/
│       └── face_detection_yunet_2023mar.onnx
└── README.md
```

## License

[MIT](../../LICENSE)
