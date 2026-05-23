# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for ChildShield desktop.

Build locally:

    pyinstaller --clean ChildShield.spec

Outputs:
    macOS   -> dist/ChildShield.app
    Windows -> dist/ChildShield/ChildShield.exe
    Linux   -> dist/ChildShield/ChildShield
"""

import sys
from pathlib import Path

import insightface  # noqa: F401  (kept to verify the package is importable)
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

APP_NAME = "ChildShield"
HERE = Path(SPECPATH).resolve()  # noqa: F821 (SPECPATH provided by PyInstaller)
PKG = HERE / "childshield"
PACKAGING = HERE / "packaging"


# --------------------------------------------------------------- icon

if sys.platform == "darwin":
    ICON = str(PACKAGING / "ChildShield.icns")
elif sys.platform.startswith("win"):
    ICON = str(PACKAGING / "ChildShield.ico")
else:
    ICON = str(PACKAGING / "ChildShield.png")


# -------------------------------------------------------- bundled data

datas = [
    (str(PKG / "models" / "det_10g.onnx"),  "childshield/models"),
    (str(PKG / "models" / "age_vit.onnx"),  "childshield/models"),
    (str(PKG / "gui"    / "style.qss"),     "childshield/gui"),
    (str(PKG / "assets" / "logo.svg"),      "childshield/assets"),
]

# Pull in the few small data files insightface needs at runtime (e.g.
# its anchor priors). We do NOT bundle the buffalo_l zip — we use our
# own ONNX path directly via model_zoo.get_model().
datas += collect_data_files("insightface", subdir=None)


# ---------------------------------------------------- hidden imports

hiddenimports = [
    "PyQt6.sip",
]
hiddenimports += collect_submodules("onnxruntime")
hiddenimports += collect_submodules("insightface")
hiddenimports += collect_submodules("cv2")


# ----------------------------------------------------------- Analysis

a = Analysis(  # noqa: F821
    ["childshield/__main__.py"],
    pathex=[str(HERE)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        # Trim large unused frameworks
        "matplotlib", "pandas", "scipy", "sklearn", "tensorflow",
        "torch", "torchvision", "timm",
        "tkinter", "PySide6", "PyQt5",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)  # noqa: F821

exe = EXE(  # noqa: F821
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=ICON,
)

coll = COLLECT(  # noqa: F821
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)

if sys.platform == "darwin":
    app = BUNDLE(  # noqa: F821
        coll,
        name=f"{APP_NAME}.app",
        icon=ICON,
        bundle_identifier="com.dycon.childshield",
        info_plist={
            "CFBundleName": APP_NAME,
            "CFBundleDisplayName": APP_NAME,
            "CFBundleShortVersionString": "0.1.0",
            "CFBundleVersion": "0.1.0",
            "LSMinimumSystemVersion": "11.0",
            "NSHighResolutionCapable": True,
            "NSHumanReadableCopyright": "MIT — https://github.com/DYCON-dev/childshield",
            # No camera / mic / network usage; the app is purely local.
            "LSApplicationCategoryType": "public.app-category.graphics-design",
        },
    )
