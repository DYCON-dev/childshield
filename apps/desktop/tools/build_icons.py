"""Render ``childshield/assets/logo.svg`` into the platform icon bundles.

Outputs three files under ``apps/desktop/packaging/`` :

- ``ChildShield.icns``  — macOS multi-resolution icon (iconutil)
- ``ChildShield.ico``   — Windows multi-resolution icon
- ``ChildShield.png``   — 1024×1024 PNG, used by Linux .AppImage and as
  a fallback by PyInstaller when no .icns/.ico is found

PyQt6 is used to rasterize the SVG (no extra dependency vs the runtime).
``iconutil`` is the macOS-only tool that packs an .iconset into an .icns;
on other OSes the .icns step is skipped.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image
from PyQt6.QtCore import QSize, Qt
from PyQt6.QtGui import QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import QApplication

ROOT = Path(__file__).resolve().parent.parent
SVG = ROOT / "childshield" / "assets" / "logo.svg"
OUT = ROOT / "packaging"
OUT.mkdir(parents=True, exist_ok=True)

# (size_px, iconset_name)
_ICONSET_SIZES = [
    (16, "16x16"),
    (32, "16x16@2x"),
    (32, "32x32"),
    (64, "32x32@2x"),
    (128, "128x128"),
    (256, "128x128@2x"),
    (256, "256x256"),
    (512, "256x256@2x"),
    (512, "512x512"),
    (1024, "512x512@2x"),
]

_ICO_SIZES = [16, 32, 48, 64, 128, 256]


def main() -> int:
    app = QApplication.instance() or QApplication(sys.argv)  # noqa: F841
    renderer = QSvgRenderer(str(SVG))

    def render_png(size: int, path: Path) -> None:
        pix = QPixmap(QSize(size, size))
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        renderer.render(painter)
        painter.end()
        if not pix.save(str(path), "PNG"):
            raise RuntimeError(f"failed to write {path}")

    # 1. High-resolution PNG for Linux .AppImage
    big_png = OUT / "ChildShield.png"
    render_png(1024, big_png)
    print(f"  {big_png}  (1024×1024)")

    # 2. macOS .icns via iconutil (skipped on non-macOS hosts)
    if shutil.which("iconutil"):
        iconset = OUT / "ChildShield.iconset"
        if iconset.exists():
            shutil.rmtree(iconset)
        iconset.mkdir()
        for size, name in _ICONSET_SIZES:
            render_png(size, iconset / f"icon_{name}.png")
        icns = OUT / "ChildShield.icns"
        subprocess.check_call(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(icns)]
        )
        shutil.rmtree(iconset)
        print(f"  {icns}")
    else:
        print("  (skipped .icns — iconutil only exists on macOS)")

    # 3. Windows .ico via PIL
    ico_path = OUT / "ChildShield.ico"
    # PIL builds .ico from the source PNG by downscaling.
    Image.open(big_png).save(
        ico_path, format="ICO", sizes=[(s, s) for s in _ICO_SIZES]
    )
    print(f"  {ico_path}  (sizes: {_ICO_SIZES})")

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
