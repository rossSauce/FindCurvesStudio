# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for tkinterFit.  Build with:
#   pyinstaller --noconfirm tkinterFit.spec
# Output: dist\tkinterFit\tkinterFit.exe (plus its supporting files)

from PyInstaller.utils.hooks import collect_all

# pyeq3 discovers its equation modules dynamically, so collect all of it
pyeq3_datas, pyeq3_binaries, pyeq3_hiddenimports = collect_all('pyeq3')

a = Analysis(
    ['tkinterFit.py'],
    pathex=[],
    binaries=pyeq3_binaries,
    datas=pyeq3_datas,
    hiddenimports=pyeq3_hiddenimports + [
        'matplotlib.backends.backend_tkagg',
        'mpl_toolkits.mplot3d',
        'scipy.stats',
        # these are imported lazily, only when saving a PDF
        'pdfCode',
        'FunctionFinderPDF',
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
    name='tkinterFit',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # GUI application - no console window
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='tkinterFit',
)
