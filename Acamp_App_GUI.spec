"""PyInstaller one-folder build for the ACAMP desktop application."""

from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files


project_root = Path(SPECPATH).resolve()

# Google API discovery loads this document dynamically at runtime.
google_discovery_data = collect_data_files(
    "googleapiclient",
    includes=["discovery_cache/documents/sheets.v4.json"],
)

a = Analysis(
    [str(project_root / "gui_main.py")],
    pathex=[str(project_root)],
    binaries=[],
    datas=google_discovery_data,
    hiddenimports=[
        "googleapiclient.discovery_cache",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "pytest",
        "tests",
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Acamp_App_GUI",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Acamp_App_GUI",
)
