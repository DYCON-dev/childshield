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

## Build a standalone bundle

The desktop app ships as a `.app` (macOS), `.exe` folder (Windows), or
`AppImage` (Linux). All three are built from the same
[`ChildShield.spec`](ChildShield.spec) PyInstaller file.

### macOS (.app + .dmg)

```bash
cd apps/desktop
python -m venv .venv && source .venv/bin/activate
pip install -e . pyinstaller pillow

# Render the icon bundles from logo.svg
python tools/build_icons.py

# Build the .app
pyinstaller --clean ChildShield.spec

# Package as .dmg
hdiutil create -volname ChildShield \
  -srcfolder dist/ChildShield.app \
  -ov -format UDZO -fs HFS+ \
  dist/ChildShield-0.1.0.dmg
```

Final bundle is ~350 MB (PyQt6 + OpenCV + ONNX Runtime + the two ONNX
models).

### Sign + notarize for distribution outside the App Store

The `.app` produced by PyInstaller is unsigned — macOS Gatekeeper will
refuse to open it. To distribute publicly, sign and notarize it with
your Apple Developer ID:

```bash
export APPLE_DEVELOPER_ID="Developer ID Application: Your Name (TEAMID12345)"
export APPLE_ID="you@example.com"
export APPLE_PASSWORD="app-specific-password"   # from https://appleid.apple.com
export APPLE_TEAM_ID="TEAMID12345"

bash tools/sign_macos.sh
```

The script wraps `codesign`, submits the bundle to `xcrun notarytool`,
waits for the notarization ticket, staples it, and rebuilds the `.dmg`.
Plan ~5 minutes for the notarization round-trip.

To do the same from GitHub Actions, add these repository secrets:
- `APPLE_CERTIFICATE_BASE64` — your Developer ID .p12 file, base64-encoded
- `APPLE_CERTIFICATE_PASSWORD` — the .p12 password
- `KEYCHAIN_PASSWORD` — any string the runner uses for the temporary keychain
- `APPLE_DEVELOPER_ID`, `APPLE_ID`, `APPLE_PASSWORD`, `APPLE_TEAM_ID` — same as above

### Windows / Linux

The same `ChildShield.spec` works on Windows (produces `dist/ChildShield/`
with `ChildShield.exe`) and Linux (`dist/ChildShield/ChildShield`). PyInstaller
does not cross-compile — run each build on the matching OS, or use the
GitHub Actions workflow in [`.github/workflows/release.yml`](../../.github/workflows/release.yml)
which builds all three on tag push.

## License

[MIT](../../LICENSE)
