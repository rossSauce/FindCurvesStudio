# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for tkinterFit.  Build with:
#   pyinstaller --noconfirm tkinterFit.spec
# Output: dist\tkinterFit\tkinterFit.exe (plus its supporting files)

from PyInstaller.utils.hooks import collect_all

# pyeq3 discovers its equation modules dynamically, so collect all of it.
# pypdfium2 (PDF graph images) loads its pdfium library at run time.
datas, binaries, hiddenimports = [], [], []
for package in ['pyeq3', 'pypdfium2', 'pypdfium2_raw']:
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

a = Analysis(
    ['tkinterFit.py'],
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
