# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for FindCurves Studio.  Build with:
#   pyinstaller --noconfirm FindCurves.spec
# Output: dist\FindCurves\FindCurves.exe (plus its supporting files)

from PyInstaller.utils.hooks import collect_all

# pyeq3 discovers its equation modules dynamically, so collect all of it.
# pypdfium2 (PDF graph images) loads its pdfium library at run time.
# Verses.txt: PDF report messages; icons: the window icons and logo
datas, binaries, hiddenimports = [('Verses.txt', '.'), ('icons', 'icons')], [], []
for package in ['pyeq3', 'pypdfium2', 'pypdfium2_raw']:
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

a = Analysis(
    ['FindCurves.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + [
        # these are imported lazily by the Import Data dialog
        'openpyxl',
        'xlrd',
        'resvg_py',
        'PIL.ImageTk',
        'matplotlib.backends.backend_tkagg',
        'mpl_toolkits.mplot3d',
        'scipy.stats',
        # these are imported lazily, only when saving a PDF
        'pdfCode',
        'FunctionFinderPDF',
        'Scripture',
        'reportlab.graphics.barcode.common',
        'reportlab.graphics.barcode.code128',
        'reportlab.graphics.barcode.code93',
        'reportlab.graphics.barcode.code39',
        'reportlab.graphics.barcode.usps',
        'reportlab.graphics.barcode.usps4s',
        'reportlab.graphics.barcode.ecc200datamatrix',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'IPython', 'jupyter', 'pytest'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='FindCurves',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # GUI application - no console window
    icon='icons/FindCurves.ico',  # the program's icon on Windows
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='FindCurves',
)

# macOS only (build-macos.sh): wrap the files in "dist/FindCurves Studio.app"
import os, re, sys
if sys.platform == 'darwin':
    with open(os.path.join(SPECPATH, 'installer', 'FindCurves.iss')) as f:
        version = re.search(r'#define MyAppVersion "([^"]+)"', f.read()).group(1)
    app = BUNDLE(
        coll,
        name='FindCurves Studio.app',
        icon='icons/FindCurves.icns',
        bundle_identifier='com.findcurves.studio',
        version=version,
        info_plist={
            'CFBundleDisplayName': 'FindCurves Studio',
            'NSRequiresAquaSystemAppearance': False,  # allow dark mode
            'CFBundleShortVersionString': version,
            'NSHighResolutionCapable': True,
            'NSHumanReadableCopyright': 'Copyright (C) 2016 James R. Phillips, (C) 2026 Ross Moffett',
        },
    )
