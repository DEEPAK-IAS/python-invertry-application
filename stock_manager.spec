# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = []
hiddenimports = []

# Collect all PySide2 dependencies
tmp_ret = collect_all('PySide2')
datas    += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Collect SQLAlchemy
tmp_ret = collect_all('sqlalchemy')
datas    += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Collect reportlab
tmp_ret = collect_all('reportlab')
datas    += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Collect PyMuPDF (fitz) — needed for native printing
tmp_ret = collect_all('fitz')
datas    += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

# Collect qtawesome — bundles its own icon font files (Font Awesome /
# Material) which must be shipped or every themed icon in the app will
# be blank in the packaged .exe.
tmp_ret = collect_all('qtawesome')
datas    += tmp_ret[0]
binaries += tmp_ret[1]
hiddenimports += tmp_ret[2]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas + [
        ('ui/themes', 'ui/themes'),       # kept for reference/debugging only —
                                           # the running app builds its stylesheet
                                           # from app/design/tokens.py at runtime
        ('assets/fonts', 'assets/fonts'), # bundled Poppins font files
        ('.env', '.'),                      # include .env if exists
        ('logo.png', '.')
    ],
    hiddenimports=hiddenimports + [
        'pydantic',
        'dotenv',
        'loguru',
        'win32print',
        'win32api',
        'win32ui',
        'win32con',
        'PIL',
        'PIL.Image',
        'PIL.ImageWin',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='StockManager',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # no black terminal window
    icon='icon.ico',        # your app icon (put icon.ico in project root)
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='StockManager',
)