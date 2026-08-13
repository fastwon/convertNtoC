# PyInstaller one-file spec for convertN2C.
#
# Build steps (from repo root):
#   cd frontend && npm install && npm run build && cd ..
#   .\.venv\Scripts\pyinstaller packaging/convertN2C.spec
#
# Output: dist/convertN2C.exe  (single windowed exe)
#
# Notes:
# - The React static build (frontend/dist) is bundled as data at "frontend_dist";
#   app/paths.py resolves it via sys._MEIPASS when frozen.
# - pywebview (Edge WebView2 backend), keyring (Windows Credential Manager), and
#   google-genai load submodules/data dynamically, so we collect_all them to
#   avoid "module not found" at runtime.
from pathlib import Path

from PyInstaller.utils.hooks import collect_all, collect_submodules

ROOT = Path(SPECPATH).resolve().parent  # noqa: F821  (SPECPATH injected by PyInstaller)

datas = [(str(ROOT / "frontend" / "dist"), "frontend_dist")]
binaries = []
hiddenimports = [
    "uvicorn.logging",
    "uvicorn.loops.auto",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan.on",
]

# Packages that pull in code/data dynamically — collect everything so the frozen
# app doesn't hit a missing submodule (pywebview's Edge backend, keyring's Windows
# backend, google-genai's client internals).
for pkg in ("webview", "keyring", "google.genai", "anthropic"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

# keyring picks its backend at runtime via entry points; make sure the Windows
# Credential Manager backend and its win32 shim are present.
hiddenimports += collect_submodules("keyring.backends")
hiddenimports += ["win32ctypes.core"]  # pywin32-ctypes shim keyring uses on Windows

a = Analysis(
    [str(ROOT / "app" / "main.py")],
    pathex=[str(ROOT)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="convertN2C",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # UPX can trip antivirus and corrupt some native DLLs; keep off
    console=False,  # windowed app (no console)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # add a .ico path here later for a custom taskbar icon
)
